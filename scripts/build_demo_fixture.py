"""
Builds ML/data/demo_fixture.json from ML/data/processed/primary_items.csv.
Extracts 60 consecutive days of real sales data for 6 mature bakery articles,
precomputes weekday point-estimates and safety stock per weekday (0..6),
and defines 1 brand-new cold-start item (Artisan Sourdough).
Runs ONCE at build time so FastAPI backend does NOT import pandas/scikit-learn.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

root_dir = Path(__file__).resolve().parent.parent
csv_path = root_dir / "ML" / "data" / "processed" / "primary_items.csv"
output_path = root_dir / "ML" / "data" / "demo_fixture.json"

if not csv_path.exists():
    raise FileNotFoundError(f"Missing {csv_path}")

df = pd.read_csv(csv_path)
df["ds"] = pd.to_datetime(df["ds"])
df["dow"] = df["ds"].dt.dayofweek

MATURE_ITEMS = [
    {
        "fixture_id": "item_baguette",
        "name": "Traditional Baguette",
        "article": "BAGUETTE",
        "category": "Bakery",
        "unit": "loaf",
        "price": 45.0,
        "isPerishable": True,
        "shelfLifeDays": 1,
        "currentStock": 8,
    },
    {
        "fixture_id": "item_croissant",
        "name": "Croissant",
        "article": "CROISSANT",
        "category": "Bakery",
        "unit": "piece",
        "price": 65.0,
        "isPerishable": True,
        "shelfLifeDays": 1,
        "currentStock": 12,
    },
    {
        "fixture_id": "item_pain_chocolat",
        "name": "Pain au Chocolat",
        "article": "PAIN AU CHOCOLAT",
        "category": "Bakery",
        "unit": "piece",
        "price": 75.0,
        "isPerishable": True,
        "shelfLifeDays": 1,
        "currentStock": 15,
    },
    {
        "fixture_id": "item_brioche",
        "name": "Brioche",
        "article": "BRIOCHE",
        "category": "Bakery",
        "unit": "piece",
        "price": 95.0,
        "isPerishable": True,
        "shelfLifeDays": 2,
        "currentStock": 6,
    },
    {
        "fixture_id": "item_banette",
        "name": "Banette",
        "article": "BANETTE",
        "category": "Bakery",
        "unit": "loaf",
        "price": 50.0,
        "isPerishable": True,
        "shelfLifeDays": 1,
        "currentStock": 10,
    },
    {
        "fixture_id": "item_whole_milk",
        "name": "Whole Milk",
        "article": "COUPE",
        "category": "Dairy",
        "unit": "liter",
        "price": 60.0,
        "isPerishable": True,
        "shelfLifeDays": 2,
        "currentStock": 4,  # Intentionally low to show restock / pace alert
    },
]

COLD_START_ITEM = {
    "fixture_id": "item_sourdough",
    "name": "Artisan Sourdough",
    "category": "Bakery",
    "unit": "loaf",
    "price": 80.0,
    "isPerishable": True,
    "shelfLifeDays": 2,
    "currentStock": 14,
    "predictedDemand": 24,
    "safetyStock": 7,
    "tier": "Learning",
    "description": "Cold-start initial forecast based on Bakery category prior (24 units/day).",
}

fixture = {
    "store_profile": {
        "store_name": "Sample Artisan Bakery",
        "timezone": "Asia/Kolkata",
        "opening_hour": 8.0,
        "closing_hour": 20.0,
        "currency": "₹",
        "replayed_dataset": True,
    },
    "mature_items": [],
    "cold_start_item": COLD_START_ITEM,
}

for item in MATURE_ITEMS:
    art = item["article"]
    art_df = df[df["article"] == art].sort_values("ds").reset_index(drop=True)
    if len(art_df) < 60:
        raise ValueError(f"Article {art} has only {len(art_df)} records; need at least 60.")

    # Last 60 trading days of historical sales
    tail_60 = art_df.tail(60).copy().reset_index(drop=True)
    sales_60 = tail_60["y"].astype(int).tolist()

    # Precalculate stock routine for 60 days
    stock_60 = []
    for idx, sold in enumerate(sales_60):
        # Morning bake with ~8% buffer
        produced = max(sold, int(round(sold * 1.08)) + (1 if idx % 3 == 0 else 0))
        closing = max(0, produced - sold)
        stock_60.append({
            "day_offset": 59 - idx,  # 0 is yesterday, 59 is 60 days ago
            "openingStock": 0,
            "producedOrRestocked": produced,
            "closingStock": closing,
            "wasteUnits": closing,
            "soldUnits": sold,
        })

    # Precompute weekday forecasts (dow 0..6: Mon..Sun)
    # Using 30-day baseline * dow ratio + safety stock (1.65 sigma)
    last_30 = tail_60.tail(30)["y"]
    base_demand = float(last_30.mean())
    daily_std = float(last_30.std()) if float(last_30.std()) > 0 else 3.5
    overall_mean = float(art_df["y"].mean()) if float(art_df["y"].mean()) > 0 else base_demand

    weekday_forecasts = {}
    for dow in range(7):
        dow_sub = art_df[art_df["dow"] == dow]["y"]
        dow_mean = float(dow_sub.mean()) if len(dow_sub) > 0 else base_demand
        ratio = dow_mean / overall_mean if overall_mean > 0 else 1.0
        dow_demand = max(5, int(round(base_demand * ratio)))
        dow_safety = max(2, int(round(1.65 * daily_std)))
        is_weekend = dow in [4, 5, 6]
        desc = f"Historical {dow_demand} units/day expectation ({'weekend peak' if is_weekend else 'weekday baseline'})."

        weekday_forecasts[str(dow)] = {
            "predictedDemand": dow_demand,
            "safetyStock": dow_safety,
            "tier": "Mature",
            "explanation": desc,
        }

    mature_entry = {
        **item,
        "sales_history_60": sales_60,
        "daily_stock_60": stock_60,
        "weekday_forecasts": weekday_forecasts,
    }
    fixture["mature_items"].append(mature_entry)

output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(fixture, f, indent=2)

print(f"[SUCCESS] Built {output_path} with {len(fixture['mature_items'])} mature items + 1 cold start item.")
