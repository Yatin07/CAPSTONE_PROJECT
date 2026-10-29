import os
import json
import asyncio
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict, Any, Tuple

from fastapi import FastAPI, HTTPException, Depends, status, Request, Header
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

# ---------------------------------------------------------------------------- #
# App & CORS Configuration
# ---------------------------------------------------------------------------- #
app = FastAPI(title="RestockIQ API", version="1.0.0")

raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if raw_origins.strip() and raw_origins.strip() != "*":
    allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
else:
    allowed_origins = [
        "https://restockiq.com",
        "https://app.restockiq.com",
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

from constants import (
    DEFAULT_FALLBACK_DEMAND,
    DEFAULT_FALLBACK_SAFETY,
    STORE_OPEN_HOUR,
    STORE_CLOSE_HOUR,
    DEFAULT_STORE_TIMEZONE,
)

def get_store_timezone(user: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None):
    tz_str = (user.get("timezone") if user else None) or (item.get("timezone") if item else None) or os.getenv("STORE_TIMEZONE") or DEFAULT_STORE_TIMEZONE
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(tz_str)
    except Exception:
        return timezone.utc

# In-memory simulated clock hours for shadow tenant users: shadow_id -> float
DEMO_SIMULATED_CLOCKS: Dict[str, float] = {}

def get_store_local_now(user: Optional[Dict[str, Any]] = None, item: Optional[Dict[str, Any]] = None) -> datetime:
    tz = get_store_timezone(user, item)
    base_now = datetime.now(tz)
    # Simulated clock hour is honored strictly and exclusively for shadow tenant users
    if user and user.get("role") == "demo_shadow":
        sim_h = user.get("simulated_clock_hour")
        if sim_h is None and "_id" in user and user["_id"] in DEMO_SIMULATED_CLOCKS:
            sim_h = DEMO_SIMULATED_CLOCKS[user["_id"]]
        if sim_h is not None:
            hours = int(sim_h)
            minutes = int(round((float(sim_h) - hours) * 60))
            return base_now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    return base_now

async def rollover_if_new_day(item: dict, user: Optional[dict] = None) -> dict:
    """
    Lazy, idempotent daily state rollover keyed on the store's local calendar date (item.intradayDate).
    Only resets intradaySales, alert flags, and discount prices when intradayDate != today_local.
    Guarantees that nightly batch or mid-day reads never contaminate live counters.
    """
    if not item:
        return item

    now_local = get_store_local_now(user, item)
    today_local_str = now_local.strftime("%Y-%m-%d")

    if item.get("intradayDate") == today_local_str:
        return item

    item_id = item["_id"]
    owner_id = item.get("owner_id")

    # Revert promotional discount to base price if applied
    base_price = item.get("originalPrice") if item.get("discountApplied") else item.get("price")

    update_fields = {
        "intradaySales": 0,
        "intradayDate": today_local_str,
        "isDismissed": False,
        "isPrimaryActionDone": False,
        "isRecommendedActionDone": False,
        "discountApplied": False,
        "bundleApplied": False,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    if base_price is not None and item.get("discountApplied"):
        update_fields["price"] = base_price

    if db is not None:
        try:
            query = {"_id": item_id}
            if owner_id:
                query["owner_id"] = owner_id
            await db.items.update_one(query, {"$set": update_fields})
        except Exception:
            pass

    item.update(update_fields)
    return item

async def rollup_daily_sales(target_date: str, owner_id: Optional[str] = None) -> dict:
    """
    Aggregates db.intraday_sales by date for any past or target day.
    Upserts into db.daily_sales with compound unique index (owner_id, item_id, date).
    Strictly scoped to owner_id when provided, or processes all owners for server jobs.
    100% idempotent and safe to run multiple times.
    """
    if db is None:
        return {"status": "skipped", "reason": "db is None"}

    match_filter: Dict[str, Any] = {"date": target_date}
    if owner_id:
        match_filter["owner_id"] = owner_id

    pipeline = [
        {"$match": match_filter},
        {"$group": {
            "_id": {
                "owner_id": "$owner_id",
                "item_id": "$item_id",
            },
            "total_units": {"$sum": "$quantity"},
        }}
    ]
    cursor = db.intraday_sales.aggregate(pipeline)
    count = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    async for doc in cursor:
        doc_owner_id = doc["_id"]["owner_id"]
        item_id = doc["_id"]["item_id"]
        units = doc["total_units"]
        await db.daily_sales.update_one(
            {"owner_id": doc_owner_id, "item_id": item_id, "date": target_date},
            {"$set": {
                "units": units,
                "source": "rollup",
                "updatedAt": now_iso,
            }},
            upsert=True
        )
        count += 1
    return {"status": "success", "date": target_date, "records_rolled_up": count, "scoped_owner": owner_id or "all"}


# ---------------------------------------------------------------------------- #
# Rate Limiting
# ---------------------------------------------------------------------------- #
class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int, action_name: str):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.action_name = action_name
        self.requests = defaultdict(list)

    def get_client_ip(self, request: Request) -> str:
        """Extracts client IP behind trusted reverse proxies via X-Forwarded-For.
        
        The right-most IP in the X-Forwarded-For chain is appended by the nearest
        trusted reverse proxy (e.g. Render edge router), ensuring that clients cannot
        bypass rate limits by injecting arbitrary fake spoofed IPs on the left.
        """
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ips = [ip.strip() for ip in forwarded_for.split(",") if ip.strip()]
            if ips:
                return ips[-1]
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    async def __call__(self, request: Request):
        client_ip = self.get_client_ip(request)
        
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
register_limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60, action_name="registration")
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
    db_name = os.getenv("MONGODB_DB", "restockiq")
    db = client[db_name]
    # Non-blocking: try ping but continue if network blocks port 27017
    try:
        await client.admin.command("ping")
        print("[DB] Connected to MongoDB Atlas successfully.")
        await db.users.create_index("email", unique=True)
        await db.daily_sales.create_index([("owner_id", 1), ("item_id", 1), ("date", 1)], unique=True)
        await db.daily_stock.create_index([("owner_id", 1), ("item_id", 1), ("date", 1)], unique=True)
        await db.items.create_index([("owner_id", 1), ("name_lower", 1)], unique=True)
        # TTL indexes on expiresAt for shadow tenant auto-expiry
        await db.users.create_index("expiresAt", expireAfterSeconds=0)
        await db.items.create_index("expiresAt", expireAfterSeconds=0)
        await db.daily_sales.create_index("expiresAt", expireAfterSeconds=0)
        await db.daily_stock.create_index("expiresAt", expireAfterSeconds=0)
        await db.intraday_sales.create_index("expiresAt", expireAfterSeconds=0)
        await db.forecasts.create_index("expiresAt", expireAfterSeconds=0)
        await db.waste_alerts.create_index("expiresAt", expireAfterSeconds=0)
    except Exception as e:
        print(f"[DB] WARNING: Could not reach Atlas on startup ({e}). "
              "Falling back to local mongomock_motor to preserve database operations.")
        try:
            import mongomock_motor
            client = mongomock_motor.AsyncMongoMockClient()
            db = client[db_name]
            print("[DB] Local in-memory mock client activated successfully.")
        except Exception as mock_err:
            print(f"[DB] Could not initialize local fallback: {mock_err}")

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


# Rate limit tracker for demo sandbox starts: user_id -> list of timestamps (max 5/hour)
DEMO_START_RATE_LIMITS: Dict[str, List[float]] = defaultdict(list)

async def get_workspace_user(request: Request, current_user=Depends(get_current_user)) -> dict:
    """
    Workspace scoping dependency.
    If the client passes X-Workspace: demo, returns the caller's shadow tenant user.
    Otherwise, returns current_user unaltered.
    Guarantees mathematically isolated multi-tenancy between sandbox and live operations.
    """
    workspace_header = request.headers.get("X-Workspace", "").strip().lower()
    if workspace_header == "demo":
        shadow_id = f"shadow_{current_user['_id']}"
        shadow_user = await db.users.find_one({"_id": shadow_id, "role": "demo_shadow"})
        if not shadow_user:
            # Fallback in-memory representation if querying before demo/start seeded
            shadow_user = {
                "_id": shadow_id,
                "name": f"Demo Store ({current_user.get('name', 'Owner')})",
                "email": f"demo_{current_user.get('email', 'user')}",
                "role": "demo_shadow",
                "shadow_of": current_user["_id"],
                "store_name": "Sample Artisan Bakery",
                "timezone": "Asia/Kolkata",
                "opening_hour": 8.0,
                "closing_hour": 20.0,
                "currency": "₹",
                "onboarding_completed": True,
                "replayed_dataset": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expiresAt": datetime.now(timezone.utc) + timedelta(hours=2),
            }
        
        # Attach in-memory simulated clock if set
        if shadow_id in DEMO_SIMULATED_CLOCKS:
            shadow_user["simulated_clock_hour"] = DEMO_SIMULATED_CLOCKS[shadow_id]
        
        return shadow_user

    return current_user


# ---------------------------------------------------------------------------- #
# Pydantic Schemas
# ---------------------------------------------------------------------------- #

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Optional[str] = None  # Ignored; server sets role to 'owner' strictly

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    role: str

class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    store_name: str
    timezone: str
    opening_hour: float
    closing_hour: float
    currency: str
    onboarding_completed: bool
    replayed_dataset: Optional[bool] = False
    created_at: str

class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    store_name: Optional[str] = None
    timezone: Optional[str] = None
    opening_hour: Optional[float] = None
    closing_hour: Optional[float] = None
    currency: Optional[str] = None
    onboarding_completed: Optional[bool] = None

class ItemCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    category: str
    unit: str = "Units"
    currentStock: int = Field(0, ge=0)
    isPerishable: bool = False
    price: Optional[float] = Field(None, ge=0)
    shelfLifeDays: Optional[int] = Field(None, ge=1)

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
    replayed_dataset: Optional[bool] = False
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
    shelfLifeDays: Optional[int] = None

class RestockRequest(BaseModel):
    quantity: Optional[int] = None

class IntradaySaleRequest(BaseModel):
    item_id: str
    quantity: int

class ClosingCountItem(BaseModel):
    item_id: str
    units_left: int = Field(..., ge=0)

class ClosingCountRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD
    counts: List[ClosingCountItem]

class MiddayCountItem(BaseModel):
    item_id: str
    remaining: int = Field(..., ge=0)

class MiddayCountRequest(BaseModel):
    counts: List[MiddayCountItem]

class ApplyBundleRequest(BaseModel):
    partner_item_id: Optional[str] = None
    bundle_discount_pct: float = 20.0

# ---------------------------------------------------------------------------- #
# Auth & User Profile Routes
# ---------------------------------------------------------------------------- #

@app.post("/api/v1/auth/register", response_model=TokenResponse, status_code=201, dependencies=[Depends(register_limiter)])
async def register(req: RegisterRequest):
    normalized_email = req.email.strip().lower()

    existing = await db.users.find_one({"email": normalized_email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    from bson import ObjectId
    user_id = str(ObjectId())

    # Role strictly assigned by server to prevent client privilege escalation
    server_assigned_role = "owner"

    user_doc = {
        "_id": user_id,
        "name": req.name.strip(),
        "email": normalized_email,
        "password_hash": hash_password(req.password),
        "role": server_assigned_role,
        "store_name": f"{req.name.strip()}'s Store",
        "timezone": os.getenv("STORE_TIMEZONE", DEFAULT_STORE_TIMEZONE),
        "opening_hour": STORE_OPEN_HOUR,
        "closing_hour": STORE_CLOSE_HOUR,
        "currency": "₹",
        "onboarding_completed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user_doc)

    token = create_access_token({"sub": user_id, "role": server_assigned_role})
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        name=req.name.strip(),
        role=server_assigned_role,
    )


# In-memory account lockout tracker: {normalized_email: {"failed_count": int, "locked_until": float}}
ACCOUNT_LOCKOUTS: Dict[str, Dict[str, Any]] = {}
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 15 * 60  # 15 minutes


@app.post("/api/v1/auth/login", response_model=TokenResponse, dependencies=[Depends(login_limiter)])
async def login(req: LoginRequest):
    normalized_email = req.email.strip().lower()
    now_ts = time.time()

    lockout_record = ACCOUNT_LOCKOUTS.get(normalized_email)
    if lockout_record and lockout_record.get("locked_until", 0) > now_ts:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Account is temporarily locked. Please try again later."
        )

    user = await db.users.find_one({"email": normalized_email})
    is_valid = user and verify_password(req.password, user["password_hash"])

    if not is_valid:
        if not lockout_record:
            lockout_record = {"failed_count": 0, "locked_until": 0}
            ACCOUNT_LOCKOUTS[normalized_email] = lockout_record

        lockout_record["failed_count"] += 1
        if lockout_record["failed_count"] >= MAX_FAILED_LOGIN_ATTEMPTS:
            lockout_record["locked_until"] = now_ts + LOCKOUT_DURATION_SECONDS
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password. Account is temporarily locked. Please try again later."
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Clear lockout tracking upon valid credentials
    if normalized_email in ACCOUNT_LOCKOUTS:
        del ACCOUNT_LOCKOUTS[normalized_email]

    token = create_access_token({"sub": user["_id"], "role": user.get("role", "owner")})
    return TokenResponse(
        access_token=token,
        user_id=user["_id"],
        name=user["name"],
        role=user.get("role", "owner"),
    )


@app.get("/api/v1/me", response_model=UserProfileResponse)
async def get_my_profile(current_user=Depends(get_workspace_user)):
    return UserProfileResponse(
        id=current_user["_id"],
        name=current_user.get("name", ""),
        email=current_user.get("email", ""),
        role=current_user.get("role", "owner"),
        store_name=current_user.get("store_name", "My Store"),
        timezone=current_user.get("timezone", os.getenv("STORE_TIMEZONE", DEFAULT_STORE_TIMEZONE)),
        opening_hour=float(current_user.get("opening_hour", STORE_OPEN_HOUR)),
        closing_hour=float(current_user.get("closing_hour", STORE_CLOSE_HOUR)),
        currency=current_user.get("currency", "₹"),
        onboarding_completed=bool(current_user.get("onboarding_completed", False)),
        replayed_dataset=bool(current_user.get("replayed_dataset", False)),
        created_at=current_user.get("created_at", ""),
    )


@app.patch("/api/v1/me", response_model=UserProfileResponse)
async def update_my_profile(req: UserProfileUpdateRequest, current_user=Depends(get_workspace_user)):
    update_data = {}
    if req.name is not None:
        update_data["name"] = req.name.strip()
    if req.store_name is not None:
        update_data["store_name"] = req.store_name.strip()
    if req.currency is not None:
        update_data["currency"] = req.currency.strip()
    if req.onboarding_completed is not None:
        update_data["onboarding_completed"] = req.onboarding_completed

    if req.timezone is not None:
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(req.timezone.strip())
            update_data["timezone"] = req.timezone.strip()
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid IANA timezone: '{req.timezone}'")

    op_h = req.opening_hour if req.opening_hour is not None else current_user.get("opening_hour", STORE_OPEN_HOUR)
    cl_h = req.closing_hour if req.closing_hour is not None else current_user.get("closing_hour", STORE_CLOSE_HOUR)
    if op_h >= cl_h:
        raise HTTPException(status_code=400, detail="opening_hour must be strictly less than closing_hour")
    if req.opening_hour is not None:
        update_data["opening_hour"] = req.opening_hour
    if req.closing_hour is not None:
        update_data["closing_hour"] = req.closing_hour

    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.users.update_one({"_id": current_user["_id"]}, {"$set": update_data})

    fresh_user = await db.users.find_one({"_id": current_user["_id"]})
    return UserProfileResponse(
        id=fresh_user["_id"],
        name=fresh_user.get("name", ""),
        email=fresh_user.get("email", ""),
        role=fresh_user.get("role", "owner"),
        store_name=fresh_user.get("store_name", "My Store"),
        timezone=fresh_user.get("timezone", os.getenv("STORE_TIMEZONE", DEFAULT_STORE_TIMEZONE)),
        opening_hour=float(fresh_user.get("opening_hour", STORE_OPEN_HOUR)),
        closing_hour=float(fresh_user.get("closing_hour", STORE_CLOSE_HOUR)),
        currency=fresh_user.get("currency", "₹"),
        onboarding_completed=bool(fresh_user.get("onboarding_completed", False)),
        created_at=fresh_user.get("created_at", ""),
    )


# ---------------------------------------------------------------------------- #
# Health & Diagnostics
# ---------------------------------------------------------------------------- #

@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    db_connected = False
    counts = {"users": 0, "items": 0, "forecasts": 0, "daily_stock": 0}
    last_forecast_time = None

    if db is not None:
        try:
            if client:
                await client.admin.command("ping")
                db_connected = True
                counts["users"] = await db.users.count_documents({})
                counts["items"] = await db.items.count_documents({})
                counts["forecasts"] = await db.forecasts.count_documents({})
                counts["daily_stock"] = await db.daily_stock.count_documents({})
                latest_fc = await db.forecasts.find_one({}, sort=[("createdAt", -1)])
                if latest_fc:
                    last_forecast_time = latest_fc.get("createdAt") or latest_fc.get("forecast_date")
        except Exception:
            db_connected = False

    commit_sha = os.getenv("RENDER_GIT_COMMIT", os.getenv("GIT_COMMIT", "74ccc0a"))

    return {
        "status": "ok" if db_connected else "degraded",
        "database": "connected" if db_connected else "disconnected",
        "last_forecast_time": last_forecast_time,
        "counts": counts,
        "RENDER_GIT_COMMIT": commit_sha,
        "store_timezone": os.getenv("STORE_TIMEZONE", DEFAULT_STORE_TIMEZONE),
        "llm_configured": get_llm_info()["configured"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------- #
# Items Routes (JWT Protected)
# ---------------------------------------------------------------------------- #

ALLOWED_CATEGORIES = ["Bakery", "Beverage", "Food", "Dessert", "Snack", "Other"]

@app.post("/api/v1/items", status_code=201)
async def create_item(req: ItemCreateRequest, current_user=Depends(get_workspace_user)):
    name_stripped = req.name.strip()
    name_lower = name_stripped.lower()

    # Enforce unique (owner_id, name_lower)
    existing = await db.items.find_one({"owner_id": current_user["_id"], "name_lower": name_lower})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An item named '{name_stripped}' already exists in your store catalog."
        )

    clean_cat = req.category.strip().title()
    matched_cat = next((c for c in ALLOWED_CATEGORIES if c.lower() == clean_cat.lower()), "Other")

    from bson import ObjectId
    item_id = str(ObjectId())

    # Cold-start category prior lookup (Pure Python, Step 1e)
    from constants import CATEGORY_PRIORS
    prior = CATEGORY_PRIORS.get(matched_cat, CATEGORY_PRIORS["Other"])
    predicted_demand = prior["predictedDemand"]
    safety_stock = prior["safetyStock"]
    explanation = f"Cold-start initial forecast based on {matched_cat} category prior ({predicted_demand} units/day)."

    item_doc = {
        "_id": item_id,
        "owner_id": current_user["_id"],
        "name": name_stripped,
        "name_lower": name_lower,
        "category": matched_cat,
        "unit": req.unit.strip(),
        "currentStock": req.currentStock,
        "isPerishable": req.isPerishable,
        "price": req.price,
        "shelfLifeDays": req.shelfLifeDays,
        "predictedDemand": predicted_demand,
        "safetyStock": safety_stock,
        "description": explanation,
        "riskLevel": "normal",
        "tier": "Learning",
        "salesHistory": [],  # cold-start: initial state
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.items.insert_one(item_doc)

    today_str = get_store_local_now(current_user).strftime("%Y-%m-%d")
    forecast_doc = {
        "_id": str(ObjectId()),
        "item_id": item_id,
        "owner_id": current_user["_id"],
        "forecast_date": today_str,
        "predictedDemand": predicted_demand,
        "safetyStock": safety_stock,
        "explanation": explanation,
        "tier": "Learning",
        "riskLevel": "normal",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.forecasts.insert_one(forecast_doc)

    return {
        "status": "created",
        "item_id": item_id,
        "message": f"'{name_stripped}' added. Immediate cold-start forecast initialized from {matched_cat} category prior.",
        "forecast": {
            "predictedDemand": predicted_demand,
            "safetyStock": safety_stock,
            "tier": "Learning",
            "explanation": explanation,
        },
        "item": {
            "id": item_id,
            "name": name_stripped,
            "category": matched_cat,
            "unit": req.unit.strip(),
            "currentStock": req.currentStock,
            "isPerishable": req.isPerishable,
            "price": req.price,
            "predictedDemand": predicted_demand,
            "safetyStock": safety_stock,
            "tier": "Learning",
            "description": explanation,
        }
    }


@app.get("/api/v1/items")
async def get_items(current_user=Depends(get_workspace_user)):
    cursor = db.items.find({"owner_id": current_user["_id"]})
    items = []
    async for doc in cursor:
        doc = await rollover_if_new_day(doc, current_user)
        items.append({
            "id": doc["_id"],
            "name": doc["name"],
            "category": doc["category"],
            "unit": doc["unit"],
            "currentStock": doc["currentStock"],
            "isPerishable": doc["isPerishable"],
            "price": doc.get("price"),
            "shelfLifeDays": doc.get("shelfLifeDays"),
            "predictedDemand": doc.get("predictedDemand"),
            "safetyStock": doc.get("safetyStock"),
            "description": doc.get("description", "LLM analysis pending"),
            "riskLevel": doc.get("riskLevel", "normal"),
            "replayed_dataset": bool(doc.get("replayed_dataset", False)),
            "updatedAt": doc.get("updatedAt", ""),
        })
    return {"items": items}


@app.put("/api/v1/items/{item_id}")
async def update_item(item_id: str, req: ItemUpdateRequest, current_user=Depends(get_workspace_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = {k: v for k, v in req.model_dump().items() if v is not None}

    if req.name is not None:
        name_stripped = req.name.strip()
        name_lower = name_stripped.lower()
        existing = await db.items.find_one({
            "owner_id": current_user["_id"],
            "name_lower": name_lower,
            "_id": {"$ne": item_id}
        })
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An item named '{name_stripped}' already exists in your store catalog."
            )
        update_data["name"] = name_stripped
        update_data["name_lower"] = name_lower

    if req.category is not None:
        clean_cat = req.category.strip().title()
        matched_cat = next((c for c in ALLOWED_CATEGORIES if c.lower() == clean_cat.lower()), "Other")
        update_data["category"] = matched_cat

    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

    await db.items.update_one({"_id": item_id, "owner_id": current_user["_id"]}, {"$set": update_data})
    updated = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    return {"status": "updated", "item": {
        "id": updated["_id"],
        "name": updated["name"],
        "category": updated["category"],
        "unit": updated["unit"],
        "currentStock": updated["currentStock"],
        "isPerishable": updated["isPerishable"],
        "price": updated.get("price"),
        "shelfLifeDays": updated.get("shelfLifeDays"),
        "predictedDemand": updated.get("predictedDemand"),
        "safetyStock": updated.get("safetyStock"),
        "riskLevel": updated.get("riskLevel", "normal"),
        "updatedAt": updated.get("updatedAt"),
    }}


@app.delete("/api/v1/items/{item_id}")
async def delete_item(item_id: str, current_user=Depends(get_workspace_user)):
    res = await db.items.delete_one({"_id": item_id, "owner_id": current_user["_id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.forecasts.delete_many({"item_id": item_id, "owner_id": current_user["_id"]})
    return {"status": "deleted", "item_id": item_id}


@app.post("/api/v1/items/{item_id}/restock")
async def restock_item(item_id: str, req: RestockRequest, current_user=Depends(get_workspace_user)):
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
        {"_id": item_id, "owner_id": current_user["_id"]},
        {"$set": {"currentStock": new_stock, "updatedAt": now_iso}}
    )

    # Track produced/restocked quantity in daily_stock for store-local today
    now_local = get_store_local_now(current_user, item)
    today_local = now_local.strftime("%Y-%m-%d")
    await db.daily_stock.update_one(
        {"owner_id": current_user["_id"], "item_id": item_id, "date": today_local},
        {
            "$inc": {"producedOrRestocked": qty_to_add},
            "$setOnInsert": {
                "openingStock": item["currentStock"],
                "status": "open",
                "soldOut": False,
                "createdAt": now_iso,
            },
            "$set": {
                "updatedAt": now_iso,
            }
        },
        upsert=True
    )

    return {
        "status": "success",
        "message": f"Restocked {qty_to_add} {item.get('unit', 'units')} of {item.get('name', 'item')}.",
        "added": qty_to_add,
        "newStock": new_stock,
    }


# ---------------------------------------------------------------------------- #
# Waste Decision Engine & Coherence Checking (Step 5 & Coherence Rule)
# ---------------------------------------------------------------------------- #

def evaluate_waste_alert_tier(is_perishable: bool, is_dismissed: bool, curr_stock: int, actual_sold: float, expected_by_now: float):
    """
    Deterministic decision engine for intraday waste risk classification.
    Evaluates:
      1. isPerishable == True (non-perishables ignored)
      2. isDismissed == False (dismissed items skipped)
      3. curr_stock > 0 (out of stock items produce no waste alert)
      4. sales_pace_ratio = round(actual_sold / expected_by_now, 2)
         - pace >= 0.70: Normal pace (No Alert)
         - 0.35 <= pace < 0.70: Low Pace (10% discount suggested)
         - pace < 0.35: Critical (20% discount + partner combo bundle suggested)
    """
    if not is_perishable or is_dismissed:
        return None
    if curr_stock <= 0:
        return None
    if expected_by_now <= 0:
        expected_by_now = 1.0

    sales_pace_ratio = round(actual_sold / expected_by_now, 2)
    if sales_pace_ratio >= 0.70:
        return None

    if sales_pace_ratio < 0.35:
        return {
            "severityLabel": "Critical",
            "severityColor": "#D97706",
            "discount_pct": 20,
            "recommendedActionText": "Apply 20% Bundle",
            "recommendedActionColor": "#FFB702",
            "recommendedDoneText": "Bundle Applied",
            "primaryActionText": "Apply Bundle",
            "primaryDoneText": "Bundle Active",
            "layoutStyle": "sideBySide",
            "salesPaceRatio": sales_pace_ratio,
        }
    else:
        return {
            "severityLabel": "Low Pace",
            "severityColor": "#B91C1C",
            "discount_pct": 10,
            "recommendedActionText": "Suggest 10% Discount",
            "recommendedActionColor": "#8B1E22",
            "recommendedDoneText": "Discount Suggested",
            "primaryActionText": "Apply Discount",
            "primaryDoneText": "Discount Applied",
            "layoutStyle": "stacked",
            "salesPaceRatio": sales_pace_ratio,
        }


def check_item_waste_alert_sync(doc: dict, current_user: dict, predicted_demand: int, curr_stock: int):
    """
    Evaluates whether an item currently has an active Low or Critical waste alert.
    Returns (has_alert, alert_label).
    """
    if doc.get("isPerishable", False) and not doc.get("isDismissed", False):
        try:
            now_local = get_store_local_now(current_user)
            current_hour = now_local.hour + (now_local.minute / 60.0)
            open_hour = float(current_user.get("opening_hour", STORE_OPEN_HOUR))
            close_hour = float(current_user.get("closing_hour", STORE_CLOSE_HOUR))
            if open_hour <= current_hour < close_hour:
                total_hours = max(1.0, close_hour - open_hour)
                elapsed_fraction = (current_hour - open_hour) / total_hours
                actual_sold = doc.get("intradaySales", 0)
                expected_by_now = max(1.0, predicted_demand * elapsed_fraction)
                tier = evaluate_waste_alert_tier(
                    is_perishable=True,
                    is_dismissed=False,
                    curr_stock=curr_stock,
                    actual_sold=actual_sold,
                    expected_by_now=expected_by_now,
                )
                if tier is not None:
                    return True, tier.get("severityLabel", "Waste Risk")
        except Exception:
            pass

    # Explicit alert indicators from mock, request, or prior classification
    if doc.get("activeAlert") or doc.get("hasWasteAlert"):
        return True, doc.get("alertSeverity") or "Waste Risk"
    if str(doc.get("riskLevel", "")).lower() in ["critical", "low pace", "waste risk"]:
        return True, "Waste Risk"

    return False, None


# ---------------------------------------------------------------------------- #
# Forecasts — Step 2: The ML Read Layer
# ---------------------------------------------------------------------------- #

@app.get("/api/v1/forecasts/today")
async def get_todays_forecasts(current_user=Depends(get_workspace_user)):
    cursor = db.items.find({"owner_id": current_user["_id"]})
    items = []
    action_required_count = 0

    async for doc in cursor:
        doc = await rollover_if_new_day(doc, current_user)
        # Check if pre-computed forecast exists in forecasts collection
        forecast = await db.forecasts.find_one(
            {"item_id": doc["_id"], "owner_id": current_user["_id"]},
            sort=[("forecast_date", -1)]
        )

        if forecast:
            predicted_demand = forecast.get("predictedDemand", doc.get("predictedDemand") or DEFAULT_FALLBACK_DEMAND)
            safety_stock = forecast.get("safetyStock", doc.get("safetyStock") or DEFAULT_FALLBACK_SAFETY)
            description = forecast.get("explanation", doc.get("description", "Demand steady — standard restocking pattern"))
            risk_level = forecast.get("riskLevel", doc.get("riskLevel", "normal"))
            tier = forecast.get("tier", "primary")
        else:
            # Fallback for cold-start / new item (TSB tier)
            predicted_demand = doc.get("predictedDemand") or DEFAULT_FALLBACK_DEMAND
            safety_stock = doc.get("safetyStock") or DEFAULT_FALLBACK_SAFETY
            description = doc.get("description") or "Cold-start analysis active — learning sales pace"
            risk_level = doc.get("riskLevel") or "normal"
            tier = "sparse_cold_start" if doc.get("isNew", True) else "primary"

        curr_stock = doc.get("currentStock", 0)
        restock_qty = max(0, predicted_demand + safety_stock - curr_stock)

        # COHERENCE ENFORCEMENT: If item has active waste alert, restock held to 0
        has_waste_alert, alert_label = check_item_waste_alert_sync(doc, current_user, predicted_demand, curr_stock)
        if has_waste_alert:
            restock_qty = 0
            description = f"Restock held to 0: {alert_label} waste alert active (waste mitigation priority)."

        denom = max(1, predicted_demand + safety_stock)
        stock_progress = round(min(1.0, max(0.0, curr_stock / denom)), 2)

        if restock_qty > 0:
            action_required_count += 1

        days_of_data = await db.daily_sales.count_documents({
            "owner_id": current_user["_id"],
            "item_id": doc["_id"],
            "status": "completed",
        })
        if days_of_data < 7:
            maturity = "Learning"
            maturity_label = f"Learning ({days_of_data}/7 days)"
        elif days_of_data < 28:
            maturity = "Improving"
            maturity_label = f"Improving ({days_of_data}/28 days)"
        else:
            maturity = "Mature"
            maturity_label = f"Mature ({days_of_data} days)"

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
            "hasWasteAlert": has_waste_alert,
            "stockProgress": stock_progress,
            "daysOfData": days_of_data,
            "maturity": maturity,
            "maturityLabel": maturity_label,
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
async def get_item_forecast_detail(item_id: str, current_user=Depends(get_workspace_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = await rollover_if_new_day(item, current_user)

    forecast = await db.forecasts.find_one(
        {"item_id": item_id, "owner_id": current_user["_id"]},
        sort=[("forecast_date", -1)]
    )

    predicted_demand = (forecast.get("predictedDemand") if forecast else item.get("predictedDemand")) or DEFAULT_FALLBACK_DEMAND
    safety_stock = (forecast.get("safetyStock") if forecast else item.get("safetyStock")) or DEFAULT_FALLBACK_SAFETY
    curr_stock = item.get("currentStock", 0)
    restock_qty = max(0, predicted_demand + safety_stock - curr_stock)

    description = (forecast.get("explanation") if forecast else item.get("description")) or "Demand steady — standard restocking pattern"

    # COHERENCE ENFORCEMENT: If item has active waste alert, restock held to 0
    has_waste_alert, alert_label = check_item_waste_alert_sync(item, current_user, predicted_demand, curr_stock)
    if has_waste_alert:
        restock_qty = 0
        description = f"Restock held to 0: {alert_label} waste alert active (waste mitigation priority)."

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

    days_of_data = await db.daily_sales.count_documents({
        "owner_id": current_user["_id"],
        "item_id": item_id,
        "status": "completed",
    })
    if days_of_data < 7:
        maturity = "Learning"
        maturity_label = f"Learning ({days_of_data}/7 days)"
    elif days_of_data < 28:
        maturity = "Improving"
        maturity_label = f"Improving ({days_of_data}/28 days)"
    else:
        maturity = "Mature"
        maturity_label = f"Mature ({days_of_data} days)"

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
        "hasWasteAlert": has_waste_alert,
        "stockProgress": stock_progress,
        "daysOfData": days_of_data,
        "maturity": maturity,
        "maturityLabel": maturity_label,
        "confidence_interval": None,  # Point-estimate constraint
        "description": description,
        "riskLevel": (forecast.get("riskLevel") if forecast else item.get("riskLevel")) or "normal",
        "historical_chart": historical_chart,
        "forecast_chart": forecast_chart,
        "updatedAt": item.get("updatedAt", datetime.now(timezone.utc).isoformat()),
    }


# ---------------------------------------------------------------------------- #
# Daily Operations & Stock Routine (Closing Count, Midday Count, Review)
# ---------------------------------------------------------------------------- #

@app.post("/api/v1/closing-count")
async def record_closing_count(req: ClosingCountRequest, current_user=Depends(get_workspace_user)):
    now_local = get_store_local_now(current_user)
    today_str = now_local.strftime("%Y-%m-%d")
    yesterday_str = (now_local.date() - timedelta(days=1)).strftime("%Y-%m-%d")

    target_date = req.date.strip() if req.date else today_str
    if target_date not in [today_str, yesterday_str]:
        raise HTTPException(
            status_code=400,
            detail=f"Closing count can only be recorded for today ({today_str}) or yesterday ({yesterday_str}) in store timezone."
        )

    from datetime import date as dt_date
    target_dt = dt_date.fromisoformat(target_date)
    next_date_str = (target_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    prev_date_str = (target_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat()

    processed_items = []

    for entry in req.counts:
        item = await db.items.find_one({"_id": entry.item_id, "owner_id": current_user["_id"]})
        if not item:
            raise HTTPException(status_code=404, detail=f"Item '{entry.item_id}' not found.")

        # Find existing daily_stock for target_date
        stock_doc = await db.daily_stock.find_one({
            "owner_id": current_user["_id"],
            "item_id": entry.item_id,
            "date": target_date
        })

        if stock_doc and "openingStock" in stock_doc and stock_doc["openingStock"] is not None:
            opening = stock_doc["openingStock"]
            produced = stock_doc.get("producedOrRestocked", 0)
        else:
            # Check previous day's closing count
            prev_stock = await db.daily_stock.find_one({
                "owner_id": current_user["_id"],
                "item_id": entry.item_id,
                "date": prev_date_str
            })
            if prev_stock and prev_stock.get("status") == "closed":
                if item.get("isPerishable", True):
                    opening = 0
                else:
                    opening = prev_stock.get("closingCount", item.get("currentStock", 0))
            else:
                opening = item.get("currentStock", 0) + item.get("intradaySales", 0)
            produced = stock_doc.get("producedOrRestocked", 0) if stock_doc else 0

        available = opening + produced
        if entry.units_left > available:
            raise HTTPException(
                status_code=400,
                detail=f"Item '{item['name']}': units_left ({entry.units_left}) cannot exceed available stock ({available} = opening {opening} + produced {produced})."
            )

        sold_units = available - entry.units_left
        is_perish = item.get("isPerishable", True)
        waste_units = entry.units_left if is_perish else 0
        sold_out = (entry.units_left == 0)

        # Upsert daily_stock for target_date idempotently
        await db.daily_stock.update_one(
            {"owner_id": current_user["_id"], "item_id": entry.item_id, "date": target_date},
            {"$set": {
                "openingStock": opening,
                "producedOrRestocked": produced,
                "closingCount": entry.units_left,
                "soldUnits": sold_units,
                "wasteUnits": waste_units,
                "status": "closed",
                "soldOut": sold_out,
                "source": "closing_count",
                "updatedAt": now_iso,
            },
            "$setOnInsert": {
                "createdAt": now_iso,
            }},
            upsert=True
        )

        # Upsert derived daily_sales record idempotently
        await db.daily_sales.update_one(
            {"owner_id": current_user["_id"], "item_id": entry.item_id, "date": target_date},
            {"$set": {
                "sales": sold_units,
                "source": "closing_count",
                "status": "completed",
                "updatedAt": now_iso,
            },
            "$setOnInsert": {
                "createdAt": now_iso,
            }},
            upsert=True
        )

        # Initialize/update next day's opening stock in daily_stock
        next_opening = 0 if is_perish else entry.units_left
        await db.daily_stock.update_one(
            {"owner_id": current_user["_id"], "item_id": entry.item_id, "date": next_date_str},
            {"$set": {
                "openingStock": next_opening,
                "updatedAt": now_iso,
            },
            "$setOnInsert": {
                "producedOrRestocked": 0,
                "status": "open",
                "soldOut": False,
                "source": "rollover",
                "createdAt": now_iso,
            }},
            upsert=True
        )

        # Update item's currentStock in items collection:
        # Perishable leftovers are recorded as waste and next opening stock = 0; non-perishable carries over
        new_curr_stock = 0 if is_perish else entry.units_left
        await db.items.update_one(
            {"_id": entry.item_id, "owner_id": current_user["_id"]},
            {"$set": {
                "currentStock": new_curr_stock,
                "intradaySales": 0,
                "intradayDate": next_date_str if target_date == today_str else item.get("intradayDate", today_str),
                "isDismissed": False,
                "isPrimaryActionDone": False,
                "isRecommendedActionDone": False,
                "discountApplied": False,
                "bundleApplied": False,
                "updatedAt": now_iso,
            }}
        )

        processed_items.append({
            "item_id": entry.item_id,
            "name": item["name"],
            "openingStock": opening,
            "producedOrRestocked": produced,
            "availableStock": available,
            "closingCount": entry.units_left,
            "soldUnits": sold_units,
            "wasteUnits": waste_units,
            "isPerishable": is_perish,
            "nextOpeningStock": next_opening,
        })

    return {
        "status": "success",
        "date": target_date,
        "processed_count": len(processed_items),
        "items": processed_items,
    }


@app.post("/api/v1/midday-count")
async def record_midday_count(req: MiddayCountRequest, current_user=Depends(get_workspace_user)):
    now_local = get_store_local_now(current_user)
    today_str = now_local.strftime("%Y-%m-%d")
    current_hour = now_local.hour + (now_local.minute / 60.0)
    open_h = float(current_user.get("opening_hour", STORE_OPEN_HOUR))
    close_h = float(current_user.get("closing_hour", STORE_CLOSE_HOUR))
    total_hours = max(1.0, close_h - open_h)

    if current_hour <= open_h:
        elapsed_fraction = 0.05
    elif current_hour >= close_h:
        elapsed_fraction = 1.0
    else:
        elapsed_fraction = (current_hour - open_h) / total_hours

    now_iso = datetime.now(timezone.utc).isoformat()
    processed = []

    for entry in req.counts:
        item = await db.items.find_one({"_id": entry.item_id, "owner_id": current_user["_id"]})
        if not item:
            raise HTTPException(status_code=404, detail=f"Item '{entry.item_id}' not found.")

        item = await rollover_if_new_day(item, current_user)

        stock_doc = await db.daily_stock.find_one({
            "owner_id": current_user["_id"],
            "item_id": entry.item_id,
            "date": today_str
        })
        if stock_doc and "openingStock" in stock_doc and stock_doc["openingStock"] is not None:
            opening = stock_doc["openingStock"]
            produced = stock_doc.get("producedOrRestocked", 0)
        else:
            opening = item.get("currentStock", 0) + item.get("intradaySales", 0)
            produced = 0

        available = opening + produced
        if entry.remaining > available:
            raise HTTPException(
                status_code=400,
                detail=f"Item '{item['name']}': remaining ({entry.remaining}) cannot exceed available stock ({available})."
            )

        sold_so_far = available - entry.remaining

        # Forecast pace calculation
        fc = await db.forecasts.find_one({"item_id": entry.item_id, "owner_id": current_user["_id"]}, sort=[("forecast_date", -1)])
        dem = (fc.get("predictedDemand") if fc else item.get("predictedDemand")) or DEFAULT_FALLBACK_DEMAND
        expected_by_now = max(1.0, dem * elapsed_fraction)
        pace = round(sold_so_far / expected_by_now, 2)

        mid_day_entry = {
            "remaining": entry.remaining,
            "sold_so_far": sold_so_far,
            "pace": pace,
            "elapsed_fraction": round(elapsed_fraction, 4),
            "timestamp": now_iso,
        }

        await db.daily_stock.update_one(
            {"owner_id": current_user["_id"], "item_id": entry.item_id, "date": today_str},
            {"$set": {
                "midDayCount": mid_day_entry,
                "source": "midday_count",
                "updatedAt": now_iso,
            },
            "$setOnInsert": {
                "openingStock": opening,
                "producedOrRestocked": produced,
                "status": "open",
                "soldOut": False,
                "createdAt": now_iso,
            }},
            upsert=True
        )

        # Update item's currentStock and intradaySales
        await db.items.update_one(
            {"_id": entry.item_id, "owner_id": current_user["_id"]},
            {"$set": {
                "currentStock": entry.remaining,
                "intradaySales": sold_so_far,
                "intradayDate": today_str,
                "updatedAt": now_iso,
            }}
        )

        processed.append({
            "item_id": entry.item_id,
            "name": item["name"],
            "remaining": entry.remaining,
            "sold_so_far": sold_so_far,
            "expected_by_now": round(expected_by_now, 1),
            "same_day_pace": pace,
        })

    return {
        "status": "success",
        "date": today_str,
        "elapsed_fraction": round(elapsed_fraction, 4),
        "items": processed,
    }


@app.get("/api/v1/review/yesterday")
async def get_yesterday_review(current_user=Depends(get_workspace_user)):
    now_local = get_store_local_now(current_user)
    yesterday_str = (now_local.date() - timedelta(days=1)).strftime("%Y-%m-%d")

    cursor = db.items.find({"owner_id": current_user["_id"]})
    reviews = []
    completed_count = 0
    missing_count = 0

    async for item in cursor:
        stock_doc = await db.daily_stock.find_one({
            "owner_id": current_user["_id"],
            "item_id": item["_id"],
            "date": yesterday_str,
        })

        if stock_doc and stock_doc.get("status") == "closed" and stock_doc.get("soldUnits") is not None:
            opening = stock_doc.get("openingStock", 0)
            produced = stock_doc.get("producedOrRestocked", 0)
            available = opening + produced
            sold = stock_doc.get("soldUnits", 0)
            waste = stock_doc.get("wasteUnits", 0)
            closing = stock_doc.get("closingCount", 0)

            sell_through = round(sold / available, 2) if available > 0 else 0.0
            if sell_through >= 0.90:
                label = "High"
                color = "#10B981"
            elif sell_through >= 0.70:
                label = "Normal"
                color = "#3B82F6"
            elif sell_through >= 0.35:
                label = "Low"
                color = "#F59E0B"
            else:
                label = "Critical"
                color = "#EF4444"

            completed_count += 1
            reviews.append({
                "itemId": item["_id"],
                "itemName": item["name"],
                "category": item.get("category", "Other"),
                "status": "completed",
                "sellThrough": sell_through,
                "sellThroughPct": int(round(sell_through * 100)),
                "label": label,
                "color": color,
                "openingStock": opening,
                "producedOrRestocked": produced,
                "availableStock": available,
                "soldUnits": sold,
                "wasteUnits": waste,
                "closingCount": closing,
                "date": yesterday_str,
            })
        else:
            missing_count += 1
            # Missing day = status 'missing', NEVER zero, excluded from training
            reviews.append({
                "itemId": item["_id"],
                "itemName": item["name"],
                "category": item.get("category", "Other"),
                "status": "missing",
                "sellThrough": None,
                "sellThroughPct": None,
                "label": "no data",
                "color": "#9CA3AF",
                "openingStock": None,
                "producedOrRestocked": None,
                "availableStock": None,
                "soldUnits": None,  # NEVER ZERO!
                "wasteUnits": None,
                "closingCount": None,
                "date": yesterday_str,
            })

    return {
        "status": "success",
        "date": yesterday_str,
        "summary": {
            "total_items": len(reviews),
            "completed_count": completed_count,
            "missing_count": missing_count,
        },
        "items": reviews,
    }


# ---------------------------------------------------------------------------- #
# Waste Action Engine (Step 5)
# ---------------------------------------------------------------------------- #

@app.post("/api/v1/sales/intraday", status_code=201)
async def record_intraday_sale(req: IntradaySaleRequest, current_user=Depends(get_workspace_user)):
    item = await db.items.find_one({"_id": req.item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = await rollover_if_new_day(item, current_user)

    new_intraday = item.get("intradaySales", 0) + req.quantity
    new_stock = max(0, item.get("currentStock", 0) - req.quantity)
    now_iso = datetime.now(timezone.utc).isoformat()
    now_local = get_store_local_now(current_user, item)
    today_local = now_local.strftime("%Y-%m-%d")

    # Log individual sales event with store-local calendar date
    await db.intraday_sales.insert_one({
        "item_id": req.item_id,
        "owner_id": current_user["_id"],
        "quantity": req.quantity,
        "timestamp": now_iso,
        "date": today_local,
    })

    # Update item state in Atlas with intradayDate
    await db.items.update_one(
        {"_id": req.item_id, "owner_id": current_user["_id"]},
        {"$set": {
            "intradaySales": new_intraday,
            "intradayDate": today_local,
            "currentStock": new_stock,
            "updatedAt": now_iso,
        }}
    )

    return {
        "status": "recorded",
        "item_id": req.item_id,
        "sold": req.quantity,
        "totalIntradaySales": new_intraday,
        "remainingStock": new_stock,
    }



@app.get("/api/v1/waste-alerts")
async def get_waste_alerts(current_user=Depends(get_workspace_user)):
    now_local = get_store_local_now(current_user)
    current_hour = now_local.hour + (now_local.minute / 60.0)
    
    open_hour = float(current_user.get("opening_hour", STORE_OPEN_HOUR))
    close_hour = float(current_user.get("closing_hour", STORE_CLOSE_HOUR))
    
    # Store operating hours check: closed outside open-close hours
    if current_hour < open_hour or current_hour >= close_hour:
        return {
            "alerts": [],
            "total_alerts": 0,
            "store_status": "closed",
            "message": f"Store is currently closed. Operating hours: {int(open_hour):02d}:00 - {int(close_hour):02d}:00 local time.",
            "local_time": now_local.strftime("%Y-%m-%d %H:%M:%S"),
        }

    total_hours = max(1.0, close_hour - open_hour)
    elapsed_fraction = (current_hour - open_hour) / total_hours
    
    cursor = db.items.find({"owner_id": current_user["_id"], "isPerishable": True})
    alerts = []
    
    async for item in cursor:
        item = await rollover_if_new_day(item, current_user)
        if item.get("isDismissed", False):
            continue

        item_id = item["_id"]
        # Fetch latest daily forecast strictly for this tenant
        forecast = await db.forecasts.find_one(
            {"item_id": item_id, "owner_id": current_user["_id"]},
            sort=[("forecast_date", -1)]
        )
        predicted_daily = (forecast.get("predictedDemand") if forecast else item.get("predictedDemand")) or DEFAULT_FALLBACK_DEMAND
        
        actual_sold = item.get("intradaySales", 0)
        expected_by_now = max(1.0, predicted_daily * elapsed_fraction)
        curr_stock = item.get("currentStock", 0)
        
        tier = evaluate_waste_alert_tier(
            is_perishable=item.get("isPerishable", False),
            is_dismissed=item.get("isDismissed", False),
            curr_stock=curr_stock,
            actual_sold=actual_sold,
            expected_by_now=expected_by_now,
        )
        if tier is not None:
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

            sales_pace_ratio = tier["salesPaceRatio"]
            pct_int = int(round(sales_pace_ratio * 100))
            sales_text = f"{pct_int}% of expected sales so far\ntoday"

            partner_item = None
            if tier["severityLabel"] == "Critical":
                # Select partner item from same store:
                # best sell-through/pace >= 1.0, preferring complementary category, else top seller
                comp_map = {
                    "bakery": ["beverage", "dessert", "food"],
                    "beverage": ["bakery", "food", "dessert"],
                    "food": ["beverage", "bakery"],
                    "dessert": ["beverage", "bakery"],
                    "snack": ["beverage"],
                }
                my_cat = item.get("category", "").lower()
                pref_cats = comp_map.get(my_cat, ["beverage", "bakery"])

                candidates_cursor = db.items.find({
                    "owner_id": current_user["_id"],
                    "_id": {"$ne": item_id}
                })
                candidates = await candidates_cursor.to_list(length=50)

                def partner_score(c):
                    c_cat = c.get("category", "").lower()
                    is_comp = 1 if c_cat in pref_cats else 0
                    sold = c.get("intradaySales", 0)
                    return (is_comp, sold)

                if candidates:
                    candidates.sort(key=partner_score, reverse=True)
                    top_candidate = candidates[0]
                    p_price = top_candidate.get("price") or 5.0
                    my_price = item.get("price") or 5.0
                    bundle_price = round((my_price + p_price) * 0.80, 2)
                    partner_item = {
                        "id": top_candidate["_id"],
                        "name": top_candidate["name"],
                        "category": top_candidate.get("category", "Other"),
                        "price": p_price,
                        "comboOriginalPrice": round(my_price + p_price, 2),
                        "bundlePrice": bundle_price,
                        "discountPct": 20,
                    }

            alerts.append({
                "id": item_id,
                "itemName": item["name"],
                "salesText": sales_text,
                "progress": round(min(1.0, sales_pace_ratio), 2),
                "salesPaceRatio": sales_pace_ratio,
                "expectedSales": round(expected_by_now, 1),
                "actualSold": actual_sold,
                "currentStock": curr_stock,
                "severityLabel": tier["severityLabel"],
                "severityColor": tier["severityColor"],
                "discount_pct": tier["discount_pct"],
                "recommendedActionText": tier["recommendedActionText"],
                "recommendedActionColor": tier["recommendedActionColor"],
                "recommendedDoneText": tier["recommendedDoneText"],
                "isRecommendedActionDone": item.get("isRecommendedActionDone", False),
                "primaryActionText": tier["primaryActionText"],
                "primaryDoneText": tier["primaryDoneText"],
                "isPrimaryActionDone": item.get("isPrimaryActionDone", False),
                "partnerItem": partner_item,
                "bundleDiscountPct": 20 if tier["severityLabel"] == "Critical" else None,
                "isBundleApplied": item.get("bundleApplied", False),
                "isDismissed": False,
                "layoutStyle": tier["layoutStyle"],
                "foodType": food_type,
            })

    return {"alerts": alerts, "total_alerts": len(alerts), "store_status": "open"}


class ApplyDiscountRequest(BaseModel):
    discount_pct: Optional[float] = None


@app.post("/api/v1/waste-alerts/{item_id}/apply-discount")
async def apply_discount_action(item_id: str, req: Optional[ApplyDiscountRequest] = None, current_user=Depends(get_workspace_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = await rollover_if_new_day(item, current_user)

    discount_pct = req.discount_pct if (req and req.discount_pct is not None) else 10.0
    current_price = item.get("price") or 5.0
    discount_multiplier = max(0.0, 1.0 - (discount_pct / 100.0))
    discounted_price = round(current_price * discount_multiplier, 2)
    now_iso = datetime.now(timezone.utc).isoformat()

    await db.items.update_one(
        {"_id": item_id, "owner_id": current_user["_id"]},
        {"$set": {
            "price": discounted_price,
            "originalPrice": item.get("originalPrice", current_price),
            "discountPct": discount_pct,
            "isPrimaryActionDone": True,
            "discountApplied": True,
            "updatedAt": now_iso,
        }}
    )
    return {
        "status": "success",
        "message": f"Applied {discount_pct:.0f}% discount to {item['name']}. New price: ${discounted_price}",
        "oldPrice": current_price,
        "newPrice": discounted_price,
        "discountPct": discount_pct,
    }


@app.post("/api/v1/waste-alerts/{item_id}/apply-bundle")
async def apply_bundle_action(item_id: str, req: Optional[ApplyBundleRequest] = None, current_user=Depends(get_workspace_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = await rollover_if_new_day(item, current_user)

    bundle_pct = req.bundle_discount_pct if req else 20.0
    partner_id = req.partner_item_id if req else None

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.items.update_one(
        {"_id": item_id, "owner_id": current_user["_id"]},
        {"$set": {
            "bundleApplied": True,
            "bundlePartnerId": partner_id,
            "bundleDiscountPct": bundle_pct,
            "isRecommendedActionDone": True,
            "isPrimaryActionDone": True,
            "updatedAt": now_iso,
        }}
    )
    return {
        "status": "success",
        "message": f"Applied {bundle_pct}% combo bundle for '{item['name']}'.",
        "bundleDiscountPct": bundle_pct,
        "partnerItemId": partner_id,
    }


@app.post("/api/v1/waste-alerts/{item_id}/dismiss")
async def dismiss_alert_action(item_id: str, current_user=Depends(get_workspace_user)):
    item = await db.items.find_one({"_id": item_id, "owner_id": current_user["_id"]})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item = await rollover_if_new_day(item, current_user)

    await db.items.update_one(
        {"_id": item_id, "owner_id": current_user["_id"]},
        {"$set": {"isDismissed": True}}
    )
    return {"status": "dismissed", "item_id": item_id}


# ---------------------------------------------------------------------------- #
# Demo Sandbox Workspace Engine (Shadow Tenant)
# ---------------------------------------------------------------------------- #

class DemoClockRequest(BaseModel):
    hour: float = Field(..., ge=0.0, le=24.0, description="Simulated local hour (e.g. 14.5 for 14:30)")


async def purge_shadow_tenant(shadow_id: str) -> dict:
    """
    Purges all documents belonging strictly and exclusively to the shadow tenant.
    Never touches real owner accounts or live production data.
    """
    filter_dict = {"owner_id": shadow_id}
    res_users = await db.users.delete_many({"_id": shadow_id})
    res_items = await db.items.delete_many(filter_dict)
    res_stock = await db.daily_stock.delete_many(filter_dict)
    res_sales = await db.daily_sales.delete_many(filter_dict)
    res_intraday = await db.intraday_sales.delete_many(filter_dict)
    res_forecasts = await db.forecasts.delete_many(filter_dict)
    res_alerts = await db.waste_alerts.delete_many(filter_dict)
    DEMO_SIMULATED_CLOCKS.pop(shadow_id, None)

    return {
        "shadow_id": shadow_id,
        "deleted_counts": {
            "users": res_users.deleted_count,
            "items": res_items.deleted_count,
            "daily_stock": res_stock.deleted_count,
            "daily_sales": res_sales.deleted_count,
            "intraday_sales": res_intraday.deleted_count,
            "forecasts": res_forecasts.deleted_count,
            "waste_alerts": res_alerts.deleted_count,
        },
        "filters_applied": {
            "users": {"_id": shadow_id},
            "collections": {"owner_id": shadow_id},
        }
    }


@app.post("/api/v1/demo/start")
async def start_demo_sandbox(real_user=Depends(get_current_user)):
    """
    Idempotently seeds the isolated shadow tenant from ML/data/demo_fixture.json.
    Rate limited to 5 starts/hour per user.
    Uses precomputed fixture so zero pandas/scikit-learn imports occur.
    """
    user_id = real_user["_id"]
    now_ts = time.time()

    # 1. Rate limiter: 5 starts per hour
    window_start = now_ts - 3600
    DEMO_START_RATE_LIMITS[user_id] = [t for t in DEMO_START_RATE_LIMITS[user_id] if t > window_start]
    if len(DEMO_START_RATE_LIMITS[user_id]) >= 5:
        raise HTTPException(
            status_code=429,
            detail="Demo start rate limit exceeded (maximum 5 sandbox creations per hour). Please wait."
        )
    DEMO_START_RATE_LIMITS[user_id].append(now_ts)

    shadow_id = f"shadow_{user_id}"

    # 2. Check if already seeded (idempotency)
    existing_items = await db.items.count_documents({"owner_id": shadow_id})
    if existing_items >= 7:
        return {
            "status": "already_started",
            "shadow_user_id": shadow_id,
            "items_count": existing_items,
            "message": "Demo sandbox is already active and seeded for this user.",
        }

    # 3. Clean up any partial shadow state before seeding
    await purge_shadow_tenant(shadow_id)

    # 4. Load precomputed fixture
    fixture_path = Path(__file__).resolve().parent.parent / "ML" / "data" / "demo_fixture.json"
    if not fixture_path.exists():
        raise HTTPException(status_code=500, detail="Demo fixture file not found on server.")

    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture = json.load(f)

    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
    now_iso = datetime.now(timezone.utc).isoformat()

    # 5. Insert shadow user document
    shadow_user_doc = {
        "_id": shadow_id,
        "name": f"Demo Store ({real_user.get('name', 'Owner')})",
        "email": f"demo_{real_user.get('email', 'user')}",
        "role": "demo_shadow",
        "shadow_of": user_id,
        "store_name": fixture["store_profile"]["store_name"],
        "timezone": fixture["store_profile"]["timezone"],
        "opening_hour": fixture["store_profile"]["opening_hour"],
        "closing_hour": fixture["store_profile"]["closing_hour"],
        "currency": fixture["store_profile"]["currency"],
        "onboarding_completed": True,
        "replayed_dataset": True,
        "created_at": now_iso,
        "expiresAt": expires_at,
    }
    await db.users.insert_one(shadow_user_doc)

    # Calculate dates ending yesterday in Asia/Kolkata
    store_tz = ZoneInfo(fixture["store_profile"]["timezone"])
    local_now = datetime.now(store_tz)
    local_today = local_now.date()
    yesterday = local_today - timedelta(days=1)
    date_strs = [(yesterday - timedelta(days=59 - i)).strftime("%Y-%m-%d") for i in range(60)]
    today_str = local_today.strftime("%Y-%m-%d")
    today_dow_str = str(local_now.weekday())

    # 6. Seed mature items, historical stock/sales, and precomputed forecasts
    items_to_insert = []
    sales_to_insert = []
    stock_to_insert = []
    forecasts_to_insert = []

    for mature in fixture["mature_items"]:
        item_id = f"{shadow_id}_{mature['fixture_id']}"
        items_to_insert.append({
            "_id": item_id,
            "owner_id": shadow_id,
            "name": mature["name"],
            "name_lower": mature["name"].strip().lower(),
            "category": mature["category"],
            "unit": mature["unit"],
            "currentStock": mature["currentStock"],
            "isPerishable": mature["isPerishable"],
            "price": mature["price"],
            "shelfLifeDays": mature.get("shelfLifeDays"),
            "intradaySales": 0,
            "intradayDate": today_str,
            "replayed_dataset": True,
            "source": "replayed_dataset",
            "expiresAt": expires_at,
            "createdAt": now_iso,
            "updatedAt": now_iso,
        })

        for idx, d_str in enumerate(date_strs):
            sold = mature["sales_history_60"][idx]
            stock_info = mature["daily_stock_60"][idx]
            sales_to_insert.append({
                "owner_id": shadow_id,
                "item_id": item_id,
                "date": d_str,
                "units": sold,
                "source": "replayed_dataset",
                "expiresAt": expires_at,
                "createdAt": now_iso,
            })
            stock_to_insert.append({
                "owner_id": shadow_id,
                "item_id": item_id,
                "date": d_str,
                "openingStock": stock_info["openingStock"],
                "producedOrRestocked": stock_info["producedOrRestocked"],
                "closingStock": stock_info["closingStock"],
                "wasteUnits": stock_info["wasteUnits"],
                "soldUnits": stock_info["soldUnits"],
                "status": "closed",
                "source": "replayed_dataset",
                "expiresAt": expires_at,
                "createdAt": now_iso,
            })

        fc_spec = mature["weekday_forecasts"].get(today_dow_str, mature["weekday_forecasts"]["0"])
        forecasts_to_insert.append({
            "owner_id": shadow_id,
            "item_id": item_id,
            "name": mature["name"],
            "category": mature["category"],
            "unit": mature["unit"],
            "price": mature["price"],
            "currentStock": mature["currentStock"],
            "predictedDemand": fc_spec["predictedDemand"],
            "safetyStock": fc_spec["safetyStock"],
            "tier": fc_spec["tier"],
            "description": fc_spec["explanation"],
            "forecast_date": today_str,
            "confidence_interval": None,
            "source": "replayed_dataset",
            "expiresAt": expires_at,
            "createdAt": now_iso,
        })

    # 7. Seed 1 cold-start item
    cs = fixture["cold_start_item"]
    cs_item_id = f"{shadow_id}_{cs['fixture_id']}"
    items_to_insert.append({
        "_id": cs_item_id,
        "owner_id": shadow_id,
        "name": cs["name"],
        "name_lower": cs["name"].strip().lower(),
        "category": cs["category"],
        "unit": cs["unit"],
        "currentStock": cs["currentStock"],
        "isPerishable": cs["isPerishable"],
        "price": cs["price"],
        "shelfLifeDays": cs.get("shelfLifeDays"),
        "intradaySales": 0,
        "intradayDate": today_str,
        "replayed_dataset": True,
        "source": "replayed_dataset",
        "expiresAt": expires_at,
        "createdAt": now_iso,
        "updatedAt": now_iso,
    })
    forecasts_to_insert.append({
        "owner_id": shadow_id,
        "item_id": cs_item_id,
        "name": cs["name"],
        "category": cs["category"],
        "unit": cs["unit"],
        "price": cs["price"],
        "currentStock": cs["currentStock"],
        "predictedDemand": cs["predictedDemand"],
        "safetyStock": cs["safetyStock"],
        "tier": cs["tier"],
        "description": cs["description"],
        "forecast_date": today_str,
        "confidence_interval": None,
        "source": "replayed_dataset",
        "expiresAt": expires_at,
        "createdAt": now_iso,
    })

    if items_to_insert:
        await db.items.insert_many(items_to_insert)
    if sales_to_insert:
        await db.daily_sales.insert_many(sales_to_insert)
    if stock_to_insert:
        await db.daily_stock.insert_many(stock_to_insert)
    if forecasts_to_insert:
        await db.forecasts.insert_many(forecasts_to_insert)

    return {
        "status": "started",
        "shadow_user_id": shadow_id,
        "items_seeded": len(items_to_insert),
        "expiresAt": expires_at.isoformat(),
        "message": "Demo sandbox successfully seeded with replayed dataset.",
    }


@app.post("/api/v1/demo/reset")
async def reset_demo_sandbox(real_user=Depends(get_current_user)):
    shadow_id = f"shadow_{real_user['_id']}"
    await purge_shadow_tenant(shadow_id)
    return await start_demo_sandbox(real_user=real_user)


@app.delete("/api/v1/demo")
async def delete_demo_sandbox(real_user=Depends(get_current_user)):
    shadow_id = f"shadow_{real_user['_id']}"
    result = await purge_shadow_tenant(shadow_id)
    return {
        "status": "deleted",
        "shadow_user_id": shadow_id,
        "result": result,
    }


@app.post("/api/v1/demo/clock")
async def set_demo_clock(req: DemoClockRequest, real_user=Depends(get_current_user)):
    shadow_id = f"shadow_{real_user['_id']}"
    DEMO_SIMULATED_CLOCKS[shadow_id] = float(req.hour)
    await db.users.update_one(
        {"_id": shadow_id},
        {"$set": {"simulated_clock_hour": float(req.hour)}}
    )
    return {
        "status": "clock_updated",
        "shadow_user_id": shadow_id,
        "simulated_clock_hour": float(req.hour),
    }


@app.post("/api/v1/jobs/rollup-daily-sales")
async def trigger_daily_sales_rollup(
    request: Request,
    target_date: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Idempotent daily sales rollup job. Aggregates intraday_sales into daily_sales for target_date.
    Authorization:
    - If X-Job-Secret matches server JOB_SECRET, processes all owners.
    - Otherwise, requires valid user Bearer JWT and restricts strictly to caller's own owner_id.
    """
    job_secret = os.getenv("JOB_SECRET")
    header_secret = request.headers.get("X-Job-Secret")
    is_server_authorized = bool(job_secret and header_secret and header_secret == job_secret)

    scoped_owner_id = None
    if is_server_authorized:
        scoped_owner_id = None
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            scoped_owner_id = payload.get("sub")
            if not scoped_owner_id:
                raise HTTPException(status_code=401, detail="Invalid token payload.")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired Bearer token.")
    else:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Valid user JWT or X-Job-Secret header required."
        )

    if not target_date:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = await rollup_daily_sales(target_date, owner_id=scoped_owner_id)
    return result


# ---------------------------------------------------------------------------- #
# AI Executive Briefing & Manager Assistant (Google Gemini 1.5/2.5/3.8 Flash)
# ---------------------------------------------------------------------------- #

class AssistantChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Manager operational query (1 to 500 characters)")


# In-memory Briefing Cache with 10-minute cooldown (Requirement 1c)
BRIEFING_CACHE: Dict[Tuple[str, str], Dict[str, Any]] = {}
BRIEFING_COOLDOWN_SECONDS = 600  # 10 minutes

# Per-user daily assistant query counter (15 queries/day limit)
ASSISTANT_DAILY_QUERY_COUNTS: Dict[Tuple[str, str], int] = {}


@app.get("/api/v1/briefing/today")
async def get_today_executive_briefing(current_user=Depends(get_workspace_user)):
    """
    Synthesizes an executive daily operational briefing for the on-duty manager
    using Google Gemini. Strictly grounded in verified MongoDB Atlas metrics.
    Caches per (owner_id, store-local date) with a 10-minute refresh cooldown.
    Returns immediately with empty state and zero LLM calls if store has 0 items.
    """
    user_id = current_user["_id"]
    local_date = get_store_local_now(current_user).strftime("%Y-%m-%d")

    cursor = db.items.find({"owner_id": user_id})
    items = await cursor.to_list(length=100)

    # Empty store check: zero LLM calls if no items exist
    if not items:
        return {
            "status": "success",
            "briefing": {
                "source": "empty",
                "provider": "system",
                "executive_summary": "Your store inventory is currently empty. Add items to enable automated demand forecasting, waste risk detection, and operational recommendations.",
                "actions": [],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    cache_key = (user_id, local_date)
    now_ts = time.time()

    cached_entry = BRIEFING_CACHE.get(cache_key)
    if cached_entry and (now_ts - cached_entry.get("cached_at", 0)) < BRIEFING_COOLDOWN_SECONDS:
        cached_data = cached_entry["briefing"].copy()
        cached_data["cached"] = True
        cached_data["cache_age_seconds"] = int(now_ts - cached_entry["cached_at"])
        return {
            "status": "success",
            "briefing": cached_data,
        }

    # Fetch alerts for this user
    alerts_resp = await get_waste_alerts(current_user=current_user)
    alerts = alerts_resp.get("alerts", [])

    briefing = await asyncio.to_thread(generate_daily_briefing, items, alerts)
    BRIEFING_CACHE[cache_key] = {
        "briefing": briefing,
        "cached_at": now_ts,
    }

    return {
        "status": "success",
        "briefing": briefing,
    }


@app.post("/api/v1/assistant/chat", dependencies=[Depends(chat_limiter)])
async def assistant_chat(req: AssistantChatRequest, current_user=Depends(get_workspace_user)):
    """
    Answers manager queries with RAG grounding from today's inventory state.
    Enforces per-user limit of 15 queries/day and returns zero-LLM empty state for 0 items.
    """
    user_id = current_user["_id"]
    cursor = db.items.find({"owner_id": user_id})
    items = await cursor.to_list(length=100)

    # Empty store check: zero LLM calls
    if not items:
        return {
            "status": "empty",
            "reply": "Your store currently has no items in inventory. Add inventory items first to consult the AI assistant on demand trends and waste mitigation.",
            "provider": "system",
            "model": "empty-store",
        }

    # Daily per-user limit: 15 queries/day
    local_date = get_store_local_now(current_user).strftime("%Y-%m-%d")
    user_query_key = (user_id, local_date)
    query_count = ASSISTANT_DAILY_QUERY_COUNTS.get(user_query_key, 0)
    if query_count >= 15:
        return {
            "status": "rate_limited",
            "reply": "Daily query limit reached (15/15 queries used today). Please try again tomorrow.",
            "provider": "system",
            "model": "rate-limit",
        }
    ASSISTANT_DAILY_QUERY_COUNTS[user_query_key] = query_count + 1

    alerts_resp = await get_waste_alerts(current_user=current_user)
    alerts = alerts_resp.get("alerts", [])

    result = await asyncio.to_thread(answer_assistant_chat, req.query, items, alerts)
    return {
        "status": "success",
        "reply": result["reply"],
        "provider": result.get("provider"),
        "model": result.get("model"),
    }



if __name__ == "__main__":
    import uvicorn
    forwarded_ips = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, proxy_headers=True, forwarded_allow_ips=forwarded_ips)
