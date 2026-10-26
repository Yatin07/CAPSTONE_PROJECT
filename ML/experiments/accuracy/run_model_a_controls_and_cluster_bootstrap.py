import sys, time, json, warnings, logging
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import timedelta
import scipy.stats as stats
from sklearn.ensemble import HistGradientBoostingRegressor
import holidays
from prophet import Prophet
from joblib import Parallel, delayed

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
logging.getLogger("prophet").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

PRIMARY_CSV = Path("e:/CAP/ML/data/processed/primary_items.csv")
WEATHER_FCST_CSV = Path("e:/CAP/ML/data/weather_guerande_forecast.csv")

def load_data():
    df = pd.read_csv(PRIMARY_CSV)
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values(["article", "ds"]).reset_index(drop=True)
    df["day_of_week"] = df["ds"].dt.dayofweek
    df["month"] = df["ds"].dt.month
    df["is_tourist_season"] = df["month"].isin([7, 8]).astype(int)

    lookup = df.set_index(["article", "ds"])["y"].to_dict()
    def get_snaive(art, d):
        for k in [1, 2, 3, 4, 5]:
            val = lookup.get((art, d - pd.Timedelta(days=7*k)))
            if val is not None and not np.isnan(val):
                return val
        return 0.0

    def get_weekday4w(art, d):
        vals = []
        for k in [1, 2, 3, 4]:
            v = lookup.get((art, d - pd.Timedelta(days=7*k)))
            if v is not None and not np.isnan(v):
                vals.append(v)
        return np.mean(vals) if len(vals) > 0 else 0.0

    df["pred_snaive_cal"] = [get_snaive(a, d) for a, d in zip(df["article"], df["ds"])]
    df["pred_weekday4w_cal"] = [get_weekday4w(a, d) for a, d in zip(df["article"], df["ds"])]
    for k in [1, 2, 3, 4]:
        df[f"y_lag_{7*k}_cal"] = [lookup.get((art, d - pd.Timedelta(days=7*k)), np.nan) for art, d in zip(df["article"], df["ds"])]

    df["y_lag_1"] = df.groupby("article")["y"].shift(1)
    df["y_roll_7"] = df.groupby("article")["y"].shift(1).rolling(7, min_periods=3).mean()

    # Weather
    w_fcst = pd.read_csv(WEATHER_FCST_CSV)
    w_fcst["ds"] = pd.to_datetime(w_fcst["ds"])
    cols_w = ["temp_anom", "rain_flag", "sunshine_anom", "temp_anom_x_summer"]
    w_fcst = w_fcst[["ds"] + cols_w].drop_duplicates("ds")
    df = pd.merge(df, w_fcst, on="ds", how="left")
    for c in cols_w:
        df[c] = df[c].fillna(0.0)

    # Holidays
    fr_public = holidays.France(years=[2021, 2022])
    hols_records = []
    for dt, name in fr_public.items():
        hols_records.append({"holiday": "pub_holiday", "ds": pd.to_datetime(dt), "lower_window": -1, "upper_window": 1})
    ponts = ["2021-05-14", "2022-05-27"]
    for dt in ponts:
        hols_records.append({"holiday": "bridge_day", "ds": pd.to_datetime(dt), "lower_window": 0, "upper_window": 0})
    vac_ranges = [
        ("2021-02-20", "2021-03-07"), ("2021-04-10", "2021-04-25"), ("2021-07-06", "2021-08-31"),
        ("2021-10-23", "2021-11-07"), ("2021-12-18", "2022-01-02"), ("2022-02-05", "2022-02-20"),
        ("2022-04-09", "2022-04-24"), ("2022-07-07", "2022-08-31")
    ]
    for s_v, e_v in vac_ranges:
        for dt_v in pd.date_range(s_v, e_v):
            hols_records.append({"holiday": "school_holiday", "ds": dt_v, "lower_window": 0, "upper_window": 0})
    hols_df = pd.DataFrame(hols_records).drop_duplicates(["holiday", "ds"])

    return df, hols_df, cols_w

def process_single_weekly_fold(f_dict, df_raw, hols_df, cols_w):
    cutoff = f_dict["cutoff"]
    s_date = f_dict["start"]
    e_date = f_dict["end"]
    f_num = f_dict["fold"]

    tr_data = df_raw[df_raw["ds"] <= cutoff].copy()
    items = sorted(tr_data["article"].unique())

    lag_feats_7d = ["day_of_week", "month", "is_tourist_season", "y_lag_7_cal", "pred_weekday4w_cal"]
    lag_feats_1d = ["day_of_week", "month", "is_tourist_season", "y_lag_1", "y_roll_7", "y_lag_7_cal", "pred_weekday4w_cal"]
    prophet_cols = ["trend", "weekly", "yearly", "holidays", "is_tourist_season_prophet", "yhat"]

    p_base_list = []
    p_cal_list = []
    p_w_list = []

    for item in items:
        grp = tr_data[tr_data["article"] == item]
        if len(grp) < 30:
            continue

        full_item = df_raw[(df_raw["article"] == item) & (df_raw["ds"] <= e_date)].copy()

        # 1. Prophet baseline
        m_base = Prophet(seasonality_mode="multiplicative", yearly_seasonality=True, weekly_seasonality=True)
        m_base.add_country_holidays(country_name="FR")
        m_base.add_regressor("is_tourist_season")
        m_base.fit(grp[["ds", "y", "is_tourist_season"]])
        fc_base = m_base.predict(full_item[["ds", "is_tourist_season"]])
        cols_extract = ["ds", "trend", "weekly", "yearly", "holidays", "is_tourist_season", "yhat"]
        for c in ["weekly", "yearly", "holidays", "is_tourist_season"]:
            if c not in fc_base.columns:
                fc_base[c] = 0.0
        r_base = fc_base[cols_extract].copy()
        r_base["article"] = item
        p_base_list.append(r_base)

        # 2. Model B: Prophet + Enhanced Calendar
        m_cal = Prophet(holidays=hols_df, seasonality_mode="multiplicative", yearly_seasonality=True, weekly_seasonality=True)
        m_cal.add_regressor("is_tourist_season")
        m_cal.fit(grp[["ds", "y", "is_tourist_season"]])
        fc_cal = m_cal.predict(full_item[["ds", "is_tourist_season"]])
        rc = fc_cal[["ds", "yhat"]].rename(columns={"yhat": "yhat_cal"})
        rc["article"] = item
        p_cal_list.append(rc)

        # 3. Prophet + Forecast Weather
        m_w = Prophet(seasonality_mode="multiplicative", yearly_seasonality=True, weekly_seasonality=True)
        m_w.add_country_holidays(country_name="FR")
        m_w.add_regressor("is_tourist_season")
        for c in cols_w:
            m_w.add_regressor(c)
        m_w.fit(grp[["ds", "y", "is_tourist_season"] + cols_w])
        fc_w = m_w.predict(full_item[["ds", "is_tourist_season"] + cols_w])
        rw = fc_w[["ds", "yhat"]].rename(columns={"yhat": "yhat_weather_fcst"})
        rw["article"] = item
        p_w_list.append(rw)

    df_pb = pd.concat(p_base_list, ignore_index=True)
    df_pc = pd.concat(p_cal_list, ignore_index=True)
    df_pw = pd.concat(p_w_list, ignore_index=True)

    merged = pd.merge(df_raw[df_raw["ds"] <= e_date], df_pb, on=["article", "ds"], suffixes=("", "_prophet"))
    merged = pd.merge(merged, df_pc, on=["article", "ds"])
    merged = pd.merge(merged, df_pw, on=["article", "ds"])
    merged["article_cat"] = merged["article"].astype("category")

    test_df = merged[(merged["ds"] >= s_date) & (merged["ds"] <= e_date)].copy()
    test_df["pred_prophet_only"] = np.maximum(test_df["yhat"], 0.0)
    test_df["pred_model_b_cal"] = np.maximum(test_df["yhat_cal"], 0.0)
    test_df["pred_prophet_weather"] = np.maximum(test_df["yhat_weather_fcst"], 0.0)

    # Corrected Hybrid (7-day horizon)
    train_h = merged[merged["ds"] <= cutoff].dropna(subset=["article_cat"] + lag_feats_7d + prophet_cols + ["y"]).copy()
    gbdt_h = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
    gbdt_h.fit(train_h[["article_cat"] + lag_feats_7d + prophet_cols], train_h["y"])
    test_df["pred_hybrid_corr"] = np.maximum(gbdt_h.predict(test_df[["article_cat"] + lag_feats_7d + prophet_cols]), 0.0)

    # Model A: 1-Day-Ahead Hybrid
    train_1d = merged[merged["ds"] <= cutoff].dropna(subset=["article_cat"] + lag_feats_1d + prophet_cols + ["y"]).copy()
    gbdt_1d = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
    gbdt_1d.fit(train_1d[["article_cat"] + lag_feats_1d + prophet_cols], train_1d["y"])

    # Control 3: GBDT with lag_1 alone (NO PROPHET FEATURES)
    train_c3 = merged[merged["ds"] <= cutoff].dropna(subset=["article_cat"] + lag_feats_1d + ["y"]).copy()
    gbdt_c3 = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
    gbdt_c3.fit(train_c3[["article_cat"] + lag_feats_1d], train_c3["y"])

    # Day-ahead simulation roll forward
    preds_day_ahead = []
    full_so_far = merged[merged["ds"] <= cutoff][["article", "ds", "y"]].copy()
    for t_date in sorted(test_df["ds"].unique()):
        day_rows = test_df[test_df["ds"] == t_date].copy()
        l1_dict = full_so_far.groupby("article").apply(lambda x: x.sort_values("ds").iloc[-1]["y"] if len(x)>0 else np.nan).to_dict()
        r7_dict = full_so_far.groupby("article").apply(lambda x: x.sort_values("ds").tail(7)["y"].mean() if len(x)>0 else np.nan).to_dict()
        day_rows["y_lag_1"] = day_rows["article"].map(l1_dict)
        day_rows["y_roll_7"] = day_rows["article"].map(r7_dict)

        # Model A prediction
        p1 = np.maximum(gbdt_1d.predict(day_rows[["article_cat"] + lag_feats_1d + prophet_cols]), 0.0)
        day_rows["pred_model_a_day_ahead"] = p1

        # Control 1: 1-Day-Ahead SNaive (lag_1)
        day_rows["pred_ctrl1_snaive_1d"] = np.maximum(day_rows["y_lag_1"].fillna(0.0), 0.0)

        # Control 2: 1-Day-Ahead MA7 (y_roll_7)
        day_rows["pred_ctrl2_ma7_1d"] = np.maximum(day_rows["y_roll_7"].fillna(0.0), 0.0)

        # Control 3: GBDT with lag_1 alone (No Prophet)
        p_c3 = np.maximum(gbdt_c3.predict(day_rows[["article_cat"] + lag_feats_1d]), 0.0)
        day_rows["pred_ctrl3_gbdt_no_prophet"] = p_c3

        preds_day_ahead.append(day_rows[["article", "ds", "pred_model_a_day_ahead", "pred_ctrl1_snaive_1d", "pred_ctrl2_ma7_1d", "pred_ctrl3_gbdt_no_prophet"]])
        full_so_far = pd.concat([full_so_far, day_rows[["article", "ds", "y"]]], ignore_index=True)

    test_df = pd.merge(test_df, pd.concat(preds_day_ahead, ignore_index=True), on=["article", "ds"])
    test_df["fold"] = f_num
    test_df["cal_days"] = f_dict["cal_days"]
    test_df["str_cutoff"] = f_dict["str_cutoff"]

    return test_df

def run_suite():
    df_raw, hols_df, cols_w = load_data()
    start_sim = pd.to_datetime("2022-01-02")
    end_sim = pd.to_datetime("2022-09-23")
    cutoffs = pd.date_range(start_sim, end_sim, freq="7D")

    folds = []
    t0 = df_raw["ds"].min()
    for idx, c in enumerate(cutoffs, 1):
        s = c + pd.Timedelta(days=1)
        e = c + pd.Timedelta(days=7)
        cal_train = (c - t0).days
        folds.append({
            "fold": idx, "cutoff": c, "start": s, "end": e, "cal_days": cal_train,
            "str_cutoff": c.strftime("%Y-%m-%d"), "str_start": s.strftime("%Y-%m-%d"), "str_end": e.strftime("%Y-%m-%d")
        })

    print(f"Launching 38 weekly folds across 12 worker processes...")
    t_start = time.time()
    results = Parallel(n_jobs=12, verbose=5)(
        delayed(process_single_weekly_fold)(f, df_raw, hols_df, cols_w) for f in folds
    )
    full_eval = pd.concat(results, ignore_index=True)
    runtime_sec = time.time() - t_start
    print(f"38-Fold processing completed in {runtime_sec:.1f}s ({runtime_sec/60:.2f} min).")

    full_eval.to_parquet("e:/CAP/scratch/predictions_38folds_with_controls.parquet", index=False)
    print("Saved e:/CAP/scratch/predictions_38folds_with_controls.parquet")

    # Evaluate models
    models = {
        "prophet_only": "Prophet-only (Baseline)",
        "hybrid_corr": "Hybrid (Corrected 7-Day)",
        "model_a_day_ahead": "Model A (1-Day-Ahead Hybrid)",
        "model_b_cal": "Model B (Prophet + Enhanced Calendar)",
        "prophet_weather": "Prophet + Weather (Forecast API)",
        "ctrl1_snaive_1d": "Control 1: 1-Day-Ahead SNaive (lag_1)",
        "ctrl2_ma7_1d": "Control 2: 1-Day-Ahead MA (trailing 7d)",
        "ctrl3_gbdt_no_prophet": "Control 3: GBDT with lag_1 (No Prophet)",
    }

    tot_y = full_eval["y"].sum()
    y_true = full_eval["y"].values
    n_folds = full_eval["fold"].nunique()
    base_col = "pred_prophet_only"
    base_wape = np.sum(np.abs(y_true - full_eval[base_col].values)) / tot_y * 100.0

    # 1. WHOLE-WEEK CLUSTER BOOTSTRAP (38 BLOCKS, 2000 DRAWS)
    print("\nRunning Whole-Week Cluster Bootstrap (38 Blocks, 2,000 Draws)...")
    rng = np.random.RandomState(42)
    fold_ids = sorted(full_eval["fold"].unique())
    n_clusters = len(fold_ids)

    # Pre-aggregate sum abs error and sum actual per fold for lightning fast cluster bootstrap
    fold_agg = {}
    for fid in fold_ids:
        f_sub = full_eval[full_eval["fold"] == fid]
        f_y = f_sub["y"].values
        f_tot = np.sum(f_y)
        f_dict = {"tot_y": f_tot}
        for m_key in models:
            pred_vals = f_sub[f"pred_{m_key}"].values
            f_dict[m_key] = np.sum(np.abs(f_y - pred_vals))
        fold_agg[fid] = f_dict

    bootstrap_cis = {}
    for m_key in models:
        if m_key == "prophet_only":
            bootstrap_cis[m_key] = (0.0, 0.0, 0.0)
            continue
        diffs = []
        for _ in range(2000):
            sample_fids = rng.choice(fold_ids, size=n_clusters, replace=True)
            sum_y = sum(fold_agg[f]["tot_y"] for f in sample_fids)
            sum_err_base = sum(fold_agg[f]["prophet_only"] for f in sample_fids)
            sum_err_cand = sum(fold_agg[f][m_key] for f in sample_fids)
            w_b = (sum_err_base / sum_y) * 100.0
            w_c = (sum_err_cand / sum_y) * 100.0
            diffs.append(w_b - w_c)
        pt_diff = base_wape - (np.sum(np.abs(y_true - full_eval[f"pred_{m_key}"].values)) / tot_y * 100.0)
        ci_lo = np.percentile(diffs, 2.5)
        ci_hi = np.percentile(diffs, 97.5)
        bootstrap_cis[m_key] = (pt_diff, ci_lo, ci_hi)

    summary_rows = []
    print("\n" + "=" * 115)
    print(f"{'Model':<42} | {'Pooled WAPE':<11} | {'Fold-Mean':<9} | {'Wins':<7} | {'Win %':<6} | {'Gain (pp)':<9} | {'Cluster 95% CI (38 blks)':<25}")
    print("=" * 115)

    for m_key, m_name in models.items():
        col_pred = f"pred_{m_key}"
        wape = np.sum(np.abs(y_true - full_eval[col_pred].values)) / tot_y * 100.0
        fold_wapes = []
        wins = 0
        for fid in fold_ids:
            f_sub = full_eval[full_eval["fold"] == fid]
            fy = f_sub["y"].values
            fw = np.sum(np.abs(fy - f_sub[col_pred].values)) / np.sum(fy) * 100.0
            fw_b = np.sum(np.abs(fy - f_sub[base_col].values)) / np.sum(fy) * 100.0
            fold_wapes.append(fw)
            if fw < fw_b:
                wins += 1
        f_mean = np.mean(fold_wapes)
        win_pct = (wins / n_folds) * 100.0
        gain_pt, ci_lo, ci_hi = bootstrap_cis[m_key]

        ci_str = f"[{ci_lo:>+5.2f}, {ci_hi:>+5.2f}]" if m_key != "prophet_only" else "Baseline"
        print(f"{m_name:<42} | {wape:>9.2f}% | {f_mean:>7.2f}% | {wins:>3}/{n_folds:<2} | {win_pct:>5.1f}% | {gain_pt:>+7.2f} pp | {ci_str:<25}")

        summary_rows.append({
            "model_key": m_key,
            "model_name": m_name,
            "pooled_wape": round(wape, 2),
            "fold_mean_wape": round(f_mean, 2),
            "fold_wins": wins,
            "total_folds": n_folds,
            "win_pct": round(win_pct, 1),
            "gain_pp": round(gain_pt, 2),
            "cluster_ci_lower": round(ci_lo, 2),
            "cluster_ci_upper": round(ci_hi, 2),
        })

    sum_df = pd.DataFrame(summary_rows)
    sum_df.to_csv("e:/CAP/scratch/model_a_controls_and_cluster_bootstrap.csv", index=False)
    print("\nSaved e:/CAP/scratch/model_a_controls_and_cluster_bootstrap.csv")

if __name__ == "__main__":
    run_suite()
