import sys
import os
import re

# Add Backend root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm_service import generate_daily_briefing, answer_assistant_chat, get_llm_info


def test_zero_math_compliance(briefing_dict, input_items, input_alerts):
    """
    ZERO-MATH AUDIT: Checks that every numerical token appearing in the LLM's
    executive summary and actions was present in the input context (or is a
    benign list counter / percentage representation).
    """
    # Collect all numbers from input context
    input_text = str(input_items) + " " + str(input_alerts)
    input_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", input_text))

    # Collect numbers from LLM output
    llm_output = briefing_dict.get("executive_summary", "") + " " + " ".join(briefing_dict.get("actions", []))
    output_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", llm_output))

    # Allowed structural counters
    allowed_counters = {"1", "2", "3", "4", "5", "10", "15", "20", "30", "100"}

    # Check for hallucinated math
    unaccounted = []
    for num in output_numbers:
        if num not in input_numbers and num not in allowed_counters:
            # Check if it's an integer version of a float (e.g. 0.42 -> 42%)
            is_pct = any(float(inp) * 100 == float(num) for inp in input_numbers if float(inp) < 1.0)
            if not is_pct:
                unaccounted.append(num)

    print(f"  Input numbers tracked: {sorted(list(input_numbers))}")
    print(f"  Output numbers detected: {sorted(list(output_numbers))}")
    if unaccounted:
        print(f"  [WARN] Unaccounted numbers in output: {unaccounted}")
    else:
        print("  [OK] Zero-math audit passed: All output numbers trace to input metrics.")
    assert len(unaccounted) == 0, f"Zero-Math violation! Hallucinated numbers found: {unaccounted}"


def test_llm_integration():
    print("=" * 60)
    print("    RESTOCKIQ: GOOGLE GEMINI PRE-DEPLOYMENT TRUTH AUDIT")
    print("=" * 60)

    # 1. Truth-check model configuration
    info = get_llm_info()
    print(f"\n[1/3] LLM Configuration:")
    print(f"  Configured: {info['configured']}")
    print(f"  Provider:   {info['provider']}")
    print(f"  Model ID:   {info['model']}")
    assert info["configured"] is True, "FAIL: LLM is not configured! GEMINI_API_KEY must be set."
    assert info["provider"] == "google-gemini", f"FAIL: Expected google-genai provider, got {info['provider']}"

    # 2. Test Mock Items and Alerts
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

    print("\n[2/3] Testing Executive Daily Briefing Generation...")
    briefing = generate_daily_briefing(test_items, test_alerts)
    assert briefing is not None, "Briefing is None"
    assert briefing.get("source") == "gemini", f"FAIL: Briefing came from {briefing.get('source')} instead of gemini!"
    assert briefing.get("provider") == "google-gemini", f"FAIL: Provider is {briefing.get('provider')}"
    assert "executive_summary" in briefing, "Missing executive_summary"
    assert "actions" in briefing, "Missing actions list"
    assert len(briefing["actions"]) > 0, "Actions list is empty"

    print(f"  Source:   {briefing.get('source')}")
    print(f"  Provider: {briefing.get('provider')}")
    print(f"  Model:    {briefing.get('model')}")
    print(f"  Summary:  {briefing['executive_summary'][:120]}...")
    print(f"  Actions ({len(briefing['actions'])}):")
    for act in briefing["actions"]:
        print(f"    - {act}")

    # Run Zero-Math check
    print("\n  Auditing Zero-Math constraint compliance:")
    test_zero_math_compliance(briefing, test_items, test_alerts)

    print("\n[3/3] Testing Manager Assistant Chat Q&A...")
    query = "Why is Whole Milk flagged as critical today?"
    answer = answer_assistant_chat(query, test_items, test_alerts)
    assert answer is not None, "Answer is None"
    assert answer.get("source") == "gemini", f"FAIL: Assistant reply source is {answer.get('source')}!"
    assert "reply" in answer, "Missing reply"
    print(f"  Query:  '{query}'")
    print(f"  Source: {answer.get('source')}")
    print(f"  Reply:  {answer['reply']}")

    print("\n" + "=" * 60)
    print("  [SUCCESS] All Gemini LLM truth checkpoints passed!")
    print("=" * 60)

if __name__ == "__main__":
    test_llm_integration()
