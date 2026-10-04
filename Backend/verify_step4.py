import urllib.request
import urllib.error
import json
import subprocess
import sys
from datetime import datetime, timezone

BASE = "http://127.0.0.1:8000/api/v1"

def req(path, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    r = urllib.request.Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

print("==================================================")
print("   STEP 4: SPARSE TIER & COLD START VERIFICATION   ")
print("==================================================")

# 1. Login
status, res = req("/auth/login", method="POST", data={"email": "admin@test.com", "password": "123456"})
assert status == 200, f"Login failed: {res}"
token = res["access_token"]
print("[OK] 1. Authenticated as admin@test.com")

# 2. Create brand new item (0 days history, cold-start)
new_item_payload = {
    "name": "Artisan Sourdough Loaf",
    "category": "Breads & Baguettes",
    "unit": "Loaves",
    "currentStock": 3,
    "isPerishable": True,
    "price": 6.50
}

status, create_res = req("/items", method="POST", data=new_item_payload, token=token)
assert status == 201, f"Failed to create new item: {create_res}"
item_id = create_res["item_id"]
print(f"[OK] 2. Created brand new item: 'Artisan Sourdough Loaf' (ID: {item_id})")
print(f"        Tagged with n=0 sales history (Pure Cold Start)")

# 3. Read expected p90 prior from category_priors_percentiles.json
with open("E:/CAP/ML/data/processed/category_priors_percentiles.json", "r") as f:
    priors = json.load(f)

now = datetime.now(timezone.utc)
dow_str = str(now.weekday())
expected_p90 = int(round(priors["Breads & Baguettes"][dow_str]["p90"]))
print(f"[ML] 3. Expected Day {dow_str} Prior for 'Breads & Baguettes': {expected_p90} units")

# 4. Run the ML Batch Job (batch_forecast.py)
print("\n[BATCH] 4. Executing batch_forecast.py...")
proc = subprocess.run(
    ["E:/CAP/ML/venv/Scripts/python.exe", "E:/CAP/ML/batch_forecast.py"],
    capture_output=True,
    text=True
)
print(proc.stdout)
assert proc.returncode == 0, f"batch_forecast.py failed:\n{proc.stderr}"

# 5. Fetch forecast via FastAPI ML Read Layer
status, forecast_detail = req(f"/forecasts/{item_id}", token=token)
assert status == 200, f"Failed to fetch forecast: {forecast_detail}"

print(f"\n[OK] 5. Fetched Cold-Start Forecast for '{forecast_detail['name']}':")
print(f"     - Predicted Demand: {forecast_detail['predictedDemand']}")
print(f"     - Expected Demand:  {expected_p90}")
print(f"     - Safety Stock:     {forecast_detail['safetyStock']}")
print(f"     - Current Stock:    {forecast_detail['currentStock']}")
print(f"     - Restock Qty:      {forecast_detail['restockQuantity']}")
print(f"     - Confidence Int:   {forecast_detail['confidence_interval']} (Point-estimate lock)")
print(f"     - Rationale:        {forecast_detail['description']}")

# 6. Verify strict equality against category 90th percentile prior
assert forecast_detail["predictedDemand"] == expected_p90, (
    f"Cold-start violation: Expected {expected_p90}, got {forecast_detail['predictedDemand']}"
)
assert forecast_detail["confidence_interval"] is None, "Violation: confidence_interval must be null"

print("\n==================================================")
print(f" >>> STEP 4 PASSED: Predicted Demand strictly equals")
print(f"     Category 90th Percentile Prior ({expected_p90} units)! <<<")
print("==================================================")
