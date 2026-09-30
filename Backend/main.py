from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="RestockIQ Backend API (Mock)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Data Models ----

class ItemModel(BaseModel):
    id: str
    name: str
    category: str
    unit: str
    currentStock: int
    isPerishable: bool
    price: Optional[float] = None

class ForecastItemModel(BaseModel):
    id: str
    name: str
    category: str
    unit: str
    currentStock: int
    isPerishable: bool
    predictedDemand: int
    safetyStock: int
    restockQuantity: int
    description: str
    confidence_interval: Optional[dict] = None
    riskLevel: str
    updatedAt: str

class WasteAlertModel(BaseModel):
    id: str
    itemName: str
    sales_pace_ratio: float
    risk_level: str
    recommended_action: str
    discount_pct: int

class InventoryClosingItem(BaseModel):
    id: str
    name: str
    expectedLeftover: int
    actualLeftover: int
    isPerishable: bool

# ---- Mock Data ----

MOCK_FORECASTS = [
    {
        "id": "1",
        "name": "Croissants",
        "category": "Bakery",
        "unit": "Units",
        "currentStock": 10,
        "isPerishable": True,
        "predictedDemand": 50,
        "safetyStock": 5,
        "restockQuantity": 45,
        "description": "LLM analysis pending",
        "confidence_interval": None,
        "riskLevel": "normal",
        "updatedAt": datetime.utcnow().isoformat() + "Z"
    },
    {
        "id": "2",
        "name": "Espresso Beans",
        "category": "Beverage",
        "unit": "LBS",
        "currentStock": 6,
        "isPerishable": False,
        "predictedDemand": 15,
        "safetyStock": 3,
        "restockQuantity": 12,
        "description": "LLM analysis pending",
        "confidence_interval": None,
        "riskLevel": "normal",
        "updatedAt": datetime.utcnow().isoformat() + "Z"
    }
]

MOCK_WASTE_ALERTS = [
    {
        "id": "1",
        "itemName": "Whole Milk",
        "sales_pace_ratio": 0.4,
        "risk_level": "HIGH",
        "recommended_action": "Apply a 20% discount now to clear inventory.",
        "discount_pct": 20
    }
]

# ---- Endpoints ----

@app.get("/api/v1/forecasts/today")
async def get_todays_forecasts():
    return {
        "summary": "LLM analysis pending",
        "items": MOCK_FORECASTS
    }

@app.get("/api/v1/forecasts/{item_id}")
async def get_item_forecast(item_id: str):
    for f in MOCK_FORECASTS:
        if f["id"] == item_id:
            return f
    return {"error": "Item not found"}

@app.get("/api/v1/inventory/closing")
async def get_expected_closing_inventory():
    return {
        "items": [
            {
                "id": "1",
                "name": "Croissants",
                "expectedLeftover": 5,
                "isPerishable": True
            }
        ]
    }

@app.post("/api/v1/inventory/closing")
async def submit_closing_inventory(items: List[InventoryClosingItem]):
    # Mock submission
    return {"status": "success", "message": f"Updated {len(items)} items"}

@app.get("/api/v1/waste-alerts")
async def get_waste_alerts():
    return {"alerts": MOCK_WASTE_ALERTS}

@app.post("/api/v1/items")
async def create_item(item: ItemModel):
    # Mock creation - in real life this flags isNew=True for TSB
    return {"status": "success", "message": f"Item {item.name} created and tagged for cold-start"}

@app.get("/api/v1/items")
async def get_items():
    return {"items": [
        {"id": "1", "name": "Croissants", "category": "Bakery", "unit": "Units", "isPerishable": True}
    ]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
