"""
RestockIQ Adaptive Forecasting Engine (adaptive-v1)
==================================================
Deterministic, pure standard-library model tournament.
Selects the best forecasting candidate per store and item based on
rolling one-step-ahead backtesting on that specific authenticated user's
historical sales records.

Rules:
- Zero external dependencies (no pandas, numpy, or sklearn).
- Deterministic: identical inputs always yield identical outputs.
- No future peeking: strictly evaluates on data strictly prior to for_date.
- Never treats missing days as zero.
"""

from __future__ import annotations
import math
from datetime import date, datetime
from statistics import NormalDist
from typing import List, Tuple, Dict, Any, Optional

DEFAULT_COGS_RATIO = 0.40
DEFAULT_K_SHRINKAGE = 1  # Empirically chosen on Dev SKUs 1-17 (36.93% WAPE vs 66.02% for K=14)

METHOD_LABELS: Dict[str, str] = {
    "last": "Yesterday's sales",
    "ewma": "Smoothed recent sales",
    "ma7": "7-day average",
    "swd": "Same-weekday average",
    "blend": "Weekday + 7-day blend",
    "prior": "Category benchmark",
}

DEFAULT_CATEGORY_PRIORS: Dict[str, float] = {
    "Bakery": 24.0,
    "Breads & Baguettes": 24.0,
    "Viennoiserie": 22.0,
    "Beverage": 18.0,
    "Beverages": 18.0,
    "Beverages & Sweets": 18.0,
    "Food": 15.0,
    "Prepared Food": 15.0,
    "Dessert": 12.0,
    "Patisserie / Desserts": 12.0,
    "Snack": 10.0,
    "Snacks": 10.0,
    "Other": 10.0,
    "General Merchandise": 10.0,
}


def _predict_last(sub_history: List[Tuple[str, int]], target_dow: int) -> Optional[float]:
    """Candidate 1: Previous available day (y_{t-1})."""
    if not sub_history:
        return None
    return float(sub_history[-1][1])


def _predict_ewma(sub_history: List[Tuple[str, int]], target_dow: int, alpha: float = 0.5) -> Optional[float]:
    """Candidate 2: Exponentially Weighted Moving Average (alpha=0.5)."""
    if not sub_history:
        return None
    s = float(sub_history[0][1])
    for _, y in sub_history[1:]:
        s = alpha * float(y) + (1.0 - alpha) * s
    return s


def _predict_ma7(sub_history: List[Tuple[str, int]], target_dow: int) -> Optional[float]:
    """Candidate 3: Mean of up to 7 latest available days."""
    if not sub_history:
        return None
    window = [float(y) for _, y in sub_history[-7:]]
    return sum(window) / len(window)


def _predict_swd(sub_history: List[Tuple[str, int]], target_dow: int) -> Optional[float]:
    """Candidate 4: Mean of up to 4 latest same-weekday values (requires >= 2)."""
    matching = [
        float(y)
        for d_str, y in sub_history
        if date.fromisoformat(d_str).weekday() == target_dow
    ]
    if len(matching) < 2:
        return None
    window = matching[-4:]
    return sum(window) / len(window)


def _predict_blend(sub_history: List[Tuple[str, int]], target_dow: int) -> Optional[float]:
    """Candidate 5: Fixed 0.60 * same-weekday + 0.40 * ma7 blend (requires swd)."""
    swd_val = _predict_swd(sub_history, target_dow)
    if swd_val is None:
        return None
    ma7_val = _predict_ma7(sub_history, target_dow)
    if ma7_val is None:
        return None
    return 0.60 * swd_val + 0.40 * ma7_val


CANDIDATE_FNS = {
    "last": _predict_last,
    "ewma": _predict_ewma,
    "ma7": _predict_ma7,
    "swd": _predict_swd,
    "blend": _predict_blend,
}


def _resolve_prior(category: str, target_dow: int, prior_by_dow: Optional[Dict[str, Any]] = None) -> float:
    """Resolves prior demand, preferring median/mean by dow if provided, else category default."""
    if prior_by_dow:
        dow_key = str(target_dow)
        if dow_key in prior_by_dow:
            val = prior_by_dow[dow_key]
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, dict):
                # Prefer p50 (median), fallback to mean, p80, p90
                for k in ["p50", "median", "mean", "p80", "p90"]:
                    if k in val and isinstance(val[k], (int, float)):
                        return float(val[k])

    # Normalize category name
    clean_cat = (category or "").strip()
    return float(DEFAULT_CATEGORY_PRIORS.get(clean_cat, DEFAULT_CATEGORY_PRIORS.get("Other", 10.0)))


def forecast_item(
    history: List[Tuple[str, int]],
    for_date: str,
    category: str = "Bakery",
    price: float = 50.0,
    cogs_ratio: float = DEFAULT_COGS_RATIO,
    prior_by_dow: Optional[Dict[str, Any]] = None,
    k_shrinkage: int = DEFAULT_K_SHRINKAGE,
) -> Dict[str, Any]:
    """
    Computes an adaptive item forecast using time-ordered historical evaluation.

    Args:
        history: List of (date_str 'YYYY-MM-DD', units sold int) from completed closing counts.
                 Store-local calendar dates. Missing days must be absent, never zero.
        for_date: Target date to predict (YYYY-MM-DD). Only history < for_date is used.
        category: Item category for cold-start and shrinkage prior.
        price: Unit sale price.
        cogs_ratio: COGS / Price ratio (default 0.40).
        prior_by_dow: Optional DOW percentile dictionary {"0": {"mean": ..., "p90": ...}}.
        k_shrinkage: Shrinkage parameter K in w = n / (n + K) (default 3).

    Returns:
        dict adhering to the RestockIQ forecast schema with adaptive metadata.
    """
    target_dt = date.fromisoformat(for_date)
    target_dow = target_dt.weekday()

    # Strictly filter history to dates strictly before for_date, strictly non-negative units
    valid_history = [
        (d_str, int(u))
        for d_str, u in history
        if d_str < for_date and u is not None and u >= 0
    ]
    valid_history.sort(key=lambda x: x[0])
    n = len(valid_history)
    based_on_date = valid_history[-1][0] if n > 0 else None

    prior = _resolve_prior(category, target_dow, prior_by_dow)

    # -------------------------------------------------------------------------
    # Case 1: Cold start (n == 0)
    # -------------------------------------------------------------------------
    if n == 0:
        pred_demand = max(1, int(round(prior)))
        safety_stock = max(1, int(round(0.25 * pred_demand)))
        explanation = (
            f"Category benchmark active: 0 days of store history observed. "
            f"Initial forecast set to {category} benchmark ({pred_demand} units/day)."
        )
        return {
            "predictedDemand": pred_demand,
            "safetyStock": safety_stock,
            "method": "prior",
            "methodLabel": METHOD_LABELS["prior"],
            "methodMae": None,
            "baselineMae": None,
            "evalDays": 0,
            "historyDays": 0,
            "basedOnDate": None,
            "engine": "adaptive-v1",
            "explanation": explanation,
        }

    w = n / (n + k_shrinkage)

    # -------------------------------------------------------------------------
    # Case 2: Short history (1 <= n < 5)
    # -------------------------------------------------------------------------
    if n < 5:
        ewma_raw = _predict_ewma(valid_history, target_dow)
        blended = (w * ewma_raw) + ((1.0 - w) * prior)
        pred_demand = max(1, int(round(blended)))
        safety_stock = max(1, int(round(0.25 * pred_demand)))
        explanation = (
            f"Smoothed recent sales blended with category benchmark ({w:.0%} weight on {n} days of history; "
            f"recent pace {ewma_raw:.1f} vs benchmark {prior:.1f})."
        )
        return {
            "predictedDemand": pred_demand,
            "safetyStock": safety_stock,
            "method": "ewma",
            "methodLabel": METHOD_LABELS["ewma"],
            "methodMae": None,
            "baselineMae": None,
            "evalDays": 0,
            "historyDays": n,
            "basedOnDate": based_on_date,
            "engine": "adaptive-v1",
            "explanation": explanation,
        }

    # -------------------------------------------------------------------------
    # Case 3: Mature tournament backtesting (n >= 5)
    # -------------------------------------------------------------------------
    m = min(14, n - 3)
    eval_indices = list(range(n - m, n))

    # Evaluate availability for each day in the evaluation window
    swd_available_days = []
    for t in eval_indices:
        h_before = valid_history[:t]
        dow_t = date.fromisoformat(valid_history[t][0]).weekday()
        if _predict_swd(h_before, dow_t) is not None:
            swd_available_days.append(t)

    # Determine common evaluation days and candidate set
    if len(swd_available_days) >= 4:
        common_days = swd_available_days
        active_candidates = ["last", "ewma", "ma7", "swd", "blend"]
    else:
        common_days = eval_indices
        active_candidates = ["last", "ewma", "ma7"]

    # Compute predictions and MAE for each active candidate over the common days
    candidate_predictions: Dict[str, List[float]] = {c: [] for c in active_candidates}
    actuals: List[float] = [float(valid_history[t][1]) for t in common_days]

    for t in common_days:
        h_before = valid_history[:t]
        dow_t = date.fromisoformat(valid_history[t][0]).weekday()
        for c in active_candidates:
            pred_t = CANDIDATE_FNS[c](h_before, dow_t)
            candidate_predictions[c].append(float(pred_t))

    maes: Dict[str, float] = {}
    for c in active_candidates:
        errors = [abs(p - a) for p, a in zip(candidate_predictions[c], actuals)]
        maes[c] = sum(errors) / len(errors) if errors else 0.0

    # Winner selection: lowest MAE, but ma7 stays unless winner beats it by >= 5%
    ma7_mae = maes["ma7"]
    best_candidate = min(active_candidates, key=lambda c: (maes[c], c != "ma7"))
    best_mae = maes[best_candidate]

    if best_candidate == "ma7":
        winner = "ma7"
    else:
        # 5% margin rule: best must improve MAE by at least 5% over ma7
        improvement = (ma7_mae - best_mae) / ma7_mae if ma7_mae > 0 else 0.0
        if improvement >= 0.05:
            winner = best_candidate
        else:
            winner = "ma7"

    winner_mae = maes[winner]

    # Predict for for_date on the FULL history using the winning candidate
    winner_raw = CANDIDATE_FNS[winner](valid_history, target_dow)
    if winner_raw is None:
        winner = "ma7"
        winner_raw = _predict_ma7(valid_history, target_dow) or prior
        winner_mae = maes.get("ma7", 0.0)

    blended_raw = (w * winner_raw) + ((1.0 - w) * prior)
    pred_demand = max(1, int(round(blended_raw)))

    # Compute Winner RMSE over common evaluation days
    winner_preds = candidate_predictions[winner]
    sq_errors = [(p - a) ** 2 for p, a in zip(winner_preds, actuals)]
    rmse = math.sqrt(sum(sq_errors) / len(sq_errors)) if sq_errors else 1.0
    sigma = max(1.0, rmse)

    # Safety stock calculation via Newsvendor Critical Ratio
    if len(common_days) < 4:
        safety_stock = max(1, int(round(0.25 * pred_demand)))
    else:
        unit_price = float(price) if price and price > 0 else 50.0
        cogs = max(0.01, min(0.95, float(cogs_ratio)))
        cr = max(0.01, min(0.99, 1.0 - cogs))
        z = NormalDist().inv_cdf(cr)
        raw_safety = z * sigma
        safety_stock = max(1, int(round(raw_safety)))
        max_cap = max(1, int(round(3.0 * sigma)))
        safety_stock = min(safety_stock, max_cap)

    winner_label = METHOD_LABELS[winner]
    other_candidates = [c for c in active_candidates if c != winner]
    other_ref = "last" if "last" in other_candidates else (other_candidates[0] if other_candidates else "ma7")
    other_label = METHOD_LABELS.get(other_ref, other_ref)
    other_mae = maes.get(other_ref, winner_mae)

    explanation = (
        f"{winner_label} picked from {len(active_candidates)} methods using your last {len(common_days)} days "
        f"(avg miss {winner_mae:.1f} vs {other_mae:.1f} for {other_label.lower()}). "
        f"Based on {n} days of your sales."
    )

    return {
        "predictedDemand": pred_demand,
        "safetyStock": safety_stock,
        "method": winner,
        "methodLabel": winner_label,
        "methodMae": round(winner_mae, 2),
        "baselineMae": round(ma7_mae, 2),
        "evalDays": len(common_days),
        "historyDays": n,
        "basedOnDate": based_on_date,
        "engine": "adaptive-v1",
        "explanation": explanation,
    }
