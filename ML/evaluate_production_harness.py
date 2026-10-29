"""
Production Code Path Verification Harness for RestockIQ ML Engine
Evaluates:
1. 38-fold weekly rolling-origin backtest against research benchmark (24.92%).
2. 6-fold temporal backtest.
3. 3-run runtime and peak memory benchmark on MongoDB staging database.
"""

import os
import sys
import time
import tracemalloc
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

# Add repo paths
root_dir = Path(__file__).resolve().parent.parent
ml_dir = root_dir / "ML"
backend_dir = root_dir / "Backend"
sys.path.insert(0, str(ml_dir))
sys.path.insert(0, str(backend_dir))

from engine import MLSharedEngine, FEATS_MODEL_IV, LAG_FEATS_1D, CAL_ENHANCED_FEATS

PRIMARY_CSV = ml_dir / "data" / "processed" / "primary_items.csv"
PARQUET_38 = root_dir / "scratch" / "predictions_38folds_with_controls.parquet"

FOLDS_6 = [
    {"fold": 1, "name": "Early Summer Ramp", "cutoff": "2022-07-15", "start": "2022-07-16", "end": "2022-07-22"},
    {"fold": 2, "name": "Mid-Summer Peak",   "cutoff": "2022-07-29", "start": "2022-07-30", "end": "2022-08-05"},
    {"fold": 3, "name": "August Holiday",   "cutoff": "2022-08-12", "start": "2022-08-13", "end": "2022-08-19"},
    {"fold": 4, "name": "Late Summer Turn", "cutoff": "2022-08-26", "start": "2022-08-27", "end": "2022-09-02"},
    {"fold": 5, "name": "Autumn Normal",    "cutoff": "2022-09-09", "start": "2022-09-10", "end": "2022-09-16"},
    {"fold": 6, "name": "Late September",   "cutoff": "2022-09-23", "start": "2022-09-24", "end": "2022-09-30"},
]


def load_raw_dataset_with_features():
    df = pd.read_csv(PRIMARY_CSV)
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["article", "ds"]).reset_index(drop=True)
    df["day_of_week"] = df["ds"].dt.dayofweek
    df["month"] = df["ds"].dt.month
    df["is_tourist_season"] = df["month"].isin([7, 8]).astype(int)

    lookup = df.set_index(["article", "ds"])["y"].to_dict()
    def get_weekday4w(art, d):
        vals = []
        for k in [1, 2, 3, 4]:
            v = lookup.get((art, d - pd.Timedelta(days=7*k)))
            if v is not None and not np.isnan(v):
                vals.append(v)
        return float(np.mean(vals)) if len(vals) > 0 else 0.0

    df["pred_weekday4w_cal"] = [get_weekday4w(a, d) for a, d in zip(df["article"], df["ds"])]
    for k in [1, 2, 3, 4]:
        df[f"y_lag_{7*k}_cal"] = [lookup.get((art, d - pd.Timedelta(days=7*k)), np.nan) for art, d in zip(df["article"], df["ds"])]

    # Holiday flags
    try:
        import holidays
        fr_public = holidays.France(years=[2021, 2022])
        pub_hols = set(pd.to_datetime(list(fr_public.keys())))
    except Exception:
        pub_hols = set()

    ponts = set(pd.to_datetime(["2021-05-14", "2022-05-27"]))
    vac_ranges = [
        ("2021-02-20", "2021-03-07"), ("2021-04-10", "2021-04-25"), ("2021-07-06", "2021-08-31"),
        ("2021-10-23", "2021-11-07"), ("2021-12-18", "2022-01-02"), ("2022-02-05", "2022-02-20"),
        ("2022-04-09", "2022-04-24"), ("2022-07-07", "2022-08-31")
    ]
    school_hols = set()
    for s, e in vac_ranges:
        for d in pd.date_range(s, e):
            school_hols.add(d)

    df["is_pub_holiday"] = df["ds"].isin(pub_hols).astype(int)
    df["is_bridge_day"] = df["ds"].isin(ponts).astype(int)
    df["is_school_holiday"] = df["ds"].isin(school_hols).astype(int)
    pub_window = set()
    for d in pub_hols:
        pub_window.add(d - pd.Timedelta(days=1))
        pub_window.add(d + pd.Timedelta(days=1))
    df["is_pub_holiday_window"] = df["ds"].isin(pub_window).astype(int)

    return df


def run_38_fold_harness(df_raw):
    print("=" * 70)
    print(" 1. EVALUATING PRODUCTION GBDT (MODEL IV) ON 38-FOLD ROLLING HARNESS ")
    print("=" * 70)
    if not PARQUET_38.exists():
        print(f"[ERROR] Could not find {PARQUET_38}")
        return None

    p38 = pd.read_parquet(PARQUET_38)
    cutoffs = sorted(p38["str_cutoff"].unique())
    fold_meta = p38[["fold", "str_cutoff"]].drop_duplicates().sort_values("fold").to_dict("records")
    p38_h = pd.merge(p38, df_raw[["article", "ds", "is_pub_holiday", "is_pub_holiday_window", "is_bridge_day", "is_school_holiday"]],
                     on=["article", "ds"], how="left")

    preds_iv = []
    t_start = time.time()
    for f_info in fold_meta:
        fid = f_info["fold"]
        cutoff = pd.to_datetime(f_info["str_cutoff"])
        f_sub = p38_h[p38_h["fold"] == fid].copy()
        test_dates = sorted(f_sub["ds"].unique())

        tr_raw = df_raw[df_raw["ds"] <= cutoff].copy()
        tr_raw["article_cat"] = tr_raw["article"].astype("category")

        tr_c4 = tr_raw.copy()
        tr_c4["y_lag_1"] = tr_c4.groupby("article")["y"].shift(1)
        tr_c4["y_roll_7"] = tr_c4.groupby("article")["y"].shift(1).rolling(7, min_periods=3).mean()
        tr_c4_clean = tr_c4.dropna(subset=FEATS_MODEL_IV + ["y"]).copy()

        gbdt = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
        gbdt.fit(tr_c4_clean[FEATS_MODEL_IV], tr_c4_clean["y"])

        full_so_far = tr_raw[["article", "ds", "y"]].copy()
        p_iv_fold = []
        for t_date in test_dates:
            day_rows = f_sub[f_sub["ds"] == t_date].copy()
            l1_dict = full_so_far.groupby("article").apply(lambda x: x.sort_values("ds").iloc[-1]["y"] if len(x)>0 else np.nan, include_groups=False).to_dict()
            r7_dict = full_so_far.groupby("article").apply(lambda x: x.sort_values("ds").tail(7)["y"].mean() if len(x)>0 else np.nan, include_groups=False).to_dict()
            day_rows["y_lag_1"] = day_rows["article"].map(l1_dict)
            day_rows["y_roll_7"] = day_rows["article"].map(r7_dict)
            day_rows["article_cat"] = day_rows["article"].astype("category")

            p4 = np.maximum(gbdt.predict(day_rows[FEATS_MODEL_IV]), 0.0)
            day_rows["pred_model_iv"] = p4
            p_iv_fold.append(day_rows[["article", "ds", "pred_model_iv", "y"]])
            full_so_far = pd.concat([full_so_far, day_rows[["article", "ds", "y"]]], ignore_index=True)
        preds_iv.append(pd.concat(p_iv_fold, ignore_index=True))

    full_p38 = pd.concat(preds_iv, ignore_index=True)
    tot_y = full_p38["y"].sum()
    pooled_wape_38 = float(np.sum(np.abs(full_p38["y"] - full_p38["pred_model_iv"])) / tot_y * 100.0)
    elapsed_38 = time.time() - t_start

    diff_pp = abs(pooled_wape_38 - 24.92)
    is_within_01 = diff_pp <= 0.10

    print(f"38-Fold Pooled WAPE (Day-Ahead Production Path): {pooled_wape_38:.2f}%")
    print(f"Research Benchmark:                             24.92%")
    print(f"Difference:                                     {pooled_wape_38 - 24.92:+.4f} pp")
    print(f"Within 0.1 pp requirement:                      {'PASS [YES]' if is_within_01 else 'FAIL [NO]'}")
    print(f"Evaluation runtime:                             {elapsed_38:.1f}s")
    return pooled_wape_38, is_within_01


def run_6_fold_harness(df_raw):
    print("\n" + "=" * 70)
    print(" 2. EVALUATING PRODUCTION GBDT (MODEL IV) ON 6-FOLD HARNESS ")
    print("=" * 70)

    preds_6 = []
    t_start = time.time()
    for f in FOLDS_6:
        cutoff = pd.to_datetime(f["cutoff"])
        s_date = pd.to_datetime(f["start"])
        e_date = pd.to_datetime(f["end"])

        tr_raw = df_raw[df_raw["ds"] <= cutoff].copy()
        tr_raw["article_cat"] = tr_raw["article"].astype("category")
        tr_raw["y_lag_1"] = tr_raw.groupby("article")["y"].shift(1)
        tr_raw["y_roll_7"] = tr_raw.groupby("article")["y"].shift(1).rolling(7, min_periods=3).mean()
        tr_clean = tr_raw.dropna(subset=FEATS_MODEL_IV + ["y"]).copy()

        gbdt = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
        gbdt.fit(tr_clean[FEATS_MODEL_IV], tr_clean["y"])

        full_so_far = tr_raw[["article", "ds", "y"]].copy()
        test_period = df_raw[(df_raw["ds"] >= s_date) & (df_raw["ds"] <= e_date)].copy()
        test_dates = sorted(test_period["ds"].unique())

        p_fold = []
        for t_date in test_dates:
            day_rows = test_period[test_period["ds"] == t_date].copy()
            l1_dict = full_so_far.groupby("article").apply(lambda x: x.sort_values("ds").iloc[-1]["y"] if len(x)>0 else np.nan, include_groups=False).to_dict()
            r7_dict = full_so_far.groupby("article").apply(lambda x: x.sort_values("ds").tail(7)["y"].mean() if len(x)>0 else np.nan, include_groups=False).to_dict()
            day_rows["y_lag_1"] = day_rows["article"].map(l1_dict)
            day_rows["y_roll_7"] = day_rows["article"].map(r7_dict)
            day_rows["article_cat"] = day_rows["article"].astype("category")

            day_rows["pred_gbdt"] = np.maximum(gbdt.predict(day_rows[FEATS_MODEL_IV]), 0.0)
            p_fold.append(day_rows[["article", "ds", "pred_gbdt", "y"]])
            full_so_far = pd.concat([full_so_far, day_rows[["article", "ds", "y"]]], ignore_index=True)

        preds_6.append(pd.concat(p_fold, ignore_index=True))

    full_p6 = pd.concat(preds_6, ignore_index=True)
    tot_y_6 = full_p6["y"].sum()
    pooled_wape_6 = float(np.sum(np.abs(full_p6["y"] - full_p6["pred_gbdt"])) / tot_y_6 * 100.0)
    elapsed_6 = time.time() - t_start

    print(f"6-Fold Pooled WAPE (Day-Ahead Production Path): {pooled_wape_6:.2f}%")
    print(f"Evaluation runtime:                            {elapsed_6:.1f}s")
    return pooled_wape_6


def run_staging_benchmark_three_times():
    print("\n" + "=" * 70)
    print(" 3. MEASURING BATCH RUNTIME & PEAK MEMORY (3 RUNS ON STAGING) ")
    print("=" * 70)
    import batch_forecast

    # Ensure connected to restockiq_staging
    batch_forecast.init_db(database_name="restockiq_staging")

    bench_results = []
    for run_i in range(1, 4):
        tracemalloc.start()
        t0 = time.perf_counter()

        batch_forecast.run_batch_job(dry_run=False, engine="gbdt")

        elapsed_sec = time.perf_counter() - t0
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak_bytes / (1024 * 1024)
        bench_results.append({
            "run": run_i,
            "runtime_sec": round(elapsed_sec, 3),
            "peak_memory_mb": round(peak_mb, 2),
        })
        print(f"  [RUN {run_i}/3] Runtime: {elapsed_sec:.3f}s | Peak Traced Memory: {peak_mb:.2f} MB")
        time.sleep(0.5)

    print("\nStaging Benchmark Summary (3 Consecutive Runs):")
    for r in bench_results:
        print(f"  Run {r['run']}: {r['runtime_sec']:.3f} s, {r['peak_memory_mb']:.2f} MB peak memory")
    return bench_results


if __name__ == "__main__":
    df_raw = load_raw_dataset_with_features()
    wape_38, is_within_01 = run_38_fold_harness(df_raw)
    wape_6 = run_6_fold_harness(df_raw)
    bench_results = run_staging_benchmark_three_times()
