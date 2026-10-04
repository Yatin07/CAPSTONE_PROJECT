import urllib.request
import urllib.error
import json
import subprocess
import sys
from datetime import datetime

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

print("==================================================================")
print("       RESTOCKIQ: STEP 6 END-TO-END MASTER INTEGRATION AUDIT      ")
print("==================================================================")

# 1. System Heartbeat
status, health = req("/health")
assert status == 200 and health.get("db") == "connected", f"Health check failed: {health}"
print(f"[OK] 1. Cloud Database Health Check: Connected to MongoDB Atlas ({health['timestamp']})")

# 2. Authentication
status, auth = req("/auth/login", method="POST", data={"email": "admin@test.com", "password": "123456"})
assert status == 200, f"Login failed: {auth}"
token = auth["access_token"]
user_id = auth["user_id"]
role = auth["role"]
print(f"[OK] 2. JWT Authentication: Logged in as '{auth['name']}' ({auth['role']})")
print(f"        Token: {token[:35]}...")

# 3. Seed / Verify Catalog Items in Atlas
status, items_res = req("/items", token=token)
items = items_res.get("items", [])
catalog_names = [i["name"] for i in items]
print(f"[OK] 3. Atlas Catalog: {len(items)} items found ({', '.join(catalog_names[:4])}...)")

# 4. Execute ML Batch Job
print("\n[ML] 4. Triggering Unified ML Batch Engine (batch_forecast.py)...")
batch_proc = subprocess.run(
    ["E:/CAP/ML/venv/Scripts/python.exe", "E:/CAP/ML/batch_forecast.py"],
    capture_output=True,
    text=True
)
assert batch_proc.returncode == 0, f"ML Batch Job failed:\n{batch_proc.stderr}"
print("     [OK] Batch Forecasting complete across Primary and Cold-Start Tiers.")

# 5. Verify Main Dashboard Endpoint
status, dash = req("/forecasts/today", token=token)
assert status == 200, f"Dashboard read failed: {dash}"
print(f"\n[OK] 5. Main Dashboard Endpoint (GET /api/v1/forecasts/today):")
print(f"     - Summary Text:        {dash['summary']}")
print(f"     - Total Tracked Items: {dash['total_items']}")
print(f"     - Actions Required:    {dash['action_required_count']}")

# Validate architectural locks on all dashboard items
for it in dash["items"]:
    assert it["confidence_interval"] is None, f"Lock violation on {it['name']}: confidence_interval must be null"
    assert "restockQuantity" in it, f"Missing restockQuantity on {it['name']}"
    assert "stockProgress" in it, f"Missing stockProgress on {it['name']}"
print("     [OK] Verified architectural constraint: all items point-estimates (confidence_interval=null).")

# 6. Deep Dive Forecast for First Item
target_item = dash["items"][0]
item_id = target_item["id"]
status, detail = req(f"/forecasts/{item_id}", token=token)
assert status == 200, f"Item detail failed: {detail}"
print(f"\n[OK] 6. Item Detail Endpoint (GET /api/v1/forecasts/{item_id}):")
print(f"     - Name:              {detail['name']}")
print(f"     - Predicted Demand:  {detail['predictedDemand']} {detail['unit']}")
print(f"     - Safety Stock:      {detail['safetyStock']} {detail['unit']}")
print(f"     - Current Stock:     {detail['currentStock']} {detail['unit']}")
print(f"     - Recommended Order: {detail['restockQuantity']} {detail['unit']}")
print(f"     - Historical 7d:     {len(detail['historical_chart'])} data points ({detail['historical_chart'][-1]['sales']} units on {detail['historical_chart'][-1]['day']})")
print(f"     - Forecast 7d:       {len(detail['forecast_chart'])} data points ({detail['forecast_chart'][0]['predicted']} units on {detail['forecast_chart'][0]['day']})")

# 7. One-Tap Restock Action
old_stock = detail["currentStock"]
status, restock = req(f"/items/{item_id}/restock", method="POST", data={"quantity": 15}, token=token)
assert status == 200 and restock["newStock"] == old_stock + 15, f"Restock failed: {restock}"
print(f"\n[OK] 7. One-Tap Restock Action (POST /api/v1/items/{item_id}/restock):")
print(f"     - Restocked: +15 {detail['unit']}")
print(f"     - Stock Level in Atlas: {old_stock} -> {restock['newStock']} {detail['unit']}")

# 8. Intraday POS Logging & Waste Action Engine
status, sale = req("/sales/intraday", method="POST", data={"item_id": item_id, "quantity": 1}, token=token)
assert status == 201, f"Intraday sale failed: {sale}"
print(f"\n[OK] 8. Intraday POS Event (POST /api/v1/sales/intraday):")
print(f"     - Recorded sale of 1 unit for {detail['name']}. Logged to Atlas 'intraday_sales'.")

status, alerts_data = req("/waste-alerts", token=token)
assert status == 200, f"Waste alerts failed: {alerts_data}"
alerts = alerts_data.get("alerts", [])
print(f"\n[OK] 9. Waste Action Engine (GET /api/v1/waste-alerts):")
print(f"     - Active Risk Alerts: {len(alerts)}")
if len(alerts) > 0:
    first_alert = alerts[0]
    print(f"     - Flagged Item:        {first_alert['itemName']}")
    print(f"     - Pace Ratio:          {first_alert['salesPaceRatio']} ({int(first_alert['salesPaceRatio']*100)}% of expected pace)")
    print(f"     - Risk Severity:       {first_alert['severityLabel']}")
    print(f"     - Discount Assigned:   {first_alert['discount_pct']}% (Locked Static Mapping)")
    print(f"     - Recommended Action:  {first_alert['recommendedActionText']}")

print("\n==================================================================")
print(" >>> STEP 6 COMPLETE: ENTIRE SYSTEM VERIFIED END-TO-END! <<<      ")
print("==================================================================")
