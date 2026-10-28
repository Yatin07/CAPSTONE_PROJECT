import os

# Centralized fallback constants for cold-start / unforecasted items
DEFAULT_FALLBACK_DEMAND: int = 20
DEFAULT_FALLBACK_SAFETY: int = 4

# Store operating hours and timezone configuration (IANA)
STORE_OPEN_HOUR: float = float(os.getenv("STORE_OPEN_HOUR", "8.0"))
STORE_CLOSE_HOUR: float = float(os.getenv("STORE_CLOSE_HOUR", "20.0"))
DEFAULT_STORE_TIMEZONE: str = os.getenv("STORE_TIMEZONE", "UTC")
