import sys
import copy
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
from mongomock_motor import AsyncMongoMockClient

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
ml_dir = backend_dir.parent / "ML"
if str(ml_dir) not in sys.path:
    sys.path.insert(0, str(ml_dir))

import main
import batch_forecast

class TestAcceptanceLifecycle(unittest.IsolatedAsyncioTestCase):
    """
    [MOCK-DB] Acceptance Test Suite for Stage 2 Daily State & Batch Idempotency.
    Validates:
      1. Batch run twice on one day leaves history unchanged (idempotent).
      2. Batch run mid-day does NOT mutate live intradaySales, flags, or prices.
      3. Batch run 6 hours late does NOT merge multi-day sales.
      4. Day 1 sales transition to Day 2: alerts start fresh via lazy rollover.
      5. daily_sales collection and idempotent rollup_daily_sales() aggregation.
    """

    async def asyncSetUp(self):
        self.client = AsyncMongoMockClient()
        self.db = self.client["restockiq_acceptance"]
        main.client = self.client
        main.db = self.db
        sync_client = getattr(self.client, "_AsyncMongoMockClient__client", None)
        if sync_client is None:
            import mongomock
            sync_client = mongomock.MongoClient()
        batch_forecast.client = sync_client
        batch_forecast.db = sync_client["restockiq_acceptance"]

        self.owner_id = "tenant_cafe_01"
        self.user = {"_id": self.owner_id, "role": "owner", "timezone": "Asia/Kolkata"}
        self.item = {
            "_id": "croissant_acc_01",
            "owner_id": self.owner_id,
            "name": "Croissants",
            "category": "Bakery",
            "unit": "Units",
            "currentStock": 50,
            "isPerishable": True,
            "price": 2.72,
            "originalPrice": 3.40,
            "discountApplied": True,
            "isPrimaryActionDone": True,
            "intradaySales": 15,
            "intradayDate": "2026-10-28",
            "salesHistory": [20, 22, 24, 21, 23],
            "predictedDemand": 26,
            "safetyStock": 10,
        }
        await self.db.items.insert_one(copy.deepcopy(self.item))
        await self.db.daily_sales.create_index([("owner_id", 1), ("item_id", 1), ("date", 1)], unique=True)

    async def test_batch_run_twice_idempotency(self):
        """[MOCK-DB] Running the batch twice on the same day must leave salesHistory unchanged."""
        # Run 1
        batch_forecast.run_batch_job(dry_run=False, as_of="2026-10-29")
        item_after_1 = await self.db.items.find_one({"_id": "croissant_acc_01"})
        hist_1 = list(item_after_1.get("salesHistory", []))

        # Run 2 on same day
        batch_forecast.run_batch_job(dry_run=False, as_of="2026-10-29")
        item_after_2 = await self.db.items.find_one({"_id": "croissant_acc_01"})
        hist_2 = list(item_after_2.get("salesHistory", []))

        self.assertEqual(hist_1, hist_2, "salesHistory mutated during duplicate batch run!")
        # Confirm forecasts collection has exactly 1 record for this day
        count_fc = await self.db.forecasts.count_documents({"item_id": "croissant_acc_01", "forecast_date": "2026-10-29"})
        self.assertEqual(count_fc, 1, "Duplicate forecast documents created for same date!")
        print("\n[ACCEPTANCE 1 PASS] Batch run twice on one day: salesHistory unchanged, exactly 1 forecast record.")

    async def test_batch_run_midday_no_intraday_mutation(self):
        """[MOCK-DB] Running the batch mid-day must NOT mutate live intradaySales, flags, or promotional price."""
        # Set mid-day shopping state
        await self.db.items.update_one(
            {"_id": "croissant_acc_01"},
            {"$set": {
                "intradaySales": 18,
                "discountApplied": True,
                "price": 2.72,
                "originalPrice": 3.40,
                "isPrimaryActionDone": True,
            }}
        )

        # Run batch at mid-day
        batch_forecast.run_batch_job(dry_run=False, as_of="2026-10-29")

        # Verify live operational fields were untouched
        item = await self.db.items.find_one({"_id": "croissant_acc_01"})
        self.assertEqual(item["intradaySales"], 18, "intradaySales was mutated by batch!")
        self.assertEqual(item["price"], 2.72, "Promotional price was reverted mid-day!")
        self.assertTrue(item["discountApplied"], "discountApplied flag was cleared mid-day!")
        self.assertTrue(item["isPrimaryActionDone"], "Action flag was cleared mid-day!")
        print("[ACCEPTANCE 2 PASS] Batch run mid-day: intradaySales (18), discount (2.72), and flags preserved 100%.")

    async def test_batch_run_late_no_merge(self):
        """[MOCK-DB] Running the batch 6 hours late must not merge morning sales with yesterday."""
        # Morning of Day 2: 4 new croissants sold
        await self.db.items.update_one(
            {"_id": "croissant_acc_01"},
            {"$set": {"intradaySales": 4, "intradayDate": "2026-10-29"}}
        )

        # Late batch runs for 2026-10-29
        batch_forecast.run_batch_job(dry_run=False, as_of="2026-10-29")

        # Today's morning sales must remain intact at 4
        item = await self.db.items.find_one({"_id": "croissant_acc_01"})
        self.assertEqual(item["intradaySales"], 4, "Late batch wiped morning sales!")
        self.assertEqual(item["intradayDate"], "2026-10-29")
        print("[ACCEPTANCE 3 PASS] Batch run late: morning intraday sales remain 4, no multi-day merge.")

    async def test_day1_to_day2_alerts_start_fresh(self):
        """[MOCK-DB] Day 1 sales transition to Day 2: alerts start fresh via lazy rollover."""
        # Day 1: 25 units sold on 2026-10-28
        await self.db.items.update_one(
            {"_id": "croissant_acc_01"},
            {"$set": {"intradaySales": 25, "intradayDate": "2026-10-28", "isDismissed": True}}
        )

        # Day 2 morning (09:00 AM local on 2026-10-29)
        dt_day2_morning = datetime(2026, 10, 29, 9, 0, tzinfo=timezone.utc)
        with patch("main.get_store_local_now", return_value=dt_day2_morning):
            alerts_resp = await main.get_waste_alerts(current_user=self.user)
            self.assertEqual(alerts_resp["store_status"], "open" if "store_status" in alerts_resp else alerts_resp.get("store_status", "open"))

            # Item in DB must have rolled over to 0 sales for 2026-10-29
            item = await self.db.items.find_one({"_id": "croissant_acc_01"})
            self.assertEqual(item["intradaySales"], 0, "intradaySales did not reset on Day 2!")
            self.assertEqual(item["intradayDate"], "2026-10-29")
            self.assertFalse(item["isDismissed"], "Dismissed flag did not reset on Day 2!")
            print("[ACCEPTANCE 4 PASS] Day 1 -> Day 2: Lazy rollover reset intradaySales to 0 and cleared dismissed flag.")

    async def test_daily_sales_rollup_idempotency(self):
        """[MOCK-DB] rollup_daily_sales aggregates intraday_sales into daily_sales idempotently."""
        # Insert 3 sales events for 2026-10-28: 2 + 5 + 3 = 10 units
        sales_events = [
            {"owner_id": self.owner_id, "item_id": "croissant_acc_01", "quantity": 2, "date": "2026-10-28"},
            {"owner_id": self.owner_id, "item_id": "croissant_acc_01", "quantity": 5, "date": "2026-10-28"},
            {"owner_id": self.owner_id, "item_id": "croissant_acc_01", "quantity": 3, "date": "2026-10-28"},
        ]
        await self.db.intraday_sales.insert_many(sales_events)

        # Execute rollup for 2026-10-28
        res1 = await main.rollup_daily_sales("2026-10-28")
        self.assertEqual(res1["status"], "success")

        # Verify daily_sales record
        record1 = await self.db.daily_sales.find_one({"owner_id": self.owner_id, "item_id": "croissant_acc_01", "date": "2026-10-28"})
        self.assertIsNotNone(record1)
        self.assertEqual(record1["units"], 10)

        # Run rollup a second time -> MUST BE IDEMPOTENT (units still 10, no duplicate record)
        res2 = await main.rollup_daily_sales("2026-10-28")
        self.assertEqual(res2["status"], "success")

        total_daily_docs = await self.db.daily_sales.count_documents({"owner_id": self.owner_id, "item_id": "croissant_acc_01", "date": "2026-10-28"})
        self.assertEqual(total_daily_docs, 1, "Duplicate daily_sales records created!")
        record2 = await self.db.daily_sales.find_one({"owner_id": self.owner_id, "item_id": "croissant_acc_01", "date": "2026-10-28"})
        self.assertEqual(record2["units"], 10)
        print("[ACCEPTANCE 5 PASS] rollup_daily_sales(): Aggregated 10 units, 100% idempotent on second run.")

if __name__ == "__main__":
    unittest.main()
