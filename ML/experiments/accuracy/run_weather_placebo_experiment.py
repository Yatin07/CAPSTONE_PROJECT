import sys, time, warnings, logging
from pathlib import Path
import numpy as np
import pandas as pd
from prophet import Prophet
from joblib import Parallel, delayed

logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
logging.getLogger('prophet').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

FOLDS_6 = [
    {"fold": 1, "name": "Early Summer Ramp", "cutoff": "2022-07-15", "start": "2022-07-16", "end": "2022-07-22"},
    {"fold": 2, "name": "Mid-Summer Peak",   "cutoff": "2022-07-29", "start": "2022-07-30", "end": "2022-08-05"},
    {"fold": 3, "name": "August Holiday",   "cutoff": "2022-08-12", "start": "2022-08-13", "end": "2022-08-19"},
    {"fold": 4, "name": "Late Summer Turn", "cutoff": "2022-08-26", "start": "2022-08-27", "end": "2022-09-02"},
    {"fold": 5, "name": "Autumn Normal",    "cutoff": "2022-09-09", "start": "2022-09-10", "end": "2022-09-16"},
    {"fold": 6, "name": "Late September",   "cutoff": "2022-09-23", "start": "2022-09-24", "end": "2022-09-30"},
]

def run_placebo_experiment():
    df_raw = pd.read_csv("e:/CAP/ML/data/processed/primary_items.csv")
    df_raw["ds"] = pd.to_datetime(df_raw["ds"])
    df_raw = df_raw.sort_values(["article", "ds"]).reset_index(drop=True)
    df_raw["is_tourist_season"] = df_raw["ds"].dt.month.isin([7, 8]).astype(int)

    # Load Real Forecast Weather
    w_fcst = pd.read_csv("e:/CAP/ML/data/weather_guerande_forecast.csv")
    w_fcst["ds"] = pd.to_datetime(w_fcst["ds"])
    cols_w = ["temp_anom", "rain_flag", "sunshine_anom", "temp_anom_x_summer"]
    w_fcst = w_fcst[["ds"] + cols_w].drop_duplicates("ds").sort_values("ds").reset_index(drop=True)

    # Create Placebo Weather: Circular shift weather features by 180 days (breaks meteorological alignment while preserving realistic weather marginals)
    # Also create a permuted weather variant
    w_placebo = w_fcst.copy()
    rng = np.random.RandomState(42)
    perm_indices = rng.permutation(len(w_placebo))
    for col in cols_w:
        w_placebo[f"{col}_placebo_shift180"] = np.roll(w_fcst[col].values, 180)
        w_placebo[f"{col}_placebo_perm"] = w_fcst[col].values[perm_indices]

    # Merge weather into dataset
    cols_all_w = cols_w + [f"{c}_placebo_shift180" for c in cols_w] + [f"{c}_placebo_perm" for c in cols_w]
    df_merged = pd.merge(df_raw, w_placebo[["ds"] + cols_all_w], on="ds", how="left")
    for c in cols_all_w:
        df_merged[c] = df_merged[c].fillna(0.0)

    print("=" * 80)
    print("   RESTOCKIQ: WEATHER PLACEBO EXPERIMENT (6 ROLLING SUMMER FOLDS)")
    print("   Models: Prophet-only (Base), Prophet+RealWeather, Prophet+PlaceboShift180, Prophet+PlaceboPerm")
    print("=" * 80)

    def process_fold(f_dict):
        c_dt = pd.to_datetime(f_dict["cutoff"])
        s_dt = pd.to_datetime(f_dict["start"])
        e_dt = pd.to_datetime(f_dict["end"])
        f_num = f_dict["fold"]

        tr = df_merged[df_merged["ds"] <= c_dt].copy()
        te = df_merged[(df_merged["ds"] >= s_dt) & (df_merged["ds"] <= e_dt)].copy()

        preds = []
        for item, group in tr.groupby("article"):
            if len(group) < 30:
                continue
            item_te = te[te["article"] == item].copy()
            if len(item_te) == 0:
                continue

            full_item = df_merged[(df_merged["article"] == item) & (df_merged["ds"] <= e_dt)].copy()

            # 1. Base Prophet
            m_base = Prophet(seasonality_mode='multiplicative', yearly_seasonality=True, weekly_seasonality=True)
            m_base.add_country_holidays(country_name='FR')
            m_base.add_regressor('is_tourist_season')
            m_base.fit(group[['ds', 'y', 'is_tourist_season']])
            fc_base = m_base.predict(item_te[['ds', 'is_tourist_season']])

            # 2. Real Weather (Forecast)
            m_real = Prophet(seasonality_mode='multiplicative', yearly_seasonality=True, weekly_seasonality=True)
            m_real.add_country_holidays(country_name='FR')
            m_real.add_regressor('is_tourist_season')
            for c in cols_w:
                m_real.add_regressor(c)
            m_real.fit(group[['ds', 'y', 'is_tourist_season'] + cols_w])
            fc_real = m_real.predict(item_te[['ds', 'is_tourist_season'] + cols_w])

            # 3. Placebo Weather (Shift 180 days)
            shift_cols = [f"{c}_placebo_shift180" for c in cols_w]
            m_shift = Prophet(seasonality_mode='multiplicative', yearly_seasonality=True, weekly_seasonality=True)
            m_shift.add_country_holidays(country_name='FR')
            m_shift.add_regressor('is_tourist_season')
            for c in shift_cols:
                m_shift.add_regressor(c)
            m_shift.fit(group[['ds', 'y', 'is_tourist_season'] + shift_cols])
            fc_shift = m_shift.predict(item_te[['ds', 'is_tourist_season'] + shift_cols])

            # 4. Placebo Weather (Permuted)
            perm_cols = [f"{c}_placebo_perm" for c in cols_w]
            m_perm = Prophet(seasonality_mode='multiplicative', yearly_seasonality=True, weekly_seasonality=True)
            m_perm.add_country_holidays(country_name='FR')
            m_perm.add_regressor('is_tourist_season')
            for c in perm_cols:
                m_perm.add_regressor(c)
            m_perm.fit(group[['ds', 'y', 'is_tourist_season'] + perm_cols])
            fc_perm = m_perm.predict(item_te[['ds', 'is_tourist_season'] + perm_cols])

            item_res = pd.DataFrame({
                "fold": f_num,
                "article": item,
                "ds": item_te["ds"].values,
                "y": item_te["y"].values,
                "pred_prophet_base": np.maximum(fc_base["yhat"].values, 0.0),
                "pred_prophet_real": np.maximum(fc_real["yhat"].values, 0.0),
                "pred_prophet_placebo_shift": np.maximum(fc_shift["yhat"].values, 0.0),
                "pred_prophet_placebo_perm": np.maximum(fc_perm["yhat"].values, 0.0),
            })
            preds.append(item_res)

        return pd.concat(preds, ignore_index=True)

    print("Running 6 folds in parallel...")
    results = Parallel(n_jobs=6)(delayed(process_fold)(f) for f in FOLDS_6)
    eval_df = pd.concat(results, ignore_index=True)

    tot_y = eval_df["y"].sum()
    models = {
        "pred_prophet_base": "Prophet-only (Baseline, No Weather)",
        "pred_prophet_real": "Prophet + Real Weather (Forecast API)",
        "pred_prophet_placebo_shift": "Prophet + Placebo Weather (Shifted 180d)",
        "pred_prophet_placebo_perm": "Prophet + Placebo Weather (Permuted)",
    }

    print("\n--- RESULTS SUMMARY across 6 Folds (32,404 Units Tested) ---")
    base_wape = np.sum(np.abs(eval_df["y"] - eval_df["pred_prophet_base"])) / tot_y * 100.0

    out_records = []
    for col, name in models.items():
        wape = np.sum(np.abs(eval_df["y"] - eval_df[col])) / tot_y * 100.0
        fold_wapes = []
        wins_vs_base = 0
        for f_num, f_df in eval_df.groupby("fold"):
            fy = f_df["y"].values
            fw = np.sum(np.abs(fy - f_df[col].values)) / np.sum(fy) * 100.0
            fw_b = np.sum(np.abs(fy - f_df["pred_prophet_base"].values)) / np.sum(fy) * 100.0
            fold_wapes.append(fw)
            if fw < fw_b:
                wins_vs_base += 1
        f_mean = np.mean(fold_wapes)
        gain_pp = base_wape - wape

        # Bootstrap CI vs base
        rng = np.random.RandomState(42)
        diffs = []
        n_rows = len(eval_df)
        blocks = [list(range(i, min(i+7, n_rows))) for i in range(0, n_rows, 7)]
        n_blks = len(blocks)
        for _ in range(1000):
            chosen = rng.choice(n_blks, size=n_blks, replace=True)
            idx = [i for b in chosen for i in blocks[b]]
            by = eval_df["y"].values[idx]
            b_tot = np.sum(by)
            w_b = np.sum(np.abs(by - eval_df["pred_prophet_base"].values[idx])) / b_tot * 100.0
            w_m = np.sum(np.abs(by - eval_df[col].values[idx])) / b_tot * 100.0
            diffs.append(w_b - w_m)
        ci_lo = np.percentile(diffs, 2.5)
        ci_hi = np.percentile(diffs, 97.5)

        print(f"{name:<42} | Pooled WAPE: {wape:>6.2f}% | Fold-Mean: {f_mean:>6.2f}% | Wins vs Base: {wins_vs_base}/6 | Gain: {gain_pp:>+6.2f} pp | 95% CI: [{ci_lo:>+5.2f}, {ci_hi:>+5.2f}]")
        out_records.append({
            "model_name": name,
            "pooled_wape": wape,
            "fold_mean_wape": f_mean,
            "wins_vs_baseline": wins_vs_base,
            "gain_pp": gain_pp,
            "ci_lower": ci_lo,
            "ci_upper": ci_hi,
        })

    pd.DataFrame(out_records).to_csv("e:/CAP/scratch/weather_placebo_results.csv", index=False)
    eval_df.to_parquet("e:/CAP/scratch/weather_placebo_preds.parquet", index=False)
    print("\nSaved e:/CAP/scratch/weather_placebo_results.csv and weather_placebo_preds.parquet")

if __name__ == '__main__':
    run_placebo_experiment()
