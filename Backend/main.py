import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv

# ---------------------------------------------------------------------------- #
# Config
# ---------------------------------------------------------------------------- #
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("JWT_SECRET", "restockiq-super-secret-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# ---------------------------------------------------------------------------- #
# App
# ---------------------------------------------------------------------------- #
app = FastAPI(title="RestockIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ---------------------------------------------------------------------------- #
# Auth Routes
# ---------------------------------------------------------------------------- #

@app.post("/api/v1/auth/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest):
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


@app.post("/api/v1/auth/login", response_model=TokenResponse)
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
# Health / DB Check
# ---------------------------------------------------------------------------- #

@app.get("/api/v1/health")
async def health_check():
    try:
        await client.admin.command("ping")
        return {"status": "ok", "db": "connected", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"status": "error", "db": "disconnected", "detail": str(e)}


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


# ---------------------------------------------------------------------------- #
# Forecasts (stub — wired in Step 2)
# ---------------------------------------------------------------------------- #

@app.get("/api/v1/forecasts/today")
async def get_todays_forecasts(current_user=Depends(get_current_user)):
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
            "predictedDemand": doc.get("predictedDemand"),
            "safetyStock": doc.get("safetyStock"),
            "restockQuantity": max(0, (doc.get("predictedDemand") or 0) + (doc.get("safetyStock") or 0) - doc["currentStock"]),
            "description": doc.get("description", "LLM analysis pending"),
            "confidence_interval": None,
            "riskLevel": doc.get("riskLevel", "normal"),
            "updatedAt": doc.get("updatedAt", ""),
        })
    return {"summary": "LLM analysis pending", "items": items}


@app.get("/api/v1/waste-alerts")
async def get_waste_alerts(current_user=Depends(get_current_user)):
    # Wired fully in Step 5 (Waste Engine)
    return {"alerts": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
