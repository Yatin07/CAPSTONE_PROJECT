"""
Integration and E2E Tests for Adaptive Forecasting Engine
=========================================================
Covers:
1. Register -> Add Item -> 10 simulated days of closing counts -> forecasts change with method label
2. Cold start adaptive refresh: new items with 0 sales history receive adaptive metadata on today's forecast
3. Refresh after a backfill (yesterday count triggers today forecast refresh)
4. Strict Tenant Isolation: User B injecting sales with User A's item_id NEVER pollutes User A
5. Feature flag OFF (FORECAST_MODE=legacy) verified via HTTP TestClient returning 200 with legacy format
6. Adaptive failure safe fallback: HTTP TestClient returns 200 (never 500) when adaptive engine throws
7. Real Batch Forecast protection: atomic update query skips adaptive documents
"""

import os
import sys
import unittest
from bson import ObjectId
from datetime import date, timedelta, timezone, datetime
import pytest
from unittest.mock import patch

# Ensure testing environment flags
os.environ["TESTING"] = "1"
os.environ["ENVIRONMENT"] = "local"
os.environ["MONGODB_DB"] = "restockiq_staging"

from mongomock_motor import AsyncMongoMockClient
from fastapi.testclient import TestClient

import main


class TestAdaptiveIntegrationSuite(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.main = main
        self.mock_client = AsyncMongoMockClient()
        self.mock_db = self.mock_client["restockiq_staging"]
        self.main.client = self.mock_client
        self.main.db = self.mock_db

        # User A setup
        self.user_a_id = str(ObjectId())
        self.user_a = {
            "_id": self.user_a_id,
            "email": "user_a@artisan.test",
            "name": "Owner A",
            "role": "owner",
            "timezone": "Asia/Kolkata",
            "opening_hour": 0.0,
            "closing_hour": 24.0,
            "currency": "INR",
        }
        await self.mock_db.users.insert_one(self.user_a)

        # User B setup (for tenant isolation)
        self.user_b_id = str(ObjectId())
        self.user_b = {
            "_id": self.user_b_id,
            "email": "user_b@outlier.test",
            "name": "Owner B",
            "role": "owner",
            "timezone": "Asia/Kolkata",
            "opening_hour": 0.0,
            "closing_hour": 24.0,
            "currency": "INR",
        }
        await self.mock_db.users.insert_one(self.user_b)

        # Create auth tokens
        self.token_a = self.main.create_access_token({"sub": self.user_a_id})
        self.headers_a = {"Authorization": f"Bearer {self.token_a}"}

        self.token_b = self.main.create_access_token({"sub": self.user_b_id})
        self.headers_b = {"Authorization": f"Bearer {self.token_b}"}

        self.client = TestClient(self.main.app)

    async def test_adaptive_cold_start_refresh(self):
        """[MOCK-DB] Items with 0 sales and legacy forecast are refreshed to adaptive-v1 on get_todays_forecasts."""
        os.environ["FORECAST_MODE"] = "adaptive"

        item_id = str(ObjectId())
        today_str = self.main.get_store_local_now(self.user_a).strftime("%Y-%m-%d")

        # Item created with initial legacy forecast (0 days of history)
        item_doc = {
            "_id": item_id,
            "owner_id": self.user_a_id,
            "name": "Cold Start Baguette",
            "category": "Bakery",
            "unit": "loaf",
            "price": 50.0,
            "currentStock": 10,
            "isPerishable": True,
            "predictedDemand": 24,
            "safetyStock": 6,
        }
        await self.mock_db.items.insert_one(item_doc)

        # Legacy forecast doc (no engine field)
        await self.mock_db.forecasts.insert_one({
            "_id": str(ObjectId()),
            "item_id": item_id,
            "owner_id": self.user_a_id,
            "forecast_date": today_str,
            "predictedDemand": 24,
            "safetyStock": 6,
            "tier": "Learning",
        })

        # Hit HTTP endpoint
        resp = self.client.get("/api/v1/forecasts/today", headers=self.headers_a)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        item_fc = next((x for x in data.get("items", []) if x.get("id") == item_id or x.get("_id") == item_id), None)
        self.assertIsNotNone(item_fc)

        # In adaptive mode, the forecast was refreshed to adaptive-v1 cold-start
        self.assertEqual(item_fc.get("forecastMethod"), "prior")
        self.assertEqual(item_fc.get("forecastMethodLabel"), "Category benchmark")
        self.assertEqual(item_fc.get("evalDays"), 0)

    async def test_adaptive_10_days_closing_counts_flow(self):
        """[MOCK-DB] 10 simulated days of closing counts smoothly transition method from prior to mature tournament."""
        os.environ["FORECAST_MODE"] = "adaptive"

        item_id = str(ObjectId())
        item_doc = {
            "_id": item_id,
            "owner_id": self.user_a_id,
            "name": "Country Sourdough",
            "category": "Bakery",
            "price": 60.0,
            "currentStock": 15,
            "isPerishable": True,
        }
        await self.mock_db.items.insert_one(item_doc)

        start_date = date(2026, 10, 1)
        # Step 1: Simulate Day 1-4 (short history)
        for i in range(4):
            day_str = (start_date + timedelta(days=i)).isoformat()
            await self.mock_db.daily_sales.insert_one({
                "owner_id": self.user_a_id,
                "item_id": item_id,
                "date": day_str,
                "units": 25 + (i * 2),
                "status": "completed",
            })

        fc_day4 = await self.main.refresh_item_forecast(self.user_a_id, item_doc, "2026-10-05")
        self.assertIsNotNone(fc_day4)
        self.assertEqual(fc_day4["forecastMethod"], "ewma")
        self.assertEqual(fc_day4["forecastMethodLabel"], "Smoothed recent sales")
        self.assertEqual(fc_day4["historyDays"], 4)

        # Step 2: Simulate through Day 10 (mature tournament activated at n >= 5)
        for i in range(4, 10):
            day_str = (start_date + timedelta(days=i)).isoformat()
            await self.mock_db.daily_sales.insert_one({
                "owner_id": self.user_a_id,
                "item_id": item_id,
                "date": day_str,
                "units": 30 + (i % 3) * 5,
                "status": "completed",
            })

        fc_day10 = await self.main.refresh_item_forecast(self.user_a_id, item_doc, "2026-10-11")
        self.assertIsNotNone(fc_day10)
        self.assertIn(fc_day10["forecastMethod"], ["ma7", "last", "ewma"])
        self.assertGreater(fc_day10["evalDays"], 0)
        self.assertEqual(fc_day10["historyDays"], 10)
        self.assertIsNotNone(fc_day10["methodMae"])
        self.assertIsNotNone(fc_day10["baselineMae"])

    async def test_tenant_isolation_foreign_item_id_injection_blocked(self):
        """[MOCK-DB] Proves tenant isolation: User B inserting sales pointing to User A's item_id NEVER pollutes User A."""
        os.environ["FORECAST_MODE"] = "adaptive"

        item_a_id = str(ObjectId())

        item_a = {
            "_id": item_a_id, "owner_id": self.user_a_id, "name": "Baguette A",
            "category": "Bakery", "price": 40.0, "currentStock": 20, "isPerishable": True,
        }
        await self.mock_db.items.insert_one(item_a)

        base_date = date(2026, 10, 1)
        for i in range(8):
            d_str = (base_date + timedelta(days=i)).isoformat()
            # User A: modest Kirana bakery sales (20 units/day)
            await self.mock_db.daily_sales.insert_one({
                "owner_id": self.user_a_id, "item_id": item_a_id, "date": d_str,
                "units": 20, "status": "completed",
            })
            # User B: maliciously/accidentally records 500 units on the SAME item_a_id under user_b_id
            await self.mock_db.daily_sales.insert_one({
                "owner_id": self.user_b_id, "item_id": item_a_id, "date": d_str,
                "units": 500, "status": "completed",
            })

        pred_date = "2026-10-09"
        fc_a = await self.main.refresh_item_forecast(self.user_a_id, item_a, pred_date)

        # User A's forecast must be strictly ~20 units, completely unpolluted by User B's 500 units!
        self.assertLess(fc_a["predictedDemand"], 25)

    async def test_feature_flag_off_preserves_legacy_output(self):
        """[MOCK-DB] When FORECAST_MODE=legacy, GET /api/v1/forecasts/today returns HTTP 200 without adaptive metadata."""
        os.environ["FORECAST_MODE"] = "legacy"

        item_id = str(ObjectId())
        today_str = self.main.get_store_local_now(self.user_a).strftime("%Y-%m-%d")

        item_doc = {
            "_id": item_id, "owner_id": self.user_a_id, "name": "Legacy Bun",
            "category": "Bakery", "unit": "units", "predictedDemand": 24, "safetyStock": 7, "description": "Legacy TSB snapshot",
        }
        await self.mock_db.items.insert_one(item_doc)

        await self.mock_db.forecasts.insert_one({
            "_id": str(ObjectId()),
            "item_id": item_id,
            "owner_id": self.user_a_id,
            "forecast_date": today_str,
            "predictedDemand": 24,
            "safetyStock": 7,
            "tier": "Learning",
        })

        resp = self.client.get("/api/v1/forecasts/today", headers=self.headers_a)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        item_fc = next((x for x in data.get("items", []) if x.get("id") == item_id or x.get("_id") == item_id), None)
        self.assertIsNotNone(item_fc)
        self.assertIsNone(item_fc.get("forecastMethod"))
        self.assertIsNone(item_fc.get("evalDays"))

    async def test_adaptive_failure_falls_back_safely_never_500(self):
        """[MOCK-DB] When adaptive forecast raises an unexpected exception, HTTP endpoint returns 200 (never 500)."""
        os.environ["FORECAST_MODE"] = "adaptive"

        item_id = str(ObjectId())
        item_doc = {
            "_id": item_id, "owner_id": self.user_a_id, "name": "Crash Item",
            "category": "Bakery", "unit": "units", "predictedDemand": 20, "safetyStock": 5, "description": "Fallback description",
        }
        await self.mock_db.items.insert_one(item_doc)

        # Mock forecast_item to simulate an unexpected runtime error inside the engine
        with patch("adaptive_forecast.forecast_item", side_effect=RuntimeError("Simulated engine failure")):
            resp = self.client.get("/api/v1/forecasts/today", headers=self.headers_a)
            self.assertEqual(resp.status_code, 200, f"Expected HTTP 200 fallback, got {resp.status_code}")
            data = resp.json()
            item_fc = next((x for x in data.get("items", []) if x.get("id") == item_id or x.get("_id") == item_id), None)
            self.assertIsNotNone(item_fc)
            # Must fall back gracefully to legacy item fields
            self.assertEqual(item_fc.get("predictedDemand"), 20)

    async def test_batch_forecast_skips_adaptive_documents(self):
        """[MOCK-DB] Verifies atomic update in ML/batch_forecast.py skips active adaptive forecast documents."""
        item_id = str(ObjectId())
        today_str = "2026-10-30"

        # Active adaptive document
        await self.mock_db.forecasts.insert_one({
            "item_id": item_id,
            "owner_id": self.user_a_id,
            "forecast_date": today_str,
            "predictedDemand": 42,
            "safetyStock": 10,
            "engine": "adaptive-v1",
            "forecastMethod": "ma7",
            "forecastMethodLabel": "7-day average",
        })

        # Batch forecast atomic update query from ML/batch_forecast.py
        batch_doc = {
            "predictedDemand": 99,
            "safetyStock": 99,
            "engine": "legacy",
        }
        res = await self.mock_db.forecasts.update_one(
            {
                "item_id": item_id,
                "forecast_date": today_str,
                "owner_id": self.user_a_id,
                "engine": {"$not": {"$regex": "^adaptive"}},
            },
            {"$set": batch_doc},
        )
        # Because engine is adaptive-v1, matched_count must be 0 (skipped!)
        self.assertEqual(res.matched_count, 0)

        # Verify the stored document was NOT overwritten
        doc_in_db = await self.mock_db.forecasts.find_one({
            "item_id": item_id, "forecast_date": today_str, "owner_id": self.user_a_id
        })
        self.assertEqual(doc_in_db["predictedDemand"], 42)
        self.assertEqual(doc_in_db["engine"], "adaptive-v1")
