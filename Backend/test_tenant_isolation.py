import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
import main
from main import app, create_access_token

def test_tenant_isolation():
    print("=" * 70)
    print("      RESTOCKIQ: MULTI-TENANT ISOLATION AUDIT & VERIFICATION       ")
    print("=" * 70)

    # 1. Setup two distinct tenants
    user_a = {
        "_id": "tenant_alpha_001",
        "name": "Cafe Alpha (Owner A)",
        "email": "owner_a@alpha.com",
        "role": "owner",
    }
    user_b = {
        "_id": "tenant_beta_002",
        "name": "Bistro Beta (Owner B)",
        "email": "owner_b@beta.com",
        "role": "owner",
    }

    token_a = create_access_token({"sub": user_a["_id"], "role": user_a["role"]})
    token_b = create_access_token({"sub": user_b["_id"], "role": user_b["role"]})

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # In-memory mock collection for strict isolation testing
    items_store = {
        "item_b_100": {
            "_id": "item_b_100",
            "owner_id": user_b["_id"],
            "name": "Beta Signature Sourdough",
            "category": "Bakery",
            "unit": "Units",
            "currentStock": 15,
            "isPerishable": True,
            "price": 6.50,
            "predictedDemand": 30,
            "safetyStock": 10,
            "riskLevel": "normal",
            "salesHistory": [],
            "updatedAt": "2026-10-17T00:00:00Z",
        }
    }

    # Mock DB find/update/delete operations matching real Atlas semantics
    class MockCursor:
        def __init__(self, items):
            self._items = items

        def __aiter__(self):
            return self._gen()

        async def _gen(self):
            for item in self._items:
                yield item

        async def to_list(self, length=None):
            return list(self._items)

    mock_db = MagicMock()

    async def mock_find_one_user(query):
        uid = query.get("_id")
        if uid == user_a["_id"]:
            return user_a
        elif uid == user_b["_id"]:
            return user_b
        return None

    mock_db.users.find_one = AsyncMock(side_effect=mock_find_one_user)

    def mock_find_items(query, *args, **kwargs):
        owner_id = query.get("owner_id")
        matching = [item for item in items_store.values() if item.get("owner_id") == owner_id]
        return MockCursor(matching)

    mock_db.items.find = MagicMock(side_effect=mock_find_items)

    async def mock_find_one_item(query, *args, **kwargs):
        item_id = query.get("_id")
        owner_id = query.get("owner_id")
        item = items_store.get(item_id)
        if item and (owner_id is None or item.get("owner_id") == owner_id):
            return item
        return None

    mock_db.items.find_one = AsyncMock(side_effect=mock_find_one_item)

    async def mock_update_one_item(filter_q, update_q, *args, **kwargs):
        item_id = filter_q.get("_id")
        owner_id = filter_q.get("owner_id")
        item = items_store.get(item_id)
        res = MagicMock()
        if item and (owner_id is None or item.get("owner_id") == owner_id):
            if "$set" in update_q:
                item.update(update_q["$set"])
            res.modified_count = 1
            res.matched_count = 1
        else:
            res.modified_count = 0
            res.matched_count = 0
        return res

    mock_db.items.update_one = AsyncMock(side_effect=mock_update_one_item)

    async def mock_delete_one_item(filter_q, *args, **kwargs):
        item_id = filter_q.get("_id")
        owner_id = filter_q.get("owner_id")
        item = items_store.get(item_id)
        res = MagicMock()
        if item and (owner_id is None or item.get("owner_id") == owner_id):
            del items_store[item_id]
            res.deleted_count = 1
        else:
            res.deleted_count = 0
        return res

    mock_db.items.delete_one = AsyncMock(side_effect=mock_delete_one_item)

    forecasts_store = {
        "fc_b_100": {
            "item_id": "item_b_100",
            "owner_id": user_b["_id"],
            "forecast_date": "2026-10-29",
            "predictedDemand": 40,
            "safetyStock": 10,
        }
    }

    async def mock_find_one_forecast(query, *args, **kwargs):
        item_id = query.get("item_id")
        owner_id = query.get("owner_id")
        for fc in forecasts_store.values():
            if fc.get("item_id") == item_id and (owner_id is None or fc.get("owner_id") == owner_id):
                return fc
        return None

    mock_db.forecasts.find_one = AsyncMock(side_effect=mock_find_one_forecast)

    async def mock_delete_many_forecasts(query, *args, **kwargs):
        item_id = query.get("item_id")
        owner_id = query.get("owner_id")
        to_del = [k for k, fc in forecasts_store.items() if fc.get("item_id") == item_id and (owner_id is None or fc.get("owner_id") == owner_id)]
        for k in to_del:
            del forecasts_store[k]
        res = MagicMock()
        res.deleted_count = len(to_del)
        return res

    mock_db.forecasts.delete_many = AsyncMock(side_effect=mock_delete_many_forecasts)
    mock_db.daily_sales.count_documents = AsyncMock(return_value=0)

    # Patch main.db
    original_db = main.db
    main.db = mock_db

    results = []

    try:
        client = TestClient(app)

        # Endpoint 1: List items (User A should NOT see User B's item)
        r1 = client.get("/api/v1/items", headers=headers_a)
        items_a = r1.json().get("items", [])
        leak1 = any(it["id"] == "item_b_100" for it in items_a)
        results.append(("GET /api/v1/items", "Filter by owner_id", "Blocked (Hidden)", r1.status_code, not leak1))

        # Endpoint 2: Today's Forecast (User A should NOT see User B's forecast)
        r2 = client.get("/api/v1/forecasts/today", headers=headers_a)
        fc_a = r2.json().get("items", [])
        leak2 = any(it["id"] == "item_b_100" for it in fc_a)
        results.append(("GET /api/v1/forecasts/today", "Filter by owner_id", "Blocked (Hidden)", r2.status_code, not leak2))

        # Endpoint 3: Direct Item Forecast Detail (User A requests User B's item_id)
        r3 = client.get("/api/v1/forecasts/item_b_100", headers=headers_a)
        results.append(("GET /api/v1/forecasts/{id}", "Enforces owner_id", "404 Not Found", r3.status_code, r3.status_code == 404))

        # Endpoint 4: Direct Item Update (User A attempts to modify User B's price/stock)
        r4 = client.put("/api/v1/items/item_b_100", json={"currentStock": 999}, headers=headers_a)
        results.append(("PUT /api/v1/items/{id}", "Enforces owner_id", "404 Not Found", r4.status_code, r4.status_code == 404))

        # Endpoint 5: Direct Item Restock (User A attempts to restock User B's item)
        r5 = client.post("/api/v1/items/item_b_100/restock", json={"quantity": 50}, headers=headers_a)
        results.append(("POST /api/v1/items/{id}/restock", "Enforces owner_id", "404 Not Found", r5.status_code, r5.status_code == 404))

        # Endpoint 6: Direct Item Delete (User A attempts to delete User B's item)
        r6 = client.delete("/api/v1/items/item_b_100", headers=headers_a)
        results.append(("DELETE /api/v1/items/{id}", "Enforces owner_id", "404 Not Found", r6.status_code, r6.status_code == 404))

        # Endpoint 7: Intraday Sale (User A attempts to record sales for User B's item)
        r7 = client.post("/api/v1/sales/intraday", json={"item_id": "item_b_100", "quantity": 5}, headers=headers_a)
        results.append(("POST /api/v1/sales/intraday", "Enforces owner_id", "404 Not Found", r7.status_code, r7.status_code == 404))

        # Endpoint 8: Waste Alert Actions (User A attempts to discount/donate/dismiss User B's item)
        r8 = client.post("/api/v1/waste-alerts/item_b_100/apply-discount", headers=headers_a)
        results.append(("POST /api/v1/waste-alerts/{id}/apply-discount", "Enforces owner_id", "404 Not Found", r8.status_code, r8.status_code == 404))

        r9 = client.post("/api/v1/waste-alerts/item_b_100/apply-bundle", headers=headers_a)
        results.append(("POST /api/v1/waste-alerts/{id}/apply-bundle", "Enforces owner_id", "404 Not Found", r9.status_code, r9.status_code == 404))

        r10 = client.post("/api/v1/waste-alerts/item_b_100/dismiss", headers=headers_a)
        results.append(("POST /api/v1/waste-alerts/{id}/dismiss", "Enforces owner_id", "404 Not Found", r10.status_code, r10.status_code == 404))

        # Verification: Legitimate owner (User B) CAN update and read their own item
        r_b_read = client.get("/api/v1/forecasts/item_b_100", headers=headers_b)
        assert r_b_read.status_code == 200, f"Owner B could not read own item: {r_b_read.status_code}"

        r_b_update = client.put("/api/v1/items/item_b_100", json={"price": 7.25}, headers=headers_b)
        assert r_b_update.status_code == 200, f"Owner B could not update own item: {r_b_update.status_code}"

        # Confirm stock was NOT tampered with by User A's attempts
        assert items_store["item_b_100"]["currentStock"] == 15, "Data breach: User A's restock/sale modified User B's stock!"
        assert "fc_b_100" in forecasts_store, "Data breach: User A's delete deleted User B's forecast!"

        # Legitimate delete by Owner B
        r_b_del = client.delete("/api/v1/items/item_b_100", headers=headers_b)
        assert r_b_del.status_code == 200, f"Owner B could not delete own item: {r_b_del.status_code}"
        assert "item_b_100" not in items_store, "Item should be deleted from items_store"
        assert "fc_b_100" not in forecasts_store, "Cascading forecast should be deleted by legitimate owner"

    finally:
        main.db = original_db

    # Print Report Table
    print(f"\n{'ENDPOINT':<40} | {'PROTECTION MECHANISM':<22} | {'EXPECTED':<16} | {'STATUS':<7} | {'VERDICT'}")
    print("-" * 105)
    all_passed = True
    for ep, mech, exp, status, passed in results:
        v_str = "PASS [SECURE]" if passed else "FAIL [LEAK]"
        if not passed:
            all_passed = False
        print(f"{ep:<40} | {mech:<22} | {exp:<16} | {status:<7} | {v_str}")
    print("-" * 105)
    print(f"Overall Multi-Tenant Isolation Audit: {'PASSED (ZERO LEAKS)' if all_passed else 'FAILED'}\n")
    assert all_passed, "Tenant isolation audit failed!"

if __name__ == "__main__":
    test_tenant_isolation()
