import sys
import os

# Add Backend root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm_service import generate_daily_briefing, answer_assistant_chat

def test_llm_integration():
    print("=" * 60)
    print("    RESTOCKIQ: GOOGLE GEMINI LLM INTEGRATION TEST")
    print("=" * 60)

    # 1. Test Mock Items and Alerts
    test_items = [
        {
            "name": "Traditional Baguette",
            "category": "Bakery",
            "currentStock": 8,
            "predictedDemand": 39,
            "safetyStock": 15,
            "price": 2.80,
            "riskLevel": "high",
        },
        {
            "name": "Whole Milk",
            "category": "Dairy",
            "currentStock": 4,
            "predictedDemand": 42,
            "safetyStock": 19,
            "price": 4.50,
            "riskLevel": "critical",
        },
    ]

    test_alerts = [
        {
            "name": "Traditional Baguette",
            "riskLevel": "high",
            "sales_pace_ratio": 0.42,
            "currentStock": 8,
            "recommendedAction": "Suggest 20% Discount",
        },
        {
            "name": "Whole Milk",
            "riskLevel": "critical",
            "sales_pace_ratio": 0.28,
            "currentStock": 4,
            "recommendedAction": "Flag for Donation",
        },
    ]

    print("\n[1/2] Testing Executive Daily Briefing Generation...")
    briefing = generate_daily_briefing(test_items, test_alerts)
    assert briefing is not None, "Briefing is None"
    assert "executive_summary" in briefing, "Missing executive_summary"
    assert "actions" in briefing, "Missing actions list"
    assert len(briefing["actions"]) > 0, "Actions list is empty"
    print(f"  Provider: {briefing.get('provider')}")
    print(f"  Model: {briefing.get('model')}")
    print(f"  Summary: {briefing['executive_summary'][:120]}...")
    print(f"  Actions ({len(briefing['actions'])}):")
    for act in briefing["actions"]:
        print(f"    - {act}")

    print("\n[2/2] Testing Manager Assistant Chat Q&A...")
    query = "Why is Whole Milk flagged as critical today?"
    answer = answer_assistant_chat(query, test_items, test_alerts)
    assert answer is not None, "Answer is None"
    assert "reply" in answer, "Missing reply"
    print(f"  Query: '{query}'")
    print(f"  Reply: {answer['reply']}")

    print("\n" + "=" * 60)
    print("  [SUCCESS] All Gemini LLM checkpoints passed!")
    print("=" * 60)

if __name__ == "__main__":
    test_llm_integration()
