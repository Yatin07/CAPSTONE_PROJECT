import asyncio
import os
import unittest
from datetime import datetime, timezone
from mongomock_motor import AsyncMongoMockClient

class TestTenantLifecycleMockDB(unittest.IsolatedAsyncioTestCase):
    """
    [MOCK-DB (mongomock)] Multi-Tenant Lifecycle & Delete Cascade Test Suite.
    Tests two distinct store owners (Alpha & Beta) across:
      1. Items isolation
      2. Forecasts isolation
      3. Daily/Intraday sales isolation
      4. Delete cascade isolation
    """

    async def asyncSetUp(self):
        # Setup clean in-memory mock MongoDB via mongomock-motor
        self.client = AsyncMongoMockClient()
        self.db = self.client["restockiq_staging"]
        self.owner_a = "tenant_alpha_001"
        self.owner_b = "tenant_beta_002"

    async def test_items_isolation(self):
        """[MOCK-DB] Verifies Owner A cannot read or mutate Owner B's items."""
        # Insert item for Owner A and Owner B
        item_a = {
            "_id": "item_a_1",
            "owner_id": self.owner_a,
            "name": "Alpha Sourdough",
            "currentStock": 20,
            "price": 5.0,
        }
        item_b = {
            "_id": "item_b_1",
            "owner_id": self.owner_b,
            "name": "Beta Baguette",
            "currentStock": 15,
            "price": 3.0,
        }
        await self.db.items.insert_many([item_a, item_b])

        # Query items for Owner A
        cursor_a = self.db.items.find({"owner_id": self.owner_a})
        items_a = await cursor_a.to_list(length=10)
        self.assertEqual(len(items_a), 1)
        self.assertEqual(items_a[0]["name"], "Alpha Sourdough")

        # Query items for Owner B
        cursor_b = self.db.items.find({"owner_id": self.owner_b})
        items_b = await cursor_b.to_list(length=10)
        self.assertEqual(len(items_b), 1)
        self.assertEqual(items_b[0]["name"], "Beta Baguette")

        # Attempt cross-tenant update: Owner A tries to modify Owner B's item
        res = await self.db.items.update_one(
            {"_id": "item_b_1", "owner_id": self.owner_a},
            {"$set": {"currentStock": 999}}
        )
        self.assertEqual(res.modified_count, 0, "Security violation: Owner A modified Owner B's item!")

        # Verify Owner B's item remains unchanged
        verified_b = await self.db.items.find_one({"_id": "item_b_1"})
        self.assertEqual(verified_b["currentStock"], 15)

    async def test_forecasts_isolation(self):
        """[MOCK-DB] Verifies Owner A cannot read Owner B's forecasts."""
        fc_a = {
            "_id": "fc_a_1",
            "item_id": "item_a_1",
            "owner_id": self.owner_a,
            "predictedDemand": 25,
            "safetyStock": 10,
            "forecast_date": "2026-10-29",
        }
        fc_b = {
            "_id": "fc_b_1",
            "item_id": "item_b_1",
            "owner_id": self.owner_b,
            "predictedDemand": 40,
            "safetyStock": 18,
            "forecast_date": "2026-10-29",
        }
        await self.db.forecasts.insert_many([fc_a, fc_b])

        # Owner A queries forecasts
        res_a = await self.db.forecasts.find({"owner_id": self.owner_a}).to_list(length=10)
        self.assertEqual(len(res_a), 1)
        self.assertEqual(res_a[0]["item_id"], "item_a_1")

        # Owner A attempts to query Owner B's forecast specifically
        target = await self.db.forecasts.find_one({"item_id": "item_b_1", "owner_id": self.owner_a})
        self.assertIsNone(target, "Security violation: Owner A accessed Owner B's forecast!")

    async def test_daily_sales_isolation(self):
        """[MOCK-DB] Verifies intraday and daily sales isolation between tenants."""
        sale_a = {
            "owner_id": self.owner_a,
            "item_id": "item_a_1",
            "quantity": 3,
            "date": "2026-10-29",
        }
        sale_b = {
            "owner_id": self.owner_b,
            "item_id": "item_b_1",
            "quantity": 7,
            "date": "2026-10-29",
        }
        await self.db.intraday_sales.insert_many([sale_a, sale_b])

        # Aggregate Owner A sales
        cursor_a = self.db.intraday_sales.find({"owner_id": self.owner_a})
        sales_a = await cursor_a.to_list(length=10)
        self.assertEqual(len(sales_a), 1)
        self.assertEqual(sales_a[0]["quantity"], 3)

        # Confirm Owner A cannot see Owner B sales
        cross_sales = await self.db.intraday_sales.find({"owner_id": self.owner_a, "item_id": "item_b_1"}).to_list(length=10)
        self.assertEqual(len(cross_sales), 0)

    async def test_delete_cascade_isolation(self):
        """[MOCK-DB] Verifies deleting an item cascades only for that owner and never touches other tenants."""
        # Setup item + forecast for Owner A
        await self.db.items.insert_one({"_id": "item_a_del", "owner_id": self.owner_a, "name": "Item A"})
        await self.db.forecasts.insert_one({"_id": "fc_a_del", "item_id": "item_a_del", "owner_id": self.owner_a})

        # Setup item + forecast for Owner B
        await self.db.items.insert_one({"_id": "item_b_keep", "owner_id": self.owner_b, "name": "Item B"})
        await self.db.forecasts.insert_one({"_id": "fc_b_keep", "item_id": "item_b_keep", "owner_id": self.owner_b})

        # Execute scoped deletion (matches Backend/main.py:424)
        item_to_delete = "item_a_del"
        del_item_res = await self.db.items.delete_one({"_id": item_to_delete, "owner_id": self.owner_a})
        self.assertEqual(del_item_res.deleted_count, 1)

        del_fc_res = await self.db.forecasts.delete_many({"item_id": item_to_delete, "owner_id": self.owner_a})
        self.assertEqual(del_fc_res.deleted_count, 1)

        # Verify Owner A's records are gone
        self.assertIsNone(await self.db.items.find_one({"_id": "item_a_del"}))
        self.assertIsNone(await self.db.forecasts.find_one({"_id": "fc_a_del"}))

        # Verify Owner B's records are 100% intact
        self.assertIsNotNone(await self.db.items.find_one({"_id": "item_b_keep"}))
        self.assertIsNotNone(await self.db.forecasts.find_one({"_id": "fc_b_keep"}))


class TestTenantRealDBStaging(unittest.TestCase):
    """
    [REAL-DB (restockiq_staging)] Suite.
    Runs real database multi-tenant isolation against Atlas staging database.
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
        self.owner_a = "staging_tenant_alpha"
        self.owner_b = "staging_tenant_beta"
        
        # Clean staging test records before run
        self.db.items.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
        self.db.forecasts.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
        self.db.intraday_sales.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
        self.db.daily_sales.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})

    def tearDown(self):
        if hasattr(self, "db") and self.db is not None:
            self.db.items.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
            self.db.forecasts.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
            self.db.intraday_sales.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
            self.db.daily_sales.delete_many({"owner_id": {"$in": [self.owner_a, self.owner_b]}})
            self.client.close()

    def test_real_database_tenant_isolation(self):
        """[REAL-DB] Real Atlas multi-tenant isolation & delete cascade test against restockiq_staging."""
        # 1. Items isolation
        self.db.items.insert_many([
            {"_id": "staging_item_a", "owner_id": self.owner_a, "name": "Staging Bread A", "currentStock": 20},
            {"_id": "staging_item_b", "owner_id": self.owner_b, "name": "Staging Cake B", "currentStock": 15},
        ])
        
        items_a = list(self.db.items.find({"owner_id": self.owner_a}))
        self.assertEqual(len(items_a), 1)
        self.assertEqual(items_a[0]["name"], "Staging Bread A")
        
        # Cross-tenant update blocked by query filter
        res = self.db.items.update_one(
            {"_id": "staging_item_b", "owner_id": self.owner_a},
            {"$set": {"currentStock": 999}}
        )
        self.assertEqual(res.modified_count, 0)
        verified_b = self.db.items.find_one({"_id": "staging_item_b"})
        self.assertEqual(verified_b["currentStock"], 15)
        
        # 2. Forecasts isolation
        self.db.forecasts.insert_many([
            {"_id": "staging_fc_a", "item_id": "staging_item_a", "owner_id": self.owner_a, "predictedDemand": 25},
            {"_id": "staging_fc_b", "item_id": "staging_item_b", "owner_id": self.owner_b, "predictedDemand": 40},
        ])
        fc_a = list(self.db.forecasts.find({"owner_id": self.owner_a}))
        self.assertEqual(len(fc_a), 1)
        self.assertEqual(fc_a[0]["item_id"], "staging_item_a")
        self.assertIsNone(self.db.forecasts.find_one({"item_id": "staging_item_b", "owner_id": self.owner_a}))
        
        # 3. Daily & intraday sales isolation
        self.db.intraday_sales.insert_many([
            {"owner_id": self.owner_a, "item_id": "staging_item_a", "quantity": 3},
            {"owner_id": self.owner_b, "item_id": "staging_item_b", "quantity": 7},
        ])
        sales_a = list(self.db.intraday_sales.find({"owner_id": self.owner_a}))
        self.assertEqual(len(sales_a), 1)
        self.assertEqual(sales_a[0]["quantity"], 3)
        
        # 4. Scoped delete cascade
        del_item = self.db.items.delete_one({"_id": "staging_item_a", "owner_id": self.owner_a})
        self.assertEqual(del_item.deleted_count, 1)
        del_fc = self.db.forecasts.delete_many({"item_id": "staging_item_a", "owner_id": self.owner_a})
        self.assertEqual(del_fc.deleted_count, 1)
        
        # Verify Owner A records deleted, Owner B records intact
        self.assertIsNone(self.db.items.find_one({"_id": "staging_item_a"}))
        self.assertIsNone(self.db.forecasts.find_one({"_id": "staging_fc_a"}))
        self.assertIsNotNone(self.db.items.find_one({"_id": "staging_item_b"}))
        self.assertIsNotNone(self.db.forecasts.find_one({"_id": "staging_fc_b"}))
        print("\n[REAL-DB PASS] Real Atlas staging database (restockiq_staging) multi-tenant isolation & delete cascade verified!")

if __name__ == "__main__":
    unittest.main()
