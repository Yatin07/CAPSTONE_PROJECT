import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv
from services.llm_service import generate_daily_briefing, answer_assistant_chat, get_llm_info

# ---------------------------------------------------------------------------- #
# Config & Secrets Validation (Fail-Fast)
# ---------------------------------------------------------------------------- #
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError(
        "CRITICAL STARTUP CONFIGURATION ERROR: Neither MONGODB_URI nor MONGO_URI is set. "
        "The application cannot start without a valid database connection string."
    )

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError(
        "CRITICAL STARTUP CONFIGURATION ERROR: JWT_SECRET is not set. "
        "Hardcoded security secrets are prohibited in production."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ALLOW_DEMO_SEED = os.getenv("ALLOW_DEMO_SEED", "false").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------- #
# App & CORS Configuration
# ---------------------------------------------------------------------------- #
app = FastAPI(title="RestockIQ API", version="1.0.0")

raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if raw_origins.strip():
    allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------- #
# Rate Limiting
# ---------------------------------------------------------------------------- #
class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int, action_name: str):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.action_name = action_name
        self.requests = defaultdict(list)

    async def __call__(self, request: Request):
        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "127.0.0.1")
        
        now = time.time()
        window_start = now - self.window_seconds
        
        # Purge timestamps outside sliding window
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self.requests[client_ip][0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {self.action_name}. Limit: {self.max_requests} requests per {self.window_seconds}s. Try again in {retry_after}s.",
                headers={"Retry-After": str(max(1, retry_after))}
            )
            
        self.requests[client_ip].append(now)

login_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60, action_name="authentication")
chat_limiter = InMemoryRateLimiter(max_requests=20, window_seconds=60, action_name="assistant chat")

# ---------------------------------------------------------------------------- #
# DB Connection
# ---------------------------------------------------------------------------- #
client: AsyncIOMotorClient = None
db = None

@app.on_event("startup")
async def startup_db():
    global client, db
    client = AsyncIOMotorClient(
        MONGO_URI,
        server_api=ServerApi("1"),
        serverSelectionTimeoutMS=5000,   # Fail fast, don't block startup
        connectTimeoutMS=5000,
    )
    db = client["restockiq"]
    # Non-blocking: try ping but continue if network blocks port 27017
    try:
        await client.admin.command("ping")
        print("[DB] Connected to MongoDB Atlas successfully.")
        await db.users.create_index("email", unique=True)
        
        # Guarded demo user seeding
        if ALLOW_DEMO_SEED:
            demo_user = await db.users.find_one({"email": "admin@test.com"})
            if not demo_user:
                from bson import ObjectId
                await db.users.insert_one({
                    "_id": str(ObjectId()),
                    "name": "Demo Admin",
                    "email": "admin@test.com",
                    "password_hash": hash_password("123456"),
                    "role": "owner",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                print("[DB] Initialized demo user admin@test.com (ALLOW_DEMO_SEED=true).")
    except Exception as e:
        print(f"[DB] WARNING: Could not reach Atlas on startup ({e}). "
              "Server will start anyway. Fix network/VPN to enable real DB operations.")

@app.on_event("shutdown")
async def shutdown_db():
    client.close()

# ---------------------------------------------------------------------------- #
# Security
# ---------------------------------------------------------------------------- #
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await db.users.find_one({"_id": user_id})
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ---------------------------------------------------------------------------- #
# Pydantic Schemas
# ---------------------------------------------------------------------------- #

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "owner"  # "owner" | "manager"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    role: str

class ItemCreateRequest(BaseModel):
    name: str
    category: str
    unit: str
    currentStock: int
    isPerishable: bool
    price: Optional[float] = None

class ItemResponse(BaseModel):
    id: str
    name: str
    category: str
    unit: str
    currentStock: int
    isPerishable: bool
    price: Optional[float]
    predictedDemand: Optional[int]
    safetyStock: Optional[int]
    description: str
    riskLevel: str
    updatedAt: str

class ItemUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    currentStock: Optional[int] = None
    isPerishable: Optional[bool] = None
    price: Optional[float] = None
    predictedDemand: Optional[int] = None
    safetyStock: Optional[int] = None
    riskLevel: Optional[str] = None

class RestockRequest(BaseModel):
    quantity: Optional[int] = None

class IntradaySaleRequest(BaseModel):
    item_id: str
    quantity: int



# ---------------------------------------------------------------------------- #
# Auth Routes
# ---------------------------------------------------------------------------- #

@app.post("/api/v1/auth/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest):
    if req.email.lower() == "admin@test.com" and not ALLOW_DEMO_SEED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Creation of default demo accounts is restricted in production environments."
        )

    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    from bson import ObjectId
    user_id = str(ObjectId())

    user_doc = {
        "_id": user_id,
        "name": req.name,
        "email": req.email,
        "password_hash": hash_password(req.password),
        "role": req.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user_doc)

    token = create_access_token({"sub": user_id, "role": req.role})
    return TokenResponse(access_token=token, user_id=user_id, name=req.name, role=req.role)


@app.post("/api/v1/auth/login", response_model=TokenResponse, dependencies=[Depends(login_limiter)])
async def login(req: LoginRequest):
    user = await db.users.find_one({"email": req.email})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user["_id"], "role": user["role"]})
    return TokenResponse(
        access_token=token,
        user_id=user["_id"],
        name=user["name"],
        role=user["role"],
    )


# ---------------------------------------------------------------------------- #
# Health / System Status (Non-leaking DB & LLM check)
# ---------------------------------------------------------------------------- #

@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    db_status = "disconnected"
    try:
        if client:
            await client.admin.command("ping")
            db_status = "connected"
    except Exception:
        db_status = "unreachable"

    llm_info = get_llm_info()
    overall_status = "ok" if db_status == "connected" else "degraded"

    return {
        "status": overall_status,
        "database": {
            "status": db_status,
        },
        "llm": {
            "status": "configured" if llm_info.get("configured") else "unconfigured",
            "model": llm_info.get("model"),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------- #
# Items Routes (JWT Protected)
# ---------------------------------------------------------------------------- #

@app.post("/api/v1/items", status_code=201)
async def create_item(req: ItemCreateRequest, current_user=Depends(get_current_user)):
    from bson import ObjectId
    item_id = str(ObjectId())

    item_doc = {
        "_id": item_id,
        "owner_id": current_user["_id"],
        "name": req.name,
        "category": req.category,
        "unit": req.unit,
        "currentStock": req.currentStock,
        "isPerishable": req.isPerishable,
        "price": req.price,
        # ML fields - populated by nightly batch job later
        "predictedDemand": None,
        "safetyStock": None,
        "description": "LLM analysis pending",
        "riskLevel": "normal",
        "salesHistory": [],  # cold-start: triggers TSB engine
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.items.insert_one(item_doc)
    return {"status": "created", "item_id": item_id, "message": f"'{req.name}' added. Routed to cold-start ML engine."}


@app.get("/api/v1/items")
async def get_items(current_user=Depends(get_current_user)):
    cursor = db.items.find({"owner_id": current_user["_id"]})
    items = []
    async for doc in cursor:
        items.append({
            "id": doc["_id"],
            "name": doc["name"],
            "category": doc["category"],
            "unit": doc["unit"],
            "currentStock": doc["currentStock"],
            "isPerishable": doc["isPerishable"],
            "price": doc.get("price"),
            "predictedDemand": doc.get("predictedDemand"),
            "safetyStock": doc.get("safetyStock"),
            "description": doc.get("description", "LLM analysis pending"),
            "riskLevel": doc.get("riskLevel", "normal"),
            "updatedAt": doc.get("updatedAt", ""),
        })
    return {"items": items}


@app.put("/api/v1/items/{item_id}")
async def update_item(item_id: str, req: ItemUpdateRequest, current_user=Depends(get_current_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = {k: v for k, v in req.dict().items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

    await db.items.update_one({"_id": item_id}, {"$set": update_data})
    updated = await db.items.find_one({"_id": item_id})
    return {"status": "updated", "item": {
        "id": updated["_id"],
        "name": updated["name"],
        "category": updated["category"],
        "unit": updated["unit"],
        "currentStock": updated["currentStock"],
        "isPerishable": updated["isPerishable"],
        "price": updated.get("price"),
        "predictedDemand": updated.get("predictedDemand"),
        "safetyStock": updated.get("safetyStock"),
        "riskLevel": updated.get("riskLevel", "normal"),
        "updatedAt": updated.get("updatedAt"),
    }}


@app.delete("/api/v1/items/{item_id}")
async def delete_item(item_id: str, current_user=Depends(get_current_user)):
    res = await db.items.delete_one({"_id": item_id, "owner_id": current_user["_id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.forecasts.delete_many({"item_id": item_id})
    return {"status": "deleted", "item_id": item_id}


@app.post("/api/v1/items/{item_id}/restock")
async def restock_item(item_id: str, req: RestockRequest, current_user=Depends(get_current_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # If quantity not provided, restock by recommended quantity
    if req.quantity is not None and req.quantity > 0:
        qty_to_add = req.quantity
    else:
        pred = item.get("predictedDemand") or 0
        safety = item.get("safetyStock") or 0
        qty_to_add = max(0, pred + safety - item["currentStock"])
        if qty_to_add == 0:
            qty_to_add = safety or 5  # minimum replenishment if already at stock

    new_stock = item["currentStock"] + qty_to_add
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.items.update_one(
        {"_id": item_id},
        {"$set": {"currentStock": new_stock, "updatedAt": now_iso}}
    )
    return {
        "status": "success",
        "message": f"Restocked {qty_to_add} {item['unit']} of {item['name']}.",
        "added": qty_to_add,
        "newStock": new_stock,
    }


# ---------------------------------------------------------------------------- #
# Forecasts — Step 2: The ML Read Layer
# ---------------------------------------------------------------------------- #

@app.get("/api/v1/forecasts/today")
async def get_todays_forecasts(current_user=Depends(get_current_user)):
    cursor = db.items.find({"owner_id": current_user["_id"]})
    items = []
    action_required_count = 0

    async for doc in cursor:
        # Check if pre-computed forecast exists in forecasts collection
        forecast = await db.forecasts.find_one(
            {"item_id": doc["_id"]},
            sort=[("forecast_date", -1)]
        )

        if forecast:
            predicted_demand = forecast.get("predictedDemand", doc.get("predictedDemand") or 15)
            safety_stock = forecast.get("safetyStock", doc.get("safetyStock") or 3)
            description = forecast.get("explanation", doc.get("description", "Demand steady — standard restocking pattern"))
            risk_level = forecast.get("riskLevel", doc.get("riskLevel", "normal"))
            tier = forecast.get("tier", "primary")
        else:
            # Fallback for cold-start / new item (TSB tier)
            predicted_demand = doc.get("predictedDemand") or 15
            safety_stock = doc.get("safetyStock") or 3
            description = doc.get("description") or "Cold-start analysis active — learning sales pace"
            risk_level = doc.get("riskLevel") or "normal"
            tier = "sparse_cold_start" if doc.get("isNew", True) else "primary"

        curr_stock = doc.get("currentStock", 0)
        restock_qty = max(0, predicted_demand + safety_stock - curr_stock)
        denom = max(1, predicted_demand + safety_stock)
        stock_progress = round(min(1.0, max(0.0, curr_stock / denom)), 2)

        if restock_qty > 0:
            action_required_count += 1

        items.append({
            "id": doc["_id"],
            "name": doc["name"],
            "category": doc["category"],
            "unit": doc["unit"],
            "currentStock": curr_stock,
            "isPerishable": doc.get("isPerishable", True),
            "price": doc.get("price"),
            "predictedDemand": predicted_demand,
            "safetyStock": safety_stock,
            "restockQuantity": restock_qty,
            "stockProgress": stock_progress,
            "description": description,
            "confidence_interval": None,  # Locked architectural constraint (point estimates)
            "riskLevel": risk_level,
            "tier": tier,
            "updatedAt": doc.get("updatedAt", datetime.now(timezone.utc).isoformat()),
        })

    total_items = len(items)
    if action_required_count > 0:
        summary = f"{action_required_count} of {total_items} items require restocking today. Cold-start engine active for new stock."
    elif total_items == 0:
        summary = "No inventory items found. Add items to enable AI forecasting."
    else:
        summary = "All inventory levels are optimal for today. Spoilage risk low."

    return {
        "summary": summary,
        "total_items": total_items,
        "action_required_count": action_required_count,
        "items": items,
    }


@app.get("/api/v1/forecasts/{item_id}")
async def get_item_forecast_detail(item_id: str, current_user=Depends(get_current_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    forecast = await db.forecasts.find_one(
        {"item_id": item_id},
        sort=[("forecast_date", -1)]
    )

    predicted_demand = (forecast.get("predictedDemand") if forecast else item.get("predictedDemand")) or 25
    safety_stock = (forecast.get("safetyStock") if forecast else item.get("safetyStock")) or 5
    curr_stock = item.get("currentStock", 0)
    restock_qty = max(0, predicted_demand + safety_stock - curr_stock)
    denom = max(1, predicted_demand + safety_stock)
    stock_progress = round(min(1.0, max(0.0, curr_stock / denom)), 2)

    # Historical 7-day sales and 7-day forecast series for chart
    if forecast and "historical_7d" in forecast and "forecast_7d" in forecast:
        historical_chart = forecast["historical_7d"]
        forecast_chart = forecast["forecast_7d"]
    else:
        # Synthesize realistic 7-day window based on item's base pace
        base = max(5, predicted_demand)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        now = datetime.now(timezone.utc)
        historical_chart = [
            {"day": days[(now.weekday() - 7 + i) % 7], "sales": int(base * (0.85 + (i * 0.04)))}
            for i in range(7)
        ]
        forecast_chart = [
            {"day": days[(now.weekday() + i) % 7], "predicted": int(base * (0.95 + ((i % 3) * 0.05)))}
            for i in range(7)
        ]

    return {
        "id": item["_id"],
        "name": item["name"],
        "category": item["category"],
        "unit": item["unit"],
        "currentStock": curr_stock,
        "isPerishable": item.get("isPerishable", True),
        "price": item.get("price"),
        "predictedDemand": predicted_demand,
        "safetyStock": safety_stock,
        "restockQuantity": restock_qty,
        "stockProgress": stock_progress,
        "confidence_interval": None,  # Point-estimate constraint
        "description": (forecast.get("explanation") if forecast else item.get("description")) or "Demand steady — standard restocking pattern",
        "riskLevel": (forecast.get("riskLevel") if forecast else item.get("riskLevel")) or "normal",
        "historical_chart": historical_chart,
        "forecast_chart": forecast_chart,
        "updatedAt": item.get("updatedAt", now_iso if 'now_iso' in locals() else datetime.now(timezone.utc).isoformat()),
    }


# ---------------------------------------------------------------------------- #
# Waste Action Engine (Step 5)
# ---------------------------------------------------------------------------- #

@app.post("/api/v1/sales/intraday", status_code=201)
async def record_intraday_sale(req: IntradaySaleRequest, current_user=Depends(get_current_user)):
    item = await db.items.find_one({"_id": req.item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    new_intraday = item.get("intradaySales", 0) + req.quantity
    new_stock = max(0, item.get("currentStock", 0) - req.quantity)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Log individual sales event
    await db.intraday_sales.insert_one({
        "item_id": req.item_id,
        "owner_id": current_user["_id"],
        "quantity": req.quantity,
        "timestamp": now_iso,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    })

    # Update item state in Atlas
    await db.items.update_one(
        {"_id": req.item_id},
        {"$set": {"intradaySales": new_intraday, "currentStock": new_stock, "updatedAt": now_iso}}
    )

    return {
        "status": "recorded",
        "item_id": req.item_id,
        "sold": req.quantity,
        "totalIntradaySales": new_intraday,
        "remainingStock": new_stock,
    }


@app.get("/api/v1/waste-alerts")
async def get_waste_alerts(current_user=Depends(get_current_user)):
    cursor = db.items.find({"owner_id": current_user["_id"], "isPerishable": True})
    alerts = []
    
    # Store operates 8:00 AM (8) to 8:00 PM (20)
    now_utc = datetime.now(timezone.utc)
    current_hour = now_utc.hour
    
    # Operational fraction of day elapsed (minimum 25% to allow initial morning pace)
    elapsed_fraction = max(0.25, min(1.0, (current_hour - 8 + 1) / 12.0))

    async for item in cursor:
        if item.get("isDismissed", False):
            continue

        item_id = item["_id"]
        # Fetch latest daily forecast
        forecast = await db.forecasts.find_one({"item_id": item_id}, sort=[("forecast_date", -1)])
        predicted_daily = (forecast.get("predictedDemand") if forecast else item.get("predictedDemand")) or 30
        
        actual_sold = item.get("intradaySales", 0)
        expected_by_now = max(1.0, predicted_daily * elapsed_fraction)
        
        # Calculate sales pace ratio
        sales_pace_ratio = round(actual_sold / expected_by_now, 2)
        
        # Flag items with slow pace (< 70% of expected volume) that still have stock
        curr_stock = item.get("currentStock", 0)
        if sales_pace_ratio < 0.70 and curr_stock > 0:
            clean_name = item["name"].lower()
            if "croissant" in clean_name:
                food_type = "croissant"
            elif any(k in clean_name for k in ["baguette", "bread", "loaf", "sourdough"]):
                food_type = "baguette"
            elif any(k in clean_name for k in ["milk", "dairy"]):
                food_type = "milk"
            elif any(k in clean_name for k in ["quiche", "savory", "lunch"]):
                food_type = "quiche"
            else:
                food_type = "pastry"

            # Strict architectural mapping: static discount based on risk tier
            if sales_pace_ratio < 0.35:
                severity_label = "Critical"
                severity_color = "#D97706"
                discount_pct = 30
                rec_action_text = "Flag for Donation"
                rec_action_color = "#FFB702"
                rec_done_text = "Flagged for Donation"
                prim_action_text = "Flag Item"
                prim_done_text = "Item Flagged"
                layout_style = "sideBySide"
            else:
                severity_label = "Low Pace"
                severity_color = "#B91C1C"
                discount_pct = 20
                rec_action_text = "Suggest 20% Discount"
                rec_action_color = "#8B1E22"
                rec_done_text = "Discount Suggested"
                prim_action_text = "Apply Discount"
                prim_done_text = "Discount Applied"
                layout_style = "stacked"

            pct_int = int(round(sales_pace_ratio * 100))
            sales_text = f"{pct_int}% of expected sales so far\ntoday"

            alerts.append({
                "id": item_id,
                "itemName": item["name"],
                "salesText": sales_text,
                "progress": round(min(1.0, sales_pace_ratio), 2),
                "salesPaceRatio": sales_pace_ratio,
                "expectedSales": round(expected_by_now, 1),
                "actualSold": actual_sold,
                "currentStock": curr_stock,
                "severityLabel": severity_label,
                "severityColor": severity_color,
                "discount_pct": discount_pct,
                "recommendedActionText": rec_action_text,
                "recommendedActionColor": rec_action_color,
                "recommendedDoneText": rec_done_text,
                "isRecommendedActionDone": item.get("isRecommendedActionDone", False),
                "primaryActionText": prim_action_text,
                "primaryDoneText": prim_done_text,
                "isPrimaryActionDone": item.get("isPrimaryActionDone", False),
                "isDismissed": False,
                "layoutStyle": layout_style,
                "foodType": food_type,
            })

    return {"alerts": alerts, "total_alerts": len(alerts)}


@app.post("/api/v1/waste-alerts/{item_id}/apply-discount")
async def apply_discount_action(item_id: str, current_user=Depends(get_current_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Static 20% discount mapping
    current_price = item.get("price") or 5.0
    discounted_price = round(current_price * 0.80, 2)
    now_iso = datetime.now(timezone.utc).isoformat()

    await db.items.update_one(
        {"_id": item_id},
        {"$set": {
            "price": discounted_price,
            "originalPrice": current_price,
            "isPrimaryActionDone": True,
            "discountApplied": True,
            "updatedAt": now_iso,
        }}
    )
    return {
        "status": "success",
        "message": f"Applied 20% discount to {item['name']}. New price: ${discounted_price}",
        "oldPrice": current_price,
        "newPrice": discounted_price,
    }


@app.post("/api/v1/waste-alerts/{item_id}/flag-donation")
async def flag_donation_action(item_id: str, current_user=Depends(get_current_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.items.update_one(
        {"_id": item_id},
        {"$set": {
            "flaggedForDonation": True,
            "isRecommendedActionDone": True,
            "updatedAt": now_iso,
        }}
    )
    return {
        "status": "success",
        "message": f"Item '{item['name']}' has been marked for community donation pickup.",
    }


@app.post("/api/v1/waste-alerts/{item_id}/dismiss")
async def dismiss_alert_action(item_id: str, current_user=Depends(get_current_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await db.items.update_one(
        {"_id": item_id},
        {"$set": {"isDismissed": True}}
    )
    return {"status": "dismissed", "item_id": item_id}


# ---------------------------------------------------------------------------- #
# AI Executive Briefing & Manager Assistant (Google Gemini 1.5/2.5/3.8 Flash)
# ---------------------------------------------------------------------------- #

class AssistantChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Manager operational query (1 to 500 characters)")


@app.get("/api/v1/briefing/today")
async def get_today_executive_briefing(current_user=Depends(get_current_user)):
    """
    Synthesizes an executive daily operational briefing for the on-duty manager
    using Google Gemini. Strictly grounded in verified MongoDB Atlas metrics.
    """
    user_id = current_user["_id"]
    cursor = db.items.find({"owner_id": user_id})
    items = await cursor.to_list(length=100)

    # Fetch alerts for this user
    alerts_resp = await get_waste_alerts(current_user=current_user)
    alerts = alerts_resp.get("alerts", [])

    briefing = generate_daily_briefing(items, alerts)
    return {
        "status": "success",
        "briefing": briefing,
    }


@app.post("/api/v1/assistant/chat", dependencies=[Depends(chat_limiter)])
async def assistant_chat(req: AssistantChatRequest, current_user=Depends(get_current_user)):
    """
    Answers manager queries with RAG grounding from today's inventory state.
    """
    user_id = current_user["_id"]
    cursor = db.items.find({"owner_id": user_id})
    items = await cursor.to_list(length=100)

    alerts_resp = await get_waste_alerts(current_user=current_user)
    alerts = alerts_resp.get("alerts", [])

    result = answer_assistant_chat(req.query, items, alerts)
    return {
        "status": "success",
        "reply": result["reply"],
        "provider": result.get("provider"),
        "model": result.get("model"),
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
