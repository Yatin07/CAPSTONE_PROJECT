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
print("     STEP 5: WASTE ACTION ENGINE VERIFICATION     ")
print("==================================================")

# 1. Login
status, res = req("/auth/login", method="POST", data={"email": "admin@test.com", "password": "123456"})
assert status == 200, f"Login failed: {res}"
token = res["access_token"]
print("[OK] 1. Authenticated as admin@test.com")

# 2. Find a perishable item with inventory
status, items_res = req("/items", token=token)
items = items_res.get("items", [])
perishable_items = [i for i in items if i.get("isPerishable") and i.get("currentStock", 0) > 0]
assert len(perishable_items) > 0, "No perishable items found in inventory"

test_item = perishable_items[0]
test_item_id = test_item["id"]
print(f"[OK] 2. Selected perishable item: '{test_item['name']}' (Stock: {test_item['currentStock']} {test_item['unit']})")

# 3. Record slow intraday sales (e.g. only 2 units sold)
status, sale_res = req("/sales/intraday", method="POST", data={"item_id": test_item_id, "quantity": 2}, token=token)
assert status == 201, f"Failed to record intraday sale: {sale_res}"
print(f"[OK] 3. Recorded intraday sale of 2 units (Total sold today: {sale_res['totalIntradaySales']})")

# 4. Fetch waste alerts from Waste Action Engine
status, alerts_res = req("/waste-alerts", token=token)
assert status == 200, f"Failed to fetch waste alerts: {alerts_res}"

alerts = alerts_res.get("alerts", [])
print(f"\n[OK] 4. Waste Action Engine returned {len(alerts)} active alerts:")
matching_alerts = [a for a in alerts if a["id"] == test_item_id]
assert len(matching_alerts) > 0, f"Expected item '{test_item['name']}' to be flagged for slow pace!"

alert = matching_alerts[0]
print(f"     - Item:               {alert['itemName']}")
print(f"     - Sales Text:         {alert['salesText'].replace(chr(10), ' ')}")
print(f"     - Sales Pace Ratio:   {alert['salesPaceRatio']}")
print(f"     - Expected Sales:     {alert['expectedSales']}")
print(f"     - Actual Sold:        {alert['actualSold']}")
print(f"     - Severity:           {alert['severityLabel']} ({alert['severityColor']})")
print(f"     - Static Discount:    {alert['discount_pct']}% (Locked Architectural Mapping)")
print(f"     - Recommended Action: {alert['recommendedActionText']}")
print(f"     - Primary Action:     {alert['primaryActionText']}")
print(f"     - Layout Style:       {alert['layoutStyle']}")
print(f"     - Food Type Key:      {alert['foodType']}")

# Assert structural requirements for Flutter UI
assert "discount_pct" in alert, "Missing discount_pct"
assert alert["discount_pct"] in [10, 20, 30], "Discount percentage must be locked static mapping"
assert alert["layoutStyle"] in ["stacked", "sideBySide"], "Invalid layoutStyle"

# 5. Test Action: Apply Discount
status, discount_res = req(f"/waste-alerts/{test_item_id}/apply-discount", method="POST", token=token)
assert status == 200, f"Failed to apply discount: {discount_res}"
print(f"\n[OK] 5. Mitigation Action: Applied discount successfully:")
print(f"     - Old Price: ${discount_res['oldPrice']} -> New Discounted Price: ${discount_res['newPrice']}")

# 6. Test Action: Apply Bundle
status, bundle_res = req(f"/waste-alerts/{test_item_id}/apply-bundle", method="POST", token=token)
assert status == 200, f"Failed to apply bundle: {bundle_res}"
print(f"\n[OK] 6. Mitigation Action: Apply combo bundle successfully:")
print(f"     - Message: {bundle_res['message']}")

# 7. Test Action: Dismiss Alert
status, dismiss_res = req(f"/waste-alerts/{test_item_id}/dismiss", method="POST", token=token)
assert status == 200, f"Failed to dismiss alert: {dismiss_res}"

# Re-check alerts: dismissed item should not appear
status, updated_alerts_res = req("/waste-alerts", token=token)
dismissed_check = [a for a in updated_alerts_res.get("alerts", []) if a["id"] == test_item_id]
assert len(dismissed_check) == 0, "Dismissed item still appears in waste alerts!"
print(f"\n[OK] 7. Dismiss Action: Verified item no longer returned in active waste alerts.")

print("\n==================================================")
print("   >>> STEP 5 COMPLETE: ALL 7 TESTS PASSED! <<<   ")
print("==================================================")
