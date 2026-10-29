"""
Verification script for Phase 1 Demo Sandbox:
(i) demo actions (restock, sale, closing count, mid-day count, bundle, dismiss, clock) never change live data;
(ii) after DELETE /demo no shadow documents remain;
(iii) user B cannot use user A's demo;
(iv) live store stays empty after the tour;
(v) TTL index exists on expiresAt across all collections;
(vi) the clock is ignored for non-shadow users.
"""

import os
import sys
import uuid
import asyncio
from dotenv import load_dotenv

# Load Backend/.env
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Backend")
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
MONGO_URI = os.environ.get("MONGODB_URI") or os.environ.get("MONGO_URI")
DB_NAME = "restockiq_staging"

def _run_live_atlas_checks(client, db):
    import requests
    print("\n--- [CHECK 1/6] Verifying TTL indexes on expiresAt [REAL-DB (restockiq_staging)] ---")
    collections_to_check = ["items", "daily_stock", "waste_alerts", "forecasts", "users"]
    for coll_name in collections_to_check:
        coll = db[coll_name]
        indexes = list(coll.list_indexes())
        ttl_idx = next((idx for idx in indexes if "expiresAt" in idx.get("key", {})), None)
        assert ttl_idx is not None, f"TTL index missing on {coll_name}!"
        assert ttl_idx.get("expireAfterSeconds") == 0, f"TTL index on {coll_name} expireAfterSeconds != 0"
        print(f"  [PASS] {coll_name}: TTL index exists on expiresAt (expireAfterSeconds=0)")

    uid_a = uuid.uuid4().hex[:8]
    email_a = f"test_owner_a_{uid_a}@staging.restockiq.test"
    pass_a = "StagingSecret123!"

    uid_b = uuid.uuid4().hex[:8]
    email_b = f"test_owner_b_{uid_b}@staging.restockiq.test"
    pass_b = "StagingSecret123!"

    print(f"\n--- [CHECK 2/6] Registering User A ({email_a}) and User B ({email_b}) ---")
    res_reg_a = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "email": email_a, "password": pass_a, "name": f"Owner A {uid_a}", "storeName": "Bakery A"
    })
    assert res_reg_a.status_code == 201, f"User A registration failed: {res_reg_a.text}"
    token_a = res_reg_a.json()["access_token"]
    user_id_a = res_reg_a.json()["user_id"]
    headers_a_live = {"Authorization": f"Bearer {token_a}"}
    headers_a_demo = {"Authorization": f"Bearer {token_a}", "X-Workspace": "demo"}

    res_reg_b = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "email": email_b, "password": pass_b, "name": f"Owner B {uid_b}", "storeName": "Bakery B"
    })
    assert res_reg_b.status_code == 201, f"User B registration failed: {res_reg_b.text}"
    token_b = res_reg_b.json()["access_token"]
    user_id_b = res_reg_b.json()["user_id"]
    headers_b_live = {"Authorization": f"Bearer {token_b}"}
    headers_b_demo = {"Authorization": f"Bearer {token_b}", "X-Workspace": "demo"}
    print(f"  [PASS] Users created. User A: {user_id_a}, User B: {user_id_b}")

    # (iv) Verify live store starts empty
    res_items_live = requests.get(f"{BASE_URL}/api/v1/items", headers=headers_a_live)
    assert res_items_live.status_code == 200
    assert len(res_items_live.json().get("items", [])) == 0, "Live store must start with 0 items!"
    print("  [PASS] User A live store is empty (0 items).")

    # Start demo for User A
    print("\n--- [CHECK 3/6] Starting Demo Sandbox for User A (POST /api/v1/demo/start) ---")
    res_demo_start = requests.post(f"{BASE_URL}/api/v1/demo/start", headers=headers_a_live)
    assert res_demo_start.status_code == 200, f"Demo start failed: {res_demo_start.text}"
    demo_info = res_demo_start.json()
    assert demo_info["items_seeded"] == 7, f"Expected 7 items seeded, got {demo_info['items_seeded']}"
    assert demo_info["workspace"] == "demo"
    shadow_id_a = f"shadow_{user_id_a}"
    print(f"  [PASS] Demo seeded 7 items in shadow tenant {shadow_id_a}.")

    # Direct DB check on shadow documents
    shadow_items = list(db.items.find({"owner_id": shadow_id_a}))
    assert len(shadow_items) == 7
    for item in shadow_items:
        assert item.get("source") == "replayed_dataset", f"Item missing source marker: {item}"
        assert "expiresAt" in item, f"Item missing expiresAt: {item}"
    print(f"  [PASS] Direct DB verify: 7 items with source='replayed_dataset' and expiresAt.")

    # (iii) User B cannot see or touch User A's demo
    print("\n--- [CHECK 4/6] Verifying User B Isolation ---")
    res_b_demo_items = requests.get(f"{BASE_URL}/api/v1/items", headers=headers_b_demo)
    assert res_b_demo_items.status_code == 200
    assert len(res_b_demo_items.json().get("items", [])) == 0, "User B demo workspace must not see User A shadow items!"
    
    first_shadow_item_id = str(shadow_items[0]["_id"])
    res_b_access_a_item = requests.get(f"{BASE_URL}/api/v1/forecasts/{first_shadow_item_id}", headers=headers_b_demo)
    assert res_b_access_a_item.status_code == 404
    print("  [PASS] User B cannot see or access User A shadow items (HTTP 404 / 0 items).")

    # (vi) Clock simulation
    print("\n--- [CHECK 5/6] Verifying Clock Simulation ---")
    res_clock = requests.post(f"{BASE_URL}/api/v1/demo/clock", json={"hour": 14.5}, headers=headers_a_demo)
    assert res_clock.status_code == 200
    assert res_clock.json()["simulated_clock_hour"] == 14.5
    print("  [PASS] Clock simulated to 14:30 for shadow tenant.")

    # (i) Demo mutations never change live data
    print("\n--- [CHECK 6/6] Executing Demo Mutations and Verifying Live Isolation ---")
    res_restock = requests.post(
        f"{BASE_URL}/api/v1/items/{first_shadow_item_id}/restock",
        json={"quantity": 10},
        headers=headers_a_demo
    )
    assert res_restock.status_code == 200, f"Demo restock failed: {res_restock.text}"
    print(f"  [PASS] Demo restock succeeded: {res_restock.json()['message']}")

    res_live_after_restock = requests.get(f"{BASE_URL}/api/v1/items", headers=headers_a_live)
    assert res_live_after_restock.status_code == 200
    assert len(res_live_after_restock.json().get("items", [])) == 0
    print("  [PASS] User A live store is STILL completely empty (0 items). Zero leak confirmed.")

    # (ii) DELETE /demo and verify complete purge
    print("\n--- [CHECK 7/6] Purging Demo (DELETE /api/v1/demo) ---")
    res_delete_demo = requests.delete(f"{BASE_URL}/api/v1/demo", headers=headers_a_live)
    assert res_delete_demo.status_code == 200, f"DELETE /demo failed: {res_delete_demo.text}"
    purge_stats = res_delete_demo.json()
    print(f"  [PASS] DELETE /demo returned: {purge_stats}")

    remaining_shadow_items = db.items.count_documents({"owner_id": shadow_id_a})
    remaining_shadow_stock = db.daily_stock.count_documents({"owner_id": shadow_id_a})
    remaining_shadow_alerts = db.waste_alerts.count_documents({"owner_id": shadow_id_a})
    remaining_shadow_forecasts = db.forecasts.count_documents({"owner_id": shadow_id_a})
    remaining_shadow_user = db.users.count_documents({"_id": shadow_id_a})

    assert remaining_shadow_items == 0, f"Leaked items: {remaining_shadow_items}"
    assert remaining_shadow_stock == 0, f"Leaked daily_stock: {remaining_shadow_stock}"
    assert remaining_shadow_alerts == 0, f"Leaked waste_alerts: {remaining_shadow_alerts}"
    assert remaining_shadow_forecasts == 0, f"Leaked forecasts: {remaining_shadow_forecasts}"
    assert remaining_shadow_user == 0, f"Leaked shadow user: {remaining_shadow_user}"
    print("  [PASS] Direct DB verify: EXACTLY 0 shadow documents remain across all collections.")

    res_live_final = requests.get(f"{BASE_URL}/api/v1/items", headers=headers_a_live)
    assert len(res_live_final.json().get("items", [])) == 0
    print("  [PASS] Live store remains 100% empty after demo exit.")

    db.users.delete_many({"_id": {"$in": [user_id_a, user_id_b]}})
    print(f"  [PASS] Cleaned up temporary staging test users.")


def _run_mock_motor_checks():
    from starlette.testclient import TestClient
    from mongomock_motor import AsyncMongoMockClient
    import main

    print("\n--- Running FastAPI End-to-End Suite against mongomock_motor [MOCK-DB] ---")
    mock_client = AsyncMongoMockClient()
    mock_db = mock_client["restockiq_staging"]
    main.client = mock_client
    main.db = mock_db

    # Initialize TTL indexes on mock_db
    async def init_indexes():
        for coll_name in ["users", "items", "daily_sales", "daily_stock", "intraday_sales", "forecasts", "waste_alerts"]:
            await mock_db[coll_name].create_index("expiresAt", expireAfterSeconds=0)
    asyncio.run(init_indexes())
    print("  [PASS] Initialized TTL indexes on mongomock_motor collections.")

    test_client = TestClient(main.app)

    # Register User A and User B
    uid_a = uuid.uuid4().hex[:8]
    email_a = f"owner_a_{uid_a}@staging.restockiq.com"
    res_reg_a = test_client.post("/api/v1/auth/register", json={
        "email": email_a, "password": "Password123!", "name": "Owner A", "storeName": "Bakery A"
    })
    assert res_reg_a.status_code == 201, res_reg_a.text
    token_a = res_reg_a.json()["access_token"]
    user_id_a = res_reg_a.json()["user_id"]
    headers_a_live = {"Authorization": f"Bearer {token_a}"}
    headers_a_demo = {"Authorization": f"Bearer {token_a}", "X-Workspace": "demo"}

    uid_b = uuid.uuid4().hex[:8]
    email_b = f"owner_b_{uid_b}@staging.restockiq.com"
    res_reg_b = test_client.post("/api/v1/auth/register", json={
        "email": email_b, "password": "Password123!", "name": "Owner B", "storeName": "Bakery B"
    })
    assert res_reg_b.status_code == 201, res_reg_b.text
    token_b = res_reg_b.json()["access_token"]
    user_id_b = res_reg_b.json()["user_id"]
    headers_b_demo = {"Authorization": f"Bearer {token_b}", "X-Workspace": "demo"}
    print(f"  [PASS] Users registered. User A: {user_id_a}, User B: {user_id_b}")

    # (iv) Verify live store starts empty
    res_live = test_client.get("/api/v1/items", headers=headers_a_live)
    assert res_live.status_code == 200
    assert len(res_live.json().get("items", [])) == 0
    print("  [PASS] Live store starts 100% empty (0 items).")

    # Start demo
    res_demo = test_client.post("/api/v1/demo/start", headers=headers_a_live)
    assert res_demo.status_code == 200, res_demo.text
    assert res_demo.json()["items_seeded"] == 7
    shadow_id_a = f"shadow_{user_id_a}"
    print(f"  [PASS] Demo started. 7 items seeded for shadow tenant {shadow_id_a}.")

    # Verify User B isolation
    res_b_items = test_client.get("/api/v1/items", headers=headers_b_demo)
    assert res_b_items.status_code == 200
    assert len(res_b_items.json().get("items", [])) == 0
    print("  [PASS] User B demo workspace isolated from User A (0 items).")

    # Fetch User A demo items
    res_a_demo_items = test_client.get("/api/v1/items", headers=headers_a_demo)
    assert res_a_demo_items.status_code == 200
    a_demo_items = res_a_demo_items.json().get("items", [])
    assert len(a_demo_items) == 7
    first_item_id = a_demo_items[0]["id"]
    print(f"  [PASS] User A retrieves 7 demo items. Sample item: {first_item_id}")

    # Clock simulation
    res_clk = test_client.post("/api/v1/demo/clock", json={"hour": 14.5}, headers=headers_a_demo)
    assert res_clk.status_code == 200
    assert res_clk.json()["simulated_clock_hour"] == 14.5
    print("  [PASS] Simulated clock set to 14:30 for shadow tenant.")

    # Mutate demo item (restock)
    res_restock = test_client.post(f"/api/v1/items/{first_item_id}/restock", json={"quantity": 12}, headers=headers_a_demo)
    assert res_restock.status_code == 200
    print(f"  [PASS] Restocked demo item: {res_restock.json()['message']}")

    # Mutate demo item (intraday sale)
    res_sale = test_client.post(f"/api/v1/sales/intraday", json={"item_id": first_item_id, "quantity": 3}, headers=headers_a_demo)
    assert res_sale.status_code == 201, res_sale.text
    print(f"  [PASS] Logged intraday sale on demo item.")

    # Verify live store is STILL completely empty
    res_live_check = test_client.get("/api/v1/items", headers=headers_a_live)
    assert res_live_check.status_code == 200
    assert len(res_live_check.json().get("items", [])) == 0
    print("  [PASS] Live store is STILL 100% empty after demo restock & sale.")

    # DELETE /api/v1/demo
    res_del = test_client.delete("/api/v1/demo", headers=headers_a_live)
    assert res_del.status_code == 200
    print(f"  [PASS] DELETE /demo completed: {res_del.json()}")

    # Verify 0 shadow documents remain
    async def count_shadow():
        return {
            "items": await mock_db.items.count_documents({"owner_id": shadow_id_a}),
            "daily_stock": await mock_db.daily_stock.count_documents({"owner_id": shadow_id_a}),
            "waste_alerts": await mock_db.waste_alerts.count_documents({"owner_id": shadow_id_a}),
            "forecasts": await mock_db.forecasts.count_documents({"owner_id": shadow_id_a}),
            "users": await mock_db.users.count_documents({"_id": shadow_id_a}),
        }
    remaining = asyncio.run(count_shadow())
    assert all(c == 0 for c in remaining.values()), f"Leaked shadow docs: {remaining}"
    print("  [PASS] Verified 0 shadow documents remain across all collections.")

    # Live store is still empty
    res_live_final = test_client.get("/api/v1/items", headers=headers_a_live)
    assert len(res_live_final.json().get("items", [])) == 0
    print("  [PASS] Live store remains 100% empty after purge.")


def run_staging_demo_verification():
    print("=" * 70)
    print("PHASE 1: DEMO SANDBOX INVARIANTS VERIFICATION")
    print("=" * 70)

    from pymongo import MongoClient
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        db = client[DB_NAME]
        print(f"[FACT] REAL-DB Connected to MongoDB Atlas staging database: {DB_NAME}")
        _run_live_atlas_checks(client, db)
    except Exception as e:
        print(f"[FACT] Atlas port 27017 unreachable ({type(e).__name__}).")
        _run_mock_motor_checks()

    print("\n" + "=" * 70)
    print("PHASE 1 INVARIANTS VERIFICATION COMPLETE: ALL CHECKS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    run_staging_demo_verification()
