"""
Offline Adaptive Tournament Simulation Benchmark
================================================
Compares:
  (A) Current production code path (ML/engine.py:predict_item for real stores:
      prior on day 0, TSB credibility shrinkage W=n/(n+14) for 1-27, 4-week weekday + roll7 for 28+)
  (B) Yesterday baseline (last)
  (C) 7-day moving average (ma7)
  (D) Same-weekday 4-week average (swd)
  (E) Adaptive model tournament (Backend/adaptive_forecast.py)

Dev split (SKUs 1-17) selects K in {1, 3, 5, 14}.
Holdout test split (SKUs 18-35) reports final evaluation.
Priors for current code path are computed strictly CUTOFF-SAFE (using only data < target date).
"""

from __future__ import annotations
import os
import sys
import json
import math
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
import numpy as np

# Add Backend to path to import adaptive_forecast
BACKEND_DIR = Path(__file__).resolve().parent.parent / "Backend"
sys.path.insert(0, str(BACKEND_DIR))
from adaptive_forecast import forecast_item

DATA_PATH = Path(__file__).resolve().parent / "data" / "processed" / "primary_items.csv"
SPARSE_DATA_PATH = Path(__file__).resolve().parent / "data" / "processed" / "sparse_items.csv"
SPARSE_CATS_PATH = Path(__file__).resolve().parent / "data" / "processed" / "sparse_categories.json"


def tsb_forecast_py(series: list[float], alpha: float = 0.2, beta: float = 0.2) -> float:
    n = len(series)
    non_zero = [x for x in series if x > 0]
    if not non_zero:
        return 0.0
    z = non_zero[0]
    p = len(non_zero) / n
    for t in range(1, n):
        if series[t] > 0:
            z = alpha * series[t] + (1 - alpha) * z
            p = beta * 1.0 + (1 - beta) * p
        else:
            p = beta * 0.0 + (1 - beta) * p
    return float(p * z)


def predict_current_code_path(history: list[tuple[str, int]], target_dow: int, p90_prior: float) -> int:
    """Exact reproduction of ML/engine.py:predict_item for real stores."""
    n = len(history)
    if n == 0:
        return 24

    if n < 28:
        # Credibility shrinkage W = n / (n + 14)
        W = n / (n + 14.0)
        vals = [float(y) for _, y in history]
        tsb_val = tsb_forecast_py(vals)
        blended = (W * tsb_val) + ((1.0 - W) * p90_prior)
        return max(1, int(round(blended)))
    else:
        # Own-data blend: 0.60 * weekday4w + 0.40 * roll_7
        vals = [float(y) for _, y in history]
        w4_vals = [history[-7 * k][1] for k in [1, 2, 3, 4] if len(history) >= 7 * k]
        weekday4w = float(np.mean(w4_vals)) if w4_vals else float(np.mean(vals[-7:]))
        roll_7 = float(np.mean(vals[-7:]))
        return max(1, int(round(0.60 * weekday4w + 0.40 * roll_7)))


def compute_cutoff_safe_priors(sparse_csv: Path, cats_json: Path, target_dates: list) -> dict:
    """Computes category DOW p90 priors strictly using sparse observations preceding each target date (ds < T)."""
    df_sparse = pd.read_csv(sparse_csv)
    df_sparse["ds"] = pd.to_datetime(df_sparse["ds"])
    df_sparse["dow"] = df_sparse["ds"].dt.dayofweek

    with open(cats_json, "r", encoding="utf-8") as f:
        categories = json.load(f)
    item_to_category = {item: cat for cat, items in categories.items() for item in items}
    df_sparse["category"] = df_sparse["article"].map(item_to_category)
    bread_df = df_sparse[df_sparse["category"] == "Breads & Baguettes"].sort_values("ds")

    priors_by_date = {}
    for d in sorted(set(target_dates)):
        sub = bread_df[bread_df["ds"] < d]
        if len(sub) > 0:
            priors_by_date[pd.to_datetime(d).strftime("%Y-%m-%d")] = sub.groupby("dow")["y"].quantile(0.90).to_dict()
        else:
            priors_by_date[pd.to_datetime(d).strftime("%Y-%m-%d")] = {}
    return priors_by_date


def run_simulation():
    print("=" * 70)
    print("   RESTOCKIQ: OFFLINE ADAPTIVE TOURNAMENT SIMULATION (CUTOFF-SAFE)")
    print("=" * 70)

    df = pd.read_csv(DATA_PATH)
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["article", "ds"]).reset_index(drop=True)

    articles = sorted(df["article"].unique())
    dev_articles = articles[:17]
    test_articles = articles[17:]

    print(f"Total SKUs: {len(articles)}")
    print(f"Dev SKUs (1-17): {dev_articles[:3]} ... {dev_articles[-1]}")
    print(f"Test SKUs (18-35): {test_articles[:3]} ... {test_articles[-1]}")

    # Collect all evaluation target dates to precompute cutoff-safe priors
    all_target_dates = []
    for art in articles:
        art_df = df[df["article"] == art].reset_index(drop=True)
        for start_idx in [0, 60, 90, 120]:
            sub_df = art_df.iloc[start_idx : start_idx + 61].reset_index(drop=True)
            if len(sub_df) >= 61:
                all_target_dates.extend(sub_df["ds"].tolist())

    print("\nComputing cutoff-safe category priors (strictly ds < target_date)...")
    cutoff_priors_by_date = compute_cutoff_safe_priors(SPARSE_DATA_PATH, SPARSE_CATS_PATH, all_target_dates)
    print(f"Precomputed cutoff-safe priors for {len(cutoff_priors_by_date)} unique dates.")

    # Step 1: Tune K in {1, 3, 5, 14} on Dev split
    print("\n--- Step 1: Tuning K in {1, 3, 5, 14} on Dev Split (SKUs 1-17) ---")
    k_candidates = [1, 3, 5, 14]
    k_wapes = {}

    for k_val in k_candidates:
        sum_abs_err = 0.0
        sum_actual = 0.0

        for art in dev_articles:
            art_df = df[df["article"] == art].reset_index(drop=True)
            for start_idx in [0, 90]:
                sub_df = art_df.iloc[start_idx : start_idx + 61].reset_index(drop=True)
                if len(sub_df) < 61:
                    continue

                for h_len in range(1, 61):
                    hist = [
                        (sub_df.iloc[i]["ds"].strftime("%Y-%m-%d"), int(sub_df.iloc[i]["y"]))
                        for i in range(h_len)
                    ]
                    target_row = sub_df.iloc[h_len]
                    target_date = target_row["ds"].strftime("%Y-%m-%d")
                    actual = float(target_row["y"])

                    res = forecast_item(
                        history=hist,
                        for_date=target_date,
                        category="Bakery",
                        k_shrinkage=k_val,
                    )
                    pred = float(res["predictedDemand"])
                    sum_abs_err += abs(pred - actual)
                    sum_actual += actual

        wape = (sum_abs_err / sum_actual) * 100.0 if sum_actual > 0 else 999.0
        k_wapes[k_val] = wape
        print(f"  K = {k_val:2d} -> Dev WAPE: {wape:.2f}%")

    best_k = min(k_wapes, key=k_wapes.get)
    print(f"\n=> Optimal K chosen on Dev split: K = {best_k} (WAPE: {k_wapes[best_k]:.2f}%)")

    # Step 2: Full Evaluation on Test Split (SKUs 18-35)
    print(f"\n--- Step 2: Evaluation on Test Split (SKUs 18-35) with K={best_k} ---")
    
    buckets = {
        "1-6": (1, 6),
        "7-13": (7, 13),
        "14-27": (14, 27),
        "28-60": (28, 60),
    }

    metrics = {
        "CURRENT": {b: {"err": 0.0, "actual": 0.0} for b in list(buckets.keys()) + ["Overall"]},
        "YESTERDAY": {b: {"err": 0.0, "actual": 0.0} for b in list(buckets.keys()) + ["Overall"]},
        "MA7": {b: {"err": 0.0, "actual": 0.0} for b in list(buckets.keys()) + ["Overall"]},
        "SWD": {b: {"err": 0.0, "actual": 0.0} for b in list(buckets.keys()) + ["Overall"]},
        "ADAPTIVE": {b: {"err": 0.0, "actual": 0.0} for b in list(buckets.keys()) + ["Overall"]},
    }

    # Tracking day-to-day absolute changes across n=27 -> 28
    day_diffs_current = []
    day_diffs_adaptive = []

    for art in test_articles:
        art_df = df[df["article"] == art].reset_index(drop=True)
        for start_idx in [0, 60, 120]:
            sub_df = art_df.iloc[start_idx : start_idx + 61].reset_index(drop=True)
            if len(sub_df) < 61:
                continue

            prev_pred_curr = None
            prev_pred_adapt = None

            for h_len in range(1, 61):
                hist = [
                    (sub_df.iloc[i]["ds"].strftime("%Y-%m-%d"), int(sub_df.iloc[i]["y"]))
                    for i in range(h_len)
                ]
                target_row = sub_df.iloc[h_len]
                target_date = target_row["ds"].strftime("%Y-%m-%d")
                target_dow = target_row["ds"].weekday()
                actual = float(target_row["y"])

                # Cutoff-safe p90 prior strictly preceding target_date
                date_priors = cutoff_priors_by_date.get(target_date, {})
                p90_prior = float(date_priors.get(target_dow, 2.0))

                # (A) CURRENT
                pred_curr = float(predict_current_code_path(hist, target_dow, p90_prior))

                # (B) YESTERDAY ONLY
                pred_yest = float(hist[-1][1])

                # (C) MA7
                last_7 = [y for _, y in hist[-7:]]
                pred_ma7 = float(sum(last_7) / len(last_7))

                # (D) SWD (mean of up to 4 same-weekday)
                matching = [y for d_str, y in hist if date.fromisoformat(d_str).weekday() == target_dow]
                pred_swd = float(sum(matching[-4:]) / len(matching[-4:])) if matching else pred_ma7

                # (E) ADAPTIVE
                res_adapt = forecast_item(
                    history=hist,
                    for_date=target_date,
                    category="Bakery",
                    k_shrinkage=best_k,
                )
                pred_adapt = float(res_adapt["predictedDemand"])

                # Track transition cliff between n=27 and n=28
                if h_len == 27:
                    prev_pred_curr = pred_curr
                    prev_pred_adapt = pred_adapt
                elif h_len == 28 and prev_pred_curr is not None:
                    day_diffs_current.append(abs(pred_curr - prev_pred_curr))
                    day_diffs_adaptive.append(abs(pred_adapt - prev_pred_adapt))

                # Classify into bucket
                target_bucket = None
                for b_name, (b_low, b_high) in buckets.items():
                    if b_low <= h_len <= b_high:
                        target_bucket = b_name
                        break

                methods = {
                    "CURRENT": pred_curr,
                    "YESTERDAY": pred_yest,
                    "MA7": pred_ma7,
                    "SWD": pred_swd,
                    "ADAPTIVE": pred_adapt,
                }

                for m_name, pred_val in methods.items():
                    err = abs(pred_val - actual)
                    metrics[m_name]["Overall"]["err"] += err
                    metrics[m_name]["Overall"]["actual"] += actual
                    if target_bucket:
                        metrics[m_name][target_bucket]["err"] += err
                        metrics[m_name][target_bucket]["actual"] += actual

    # Compile Results Table
    print("\n" + "=" * 70)
    print("POOLED WAPE (%) BY HISTORY BUCKET (TEST SET: SKUs 18-35)")
    print("=" * 70)
    print(f"{'Method':<12} | {'1-6d':<8} | {'7-13d':<8} | {'14-27d':<8} | {'28-60d':<8} | {'Overall':<8}")
    print("-" * 65)

    wape_table = {}
    for m in ["CURRENT", "YESTERDAY", "MA7", "SWD", "ADAPTIVE"]:
        wape_table[m] = {}
        for b in ["1-6", "7-13", "14-27", "28-60", "Overall"]:
            err = metrics[m][b]["err"]
            act = metrics[m][b]["actual"]
            w = (err / act * 100.0) if act > 0 else 0.0
            wape_table[m][b] = w

    for m in ["CURRENT", "YESTERDAY", "MA7", "SWD", "ADAPTIVE"]:
        print(
            f"{m:<12} | {wape_table[m]['1-6']:6.2f}% | {wape_table[m]['7-13']:6.2f}% | "
            f"{wape_table[m]['14-27']:6.2f}% | {wape_table[m]['28-60']:6.2f}% | {wape_table[m]['Overall']:6.2f}%"
        )
    print("-" * 65)

    # Day 28 Cliff Analysis
    mean_cliff_curr = np.mean(day_diffs_current) if day_diffs_current else 0.0
    mean_cliff_adapt = np.mean(day_diffs_adaptive) if day_diffs_adaptive else 0.0

    print(f"\n--- Boundary Transition Analysis (n=27 -> n=28) ---")
    print(f"  Current Code Path Mean Jump : {mean_cliff_curr:.2f} units")
    print(f"  Adaptive Engine Mean Jump    : {mean_cliff_adapt:.2f} units")
    cliff_reduction = (mean_cliff_curr - mean_cliff_adapt) / mean_cliff_curr * 100.0 if mean_cliff_curr > 0 else 0.0
    print(f"  Jump Reduction              : {cliff_reduction:.1f}% smoother")

    # Gate Verification
    print("\n--- GATES VERIFICATION ---")
    gates_passed = True
    for b_name in list(buckets.keys()) + ["Overall"]:
        curr_w = wape_table["CURRENT"][b_name]
        adapt_w = wape_table["ADAPTIVE"][b_name]
        diff_pp = adapt_w - curr_w
        # Gate: adaptive <= current (never worse than 1 pp)
        passed = diff_pp <= 1.0
        status = "PASS" if passed else "FAIL"
        if not passed:
            gates_passed = False
        print(f"  Gate [{b_name:<7}]: Adaptive {adapt_w:.2f}% vs Current {curr_w:.2f}% (diff {diff_pp:+.2f} pp) -> {status}")

    overall_better = wape_table["ADAPTIVE"]["Overall"] < wape_table["CURRENT"]["Overall"]
    print(f"  Gate [Overall Better] : {'PASS' if overall_better else 'FAIL'}")
    if not overall_better:
        gates_passed = False

    cliff_passed = mean_cliff_adapt <= mean_cliff_curr
    print(f"  Gate [No Day-28 Cliff]: {'PASS' if cliff_passed else 'FAIL'}")
    if not cliff_passed:
        gates_passed = False

    print("\nOVERALL GATES RESULT: " + ("ALL GATES PASSED! SUCCESS" if gates_passed else "GATE FAILED!"))
    return wape_table, best_k, mean_cliff_curr, mean_cliff_adapt, gates_passed


if __name__ == "__main__":
    run_simulation()
