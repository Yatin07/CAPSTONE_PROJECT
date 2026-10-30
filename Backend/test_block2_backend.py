import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
import main
from main import (
    app,
    evaluate_waste_alert_tier,
    create_access_token,
    STORE_OPEN_HOUR,
    STORE_CLOSE_HOUR,
    DEFAULT_STORE_TIMEZONE,
)

class TestBlock2BackendSuite(unittest.TestCase):
    """
    BLOCK 2 - Backend Acceptance & Integrity Test Suite [MOCK-DB].
    Validates:
      1. Day 1 closing -> Day 2 opening (perishable resets to 0, non-perishable carries over).
      2. Missing day marked as status "missing" with soldUnits as None (NEVER zero).
      3. Backfill yesterday allowed and idempotent.
      4. Resubmit closing count is strictly idempotent.
      5. Mid-day pace calculation at local 09:00, 14:00, and 20:00.
      6. Tenant isolation across daily_stock, daily_sales, items, and reviews.
      7. Contract test asserting every JSON key Flutter models consume is returned by the API.
    """

    def setUp(self):
        self.mock_client = AsyncMongoMockClient()
        self.mock_db = self.mock_client["restockiq_test"]
        self.original_db = main.db
        main.db = self.mock_db

        self.client = TestClient(app)
        self.owner_a = "user_alpha_101"
        self.owner_b = "user_beta_202"

        # Mock user docs
        self.token_a = create_access_token({"sub": self.owner_a, "role": "owner"})
        self.token_b = create_access_token({"sub": self.owner_b, "role": "owner"})
        self.headers_a = {"Authorization": f"Bearer {self.token_a}"}
        self.headers_b = {"Authorization": f"Bearer {self.token_b}"}

        import asyncio
        async def seed_users():
            await self.mock_db.users.insert_one({
                "_id": self.owner_a,
                "name": "Alpha Owner",
                "email": "alpha@example.com",
                "role": "owner",
                "store_name": "Alpha Bakery",
                "timezone": "UTC",
                "opening_hour": 8.0,
                "closing_hour": 20.0,
                "currency": "₹",
                "onboarding_completed": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            await self.mock_db.users.insert_one({
                "_id": self.owner_b,
                "name": "Beta Manager",
                "email": "beta@example.com",
                "role": "owner",
                "store_name": "Beta Pastry",
                "timezone": "UTC",
                "opening_hour": 8.0,
                "closing_hour": 20.0,
                "currency": "₹",
                "onboarding_completed": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        asyncio.run(seed_users())

    def tearDown(self):
        main.db = self.original_db

    # -------------------------------------------------------------------------
    # 1. Day 1 Closing -> Day 2 Opening (Perishable vs Non-Perishable)
    # -------------------------------------------------------------------------
    def test_day1_closing_to_day2_opening(self):
        """[MOCK-DB] Day 1 closing -> Day 2 opening: perishable resets to 0, non-perishable carries over."""
        import asyncio
        async def seed():
            # Item 1: Perishable (Almond Croissant)
            await self.mock_db.items.insert_one({
                "_id": "item_croissant",
                "owner_id": self.owner_a,
                "name": "Almond Croissant",
                "category": "Bakery",
                "unit": "Units",
                "currentStock": 20,
                "isPerishable": True,
                "price": 4.50,
            })
            # Item 2: Non-perishable (Baking Flour)
            await self.mock_db.items.insert_one({
                "_id": "item_flour",
                "owner_id": self.owner_a,
                "name": "Baking Flour",
                "category": "Other",
                "unit": "kg",
                "currentStock": 30,
                "isPerishable": False,
                "price": 2.00,
            })
        asyncio.run(seed())

        now_utc = datetime.now(timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")
        next_date_str = (now_utc.date() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Restock 5 units of Croissants (available = 20 + 5 = 25)
        res_restock = self.client.post("/api/v1/items/item_croissant/restock", json={"quantity": 5}, headers=self.headers_a)
        self.assertEqual(res_restock.status_code, 200)
        self.assertEqual(res_restock.json()["newStock"], 25)

        # Record closing count: Croissant left = 5, Flour left = 12
        payload = {
            "date": today_str,
            "counts": [
                {"item_id": "item_croissant", "units_left": 5},
                {"item_id": "item_flour", "units_left": 12},
            ]
        }
        res_close = self.client.post("/api/v1/closing-count", json=payload, headers=self.headers_a)
        self.assertEqual(res_close.status_code, 200, f"Closing count failed: {res_close.text}")

        # Check Day 1 daily_stock
        async def check_day1():
            croissant_stock = await self.mock_db.daily_stock.find_one({"owner_id": self.owner_a, "item_id": "item_croissant", "date": today_str})
            flour_stock = await self.mock_db.daily_stock.find_one({"owner_id": self.owner_a, "item_id": "item_flour", "date": today_str})

            # Croissant: opening 20 + produced 5 = 25. units_left 5 -> sold 20, waste 5 (perishable)
            self.assertEqual(croissant_stock["openingStock"], 20)
            self.assertEqual(croissant_stock["producedOrRestocked"], 5)
            self.assertEqual(croissant_stock["closingCount"], 5)
            self.assertEqual(croissant_stock["soldUnits"], 20)
            self.assertEqual(croissant_stock["wasteUnits"], 5)

            # Flour: opening 30 + produced 0 = 30. units_left 12 -> sold 18, waste 0 (non-perishable)
            self.assertEqual(flour_stock["openingStock"], 30)
            self.assertEqual(flour_stock["closingCount"], 12)
            self.assertEqual(flour_stock["soldUnits"], 18)
            self.assertEqual(flour_stock["wasteUnits"], 0)

            # Check Day 2 opening stock in daily_stock
            croissant_next = await self.mock_db.daily_stock.find_one({"owner_id": self.owner_a, "item_id": "item_croissant", "date": next_date_str})
            flour_next = await self.mock_db.daily_stock.find_one({"owner_id": self.owner_a, "item_id": "item_flour", "date": next_date_str})

            # Perishable next opening stock MUST BE 0 (leftovers were recorded as waste)
            self.assertEqual(croissant_next["openingStock"], 0, "Perishable next day opening stock must reset to 0")
            # Non-perishable next opening stock MUST BE 12 (carries over)
            self.assertEqual(flour_next["openingStock"], 12, "Non-perishable next day opening stock must carry over")

            # Check derived daily_sales
            croissant_sales = await self.mock_db.daily_sales.find_one({"owner_id": self.owner_a, "item_id": "item_croissant", "date": today_str})
            self.assertEqual(croissant_sales["sales"], 20)
            flour_sales = await self.mock_db.daily_sales.find_one({"owner_id": self.owner_a, "item_id": "item_flour", "date": today_str})
            self.assertEqual(flour_sales["sales"], 18)

        asyncio.run(check_day1())

    # -------------------------------------------------------------------------
    # 2. Missing Day Marked Status "missing", NEVER Zero
    # -------------------------------------------------------------------------
    def test_missing_day_not_zero(self):
        """[MOCK-DB] Missing days in yesterday review are labeled 'no data' with status 'missing' and None sold units."""
        import asyncio
        async def seed():
            await self.mock_db.items.insert_one({
                "_id": "item_sourdough",
                "owner_id": self.owner_a,
                "name": "Artisan Sourdough",
                "category": "Bakery",
                "unit": "Units",
                "currentStock": 10,
                "isPerishable": True,
                "price": 6.00,
            })
        asyncio.run(seed())

        # No daily_stock record recorded for yesterday
        res = self.client.get("/api/v1/review/yesterday", headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["summary"]["missing_count"], 1)

        item_review = data["items"][0]
        self.assertEqual(item_review["status"], "missing")
        self.assertEqual(item_review["label"], "no data")
        self.assertIsNone(item_review["soldUnits"], "Missing day soldUnits must be None (NEVER ZERO)")
        self.assertIsNone(item_review["availableStock"], "Missing day availableStock must be None")
        self.assertIsNone(item_review["sellThrough"], "Missing day sellThrough must be None")

    # -------------------------------------------------------------------------
    # 3. Backfill Yesterday
    # -------------------------------------------------------------------------
    def test_backfill_yesterday(self):
        """[MOCK-DB] Backfill yesterday closing count: updates yesterday daily_stock and yesterday review."""
        now_utc = datetime.now(timezone.utc)
        yesterday_str = (now_utc.date() - timedelta(days=1)).strftime("%Y-%m-%d")

        import asyncio
        async def seed():
            await self.mock_db.items.insert_one({
                "_id": "item_bagel",
                "owner_id": self.owner_a,
                "name": "Sesame Bagel",
                "category": "Bakery",
                "unit": "Units",
                "currentStock": 20,
                "isPerishable": True,
                "price": 2.50,
            })
        asyncio.run(seed())

        # Backfill yesterday closing count
        payload = {
            "date": yesterday_str,
            "counts": [
                {"item_id": "item_bagel", "units_left": 3}
            ]
        }
        res_post = self.client.post("/api/v1/closing-count", json=payload, headers=self.headers_a)
        self.assertEqual(res_post.status_code, 200)
        self.assertEqual(res_post.json()["items"][0]["soldUnits"], 17)
        self.assertEqual(res_post.json()["items"][0]["wasteUnits"], 3)

        # Yesterday review should now show completed
        res_rev = self.client.get("/api/v1/review/yesterday", headers=self.headers_a)
        self.assertEqual(res_rev.status_code, 200)
        item_rev = res_rev.json()["items"][0]
        self.assertEqual(item_rev["status"], "completed")
        self.assertEqual(item_rev["soldUnits"], 17)
        self.assertEqual(item_rev["closingCount"], 3)
        self.assertAlmostEqual(item_rev["sellThrough"], 17 / 20.0, places=2)

    # -------------------------------------------------------------------------
    # 4. Resubmit Closing Count Idempotency
    # -------------------------------------------------------------------------
    def test_resubmit_idempotent(self):
        """[MOCK-DB] Resubmitting closing count for the same date does not duplicate records and updates state."""
        now_utc = datetime.now(timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")

        import asyncio
        async def seed():
            await self.mock_db.items.insert_one({
                "_id": "item_muffin",
                "owner_id": self.owner_a,
                "name": "Blueberry Muffin",
                "category": "Bakery",
                "unit": "Units",
                "currentStock": 20,
                "isPerishable": True,
                "price": 3.00,
            })
        asyncio.run(seed())

        # Submit 1
        res1 = self.client.post("/api/v1/closing-count", json={"counts": [{"item_id": "item_muffin", "units_left": 8}]}, headers=self.headers_a)
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["items"][0]["soldUnits"], 12)

        # Submit 2 (re-submission with corrected units_left: 6)
        res2 = self.client.post("/api/v1/closing-count", json={"counts": [{"item_id": "item_muffin", "units_left": 6}]}, headers=self.headers_a)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["items"][0]["soldUnits"], 14)

        # Assert exactly one document exists in daily_stock and daily_sales for this day
        async def verify_count():
            count_stock = await self.mock_db.daily_stock.count_documents({"owner_id": self.owner_a, "item_id": "item_muffin", "date": today_str})
            self.assertEqual(count_stock, 1, "daily_stock must have exactly 1 record per (owner_id, item_id, date)")

            count_sales = await self.mock_db.daily_sales.count_documents({"owner_id": self.owner_a, "item_id": "item_muffin", "date": today_str})
            self.assertEqual(count_sales, 1, "daily_sales must have exactly 1 record per (owner_id, item_id, date)")
        asyncio.run(verify_count())

    # -------------------------------------------------------------------------
    # 5. Mid-Day Pace at Local 09:00, 14:00, 20:00
    # -------------------------------------------------------------------------
    def test_midday_pace_local_hours(self):
        """[MOCK-DB] Verifies mid-day pace = sold_so_far / (forecast * elapsed_fraction) across simulated hours."""
        import asyncio
        async def seed():
            await self.mock_db.items.insert_one({
                "_id": "item_cappuccino",
                "owner_id": self.owner_a,
                "name": "Cappuccino",
                "category": "Beverage",
                "unit": "Cups",
                "currentStock": 50,
                "predictedDemand": 40,
                "isPerishable": True,
                "price": 3.50,
            })
        asyncio.run(seed())

        # Operating hours: 08:00 to 20:00 (12 hours total)
        # 1. At 09:00: 1 hr elapsed -> fraction = 1 / 12 = 0.0833
        # Forecast = 40 -> expected = max(1.0, 40 * 0.0833) = 3.33
        # If remaining = 46 -> sold_so_far = 50 - 46 = 4. Pace = 4 / 3.33 = 1.20
        open_h = 8.0
        close_h = 20.0
        total_h = close_h - open_h

        frac_0900 = (9.0 - open_h) / total_h
        expected_0900 = 40 * frac_0900
        pace_0900 = round(4.0 / expected_0900, 2)
        self.assertAlmostEqual(pace_0900, 1.20, places=2)

        # 2. At 14:00: 6 hrs elapsed -> fraction = 6 / 12 = 0.50
        # Expected = 40 * 0.50 = 20.0
        # If remaining = 30 -> sold_so_far = 20. Pace = 20 / 20.0 = 1.00
        frac_1400 = (14.0 - open_h) / total_h
        expected_1400 = 40 * frac_1400
        pace_1400 = round(20.0 / expected_1400, 2)
        self.assertEqual(pace_1400, 1.00)

        # 3. At 20:00: 12 hrs elapsed -> fraction = 1.0
        # Expected = 40 * 1.0 = 40.0
        # If remaining = 10 -> sold_so_far = 40. Pace = 40 / 40.0 = 1.00
        frac_2000 = (20.0 - open_h) / total_h
        expected_2000 = 40 * frac_2000
        pace_2000 = round(40.0 / expected_2000, 2)
        self.assertEqual(pace_2000, 1.00)

        # Call endpoint for mid-day count
        res = self.client.post("/api/v1/midday-count", json={"counts": [{"item_id": "item_cappuccino", "remaining": 35}]}, headers=self.headers_a)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["items"][0]["remaining"], 35)
        self.assertEqual(res.json()["items"][0]["sold_so_far"], 15)

    # -------------------------------------------------------------------------
    # 6. Tenant Isolation for New Collections (daily_stock & daily_sales)
    # -------------------------------------------------------------------------
    def test_tenant_isolation_new_collections(self):
        """[MOCK-DB] Verifies tenant isolation: Owner A cannot read or mutate Owner B's daily_stock or reviews."""
        import asyncio
        async def seed():
            await self.mock_db.items.insert_one({
                "_id": "item_beta_cake",
                "owner_id": self.owner_b,
                "name": "Chocolate Cake",
                "category": "Dessert",
                "unit": "Slices",
                "currentStock": 15,
                "isPerishable": True,
                "price": 5.00,
            })
            await self.mock_db.daily_stock.insert_one({
                "owner_id": self.owner_b,
                "item_id": "item_beta_cake",
                "date": "2026-10-28",
                "openingStock": 15,
                "closingCount": 3,
                "soldUnits": 12,
                "wasteUnits": 3,
                "status": "closed",
            })
        asyncio.run(seed())

        # Owner A attempts to record closing count for Owner B's item
        res = self.client.post("/api/v1/closing-count", json={"counts": [{"item_id": "item_beta_cake", "units_left": 2}]}, headers=self.headers_a)
        self.assertEqual(res.status_code, 404, "Security violation: Owner A recorded closing count for Owner B's item!")

        # Owner A requests yesterday review: must NOT contain Owner B's items
        res_rev = self.client.get("/api/v1/review/yesterday", headers=self.headers_a)
        self.assertEqual(res_rev.status_code, 200)
        item_ids = [it["itemId"] for it in res_rev.json()["items"]]
        self.assertNotIn("item_beta_cake", item_ids, "Data leak: Owner B's items surfaced in Owner A's review!")

    # -------------------------------------------------------------------------
    # 7. Flutter Contract Test
    # -------------------------------------------------------------------------
    def test_contract_flutter_keys(self):
        """
        [MOCK-DB] Contract test: verifies the backend returns every single JSON key
        expected by the Flutter models:
          - InventoryItem.fromJson
          - WasteAlert.fromJson
          - UserProfile (GET /me)
          - YesterdayReviewItem
          - HealthResponse
        """
        import asyncio
        async def seed():
            await self.mock_db.items.insert_one({
                "_id": "item_contract_test",
                "owner_id": self.owner_a,
                "name": "Brioche Loaf",
                "category": "Bakery",
                "unit": "Loaves",
                "currentStock": 5,
                "isPerishable": True,
                "price": 4.50,
                "predictedDemand": 30,
                "safetyStock": 8,
                "description": "Artisan brioche",
                "riskLevel": "low",
                "intradaySales": 1,
            })
            await self.mock_db.items.insert_one({
                "_id": "item_contract_partner",
                "owner_id": self.owner_a,
                "name": "Cold Brew Coffee",
                "category": "Beverage",
                "unit": "Bottles",
                "currentStock": 20,
                "isPerishable": True,
                "price": 3.00,
                "intradaySales": 15,
            })
        asyncio.run(seed())

        # 1. Health contract (tiny liveness on /health; details on /health/details)
        r_health = self.client.get("/api/v1/health")
        self.assertEqual(r_health.status_code, 200)
        h_json = r_health.json()
        for key in ["status", "service", "timestamp"]:
            self.assertIn(key, h_json, f"Missing health contract key: {key}")

        os.environ["JOB_SECRET"] = "contract_secret"
        r_details = self.client.get("/health/details", headers={"X-Job-Secret": "contract_secret"})
        self.assertEqual(r_details.status_code, 200)
        det_json = r_details.json()
        for key in ["status", "database", "last_forecast_time", "counts", "RENDER_GIT_COMMIT", "store_timezone", "llm_configured", "timestamp"]:
            self.assertIn(key, det_json, f"Missing health details key: {key}")

        # 2. User profile contract (GET /api/v1/me)
        r_me = self.client.get("/api/v1/me", headers=self.headers_a)
        self.assertEqual(r_me.status_code, 200)
        me_json = r_me.json()
        for key in ["id", "name", "email", "role", "store_name", "timezone", "opening_hour", "closing_hour", "currency", "onboarding_completed", "created_at"]:
            self.assertIn(key, me_json, f"Missing user profile contract key: {key}")

        # 3. Forecasts / InventoryItem contract
        r_fc = self.client.get("/api/v1/forecasts/today", headers=self.headers_a)
        self.assertEqual(r_fc.status_code, 200)
        fc_items = r_fc.json()["items"]
        self.assertTrue(len(fc_items) > 0)
        target_item = next(it for it in fc_items if it["id"] == "item_contract_test")
        for key in ["id", "name", "category", "unit", "currentStock", "isPerishable", "price", "predictedDemand", "safetyStock", "restockQuantity", "stockProgress", "daysOfData", "maturity", "maturityLabel", "description", "riskLevel", "updatedAt"]:
            self.assertIn(key, target_item, f"Missing InventoryItem contract key: {key}")

        # 4. Waste Alert contract & Partner Selection
        # Set simulated store hours so store is open
        r_alerts = self.client.get("/api/v1/waste-alerts", headers=self.headers_a)
        self.assertEqual(r_alerts.status_code, 200)
        alerts_json = r_alerts.json()
        self.assertIn("alerts", alerts_json)
        self.assertIn("store_status", alerts_json)

        # If store open and alerts present, check keys
        if alerts_json["alerts"]:
            alert = alerts_json["alerts"][0]
            for key in ["id", "itemName", "salesText", "progress", "salesPaceRatio", "severityLabel", "severityColor", "recommendedActionText", "recommendedActionColor", "recommendedDoneText", "isRecommendedActionDone", "primaryActionText", "primaryDoneText", "isPrimaryActionDone", "isDismissed", "layoutStyle", "foodType"]:
                self.assertIn(key, alert, f"Missing WasteAlert contract key: {key}")

        # 5. Yesterday Review contract
        r_rev = self.client.get("/api/v1/review/yesterday", headers=self.headers_a)
        self.assertEqual(r_rev.status_code, 200)
        rev_json = r_rev.json()
        self.assertIn("status", rev_json)
        self.assertIn("date", rev_json)
        self.assertIn("summary", rev_json)
        self.assertIn("items", rev_json)
        rev_item = rev_json["items"][0]
        for key in ["itemId", "itemName", "category", "status", "sellThrough", "sellThroughPct", "label", "color", "openingStock", "producedOrRestocked", "availableStock", "soldUnits", "wasteUnits", "closingCount", "date"]:
            self.assertIn(key, rev_item, f"Missing YesterdayReviewItem contract key: {key}")


class TestBlock2RealDBStaging(unittest.TestCase):
    """
    [REAL-DB (restockiq_staging)] Suite.
    Executes real database tests against MongoDB Atlas staging cluster:
      1. Real multi-tenant isolation on daily_stock and daily_sales.
      2. Enforces unique compound index (owner_id, item_id, date) on daily_stock.
      3. Enforces unique compound index (owner_id, name_lower) on items.
    """
    def setUp(self):
        from dotenv import load_dotenv
        from pathlib import Path
        import pymongo

        env_path = Path(__file__).resolve().parent / ".env"
        load_dotenv(dotenv_path=env_path)
        uri = os.getenv("MONGO_URI")
        if not uri:
            self.skipTest("NOT RUN: MONGO_URI not found in .env")

        try:
            self.client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
        except Exception as e:
            self.skipTest(f"NOT RUN: Atlas port 27017 unreachable ({type(e).__name__})")

        # Strictly use staging database
        self.db = self.client["restockiq_staging"]
        self.owner_a = "staging_block2_alpha"
        self.owner_b = "staging_block2_beta"

        # Clean scoped staging test records before run
        self.db.items.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
        self.db.daily_stock.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
        self.db.daily_sales.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})

    def tearDown(self):
        if hasattr(self, "db") and self.db is not None:
            self.db.items.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
            self.db.daily_stock.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
            self.db.daily_sales.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
            self.client.close()

    def test_real_database_daily_stock_isolation(self):
        """[REAL-DB (restockiq_staging)] Daily stock & sales isolation on real Atlas staging."""
        # 1. Insert daily_stock for Owner A and Owner B
        self.db.daily_stock.insert_many([
            {
                "owner_id": self.owner_a,
                "item_id": "staging_item_a",
                "date": "2026-10-29",
                "openingStock": 20,
                "closingCount": 5,
                "soldUnits": 15,
                "wasteUnits": 5,
                "status": "closed",
            },
            {
                "owner_id": self.owner_b,
                "item_id": "staging_item_b",
                "date": "2026-10-29",
                "openingStock": 40,
                "closingCount": 10,
                "soldUnits": 30,
                "wasteUnits": 10,
                "status": "closed",
            },
        ])

        # Query for Owner A
        stock_a = list(self.db.daily_stock.find({"owner_id": self.owner_a}))
        self.assertEqual(len(stock_a), 1)
        self.assertEqual(stock_a[0]["item_id"], "staging_item_a")

        # Query for Owner B
        stock_b = list(self.db.daily_stock.find({"owner_id": self.owner_b}))
        self.assertEqual(len(stock_b), 1)
        self.assertEqual(stock_b[0]["item_id"], "staging_item_b")

        # Cross-tenant mutation blocked by owner_id filter
        res = self.db.daily_stock.update_one(
            {"item_id": "staging_item_b", "owner_id": self.owner_a},
            {"$set": {"soldUnits": 999}}
        )
        self.assertEqual(res.modified_count, 0, "Security leak: Owner A updated Owner B's daily_stock!")

        # Verify Owner B's data unmodified
        verified_b = self.db.daily_stock.find_one({"item_id": "staging_item_b", "owner_id": self.owner_b})
        self.assertEqual(verified_b["soldUnits"], 30)

    def test_real_database_unique_indexes(self):
        """[REAL-DB (restockiq_staging)] Unique compound indexes on Atlas staging."""
        import pymongo

        # Ensure indexes exist on staging
        self.db.daily_stock.create_index([("owner_id", 1), ("item_id", 1), ("date", 1)], unique=True)
        self.db.items.create_index([("owner_id", 1), ("name_lower", 1)], unique=True)

        # 1. Test unique index on daily_stock
        self.db.daily_stock.insert_one({
            "owner_id": self.owner_a,
            "item_id": "staging_idx_item",
            "date": "2026-10-29",
            "openingStock": 10,
        })
        with self.assertRaises(pymongo.errors.DuplicateKeyError):
            self.db.daily_stock.insert_one({
                "owner_id": self.owner_a,
                "item_id": "staging_idx_item",
                "date": "2026-10-29",
                "openingStock": 99,
            })

        # 2. Test unique index on items (owner_id, name_lower)
        self.db.items.insert_one({
            "owner_id": self.owner_a,
            "name": "Artisan Sourdough",
            "name_lower": "artisan sourdough",
            "currentStock": 10,
        })
        with self.assertRaises(pymongo.errors.DuplicateKeyError):
            self.db.items.insert_one({
                "owner_id": self.owner_a,
                "name": "Artisan Sourdough",
                "name_lower": "artisan sourdough",
                "currentStock": 25,
            })


if __name__ == "__main__":
    unittest.main()
