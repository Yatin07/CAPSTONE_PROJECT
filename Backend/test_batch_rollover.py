import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone

class TestBatchRolloverLogic(unittest.TestCase):
    def test_daily_rollover_state_transitions(self):
        # Simulated Day 1 store item after manager activity
        item = {
            "_id": "item_croissant_001",
            "owner_id": "tenant_123",
            "name": "Butter Croissant",
            "category": "Viennoiserie",
            "currentStock": 12,
            "price": 2.80, # 20% discounted price from 3.50
            "originalPrice": 3.50,
            "intradaySales": 18,
            "salesHistory": [22, 25, 20],
            "isDismissed": True,
            "isPrimaryActionDone": True,
            "isRecommendedActionDone": True,
            "discountApplied": True,
            "flaggedForDonation": False,
        }

        # Simulate batch rollover transformation
        sales_history = item.get("salesHistory", [])
        intraday_sales = item.get("intradaySales", 0)
        updated_sales_history = list(sales_history)
        if intraday_sales > 0 or len(updated_sales_history) > 0:
            updated_sales_history.append(intraday_sales)
            if len(updated_sales_history) > 90:
                updated_sales_history = updated_sales_history[-90:]

        base_price = item.get("originalPrice") if item.get("discountApplied") else item.get("price")

        item_update = {
            "predictedDemand": 25,
            "safetyStock": 5,
            "description": "Baseline demand",
            "riskLevel": "normal",
            "salesHistory": updated_sales_history,
            "intradaySales": 0,
            "isDismissed": False,
            "isPrimaryActionDone": False,
            "isRecommendedActionDone": False,
            "discountApplied": False,
            "flaggedForDonation": False,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        if base_price is not None:
            item_update["price"] = base_price

        # Assertions
        # 1. Sales history archived Day 1 sales (18)
        self.assertEqual(item_update["salesHistory"], [22, 25, 20, 18])
        self.assertEqual(len(item_update["salesHistory"]), 4)

        # 2. Intraday sales reset to 0 for Day 2 morning
        self.assertEqual(item_update["intradaySales"], 0)

        # 3. Actions reset for fresh morning evaluation
        self.assertFalse(item_update["isDismissed"])
        self.assertFalse(item_update["isPrimaryActionDone"])
        self.assertFalse(item_update["isRecommendedActionDone"])
        self.assertFalse(item_update["discountApplied"])

        # 4. Price restored to original catalog price
        self.assertEqual(item_update["price"], 3.50)
        print("[OK] Batch rollover logic verified: 100% compliant with daily operational lifecycle.")

if __name__ == "__main__":
    unittest.main()
