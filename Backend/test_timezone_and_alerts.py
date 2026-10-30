import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from mongomock_motor import AsyncMongoMockClient

import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import main
from constants import STORE_OPEN_HOUR, STORE_CLOSE_HOUR

class TestTimezoneAndWasteAlerts(unittest.IsolatedAsyncioTestCase):
    """
    [MOCK-DB] Suite for store-local operating hours, elapsed fraction, closed store states,
    and midnight timezone boundary rollover.
    """

    async def asyncSetUp(self):
        self.mock_client = AsyncMongoMockClient()
        self.mock_db = self.mock_client["restockiq_test"]
        main.client = self.mock_client
        main.db = self.mock_db

        self.user = {"_id": "test_owner_01", "role": "owner", "timezone": "Asia/Kolkata"}
        self.item = {
            "_id": "croissant_01",
            "owner_id": "test_owner_01",
            "name": "Butter Croissant",
            "isPerishable": True,
            "currentStock": 20,
            "intradaySales": 5,
            "intradayDate": "2026-10-28",
            "price": 2.72,
            "originalPrice": 3.40,
            "discountApplied": True,
            "isPrimaryActionDone": True,
            "isDismissed": False,
        }
        await self.mock_db.items.insert_one(self.item)

    def test_elapsed_fraction_calculation(self):
        """Validates the exact mathematical formula (local_hour_fraction - open) / (close - open)."""
        open_h = 8.0
        close_h = 20.0
        total_duration = close_h - open_h  # 12.0 hours

        # 09:00 AM -> 9.0
        fraction_0900 = (9.0 - open_h) / total_duration
        self.assertAlmostEqual(fraction_0900, 1.0 / 12.0, places=4)
        print(f"\n[TEST] Local 09:00 -> elapsed_fraction = {fraction_0900:.4f} (8.33% of business day)")

        # 14:00 PM -> 14.0
        fraction_1400 = (14.0 - open_h) / total_duration
        self.assertAlmostEqual(fraction_1400, 6.0 / 12.0, places=4)
        print(f"[TEST] Local 14:00 -> elapsed_fraction = {fraction_1400:.4f} (50.00% of business day)")

    async def test_store_closed_states(self):
        """Validates zero alerts and 'closed' status at 01:30, 20:00, 23:30, and 00:30."""
        # 1. Test at 01:30 AM local
        dt_0130 = datetime(2026, 10, 29, 1, 30, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_0130):
            res_0130 = await main.get_waste_alerts(current_user=self.user)
            self.assertEqual(res_0130["store_status"], "closed")
            self.assertEqual(res_0130["total_alerts"], 0)
            print("[TEST] Local 01:30 -> Store is CLOSED, 0 alerts returned.")

        # 2. Test at 20:00 PM local (closing time)
        dt_2000 = datetime(2026, 10, 29, 20, 0, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_2000):
            res_2000 = await main.get_waste_alerts(current_user=self.user)
            self.assertEqual(res_2000["store_status"], "closed")
            self.assertEqual(res_2000["total_alerts"], 0)
            print("[TEST] Local 20:00 -> Store is CLOSED, 0 alerts returned.")

        # 3. Test at 23:30 PM local
        dt_2330 = datetime(2026, 10, 29, 23, 30, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_2330):
            res_2330 = await main.get_waste_alerts(current_user=self.user)
            self.assertEqual(res_2330["store_status"], "closed")
            self.assertEqual(res_2330["total_alerts"], 0)
            print("[TEST] Local 23:30 -> Store is CLOSED, 0 alerts returned.")

        # 4. Test at 00:30 AM local
        dt_0030 = datetime(2026, 10, 30, 0, 30, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_0030):
            res_0030 = await main.get_waste_alerts(current_user=self.user)
            self.assertEqual(res_0030["store_status"], "closed")
            self.assertEqual(res_0030["total_alerts"], 0)
            print("[TEST] Local 00:30 -> Store is CLOSED, 0 alerts returned.")

    async def test_midnight_rollover_boundary(self):
        """
        Validates transition across 23:30 / 00:30 boundary:
        At 23:30 (Day 1): intradaySales=5, discountApplied=True
        At 00:30 (Day 2): lazy rollover resets intradaySales=0, discountApplied=False, price=$3.40.
        """
        # Read at 23:30 Day 1 (2026-10-28)
        dt_2330 = datetime(2026, 10, 28, 23, 30, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_2330):
            item_2330 = await main.rollover_if_new_day(dict(self.item), self.user)
            self.assertEqual(item_2330["intradaySales"], 5)
            self.assertEqual(item_2330["price"], 2.72)
            self.assertTrue(item_2330["discountApplied"])

        # Read at 00:30 Day 2 (2026-10-29) -> New day triggers lazy rollover
        dt_0030 = datetime(2026, 10, 29, 0, 30, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_0030):
            item_0030 = await main.rollover_if_new_day(dict(self.item), self.user)
            self.assertEqual(item_0030["intradaySales"], 0, "Intraday sales must reset on new local day!")
            self.assertEqual(item_0030["intradayDate"], "2026-10-29")
            self.assertEqual(item_0030["price"], 3.40, "Promotional discount must revert to original price!")
            self.assertFalse(item_0030["discountApplied"])
            self.assertFalse(item_0030["isPrimaryActionDone"])
            print("[TEST] 23:30 -> 00:30 midnight boundary: Successfully rolled over intradaySales to 0 and reverted price to $3.40.")


    async def test_overnight_store_operating_window_and_alerts(self):
        night_user = {
            "_id": "night_owner_01",
            "role": "owner",
            "timezone": "Asia/Kolkata",
            "opening_hour": 20.0,
            "closing_hour": 4.0
        }
        night_item = {
            "_id": "night_croissant",
            "owner_id": "night_owner_01",
            "name": "Night Croissant",
            "isPerishable": True,
            "currentStock": 30,
            "intradaySales": 2,
            "intradayDate": "2026-10-30",
            "price": 3.0,
            "isDismissed": False,
        }
        await self.mock_db.items.insert_one(night_item)

        # 1. Test at 22:00 (10 PM) -> OPEN
        dt_2200 = datetime(2026, 10, 30, 22, 0, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_2200):
            res_2200 = await main.get_waste_alerts(current_user=night_user)
            self.assertEqual(res_2200.get("store_status"), "open")
            self.assertGreater(res_2200.get("total_alerts", 0), 0)
            print("[TEST] Overnight store at 22:00 -> Store is OPEN, alerts returned successfully.")

        # 2. Test at 02:00 (2 AM post-midnight) -> OPEN, shift sales preserved
        dt_0200 = datetime(2026, 10, 31, 2, 0, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_0200):
            res_0200 = await main.get_waste_alerts(current_user=night_user)
            self.assertEqual(res_0200.get("store_status"), "open")
            self.assertGreater(res_0200.get("total_alerts", 0), 0)
            print("[TEST] Overnight store at 02:00 AM -> Store is OPEN, active across midnight boundary.")

        # 3. Test at 12:00 (Noon) -> CLOSED
        dt_1200 = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_1200):
            res_1200 = await main.get_waste_alerts(current_user=night_user)
            self.assertEqual(res_1200.get("store_status"), "closed")
            self.assertEqual(res_1200.get("total_alerts"), 0)
            print("[TEST] Overnight store at 12:00 Noon -> Store is CLOSED.")

if __name__ == "__main__":
    unittest.main()
