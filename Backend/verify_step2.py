import urllib.request
import urllib.error
import json
import sys

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
print("       STEP 2: ML READ LAYER VERIFICATION         ")
print("==================================================")

# 1. Login
status, res = req("/auth/login", method="POST", data={"email": "admin@test.com", "password": "123456"})
assert status == 200, f"Login failed: {res}"
token = res["access_token"]
user_id = res["user_id"]
print(f"[OK] 1. Authenticated as admin@test.com (User: {user_id})")

# 2. Seed realistic bakery items if not already present
status, items_res = req("/items", token=token)
existing_names = [i["name"] for i in items_res.get("items", [])]

bakery_items = [
    {"name": "Croissants", "category": "Bakery", "unit": "Units", "currentStock": 12, "isPerishable": True, "price": 3.50},
    {"name": "Traditional Baguette", "category": "Bakery", "unit": "Units", "currentStock": 8, "isPerishable": True, "price": 2.80},
    {"name": "Pain au Chocolat", "category": "Bakery", "unit": "Units", "currentStock": 15, "isPerishable": True, "price": 3.75},
    {"name": "Whole Milk", "category": "Dairy", "unit": "GAL", "currentStock": 4, "isPerishable": True, "price": 4.50},
    {"name": "Espresso Beans", "category": "Beverage", "unit": "LBS", "currentStock": 20, "isPerishable": False, "price": 14.00},
]

for b in bakery_items:
    if b["name"] not in existing_names:
        s, c = req("/items", method="POST", data=b, token=token)
        print(f"     + Created item: {b['name']} ({s})")

# Re-fetch items
status, items_res = req("/items", token=token)
items = items_res["items"]
print(f"[OK] 2. Inventory contains {len(items)} active items in Atlas.")

# 3. Test GET /api/v1/forecasts/today (The primary dashboard endpoint)
status, dashboard = req("/forecasts/today", token=token)
assert status == 200, f"Failed GET /forecasts/today: {dashboard}"
print("\n[OK] 3. Dashboard endpoint (GET /api/v1/forecasts/today) responded 200:")
print(f"     - Summary: {dashboard['summary']}")
print(f"     - Total items: {dashboard['total_items']}")
print(f"     - Action required: {dashboard['action_required_count']}")

first_item = dashboard["items"][0]
print(f"     - Sample item: {first_item['name']}")
print(f"       * Current Stock: {first_item['currentStock']} {first_item['unit']}")
print(f"       * Predicted Demand: {first_item['predictedDemand']}")
print(f"       * Safety Stock: {first_item['safetyStock']}")
print(f"       * Restock Quantity: {first_item['restockQuantity']}")
print(f"       * Stock Progress: {first_item['stockProgress']}")
print(f"       * Confidence Interval: {first_item['confidence_interval']} (Point-estimate lock)")
print(f"       * Risk Level: {first_item['riskLevel']}")

# Assert architectural locks
assert first_item["confidence_interval"] is None, "Violation: confidence_interval must be null"
assert "restockQuantity" in first_item, "Missing restockQuantity"
assert "stockProgress" in first_item, "Missing stockProgress"

# 4. Test GET /api/v1/forecasts/{item_id} (Item detail & chart screen)
test_item_id = first_item["id"]
status, detail = req(f"/forecasts/{test_item_id}", token=token)
assert status == 200, f"Failed GET /forecasts/{test_item_id}: {detail}"
print(f"\n[OK] 4. Item Detail endpoint (GET /api/v1/forecasts/{test_item_id}) responded 200:")
print(f"     - Name: {detail['name']}")
print(f"     - Historical 7d data points: {len(detail['historical_chart'])}")
print(f"     - Forecast 7d data points: {len(detail['forecast_chart'])}")
print(f"     - Sample Historical Day: {detail['historical_chart'][0]}")
print(f"     - Sample Forecast Day: {detail['forecast_chart'][0]}")

# 5. Test POST /api/v1/items/{item_id}/restock (Confirm restock action)
initial_stock = first_item["currentStock"]
status, restock_res = req(f"/items/{test_item_id}/restock", method="POST", data={"quantity": 10}, token=token)
assert status == 200, f"Restock failed: {restock_res}"
assert restock_res["newStock"] == initial_stock + 10
print(f"\n[OK] 5. Restock Action (POST /api/v1/items/{test_item_id}/restock) verified:")
print(f"     - Added: {restock_res['added']}")
print(f"     - Old Stock: {initial_stock} -> New Stock: {restock_res['newStock']}")

# 6. Test PUT /api/v1/items/{item_id}
status, update_res = req(f"/items/{test_item_id}", method="PUT", data={"price": 4.25}, token=token)
assert status == 200, f"Update failed: {update_res}"
assert update_res["item"]["price"] == 4.25
print(f"\n[OK] 6. Item Update (PUT /api/v1/items/{test_item_id}) verified: Price updated to 4.25")

print("\n==================================================")
print("   >>> STEP 2 COMPLETE: ALL 6 TESTS PASSED! <<<   ")
print("==================================================")
