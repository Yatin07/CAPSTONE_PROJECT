import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Initialize client safely if key exists
_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[LLM] Warning: Could not initialize google-genai Client: {e}")


def _build_deterministic_fallback(items: List[Dict[str, Any]], alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback generator when LLM API is unreachable or not configured."""
    restock_needed = [
        it for it in items
        if it.get("currentStock", 0) <= it.get("safetyStock", 0)
        or it.get("currentStock", 0) < it.get("predictedDemand", 0)
    ]
    urgent_alerts = [a for a in alerts if a.get("riskLevel") in ["high", "critical"]]

    summary = (
        f"Operational status: {len(items)} items tracked. "
        f"{len(restock_needed)} items require restocking attention today, and "
        f"{len(urgent_alerts)} waste mitigation alerts are currently active."
    )

    actions = []
    if restock_needed:
        names = ", ".join([it.get("name", "Item") for it in restock_needed[:3]])
        actions.append(f"Restock priority items: {names}.")
    if urgent_alerts:
        alert_names = ", ".join([a.get("name", "Item") for a in urgent_alerts[:2]])
        actions.append(f"Review waste alerts for {alert_names} to apply scheduled discount or donation.")
    else:
        actions.append("Inventory levels stable with standard turnover pace.")

    return {
        "provider": "deterministic-fallback",
        "model": "rule-based",
        "executive_summary": summary,
        "actions": actions,
        "raw_text": f"### Daily Executive Brief\n\n{summary}\n\n**Key Actions Today:**\n" + "\n".join([f"- {a}" for a in actions]),
    }


def generate_daily_briefing(items: List[Dict[str, Any]], alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a natural-language executive briefing for the store manager.
    ZERO-MATH CONSTRAINT: The LLM narrates and prioritizes verified data only.
    It does NOT hallucinate confidence intervals or compute new forecasts.
    """
    global _client
    if not _client:
        return _build_deterministic_fallback(items, alerts)

    # Compile sanitized metrics for LLM grounding
    inventory_summary = []
    for it in items[:15]:
        inventory_summary.append({
            "name": it.get("name"),
            "category": it.get("category"),
            "current_stock": it.get("currentStock"),
            "predicted_demand": it.get("predictedDemand"),
            "safety_stock": it.get("safetyStock"),
            "price": it.get("price"),
            "risk_level": it.get("riskLevel"),
        })

    alerts_summary = []
    for a in alerts[:10]:
        alerts_summary.append({
            "name": a.get("name"),
            "risk_level": a.get("riskLevel"),
            "sales_pace_ratio": a.get("sales_pace_ratio"),
            "current_stock": a.get("currentStock"),
            "recommended_action": a.get("recommendedAction"),
        })

    prompt = f"""
You are RestockIQ's Executive Inventory & Waste Mitigation AI Assistant.
Analyze this morning's store operational data and write a concise, professional executive briefing for the store manager.

STRICT INSTRUCTIONS:
1. ZERO-MATH: Do NOT invent, recalculate, or guess any numbers, prices, or confidence intervals. Use ONLY the figures provided below.
2. Structure your response into two distinct parts:
   - Part 1: "Executive Summary" (2-3 concise sentences on shift priorities and operational health).
   - Part 2: "Action Checklist" (exactly 3 high-priority bullet points specifying item names and recommended actions).
3. Tone: Direct, operational, professional, and clear.

CURRENT INVENTORY STATE:
{json.dumps(inventory_summary, indent=2)}

ACTIVE INTRADAY WASTE ALERTS:
{json.dumps(alerts_summary, indent=2)}
"""

    try:
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        text = response.text.strip() if response and response.text else ""
        if not text:
            return _build_deterministic_fallback(items, alerts)

        # Parse sections cleanly
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        summary_lines = []
        action_lines = []
        collecting_actions = False

        for line in lines:
            if "action" in line.lower() or "checklist" in line.lower():
                collecting_actions = True
                continue
            if collecting_actions:
                if line.startswith(("-", "*", "1.", "2.", "3.")):
                    cleaned = line.lstrip("-*0123456789. ")
                    action_lines.append(cleaned)
            else:
                if not line.startswith("#"):
                    summary_lines.append(line)

        exec_summary = " ".join(summary_lines[:3]) if summary_lines else text[:250]
        if not action_lines:
            action_lines = [
                "Review items below safety stock threshold.",
                "Inspect high-risk waste alerts for intraday markdown.",
                "Confirm morning delivery arrivals."
            ]

        return {
            "provider": "google-gemini",
            "model": GEMINI_MODEL,
            "executive_summary": exec_summary,
            "actions": action_lines[:4],
            "raw_text": text,
        }

    except Exception as e:
        print(f"[LLM] Error calling Gemini: {e}")
        return _build_deterministic_fallback(items, alerts)


def answer_assistant_chat(
    user_query: str,
    items: List[Dict[str, Any]],
    alerts: List[Dict[str, Any]],
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    RAG-grounded store manager assistant Q&A.
    """
    global _client
    if not _client:
        return {
            "reply": "RestockIQ AI Assistant is currently running in local fallback mode. Please ensure GEMINI_API_KEY is configured.",
            "provider": "fallback"
        }

    inventory_context = [
        f"- {it.get('name')}: Stock={it.get('currentStock')}, Demand={it.get('predictedDemand')}, Safety={it.get('safetyStock')}, Risk={it.get('riskLevel')}"
        for it in items[:20]
    ]

    alerts_context = [
        f"- Alert on {a.get('name')}: Risk={a.get('riskLevel')}, Action={a.get('recommendedAction')}, Pace={a.get('sales_pace_ratio')}"
        for a in alerts[:15]
    ]

    prompt = f"""
You are the RestockIQ On-Duty Store Assistant.
Answer the store manager's question using the store's verified inventory data below.

RULES:
- Answer directly in 2 to 4 sentences.
- Use only facts from the store data. Never hallucinate items or metrics not listed.
- If the item or information is not present, clearly state that it is not in today's active catalog.

STORE INVENTORY:
{chr(10).join(inventory_context)}

WASTE ALERTS:
{chr(10).join(alerts_context)}

STORE MANAGER'S QUESTION:
{user_query}
"""

    try:
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return {
            "reply": response.text.strip(),
            "provider": "google-gemini",
            "model": GEMINI_MODEL,
        }
    except Exception as e:
        return {
            "reply": f"Sorry, could not process query with AI assistant: {str(e)}",
            "provider": "error"
        }
