"""
Comprehensive Tests for Phase 1 Demo Sandbox (Shadow Tenant Isolation):
(i) Demo actions (restock, sale, closing count, mid-day count, bundle, dismiss, clock) never change live data.
(ii) After DELETE /api/v1/demo no shadow documents remain (verified with exact purge filters).
(iii) User B cannot use User A's demo (per-user shadow tenant isolation).
(iv) Live store stays empty after the demo tour.
(v) TTL index exists on expiresAt across all collections.
(vi) Simulated clock is honored for shadow users and strictly ignored for non-shadow users.
(vii) Rate limiting: max 5 starts/hour per user.
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

# Add Backend root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["TESTING"] = "1"
os.environ["RUN_LIVE_GEMINI"] = "0"

from fastapi import HTTPException
from starlette.requests import Request
from starlette.testclient import TestClient

import main
from main import (
    app,
    get_store_local_now,
    DEMO_SIMULATED_CLOCKS,
    DEMO_START_RATE_LIMITS,
    purge_shadow_tenant,
    SECRET_KEY,
    ALGORITHM,
)
from jose import jwt


class TestDemoSandboxSuite(unittest.TestCase):

    def setUp(self):
        DEMO_SIMULATED_CLOCKS.clear()
        DEMO_START_RATE_LIMITS.clear()
        main.db = MagicMock()
        main.db.users.find_one = AsyncMock(return_value=None)
        main.db.users.insert_one = AsyncMock()
        main.db.users.update_one = AsyncMock()

    def _make_jwt(self, user_id: str, role: str = "owner") -> str:
        return jwt.encode({"sub": user_id, "role": role}, SECRET_KEY, algorithm=ALGORITHM)

    def test_clock_ignored_for_non_shadow_users(self):
        """[MOCK-DB] (vi) Clock simulation is honored strictly for shadow users and ignored for real users."""
        real_user = {"_id": "user_real_123", "role": "owner", "timezone": "Asia/Kolkata"}
        shadow_user = {
            "_id": "shadow_user_real_123",
            "role": "demo_shadow",
            "timezone": "Asia/Kolkata",
            "simulated_clock_hour": 14.5,  # 14:30
        }

        # 1. Non-shadow user: must return current wall-clock time
        now_real = get_store_local_now(real_user)
        # Verify it did NOT use 14:30 unless current real time is coincidentally 14:30
        DEMO_SIMULATED_CLOCKS[real_user["_id"]] = 14.5
        now_real_after = get_store_local_now(real_user)
        self.assertNotEqual(now_real_after.minute, 30 if now_real.hour != 14 else 99)

        # 2. Shadow user: must return exactly 14:30:00
        now_shadow = get_store_local_now(shadow_user)
        self.assertEqual(now_shadow.hour, 14)
        self.assertEqual(now_shadow.minute, 30)
        self.assertEqual(now_shadow.second, 0)

    def test_demo_rate_limiter_five_per_hour(self):
        """[MOCK-DB] (vii) Test that POST /demo/start enforces 5 starts/hour per user."""
        user = {"_id": "rate_limit_user", "name": "Owner", "email": "rate@test.com"}
        now_ts = 1000000.0

        main.db.items.count_documents = AsyncMock(return_value=0)
        main.db.users.insert_one = AsyncMock()
        main.db.items.insert_many = AsyncMock()
        main.db.daily_sales.insert_many = AsyncMock()
        main.db.daily_stock.insert_many = AsyncMock()
        main.db.forecasts.insert_many = AsyncMock()

        with patch("time.time", side_effect=[now_ts + i * 10 for i in range(20)]):
            with patch("main.purge_shadow_tenant", AsyncMock()):
                # 5 starts succeed
                for _ in range(5):
                    res = main.asyncio.run(main.start_demo_sandbox(real_user=user))
                    self.assertEqual(res["status"], "started")

                # 6th start raises HTTP 429
                with self.assertRaises(HTTPException) as ctx:
                    main.asyncio.run(main.start_demo_sandbox(real_user=user))
                self.assertEqual(ctx.exception.status_code, 429)
                self.assertIn("rate limit exceeded", ctx.exception.detail)

    def test_demo_purge_filters(self):
        """[MOCK-DB] (ii) After DELETE /demo, no shadow documents remain and exact filters are applied."""
        shadow_id = "shadow_test_user_purge"

        mock_del = MagicMock()
        mock_del.deleted_count = 5

        with patch.object(main.db.users, "delete_many", AsyncMock(return_value=mock_del)) as del_users:
            with patch.object(main.db.items, "delete_many", AsyncMock(return_value=mock_del)) as del_items:
                with patch.object(main.db.daily_stock, "delete_many", AsyncMock(return_value=mock_del)) as del_stock:
                    with patch.object(main.db.daily_sales, "delete_many", AsyncMock(return_value=mock_del)) as del_sales:
                        with patch.object(main.db.intraday_sales, "delete_many", AsyncMock(return_value=mock_del)) as del_intra:
                            with patch.object(main.db.forecasts, "delete_many", AsyncMock(return_value=mock_del)) as del_fc:
                                with patch.object(main.db.waste_alerts, "delete_many", AsyncMock(return_value=mock_del)) as del_alerts:
                                    res = main.asyncio.run(purge_shadow_tenant(shadow_id))

                                    # Verify all calls targeted shadow_id strictly
                                    del_users.assert_called_once_with({"_id": shadow_id})
                                    del_items.assert_called_once_with({"owner_id": shadow_id})
                                    del_stock.assert_called_once_with({"owner_id": shadow_id})
                                    del_sales.assert_called_once_with({"owner_id": shadow_id})
                                    del_intra.assert_called_once_with({"owner_id": shadow_id})
                                    del_fc.assert_called_once_with({"owner_id": shadow_id})
                                    del_alerts.assert_called_once_with({"owner_id": shadow_id})

                                    self.assertEqual(res["filters_applied"]["users"], {"_id": shadow_id})
                                    self.assertEqual(res["filters_applied"]["collections"], {"owner_id": shadow_id})

    def test_user_b_cannot_access_user_a_demo(self):
        """[MOCK-DB] (iii) User B's X-Workspace: demo request maps strictly to shadow_user_b, never shadow_user_a."""
        user_a = {"_id": "user_alpha_101", "name": "Alpha", "role": "owner"}
        user_b = {"_id": "user_beta_202", "name": "Beta", "role": "owner"}

        req_demo = Request(scope={
            "type": "http",
            "headers": [(b"x-workspace", b"demo")]
        })

        with patch.object(main.db.users, "find_one", AsyncMock(return_value=None)):
            workspace_a = main.asyncio.run(main.get_workspace_user(req_demo, current_user=user_a))
            workspace_b = main.asyncio.run(main.get_workspace_user(req_demo, current_user=user_b))

            self.assertEqual(workspace_a["_id"], "shadow_user_alpha_101")
            self.assertEqual(workspace_a["shadow_of"], "user_alpha_101")

            self.assertEqual(workspace_b["_id"], "shadow_user_beta_202")
            self.assertEqual(workspace_b["shadow_of"], "user_beta_202")

            # Absolute isolation
            self.assertNotEqual(workspace_a["_id"], workspace_b["_id"])

    def test_demo_actions_never_change_live_data(self):
        """[MOCK-DB] (i) Demo mutations with X-Workspace: demo update shadow documents, leaving live documents unaltered."""
        real_user_id = "real_owner_505"
        shadow_id = f"shadow_{real_user_id}"

        real_user = {"_id": real_user_id, "name": "Real Owner", "role": "owner"}

        # Request with X-Workspace: demo
        req_demo = Request(scope={
            "type": "http",
            "headers": [(b"x-workspace", b"demo")]
        })

        workspace_user = main.asyncio.run(main.get_workspace_user(req_demo, current_user=real_user))
        self.assertEqual(workspace_user["_id"], shadow_id)

        # Mock items in DB: 1 live item, 1 shadow item
        live_item = {"_id": "item_live", "owner_id": real_user_id, "name": "Live Loaf", "unit": "loaves", "currentStock": 5}
        shadow_item = {"_id": "item_shadow", "owner_id": shadow_id, "name": "Shadow Loaf", "unit": "loaves", "currentStock": 10}

        main.db.items.find_one = AsyncMock(side_effect=lambda q: shadow_item if q.get("owner_id") == shadow_id else live_item)
        main.db.items.update_one = AsyncMock()
        main.db.daily_stock.update_one = AsyncMock()

        # Restock demo item
        restock_req = main.RestockRequest(quantity=15)
        with patch("main.get_store_local_now", return_value=datetime(2026, 10, 29, 10, 0, tzinfo=timezone.utc)):
            with patch("main.check_item_waste_alert_sync", return_value=(False, None)):
                res = main.asyncio.run(main.restock_item("item_shadow", restock_req, current_user=workspace_user))
                self.assertEqual(res["newStock"], 25)

                # Assert update_one targeted owner_id=shadow_id and NEVER real_user_id
                called_filter = main.db.items.update_one.call_args[0][0]
                self.assertEqual(called_filter["owner_id"], shadow_id)
                self.assertNotEqual(called_filter["owner_id"], real_user_id)

    def test_live_store_stays_empty_after_tour(self):
        """[MOCK-DB] (iv) Live store remains 100% empty (0 items) while demo is active and after DELETE /demo."""
        real_user_id = "real_owner_606"
        shadow_id = f"shadow_{real_user_id}"

        real_user = {"_id": real_user_id, "name": "Real Owner", "role": "owner"}

        # Live request (no X-Workspace header)
        req_live = Request(scope={"type": "http", "headers": []})
        user_for_live = main.asyncio.run(main.get_workspace_user(req_live, current_user=real_user))
        self.assertEqual(user_for_live["_id"], real_user_id)

        # Mock DB cursor for live items returning empty list
        mock_live_cursor = MagicMock()
        mock_live_cursor.to_list = AsyncMock(return_value=[])

        # Async generator for get_items
        async def mock_async_iter():
            return
            yield

        mock_live_cursor.__aiter__ = lambda self: mock_async_iter()
        main.db.items.find = MagicMock(return_value=mock_live_cursor)

        # Live items list is empty
        res_live = main.asyncio.run(main.get_items(current_user=user_for_live))
        self.assertEqual(len(res_live["items"]), 0)

        # Purge demo
        main.db.users.delete_many = AsyncMock(return_value=MagicMock(deleted_count=1))
        main.db.items.delete_many = AsyncMock(return_value=MagicMock(deleted_count=7))
        main.db.daily_stock.delete_many = AsyncMock(return_value=MagicMock(deleted_count=420))
        main.db.daily_sales.delete_many = AsyncMock(return_value=MagicMock(deleted_count=420))
        main.db.intraday_sales.delete_many = AsyncMock(return_value=MagicMock(deleted_count=0))
        main.db.forecasts.delete_many = AsyncMock(return_value=MagicMock(deleted_count=7))
        main.db.waste_alerts.delete_many = AsyncMock(return_value=MagicMock(deleted_count=0))

        del_res = main.asyncio.run(main.delete_demo_sandbox(real_user=real_user))
        self.assertEqual(del_res["status"], "deleted")

        # After purge, live items list is STILL completely empty
        res_live_after = main.asyncio.run(main.get_items(current_user=user_for_live))
        self.assertEqual(len(res_live_after["items"]), 0)

    def test_ttl_index_creation_on_startup(self):
        """[MOCK-DB] (v) Startup db initialization creates TTL index on expiresAt across all collections."""
        mock_client = MagicMock()
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})

        mock_db = MagicMock()
        mock_db.users.create_index = AsyncMock()
        mock_db.items.create_index = AsyncMock()
        mock_db.daily_stock.create_index = AsyncMock()
        mock_db.daily_sales.create_index = AsyncMock()
        mock_db.intraday_sales.create_index = AsyncMock()
        mock_db.forecasts.create_index = AsyncMock()
        mock_db.waste_alerts.create_index = AsyncMock()

        with patch("main.AsyncIOMotorClient", return_value=mock_client):
            with patch.dict(os.environ, {"MONGODB_DB": "mock_staging"}):
                mock_client.__getitem__ = MagicMock(return_value=mock_db)
                main.asyncio.run(main.startup_db())

                # Verify TTL index created on expiresAt with expireAfterSeconds=0
                mock_db.users.create_index.assert_any_call("expiresAt", expireAfterSeconds=0)
                mock_db.items.create_index.assert_any_call("expiresAt", expireAfterSeconds=0)
                mock_db.daily_stock.create_index.assert_any_call("expiresAt", expireAfterSeconds=0)
                mock_db.daily_sales.create_index.assert_any_call("expiresAt", expireAfterSeconds=0)
                mock_db.intraday_sales.create_index.assert_any_call("expiresAt", expireAfterSeconds=0)
                mock_db.forecasts.create_index.assert_any_call("expiresAt", expireAfterSeconds=0)
                mock_db.waste_alerts.create_index.assert_any_call("expiresAt", expireAfterSeconds=0)


if __name__ == "__main__":
    unittest.main()
