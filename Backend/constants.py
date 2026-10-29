import os

# Centralized fallback constants for cold-start / unforecasted items
DEFAULT_FALLBACK_DEMAND: int = 20
DEFAULT_FALLBACK_SAFETY: int = 4

# Pure-Python Category Priors for Immediate Cold-Start Item Creation (Step 1e)
CATEGORY_PRIORS = {
    "Bakery": {"predictedDemand": 24, "safetyStock": 7, "norm_cat": "Breads & Baguettes"},
    "Beverage": {"predictedDemand": 18, "safetyStock": 5, "norm_cat": "Beverages"},
    "Food": {"predictedDemand": 15, "safetyStock": 5, "norm_cat": "Prepared Food"},
    "Dessert": {"predictedDemand": 12, "safetyStock": 4, "norm_cat": "Desserts & Pastries"},
    "Snack": {"predictedDemand": 10, "safetyStock": 3, "norm_cat": "Snacks"},
    "Other": {"predictedDemand": 10, "safetyStock": 3, "norm_cat": "General Merchandise"},
}

# Store operating hours and timezone configuration (IANA)
STORE_OPEN_HOUR: float = float(os.getenv("STORE_OPEN_HOUR", "8.0"))
STORE_CLOSE_HOUR: float = float(os.getenv("STORE_CLOSE_HOUR", "20.0"))
DEFAULT_STORE_TIMEZONE: str = os.getenv("STORE_TIMEZONE", "UTC")
