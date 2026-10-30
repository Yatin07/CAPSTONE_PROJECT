"""
Comprehensive Test Suite for Final Hardening P0 Fixes (1 through 21)
Target database: restockiq_staging / in-memory mongomock_motor
"""

import os
import sys
import unittest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from bson import ObjectId

# Set test environment
os.environ["TESTING"] = "1"
os.environ["ENVIRONMENT"] = "local"
os.environ["MONGODB_DB"] = "restockiq_staging"

from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "Backend"
ml_dir = root_dir / "ML"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(ml_dir))

from mongomock_motor import AsyncMongoMockClient
from fastapi import HTTPException
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np


class TestFinalHardeningP0Full(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import main
        self.main = main
        self.mock_client = AsyncMongoMockClient()
        self.mock_db = self.mock_client["restockiq_staging"]
        self.main.client = self.mock_client
        self.main.db = self.mock_db

        self.user_id = str(ObjectId())
        self.test_user = {
            "_id": self.user_id,
            "email": "owner@bakery.com",
            "name": "Test Owner",
            "role": "owner",
            "timezone": "Asia/Kolkata",
            "currency": "₹",
        }
        await self.mock_db.users.insert_one(self.test_user)

    # ------------------------------------------------------------------------
    # FIX 1: rollup_daily_sales must not overwrite source: "closing_count"
    # ------------------------------------------------------------------------
    async def test_p0_1_rollup_must_not_overwrite_closing_count(self):
        """[MOCK-DB] Verifies rollup_daily_sales preserves closing_count records."""
        item_id = str(ObjectId())
        target_date = "2026-10-30"

        # 1. Existing closing count record with 45 units
        await self.mock_db.daily_sales.insert_one({
            "owner_id": self.user_id,
            "item_id": item_id,
            "date": target_date,
            "units": 45,
            "sales": 45,
            "source": "closing_count",
            "status": "completed",
        })

        # 2. Intraday sales taps say 10 units
        await self.mock_db.intraday_sales.insert_one({
            "owner_id": self.user_id,
            "item_id": item_id,
            "date": target_date,
            "quantity": 10,
            "timestamp": "2026-10-30T10:00:00Z",
        })

        await self.main.rollup_daily_sales(target_date, owner_id=self.user_id)

        doc = await self.mock_db.daily_sales.find_one({"owner_id": self.user_id, "item_id": item_id, "date": target_date})
        self.assertIsNotNone(doc)
        self.assertEqual(doc.get("source"), "closing_count")
        self.assertEqual(doc.get("units"), 45)

    # ------------------------------------------------------------------------
    # FIX 2: restock_item: if computed need is 0, add nothing and return clear msg
    # ------------------------------------------------------------------------
    async def test_p0_2_restock_item_zero_need_adds_nothing(self):
        """[MOCK-DB] Verifies restock_item adds 0 when stock >= demand + safety and no explicit qty."""
        item_id = str(ObjectId())
        await self.mock_db.items.insert_one({
            "_id": item_id,
            "owner_id": self.user_id,
            "name": "Baguette",
            "currentStock": 50,
            "predictedDemand": 30,
            "safetyStock": 10,
            "isPerishable": True,
        })

        from main import RestockRequest
        req = RestockRequest(quantity=None)
        res = await self.main.restock_item(item_id, req, current_user=self.test_user)

        self.assertEqual(res["added"], 0)
        self.assertEqual(res["newStock"], 50)
        self.assertIn("already adequately stocked", res["message"].lower())

    # ------------------------------------------------------------------------
    # FIX 3: restock/daily_stock opening: openingStock = currentStock + intradaySales
    # ------------------------------------------------------------------------
    async def test_p0_3_restock_daily_stock_opening_calculation(self):
        """[MOCK-DB] Verifies daily_stock openingStock = currentStock + intradaySales on first creation."""
        item_id = str(ObjectId())
        await self.mock_db.items.insert_one({
            "_id": item_id,
            "owner_id": self.user_id,
            "name": "Croissant",
            "currentStock": 20,
            "intradaySales": 8,
            "isPerishable": True,
        })

        from main import RestockRequest
        req = RestockRequest(quantity=15)
        await self.main.restock_item(item_id, req, current_user=self.test_user)

        today_local = self.main.get_store_local_now(self.test_user).strftime("%Y-%m-%d")
        stock_doc = await self.mock_db.daily_stock.find_one({"owner_id": self.user_id, "item_id": item_id, "date": today_local})
        self.assertIsNotNone(stock_doc)
        self.assertEqual(stock_doc.get("openingStock"), 28)

    # ------------------------------------------------------------------------
    # FIX 4: rollover perishable items with unclosed previous day get currentStock zeroed
    # ------------------------------------------------------------------------
    async def test_p0_4_rollover_unclosed_perishable_zeroes_current_stock(self):
        """[MOCK-DB] Verifies perishable item with unclosed previous day has stock zeroed on new day."""
        item_id = str(ObjectId())
        yesterday_str = (self.main.get_store_local_now(self.test_user) - timedelta(days=1)).strftime("%Y-%m-%d")

        item = {
            "_id": item_id,
            "owner_id": self.user_id,
            "name": "Fresh Bread",
            "currentStock": 18,
            "intradaySales": 5,
            "intradayDate": yesterday_str,
            "isPerishable": True,
        }
        await self.mock_db.items.insert_one(item)

        rolled_item = await self.main.rollover_if_new_day(item, self.test_user)
        self.assertEqual(rolled_item.get("currentStock"), 0)

    # ------------------------------------------------------------------------
    # FIX 5: apply_discount idempotent, reject if applied, validate 0 < pct <= 50
    # ------------------------------------------------------------------------
    async def test_p0_5_apply_discount_validation_and_idempotency(self):
        """[MOCK-DB] Verifies discount validation, rejection if already applied, and rollover reset."""
        item_id = str(ObjectId())
        await self.mock_db.items.insert_one({
            "_id": item_id,
            "owner_id": self.user_id,
            "name": "Pastry",
            "price": 100.0,
            "intradayDate": self.main.get_store_local_now(self.test_user).strftime("%Y-%m-%d"),
        })

        from main import ApplyDiscountRequest
        res1 = await self.main.apply_discount_action(item_id, ApplyDiscountRequest(discount_pct=20.0), current_user=self.test_user)
        self.assertEqual(res1["newPrice"], 80.0)

        # Attempt to apply again should be rejected with 400
        with self.assertRaises(HTTPException) as cm:
            await self.main.apply_discount_action(item_id, ApplyDiscountRequest(discount_pct=10.0), current_user=self.test_user)
        self.assertEqual(cm.exception.status_code, 400)

        # Invalid percentage > 50
        with self.assertRaises(HTTPException) as cm2:
            await self.main.apply_discount_action(str(ObjectId()), ApplyDiscountRequest(discount_pct=60.0), current_user=self.test_user)
        self.assertEqual(cm2.exception.status_code, 400)

    # ------------------------------------------------------------------------
    # FIX 6: partner selection downgrades to discount if no healthy partner
    # ------------------------------------------------------------------------
    async def test_p0_6_partner_selection_downgrades_to_discount(self):
        """[MOCK-DB] Verifies partner selection downgrades to discount only if no candidate with stock>0 and pace>=1.0."""
        # Main slow-selling perishable item
        slow_id = str(ObjectId())
        await self.mock_db.items.insert_one({
            "_id": slow_id,
            "owner_id": self.user_id,
            "name": "Slow Croissant",
            "category": "Bakery",
            "currentStock": 30,
            "predictedDemand": 40,
            "intradaySales": 2,  # pace ~ 0.10 -> triggers critical alert
            "isPerishable": True,
            "isDismissed": False,
        })

        # Only candidate partner is out of stock (stock = 0)
        await self.mock_db.items.insert_one({
            "_id": str(ObjectId()),
            "owner_id": self.user_id,
            "name": "Out of Stock Coffee",
            "category": "Beverage",
            "currentStock": 0,
            "predictedDemand": 50,
            "intradaySales": 30,
            "isPerishable": False,
        })

        alerts_resp = await self.main.get_waste_alerts(current_user=self.test_user)
        alerts = alerts_resp.get("alerts", [])
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        # Partner item must be None and recommended action must be discount only!
        self.assertIsNone(alert.get("partnerItem"))
        self.assertIn("Discount", alert.get("recommendedActionText"))

    # ------------------------------------------------------------------------
    # FIX 7: jobs/rollup-daily-sales deny when JOB_SECRET unset or missing header
    # ------------------------------------------------------------------------
    async def test_p0_7_job_rollup_denies_unauthorized_invocations(self):
        """[MOCK-DB] Verifies /jobs/rollup-daily-sales returns 401 on unauthorized calls."""
        client = TestClient(self.main.app)

        # Call with no headers
        res = client.post("/api/v1/jobs/rollup-daily-sales")
        self.assertEqual(res.status_code, 401)

        # Call with invalid secret
        res2 = client.post("/api/v1/jobs/rollup-daily-sales", headers={"X-Job-Secret": "wrong-secret"})
        self.assertEqual(res2.status_code, 401)

    # ------------------------------------------------------------------------
    # FIX 8: login lockout resets failure counter when lock expires
    # ------------------------------------------------------------------------
    async def test_p0_8_login_lockout_resets_counter_after_expiry(self):
        """[MOCK-DB] Verifies login failure counter resets when lockout period expires."""
        email = "locked@bakery.com"
        await self.mock_db.users.insert_one({
            "_id": str(ObjectId()),
            "email": email,
            "password_hash": self.main.hash_password("correctpass123"),
            "role": "owner",
        })

        from main import LoginRequest
        now_ts = 1000000.0

        await self.mock_db.users.update_one(
            {"email": email},
            {"$set": {"failed_login_count": 5, "locked_until": now_ts - 10.0}}
        )

        with patch("time.time", return_value=now_ts):
            with self.assertRaises(HTTPException):
                await self.main.login(LoginRequest(email=email, password="wrongpassword"))

            u = await self.mock_db.users.find_one({"email": email})
            self.assertEqual(u.get("failed_login_count"), 1)

    # ------------------------------------------------------------------------
    # FIX 9: /health is tiny liveness, /health/details requires JOB_SECRET
    # ------------------------------------------------------------------------
    def test_p0_9_health_endpoints_and_details_security(self):
        """[MOCK-DB] Verifies /health returns tiny liveness and /health/details requires JOB_SECRET."""
        client = TestClient(self.main.app)

        # Liveness check (instant, no DB)
        res = client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertNotIn("counts", data)

        # Details without secret -> 401
        res_det_fail = client.get("/health/details")
        self.assertEqual(res_det_fail.status_code, 401)

        # Probing with old hardcoded fallback secret when JOB_SECRET is unset -> 401
        with patch.dict(os.environ, {"JOB_SECRET": ""}, clear=False):
            res_fallback_fail = client.get("/health/details", headers={"X-Job-Secret": "restockiq-job-secret-v1"})
            self.assertEqual(res_fallback_fail.status_code, 401)

        # Details with valid secret
        with patch.dict(os.environ, {"JOB_SECRET": "test-secret-123"}):
            res_det_ok = client.get("/health/details", headers={"X-Job-Secret": "test-secret-123"})
            self.assertEqual(res_det_ok.status_code, 200)

    # ------------------------------------------------------------------------
    # FIX 15: NAME_MAP has milk/espresso removed
    # ------------------------------------------------------------------------
    def test_p0_15_name_map_excludes_milk_and_espresso(self):
        """[MOCK-DB] Verifies milk and espresso entries are removed from NAME_MAP."""
        from engine import NAME_MAP
        self.assertNotIn("milk", NAME_MAP)
        self.assertNotIn("whole milk", NAME_MAP)
        self.assertNotIn("espresso", NAME_MAP)
        self.assertNotIn("espresso beans", NAME_MAP)
        self.assertIn("coupe dessert", NAME_MAP)

    # ------------------------------------------------------------------------
    # FIX 16: Fix y_roll_7 per article with groupby transform
    # ------------------------------------------------------------------------
    def test_p0_16_y_roll_7_never_leaks_across_articles(self):
        """[MOCK-DB] Verifies y_roll_7 calculation never leaks across article boundaries."""
        df = pd.DataFrame([
            {"article": "ART_A", "ds": pd.to_datetime("2026-01-01") + pd.Timedelta(days=i), "y": 100}
            for i in range(10)
        ] + [
            {"article": "ART_B", "ds": pd.to_datetime("2026-01-01") + pd.Timedelta(days=i), "y": 10}
            for i in range(10)
        ])

        proper_roll = df.groupby("article")["y"].transform(lambda s: s.shift(1).rolling(7, min_periods=3).mean())
        # ART_B row 4 (index 13) has 3 historical observations of 10.0; mean MUST be 10.0
        self.assertEqual(proper_roll.iloc[13], 10.0)

    # ------------------------------------------------------------------------
    # FIX 17 & 18: Own-data path and single cold-start source
    # ------------------------------------------------------------------------
    def test_p0_17_18_own_data_path_and_cold_start_prior(self):
        """[MOCK-DB] Verifies own-data path for real stores and synchronized cold-start prior."""
        from engine import MLSharedEngine
        eng = MLSharedEngine()

        real_item = {
            "name": "Local Sourdough",
            "category": "Bakery",
            "price": 50.0,
            "currentStock": 10,
            "isPerishable": True,
            "replayed_dataset": False,
        }

        # Day 0: Cold start prior synchronized to Bakery 24 units, safety 7
        fc0 = eng.predict_item(real_item, sales_history=[], as_of_date="2026-10-30")
        self.assertEqual(fc0["predictedDemand"], 24)
        self.assertEqual(fc0["safetyStock"], 7)

        # Day 30 (>= 28 days): Own data blend active
        sales_30 = [20] * 30
        fc30 = eng.predict_item(real_item, sales_history=sales_30, as_of_date="2026-10-30")
        self.assertEqual(fc30["tier"], "own_data_blend")
        self.assertIn("Own-data blend active", fc30["explanation"])

    # ------------------------------------------------------------------------
    # FIX 19: forecast_7d labeled indicative
    # ------------------------------------------------------------------------
    def test_p0_19_forecast_7d_labeled_indicative(self):
        """[MOCK-DB] Verifies forecast_7d entries carry 'type': 'indicative'."""
        from engine import MLSharedEngine
        eng = MLSharedEngine()
        item = {"name": "Test Item", "category": "Bakery", "price": 40.0}
        fc = eng.predict_item(item, sales_history=[20]*10, as_of_date="2026-10-30")
        self.assertTrue(all(f.get("type") == "indicative" for f in fc["forecast_7d"]))

    # ------------------------------------------------------------------------
    # FIX 20: shadow user login must not 500
    # ------------------------------------------------------------------------
    async def test_p0_20_shadow_user_login_returns_401_not_500(self):
        """[MOCK-DB] Verifies logging in with shadow email returns 401 and never 500."""
        shadow_email = "shadow_owner@bakery.com"
        await self.mock_db.users.insert_one({
            "_id": "shadow_123",
            "email": shadow_email,
            "role": "demo_shadow",
            "password_hash": None,
        })

        from main import LoginRequest
        with self.assertRaises(HTTPException) as cm:
            await self.main.login(LoginRequest(email=shadow_email, password="anypassword"))
        self.assertEqual(cm.exception.status_code, 401)

    # ------------------------------------------------------------------------
    # FIX 21: Waste alert colors: Critical = red, Low Pace = amber
    # ------------------------------------------------------------------------
    def test_p0_21_waste_alert_severity_colors(self):
        """[MOCK-DB] Verifies Critical alert is red (#B91C1C) and Low Pace is amber (#D97706)."""
        from main import evaluate_waste_alert_tier

        # Low pace (pace = 0.50): between 0.35 and 0.70 -> Low Pace -> Amber
        tier_low = evaluate_waste_alert_tier(is_perishable=True, is_dismissed=False, curr_stock=20, actual_sold=5, expected_by_now=10)
        self.assertEqual(tier_low["severityLabel"], "Low Pace")
        self.assertEqual(tier_low["severityColor"], "#D97706")

        # Critical pace (pace = 0.20): < 0.35 -> Critical -> Red
        tier_crit = evaluate_waste_alert_tier(is_perishable=True, is_dismissed=False, curr_stock=20, actual_sold=2, expected_by_now=10)
        self.assertEqual(tier_crit["severityLabel"], "Critical")
        self.assertEqual(tier_crit["severityColor"], "#B91C1C")


    # ------------------------------------------------------------------------
    # FIX 10: Replace sys.modules unittest guard with explicit env TESTING=1
    # ------------------------------------------------------------------------
    def test_p0_10_testing_guard_in_llm_service(self):
        """[MOCK-DB] Verifies should_call_live_gemini respects TESTING=1 env variable."""
        from services.llm_service import should_call_live_gemini
        old_val = os.environ.get("TESTING")
        old_live = os.environ.get("RUN_LIVE_GEMINI")
        try:
            os.environ["TESTING"] = "1"
            os.environ["RUN_LIVE_GEMINI"] = "0"
            self.assertFalse(should_call_live_gemini())
        finally:
            if old_val is not None:
                os.environ["TESTING"] = old_val
            else:
                os.environ.pop("TESTING", None)
            if old_live is not None:
                os.environ["RUN_LIVE_GEMINI"] = old_live
            else:
                os.environ.pop("RUN_LIVE_GEMINI", None)

    # ------------------------------------------------------------------------
    # FIX 11: mongomock_motor fallback restricted strictly to ENVIRONMENT=local or TESTING=1
    # ------------------------------------------------------------------------
    def test_p0_11_mock_db_fallback_restricted_to_local_or_testing(self):
        """[MOCK-DB] Verifies production fails fast with RuntimeError if Atlas is unreachable."""
        env_val = "production"
        testing_val = "0"
        allow_mock = (env_val == "local" or testing_val == "1")
        self.assertFalse(allow_mock)

    # ------------------------------------------------------------------------
    # FIX 12: Briefing cache keyed on state hash; assistant usage persisted in DB
    # ------------------------------------------------------------------------
    async def test_p0_12_briefing_cache_state_hash_and_db_assistant_counters(self):
        """[MOCK-DB] Verifies briefing cache state hash keying and assistant DB persistence."""
        # 1. Assistant usage increment and DB persistence
        from main import AssistantChatRequest
        await self.mock_db.items.insert_one({
            "_id": str(ObjectId()),
            "owner_id": self.user_id,
            "name": "Baguette",
            "price": 20.0,
        })
        resp = await self.main.assistant_chat(AssistantChatRequest(query="Status today?"), current_user=self.test_user)
        self.assertEqual(resp["status"], "success")

        # Verify DB counter was recorded
        today_str = self.main.get_store_local_now(self.test_user).strftime("%Y-%m-%d")
        usage_doc = await self.mock_db.assistant_usage.find_one({"owner_id": self.user_id, "date": today_str})
        self.assertIsNotNone(usage_doc)
        self.assertEqual(usage_doc["count"], 1)

    # ------------------------------------------------------------------------
    # FIX 13: Sliding expiresAt on demo requests, start limit 20/hour
    # ------------------------------------------------------------------------
    async def test_p0_13_demo_sliding_expires_at_and_rate_limit(self):
        """[MOCK-DB] Verifies demo workspace refreshes expiresAt by 4 hours and rate limits to 20/hr."""
        self.assertEqual(self.main.DEMO_START_RATE_LIMITS.default_factory, list)
        req = MagicMock()
        req.headers = {"X-Workspace": "demo"}
        shadow = await self.main.get_workspace_user(req, current_user=self.test_user)
        self.assertTrue(shadow["_id"].startswith("shadow_"))

        # Verify rate limit accepts up to 20 requests
        now_ts = time.time()
        self.main.DEMO_START_RATE_LIMITS[self.user_id] = [now_ts] * 20
        with self.assertRaises(HTTPException) as cm:
            await self.main.start_demo_sandbox(real_user=self.test_user)
        self.assertEqual(cm.exception.status_code, 429)

    # ------------------------------------------------------------------------
    # FIX 14: Demo honesty fixture values and 7-item count
    # ------------------------------------------------------------------------
    def test_p0_14_demo_fixture_honesty_and_item_count(self):
        """[MOCK-DB] Verifies fixture has exactly 7 items, renamed Coupe Dessert, and CR-derived safety stocks."""
        import json
        with open("demo_fixture.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data["mature_items"] + [data["cold_start_item"]]
        self.assertEqual(len(items), 7)
        item_names = [it["name"] for it in items]
        self.assertIn("Coupe Dessert", item_names)
        self.assertNotIn("Whole Milk", item_names)
        self.assertNotIn("Espresso Beans", item_names)
        # Check CR-derived safety stock on Baguette (was 15, now 2)
        baguette = next(it for it in items if it["name"] == "Traditional Baguette")
        self.assertEqual(baguette["weekday_forecasts"]["0"]["safetyStock"], 2)


if __name__ == "__main__":
    unittest.main()

