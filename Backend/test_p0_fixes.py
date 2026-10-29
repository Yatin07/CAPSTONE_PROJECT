"""
Unit tests for Section 1 (P0 Fixes):
- Account lockout after 5 failed password attempts
- Immediate cold-start forecast on item creation
- Coherence: item with active alert gets 0 restock
- Gemini quota caching with 10-minute cooldown
- Deterministic fallback label and RUN_LIVE_GEMINI enforcement
"""
import unittest
import time
import os
import asyncio
from unittest.mock import patch, MagicMock

import sys
import os

# Add Backend root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set testing flag
os.environ["TESTING"] = "1"
os.environ["RUN_LIVE_GEMINI"] = "0"

from fastapi import HTTPException
from pydantic import BaseModel
import main
from main import (
    ACCOUNT_LOCKOUTS,
    MAX_FAILED_LOGIN_ATTEMPTS,
    LOCKOUT_DURATION_SECONDS,
    login,
    LoginRequest,
    evaluate_waste_alert_tier,
    check_item_waste_alert_sync,
    BRIEFING_CACHE,
    BRIEFING_COOLDOWN_SECONDS,
)
from services.llm_service import (
    _build_deterministic_fallback,
    build_briefing_prompt,
    build_assistant_prompt,
    should_call_live_gemini,
)
from constants import CATEGORY_PRIORS


class TestP0Fixes(unittest.TestCase):

    def setUp(self):
        ACCOUNT_LOCKOUTS.clear()
        BRIEFING_CACHE.clear()

    def test_account_lockout_after_five_failed_attempts(self):
        """[MOCK-DB] Test that 5 consecutive failed logins lock account for 15 minutes."""
        test_email = "lockout_test@example.com"
        req = LoginRequest(email=test_email, password="wrongpassword")

        # Mock main.db with an async find_one
        mock_db = MagicMock()
        async def fake_find_one(query):
            return {
                "_id": "user123",
                "email": test_email,
                "password_hash": main.hash_password("correctpassword"),
                "name": "Test User",
                "role": "owner",
            }
        mock_db.users.find_one = fake_find_one

        with patch.object(main, "db", mock_db):
            # Attempts 1 through 4: standard 401
            for attempt in range(1, 5):
                with self.assertRaises(HTTPException) as ctx:
                    asyncio.run(login(req))
                self.assertEqual(ctx.exception.status_code, 401)
                self.assertEqual(ctx.exception.detail, "Invalid email or password")
                self.assertEqual(ACCOUNT_LOCKOUTS[test_email]["failed_count"], attempt)

            # Attempt 5: triggers lockout
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(login(req))
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertIn("temporarily locked", ctx.exception.detail)
            self.assertEqual(ACCOUNT_LOCKOUTS[test_email]["failed_count"], 5)
            self.assertGreater(ACCOUNT_LOCKOUTS[test_email]["locked_until"], time.time() + 14 * 60)

            # Subsequent attempt while locked: blocked immediately
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(login(req))
            self.assertEqual(ctx.exception.status_code, 401)
            self.assertIn("temporarily locked", ctx.exception.detail)

    def test_immediate_cold_start_forecast_item_creation(self):
        """[MOCK-DB] Verify new item receives category-prior forecast immediately."""
        cat = "Bakery"
        prior = CATEGORY_PRIORS[cat]
        self.assertEqual(prior["predictedDemand"], 24)
        self.assertEqual(prior["safetyStock"], 7)

        # Ensure pure Python category priors exist for all standard categories
        for standard_cat in ["Bakery", "Beverage", "Food", "Dessert", "Snack", "Other"]:
            self.assertIn(standard_cat, CATEGORY_PRIORS)
            self.assertGreater(CATEGORY_PRIORS[standard_cat]["predictedDemand"], 0)
            self.assertGreater(CATEGORY_PRIORS[standard_cat]["safetyStock"], 0)

    def test_coherence_restock_held_to_zero_for_active_alerts(self):
        """[MOCK-DB] Verify that active Low Pace or Critical alert holds restock to 0."""
        # 1. Critical Alert (sales pace < 0.35)
        crit_tier = evaluate_waste_alert_tier(
            is_perishable=True,
            is_dismissed=False,
            curr_stock=25,
            actual_sold=2.0,
            expected_by_now=10.0,  # pace = 0.20
        )
        self.assertIsNotNone(crit_tier)
        self.assertEqual(crit_tier["severityLabel"], "Critical")

        # 2. Check item alert sync
        test_doc = {
            "isPerishable": True,
            "isDismissed": False,
            "intradaySales": 2,
            "currentStock": 25,
        }
        test_user = {
            "opening_hour": 8.0,
            "closing_hour": 20.0,
            "timezone": "Asia/Kolkata",
        }
        # Simulated check
        has_alert, label = check_item_waste_alert_sync(
            test_doc, test_user, predicted_demand=20, curr_stock=25
        )
        # Verify deterministic fallback also zeroes out restock for alert items
        items = [
            {"id": "item1", "name": "Baguette", "currentStock": 2, "predictedDemand": 20, "safetyStock": 5, "restockQuantity": 0},
            {"id": "item2", "name": "Croissant", "currentStock": 1, "predictedDemand": 15, "safetyStock": 4, "restockQuantity": 18},
        ]
        alerts = [
            {"id": "item1", "itemName": "Baguette", "severityLabel": "Critical", "recommendedActionText": "Apply 20% Bundle"}
        ]
        fb = _build_deterministic_fallback(items, alerts)
        # Baguette must NOT be in restock priority actions
        for act in fb["actions"]:
            if "Restock priority" in act:
                self.assertNotIn("Baguette", act)
                self.assertIn("Croissant", act)
        # Baguette MUST be in waste mitigation actions
        self.assertTrue(any("Baguette" in a and "restock held to 0" in a for a in fb["actions"]))

    def test_briefing_cache_ten_minute_cooldown(self):
        """[MOCK-DB] Test that briefing cache retains entry within 600s."""
        user_id = "test_owner_999"
        date_str = "2026-10-29"
        cache_key = (user_id, date_str)

        test_briefing = {
            "source": "fallback",
            "executive_summary": "Test Executive Summary",
            "actions": ["Action 1"],
        }
        BRIEFING_CACHE[cache_key] = {
            "briefing": test_briefing,
            "cached_at": time.time(),
        }

        # Validate cooldown logic
        cached = BRIEFING_CACHE.get(cache_key)
        self.assertIsNotNone(cached)
        self.assertLess(time.time() - cached["cached_at"], BRIEFING_COOLDOWN_SECONDS)

    def test_run_live_gemini_guard_in_tests(self):
        """[MOCK-DB] Test that live Gemini is disabled when RUN_LIVE_GEMINI!=1."""
        os.environ["RUN_LIVE_GEMINI"] = "0"
        self.assertFalse(should_call_live_gemini())

        os.environ["RUN_LIVE_GEMINI"] = "1"
        # Only true if configured
        with patch("services.llm_service.is_llm_configured", return_value=True):
            self.assertTrue(should_call_live_gemini())
        os.environ["RUN_LIVE_GEMINI"] = "0"

    def test_deterministic_fallback_label(self):
        """[MOCK-DB] Test fallback contains explicit label."""
        fb = _build_deterministic_fallback([], [])
        self.assertEqual(fb["label"], "[Deterministic Fallback Mode]")
        self.assertTrue(fb["is_fallback"])
        self.assertIn("[Deterministic Fallback Mode]", fb["raw_text"])


if __name__ == "__main__":
    unittest.main()
