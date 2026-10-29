#!/usr/bin/env python3
"""
Seed Demo Store (Idempotent; Staging First)
Owner: demo_manager@restockiq.com
7 bakery items mapped via NAME_MAP
60 days of daily_stock and daily_sales replayed from primary_items.csv ending yesterday in store timezone.
Flagged as "replayed dataset" in DB and app footer.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

# Load environment
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "Backend"
ml_dir = root_dir / "ML"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(ml_dir))

from dotenv import load_dotenv
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

import pandas as pd
from pymongo import MongoClient
from passlib.context import CryptContext
from bson import ObjectId

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DEMO_EMAIL = "demo_manager@restockiq.com"
DEFAULT_STORE_TZ = "Asia/Kolkata"

DEMO_ITEMS_SPEC = [
    {
        "name": "Traditional Baguette",
        "name_lower": "traditional baguette",
        "article": "BAGUETTE",
        "category": "Breads & Baguettes",
        "unit": "loaf",
        "price": 45.0,
        "isPerishable": True,
        "shelfLifeDays": 1,
    },
    {
        "name": "Croissant",
        "name_lower": "croissant",
        "article": "CROISSANT",
        "category": "Viennoiserie",
        "unit": "piece",
        "price": 65.0,
        "isPerishable": True,
        "shelfLifeDays": 1,
    },
    {
        "name": "Pain au Chocolat",
        "name_lower": "pain au chocolat",
        "article": "PAIN AU CHOCOLAT",
        "category": "Viennoiserie",
        "unit": "piece",
        "price": 75.0,
        "isPerishable": True,
        "shelfLifeDays": 1,
    },
    {
        "name": "Brioche",
        "name_lower": "brioche",
        "article": "BRIOCHE",
        "category": "Viennoiserie",
        "unit": "piece",
        "price": 95.0,
        "isPerishable": True,
        "shelfLifeDays": 2,
    },
    {
        "name": "Banette",
        "name_lower": "banette",
        "article": "BANETTE",
        "category": "Breads & Baguettes",
        "unit": "loaf",
        "price": 50.0,
        "isPerishable": True,
        "shelfLifeDays": 1,
    },
    {
        "name": "Whole Milk",
        "name_lower": "whole milk",
        "article": "COUPE",
        "category": "Beverages & Sweets",
        "unit": "liter",
        "price": 60.0,
        "isPerishable": True,
        "shelfLifeDays": 2,
    },
    {
        "name": "Espresso Beans",
        "name_lower": "espresso beans",
        "article": "CAFE OU EAU",
        "category": "Beverages & Sweets",
        "unit": "cup",
        "price": 120.0,
        "isPerishable": False,
        "shelfLifeDays": 30,
    },
]


def seed_demo_store(mongo_uri: str = None, db_name: str = "restockiq_staging", demo_password: str = None):
    uri = mongo_uri or os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
    if not uri:
        print("[ERROR] Neither MONGODB_URI nor MONGO_URI set in environment.")
        sys.exit(1)

    # Password extraction (never print)
    raw_password = demo_password or os.getenv("DEMO_PASSWORD", "DemoStorePass2026!")
    if len(raw_password) < 8:
        print("[ERROR] DEMO_PASSWORD must be >= 8 characters.")
        sys.exit(1)

    print(f"[SEED] Target Database: {db_name}")
    print(f"[SEED] Demo Account: {DEMO_EMAIL}")
    print("[SEED] Password: [PROTECTED / CONCEALED]")

    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    db = client[db_name]

    # Load 60 days of historical data from primary_items.csv
    csv_path = root_dir / "ML" / "data" / "processed" / "primary_items.csv"
    if not csv_path.exists():
        print(f"[ERROR] Could not find primary_items.csv at {csv_path}")
        sys.exit(1)

    df_hist = pd.read_csv(csv_path)
    df_hist["ds"] = pd.to_datetime(df_hist["ds"])
    df_hist = df_hist.sort_values(["article", "ds"]).reset_index(drop=True)

    # Calculate 60 dates ending yesterday in store timezone
    store_tz = os.getenv("STORE_TIMEZONE", DEFAULT_STORE_TZ)
    local_now = datetime.now(ZoneInfo(store_tz))
    local_today = local_now.date()
    yesterday = local_today - timedelta(days=1)
    dates_60 = [yesterday - timedelta(days=59 - i) for i in range(60)]
    date_strs = [d.strftime("%Y-%m-%d") for d in dates_60]

    print(f"[SEED] Store Timezone: {store_tz}")
    print(f"[SEED] Replaying 60 consecutive days: {date_strs[0]} through {date_strs[-1]} (ending yesterday)")

    # 1. Idempotency: Locate or initialize user
    user = db.users.find_one({"email": DEMO_EMAIL})
    hashed_pw = pwd_context.hash(raw_password)

    user_doc = {
        "email": DEMO_EMAIL,
        "name": "Demo Manager",
        "role": "owner",
        "store_name": "RestockIQ Bakery Demo",
        "timezone": store_tz,
        "opening_hour": 6.0,
        "closing_hour": 20.0,
        "currency": "INR",
        "onboarding_completed": True,
        "onboardingCompleted": True,
        "replayed_dataset": True,
        "password_hash": hashed_pw,
        "updated_at": datetime.now(ZoneInfo("UTC")).isoformat(),
    }

    if user:
        user_id = user["_id"]
        db.users.update_one({"_id": user_id}, {"$set": user_doc})
        print(f"[SEED] Existing user found ({user_id}). Purging prior demo records for idempotency...")
        db.items.delete_many({"owner_id": user_id})
        db.daily_stock.delete_many({"owner_id": user_id})
        db.daily_sales.delete_many({"owner_id": user_id})
        db.forecasts.delete_many({"owner_id": user_id})
    else:
        user_doc["_id"] = str(ObjectId())
        user_doc["created_at"] = datetime.now(ZoneInfo("UTC")).isoformat()
        db.users.insert_one(user_doc)
        user_id = user_doc["_id"]
        print(f"[SEED] Created new user ({user_id}).")

    # 2. Seed 7 Items and Replay 60 Days of Data
    created_items = []
    total_sales_records = 0
    total_stock_records = 0

    for spec in DEMO_ITEMS_SPEC:
        item_id = str(ObjectId())
        art = spec["article"]
        art_sub = df_hist[df_hist["article"] == art].tail(60).copy().reset_index(drop=True)
        if len(art_sub) < 60:
            print(f"[ERROR] Article {art} has fewer than 60 rows ({len(art_sub)}) in primary_items.csv")
            sys.exit(1)

        y_vals = art_sub["y"].values

        # Generate 60 days of stock and sales
        daily_sales_batch = []
        daily_stock_batch = []
        prev_closing = 20  # initial non-perishable opening

        for idx, d_str in enumerate(date_strs):
            sold = int(y_vals[idx])
            is_perish = spec["isPerishable"]

            if is_perish:
                # Perishable: morning bake produced, leftovers become waste
                # 8% buffer over sales
                produced = max(sold, int(round(sold * 1.08)) + (1 if idx % 3 == 0 else 0))
                closing = max(0, produced - sold)
                waste = closing
                opening = 0
            else:
                # Non-perishable: carry over from yesterday
                opening = prev_closing
                produced = 40 if opening < 15 else 0
                closing = max(0, opening + produced - sold)
                waste = 0
                prev_closing = closing

            daily_sales_batch.append({
                "owner_id": user_id,
                "item_id": item_id,
                "date": d_str,
                "units": sold,
                "source": "replayed_dataset",
                "created_at": f"{d_str}T20:00:00Z",
            })

            daily_stock_batch.append({
                "owner_id": user_id,
                "item_id": item_id,
                "date": d_str,
                "openingStock": opening,
                "producedOrRestocked": produced,
                "closingCount": closing,
                "soldUnits": sold,
                "wasteUnits": waste,
                "status": "completed",
                "midDayCount": None,
                "soldOut": (closing == 0),
                "source": "replayed_dataset",
                "created_at": f"{d_str}T20:05:00Z",
            })

        if daily_sales_batch:
            db.daily_sales.insert_many(daily_sales_batch)
            total_sales_records += len(daily_sales_batch)

        if daily_stock_batch:
            db.daily_stock.insert_many(daily_stock_batch)
            total_stock_records += len(daily_stock_batch)

        # Final current stock for today
        if spec["isPerishable"]:
            last_sold = int(y_vals[-1])
            current_stock = max(5, int(round(last_sold * 0.4)))
        else:
            current_stock = prev_closing

        item_doc = {
            "_id": item_id,
            "owner_id": user_id,
            "name": spec["name"],
            "name_lower": spec["name_lower"],
            "category": spec["category"],
            "unit": spec["unit"],
            "price": spec["price"],
            "isPerishable": spec["isPerishable"],
            "shelfLifeDays": spec["shelfLifeDays"],
            "currentStock": current_stock,
            "daysOfData": 60,
            "maturity": "Mature",
            "maturityLabel": "Mature (60 days)",
            "replayed_dataset": True,
            "description": f"60-day replayed operational dataset from historical bakery reference ({spec['article']}).",
            "riskLevel": "normal",
            "updatedAt": datetime.now(ZoneInfo("UTC")).isoformat(),
        }
        db.items.insert_one(item_doc)
        created_items.append(spec["name"])

    print(f"[SUCCESS] Seeded demo store in '{db_name}':")
    print(f"  - User: {DEMO_EMAIL} (owner_id={user_id})")
    print(f"  - Items created: {len(created_items)} ({', '.join(created_items)})")
    print(f"  - Daily sales inserted: {total_sales_records}")
    print(f"  - Daily stock inserted: {total_stock_records}")
    print(f"  - Flags: replayed_dataset=True on store and items")

    client.close()
    return user_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed RestockIQ Demo Store")
    parser.add_argument("--db", type=str, default="restockiq_staging", help="Target database name (default: restockiq_staging)")
    args = parser.parse_args()

    seed_demo_store(db_name=args.db)
