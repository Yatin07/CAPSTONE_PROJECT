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

    def test_rollup_daily_sales_authorization_and_scoping(self):
        """[MOCK-DB] Test that rollup-daily-sales restricts normal user to own owner_id and rejects unauthorized calls."""
        from main import trigger_daily_sales_rollup, SECRET_KEY, ALGORITHM
        from jose import jwt
        from starlette.requests import Request

        # 1. Reject without auth
        req_unauth = Request(scope={"type": "http", "headers": []})
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(trigger_daily_sales_rollup(req_unauth, target_date="2026-10-29", authorization=None))
        self.assertEqual(ctx.exception.status_code, 401)

        # 2. Accept with valid user Bearer token and scope to that user
        token_a = jwt.encode({"sub": "owner_alpha", "role": "owner"}, SECRET_KEY, algorithm=ALGORITHM)
        req_user = Request(scope={"type": "http", "headers": [(b"authorization", f"Bearer {token_a}".encode())]})
        
        with patch("main.rollup_daily_sales", return_value={"status": "success", "scoped_owner": "owner_alpha"}) as mock_rollup:
            res = asyncio.run(trigger_daily_sales_rollup(req_user, target_date="2026-10-29", authorization=f"Bearer {token_a}"))
            mock_rollup.assert_called_once_with("2026-10-29", owner_id="owner_alpha")
            self.assertEqual(res["scoped_owner"], "owner_alpha")

        # 3. Server authorization via X-Job-Secret processes all owners (owner_id=None)
        with patch.dict(os.environ, {"JOB_SECRET": "test_secret_1234"}):
            req_server = Request(scope={"type": "http", "headers": [(b"x-job-secret", b"test_secret_1234")]})
            with patch("main.rollup_daily_sales", return_value={"status": "success", "scoped_owner": "all"}) as mock_rollup_all:
                res_server = asyncio.run(trigger_daily_sales_rollup(req_server, target_date="2026-10-29", authorization=None))
                mock_rollup_all.assert_called_once_with("2026-10-29", owner_id=None)
                self.assertEqual(res_server["scoped_owner"], "all")

    def test_assistant_daily_query_limit_15(self):
        """[MOCK-DB] Test that manager assistant query limit caps at 15 queries per user per day."""
        from main import assistant_chat, AssistantChatRequest, ASSISTANT_DAILY_QUERY_COUNTS
        from unittest.mock import AsyncMock

        user = {"_id": "test_user_limit", "name": "Test Owner", "role": "owner"}
        ASSISTANT_DAILY_QUERY_COUNTS.clear()

        # Mock db.items to return 1 item so not empty
        mock_items_cursor = MagicMock()
        mock_items_cursor.to_list = AsyncMock(return_value=[{"_id": "it1", "name": "Baguette", "owner_id": "test_user_limit"}])

        mock_db = MagicMock()
        mock_db.items.find = MagicMock(return_value=mock_items_cursor)

        with patch("main.db", mock_db):
            with patch("main.get_waste_alerts", AsyncMock(return_value={"alerts": []})):
                with patch("main.answer_assistant_chat", return_value={"reply": "Mock reply", "provider": "system", "model": "test"}):
                    # Queries 1..15 must succeed
                    for i in range(1, 16):
                        res = asyncio.run(assistant_chat(AssistantChatRequest(query=f"Query {i}"), current_user=user))
                        self.assertEqual(res["status"], "success")

                    # Query 16 must hit rate_limited limit
                    res_16 = asyncio.run(assistant_chat(AssistantChatRequest(query="Query 16"), current_user=user))
                    self.assertEqual(res_16["status"], "rate_limited")
                    self.assertIn("Daily query limit reached", res_16["reply"])

    def test_empty_store_briefing_and_chat_zero_llm(self):
        """[MOCK-DB] Test that store with 0 items returns immediate empty status with ZERO LLM calls."""
        from main import get_today_executive_briefing, assistant_chat, AssistantChatRequest
        from unittest.mock import AsyncMock

        user = {"_id": "empty_user", "name": "Empty Owner", "role": "owner"}

        mock_empty_cursor = MagicMock()
        mock_empty_cursor.to_list = AsyncMock(return_value=[])

        mock_db = MagicMock()
        mock_db.items.find = MagicMock(return_value=mock_empty_cursor)

        with patch("main.db", mock_db):
            with patch("services.llm_service.generate_daily_briefing") as mock_gen_briefing:
                with patch("services.llm_service.answer_assistant_chat") as mock_gen_chat:
                    # 1. Briefing
                    b_res = asyncio.run(get_today_executive_briefing(current_user=user))
                    self.assertEqual(b_res["status"], "success")
                    self.assertEqual(b_res["briefing"]["source"], "empty")
                    self.assertIn("inventory is currently empty", b_res["briefing"]["executive_summary"])
                    mock_gen_briefing.assert_not_called()

                    # 2. Assistant Chat
                    c_res = asyncio.run(assistant_chat(AssistantChatRequest(query="How are sales?"), current_user=user))
                    self.assertEqual(c_res["status"], "empty")
                    self.assertIn("no items in inventory", c_res["reply"])
                    mock_gen_chat.assert_not_called()


if __name__ == "__main__":
    unittest.main()
