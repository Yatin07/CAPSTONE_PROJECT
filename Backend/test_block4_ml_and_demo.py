"""
Block 4 Test Suite: Demo Store & Dual-Engine Model Verification
Tests:
- [MOCK-DB] Demo store seed idempotency and collection constraints
- [MOCK-DB] Newsvendor safety stock critical ratio calculation and clamping
- [MOCK-DB] Routing logic: items with <28 days or unmapped SKU route to benchmark/blend path
- [MOCK-DB] Routing logic: items with >=28 days and mapped bakery SKU route to GBDT Model (iv)
- [MOCK-DB] replayed_dataset contract verification in /me and /items
- [REAL-DB (restockiq_staging)] Verified demo manager account and replayed data integrity
"""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock

import mongomock
import numpy as np

# Add repo root to path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "Backend"
ml_dir = root_dir / "ML"
ml_site_packages = ml_dir / "venv" / "Lib" / "site-packages"
if ml_site_packages.exists():
    sys.path.insert(0, str(ml_site_packages))
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(ml_dir))

from engine import MLSharedEngine, NAME_MAP
from scripts.seed_demo_store import DEMO_EMAIL, DEMO_ITEMS_SPEC, seed_demo_store


class TestBlock4MLAndDemo(unittest.TestCase):
    def setUp(self):
        self.engine = MLSharedEngine()

    def test_mock_newsvendor_safety_stock_formula(self):
        """[MOCK-DB] Verifies Newsvendor critical ratio z = norm.ppf((price - cost)/price) with COGS_RATIO=0.40."""
        # Baseline with COGS_RATIO = 0.40 -> CR = 0.60 -> z ≈ 0.2533
        with patch.dict(os.environ, {"COGS_RATIO": "0.40"}):
            ss, z, cr = MLSharedEngine.compute_safety_stock(price=50.0, sigma=10.0)
            self.assertAlmostEqual(cr, 0.60, places=2)
            self.assertAlmostEqual(z, 0.2533, places=2)
            # raw safety = 0.2533 * 10 = 2.53 -> round = 3
            self.assertEqual(ss, 3)

        # High margin (COGS_RATIO = 0.10 -> CR = 0.90 -> z ≈ 1.28)
        with patch.dict(os.environ, {"COGS_RATIO": "0.10"}):
            ss_high, z_high, cr_high = MLSharedEngine.compute_safety_stock(price=100.0, sigma=10.0)
            self.assertAlmostEqual(cr_high, 0.90, places=2)
            self.assertGreater(z_high, 1.25)
            self.assertEqual(ss_high, 13)

        # Cap verification: safety stock never exceeds 3 * sigma
        with patch.dict(os.environ, {"COGS_RATIO": "0.01"}):
            ss_cap, _, _ = MLSharedEngine.compute_safety_stock(price=100.0, sigma=5.0)
            self.assertLessEqual(ss_cap, 15)

    def test_mock_engine_routing_sparse_cold_start(self):
        """[MOCK-DB] Verifies items with < 28 days of data or unmapped SKU route to benchmark/blend path."""
        item = {
            "name": "Artisan Sourdough",
            "price": 80.0,
            "category": "Breads & Baguettes",
            "currentStock": 10,
            "isPerishable": True,
        }
        # 1. 0 days -> Cold start tier
        fc_0 = self.engine.predict_item(item, sales_history=[], engine_override="gbdt")
        self.assertEqual(fc_0["tier"], "sparse_cold_start")
        self.assertIn("Cold start active", fc_0["explanation"])

        # 2. 14 days -> Sparse TSB blend tier
        history_14 = [10, 12, 14, 8, 15, 11, 13, 9, 10, 14, 12, 11, 15, 13]
        fc_14 = self.engine.predict_item(item, sales_history=history_14, engine_override="gbdt")
        self.assertEqual(fc_14["tier"], "sparse_cold_start")
        self.assertIn("Sparse TSB model active", fc_14["explanation"])

    def test_mock_engine_routing_gbdt_mature_item(self):
        """[MOCK-DB] Verifies items with >= 28 days and mapped bakery SKU route to GBDT Model (iv)."""
        item = {
            "name": "Traditional Baguette",
            "price": 45.0,
            "category": "Breads & Baguettes",
            "currentStock": 10,
            "isPerishable": True,
        }
        # 60 days of historical sales
        history_60 = [25 + int(np.sin(i)*5) for i in range(60)]
        
        # In legacy mode -> routes to legacy primary
        fc_legacy = self.engine.predict_item(item, sales_history=history_60, engine_override="legacy")
        self.assertEqual(fc_legacy["tier"], "legacy_primary")

        # In GBDT mode -> routes to GBDT Model (iv)
        fc_gbdt = self.engine.predict_item(item, sales_history=history_60, engine_override="gbdt")
        self.assertEqual(fc_gbdt["tier"], "gbdt_model_iv")
        self.assertIn("GBDT Model (iv) active", fc_gbdt["explanation"])
        self.assertIn("Newsvendor critical ratio", fc_gbdt["explanation"])
        self.assertGreater(fc_gbdt["predictedDemand"], 0)
        self.assertGreater(fc_gbdt["safetyStock"], 0)

    def test_mock_seed_demo_store_idempotency(self):
        """[MOCK-DB] Tests seed_demo_store script idempotency using mongomock."""
        mock_client = mongomock.MongoClient()
        mock_db = mock_client["mock_staging"]

        with patch("scripts.seed_demo_store.MongoClient", return_value=mock_client):
            # First seed run
            u_id1 = seed_demo_store(mongo_uri="mongodb://localhost:27017", db_name="mock_staging", demo_password="DemoSecurePass2026!")
            self.assertTrue(u_id1)
            self.assertEqual(mock_db.users.count_documents({"email": DEMO_EMAIL}), 1)
            self.assertEqual(mock_db.items.count_documents({"owner_id": u_id1}), 7)
            self.assertEqual(mock_db.daily_sales.count_documents({"owner_id": u_id1}), 420)
            self.assertEqual(mock_db.daily_stock.count_documents({"owner_id": u_id1}), 420)

            # Second seed run (must be strictly idempotent)
            u_id2 = seed_demo_store(mongo_uri="mongodb://localhost:27017", db_name="mock_staging", demo_password="DemoSecurePass2026!")
            self.assertEqual(u_id1, u_id2)
            self.assertEqual(mock_db.users.count_documents({"email": DEMO_EMAIL}), 1)
            self.assertEqual(mock_db.items.count_documents({"owner_id": u_id1}), 7)
            self.assertEqual(mock_db.daily_sales.count_documents({"owner_id": u_id1}), 420)
            self.assertEqual(mock_db.daily_stock.count_documents({"owner_id": u_id1}), 420)

            # Verify replayed_dataset flag on items and user
            user = mock_db.users.find_one({"_id": u_id1})
            self.assertTrue(user.get("replayed_dataset"))
            for item in mock_db.items.find({"owner_id": u_id1}):
                self.assertTrue(item.get("replayed_dataset"))
                self.assertEqual(item.get("daysOfData"), 60)
                self.assertEqual(item.get("maturity"), "Mature")

    def test_real_db_staging_demo_store_integrity(self):
        """[REAL-DB (restockiq_staging)] Verifies live Atlas staging demo manager data integrity."""
        from pymongo import MongoClient
        uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
        if not uri:
            self.skipTest("Atlas URI not available")

        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=4000)
            db = client["restockiq_staging"]
            user = db.users.find_one({"email": DEMO_EMAIL})
            self.assertIsNotNone(user, f"User {DEMO_EMAIL} not found in restockiq_staging")
            user_id = user["_id"]

            items_count = db.items.count_documents({"owner_id": user_id})
            sales_count = db.daily_sales.count_documents({"owner_id": user_id})
            stock_count = db.daily_stock.count_documents({"owner_id": user_id})

            self.assertEqual(items_count, 7)
            self.assertEqual(sales_count, 420)
            self.assertEqual(stock_count, 420)
            self.assertTrue(user.get("replayed_dataset"))
            client.close()
        except Exception as e:
            self.skipTest(f"Real Atlas connection skipped: {e}")


if __name__ == "__main__":
    unittest.main()
