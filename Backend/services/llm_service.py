import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("restockiq.llm")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [LLM] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

# Initialize client safely if key exists
_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Initialized Google GenAI client with model: %s", GEMINI_MODEL)
    except Exception as e:
        logger.warning("Could not initialize google-genai Client: %s", e)


def is_llm_configured() -> bool:
    return bool(GEMINI_API_KEY and _client)


def get_llm_info() -> Dict[str, Any]:
    return {
        "configured": is_llm_configured(),
        "provider": "google-gemini" if is_llm_configured() else "deterministic-fallback",
        "model": GEMINI_MODEL if is_llm_configured() else "rule-based",
    }


def _call_gemini_with_retry(prompt: str, max_retries: int = 3, initial_delay: float = 1.0) -> Optional[str]:
    """
    Executes generate_content with exponential backoff on 429 rate limit or 5xx errors.
    If the primary model is unavailable, attempts a backup Flash model.
    """
    global _client
    if not _client:
        return None

    model_candidates = [GEMINI_MODEL, "gemini-3.1-flash-lite-preview", "gemini-3-flash-preview"]
    # Deduplicate while preserving order
    models_to_try = []
    for m in model_candidates:
        if m not in models_to_try:
            models_to_try.append(m)

    for active_model in models_to_try:
        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                response = _client.models.generate_content(
                    model=active_model,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text.strip()
                return None
            except Exception as e:
                err_str = str(e).lower()
                is_daily_limit = any(k in err_str for k in ["per day limit", "quota exceeded", "limit exceeded on free tier"])
                if is_daily_limit:
                    logger.warning("Gemini API daily quota limit reached: %s. Falling back to deterministic engine.", e)
                    return None
                is_retryable = any(k in err_str for k in ["429", "rate", "exhausted", "500", "502", "503", "504", "server error", "timeout"])
                logger.warning("Gemini API (model %s) attempt %d/%d failed: %s", active_model, attempt, max_retries, e)
                if attempt < max_retries and is_retryable:
                    time.sleep(delay)
                    delay *= 2.0
                else:
                    break
    return None


def _build_deterministic_fallback(items: List[Dict[str, Any]], alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback generator when LLM API is unreachable or not configured."""
    logger.info("Activating deterministic rule-based fallback for daily briefing.")
    restock_needed = [
        it for it in items
        if (it.get("currentStock") or 0) <= (it.get("safetyStock") or 0)
        or (it.get("currentStock") or 0) < (it.get("predictedDemand") or 0)
    ]
    urgent_alerts = [
        a for a in alerts
        if (a.get("severityLabel") or a.get("riskLevel") or "").lower() in ["high", "critical", "low pace"]
    ]

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
        alert_names = ", ".join([a.get("itemName") or a.get("name", "Item") for a in urgent_alerts[:2]])
        actions.append(f"Review waste alerts for {alert_names} to apply scheduled discount or combo bundle.")
    else:
        actions.append("Inventory levels stable with standard turnover pace.")

    return {
        "source": "fallback",
        "provider": "deterministic-fallback",
        "model": "rule-based",
        "executive_summary": summary,
        "actions": actions,
        "raw_text": f"### Daily Executive Brief\n\n{summary}\n\n**Key Actions Today:**\n" + "\n".join([f"- {a}" for a in actions]),
    }


def build_briefing_prompt(items: List[Dict[str, Any]], alerts: List[Dict[str, Any]]) -> str:
    from constants import DEFAULT_FALLBACK_DEMAND, DEFAULT_FALLBACK_SAFETY

    inventory_summary = []
    for it in items[:15]:
        curr = it.get("currentStock", 0)
        dem = it.get("predictedDemand") or DEFAULT_FALLBACK_DEMAND
        saf = it.get("safetyStock") or DEFAULT_FALLBACK_SAFETY
        restock = max(0, dem + saf - curr)
        tier = it.get("tier") or ("sparse_cold_start" if it.get("isNew") else "primary")
        inventory_summary.append({
            "name": it.get("name"),
            "category": it.get("category"),
            "current_stock": curr,
            "predicted_demand": dem,
            "safety_stock": saf,
            "recommended_restock": restock,
            "tier": tier,
            "price": it.get("price"),
            "risk_level": it.get("riskLevel"),
        })

    alerts_summary = []
    for a in alerts[:10]:
        pace = a.get("salesPaceRatio") if a.get("salesPaceRatio") is not None else a.get("sales_pace_ratio")
        partner_info = a.get("partnerItem")
        partner_desc = f"{partner_info['name']} (-{a.get('bundleDiscountPct', 20)}% combo)" if partner_info else None
        alerts_summary.append({
            "name": a.get("itemName") or a.get("name"),
            "tier": a.get("tier") or a.get("severityLabel") or a.get("riskLevel"),
            "sales_pace_ratio": pace,
            "current_stock": a.get("currentStock"),
            "recommended_action": a.get("recommended_action") or a.get("recommendedActionText") or a.get("recommendedAction"),
            "partner_combo": partner_desc,
        })

    return f"""
You are RestockIQ's Executive Inventory & Waste Mitigation AI Assistant.
Analyze this morning's store operational data and write a concise, professional executive briefing for the store manager.

STRICT INSTRUCTIONS:
1. ZERO-MATH: Do NOT invent, recalculate, or guess any numbers, prices, or confidence intervals. Use ONLY the figures provided below.
2. Structure your response into two distinct parts:
   - Part 1: "Executive Summary" (2-3 concise sentences on shift priorities, restock quantities, and operational health).
   - Part 2: "Action Checklist" (exactly 3 high-priority bullet points specifying item names, exact restock quantities, and recommended discount or combo bundle actions).
3. Waste Mitigation Actions: Recommended actions are promotional markdowns (10% discount) and combo bundle pairings (20% combo discount). Never suggest donations.
4. Tone: Direct, operational, professional, and clear.

CURRENT INVENTORY STATE:
{json.dumps(inventory_summary, indent=2)}

ACTIVE INTRADAY WASTE ALERTS:
{json.dumps(alerts_summary, indent=2)}
"""


def build_assistant_prompt(
    user_query: str,
    items: List[Dict[str, Any]],
    alerts: List[Dict[str, Any]],
) -> str:
    from constants import DEFAULT_FALLBACK_DEMAND, DEFAULT_FALLBACK_SAFETY

    inventory_context = []
    for it in items[:20]:
        curr = it.get("currentStock", 0)
        dem = it.get("predictedDemand") or DEFAULT_FALLBACK_DEMAND
        saf = it.get("safetyStock") or DEFAULT_FALLBACK_SAFETY
        restock = max(0, dem + saf - curr)
        tier = it.get("tier") or ("sparse_cold_start" if it.get("isNew") else "primary")
        inventory_context.append(
            f"- {it.get('name')}: Stock={curr}, Demand={dem}, Safety={saf}, Restock={restock}, Risk={it.get('riskLevel', 'normal')}, Tier={tier}"
        )

    alerts_context = []
    for a in alerts[:15]:
        a_name = a.get("itemName") or a.get("name")
        a_tier = a.get("tier") or a.get("severityLabel") or a.get("riskLevel")
        a_action = a.get("recommended_action") or a.get("recommendedActionText") or a.get("recommendedAction")
        a_pace = a.get("salesPaceRatio") if a.get("salesPaceRatio") is not None else a.get("sales_pace_ratio")
        partner_desc = f", Partner={a['partnerItem']['name']}" if a.get("partnerItem") else ""
        alerts_context.append(f"- Alert on {a_name}: Tier={a_tier}, Action={a_action}, Pace={a_pace}{partner_desc}")

    return f"""
You are the RestockIQ On-Duty Store Assistant.
Answer the store manager's question using the store's verified inventory data below.

RULES:
- Answer directly in 2 to 4 sentences.
- Use only facts from the store data. Never hallucinate items or metrics not listed.
- Waste mitigation actions are discounts and combo bundles (never donations).
- If the item or information is not present, clearly state that it is not in today's active catalog.

STORE INVENTORY:
{chr(10).join(inventory_context)}

WASTE ALERTS:
{chr(10).join(alerts_context)}

STORE MANAGER'S QUESTION:
{user_query}
"""


def generate_daily_briefing(items: List[Dict[str, Any]], alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a natural-language executive briefing for the store manager.
    ZERO-MATH CONSTRAINT: The LLM narrates and prioritizes verified data only.
    It does NOT hallucinate confidence intervals or compute new forecasts.
    """
    global _client
    if not _client:
        return _build_deterministic_fallback(items, alerts)

    prompt = build_briefing_prompt(items, alerts)
    text = _call_gemini_with_retry(prompt)
    if not text:
        logger.warning("Gemini generation failed or timed out; falling back to deterministic engine.")
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
            "Inspect high-risk waste alerts for intraday markdown or combo bundle.",
            "Confirm morning delivery arrivals."
        ]

    return {
        "source": "gemini",
        "provider": "google-gemini",
        "model": GEMINI_MODEL,
        "executive_summary": exec_summary,
        "actions": action_lines[:4],
        "raw_text": text,
    }


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
        logger.info("Assistant chat running in fallback mode.")
        return {
            "reply": "RestockIQ AI Assistant is currently running in local fallback mode. Please configure GEMINI_API_KEY.",
            "source": "fallback",
            "provider": "deterministic-fallback",
            "model": "rule-based",
        }

    prompt = build_assistant_prompt(user_query, items, alerts)

    text = _call_gemini_with_retry(prompt)
    if not text:
        logger.warning("Gemini assistant chat call failed; returning fallback message.")
        return {
            "reply": "Sorry, the AI assistant is currently experiencing high load or connection delay. Please try again shortly.",
            "source": "fallback",
            "provider": "fallback",
            "model": GEMINI_MODEL,
        }

    return {
        "reply": text,
        "source": "gemini",
        "provider": "google-gemini",
        "model": GEMINI_MODEL,
    }
