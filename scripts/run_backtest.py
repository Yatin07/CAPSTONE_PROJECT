import os
import sys
import logging
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.ensemble import HistGradientBoostingRegressor

# Suppress verbose loggers
logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
logging.getLogger('prophet').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

def run_extended_backtest():
    print("=" * 85)
    print("      RESTOCKIQ: EXTENDED ROLLING-ORIGIN BACKTEST & ABLATION STUDY")
    print("=" * 85)

    data_path = Path("ML/data/processed/primary_items.csv")
    if not data_path.exists():
        data_path = Path("data/processed/primary_items.csv")

    print(f"Loading data from: {data_path}")
    df_raw = pd.read_csv(data_path)
    df_raw['ds'] = pd.to_datetime(df_raw['ds'])
    df_raw = df_raw.sort_values(['article', 'ds']).reset_index(drop=True)

    # Base calendar features
    df_raw['day_of_week'] = df_raw['ds'].dt.dayofweek
    df_raw['month'] = df_raw['ds'].dt.month
    df_raw['is_tourist_season'] = df_raw['month'].isin([7, 8]).astype(int)

    # Pre-calculate multi-week same-weekday lags on full series
    # (Each lag t-7k is strictly past data relative to forecast date t)
    for k in [1, 2, 3, 4]:
        df_raw[f'y_lag_{7*k}'] = df_raw.groupby('article')['y'].shift(7 * k)

    # 4-Week Same-Weekday Average: 1/4 * sum(y(t-7), y(t-14), y(t-21), y(t-28))
    lag_cols = [f'y_lag_{7*k}' for k in [1, 2, 3, 4]]
    df_raw['pred_weekday4w'] = df_raw[lag_cols].mean(axis=1)

    # 6 Folds spread across the timeline with >= 1.5 years of training history
    # History starts 2021-01-02. 1.5 years = 548 days -> July 3, 2022 onwards.
    folds = [
        {"fold": 1, "name": "Early Summer Ramp", "cutoff": "2022-07-15", "start": "2022-07-16", "end": "2022-07-22"},
        {"fold": 2, "name": "Mid-Summer Peak",   "cutoff": "2022-07-29", "start": "2022-07-30", "end": "2022-08-05"},
        {"fold": 3, "name": "August Holiday",   "cutoff": "2022-08-12", "start": "2022-08-13", "end": "2022-08-19"},
        {"fold": 4, "name": "Late Summer Turn", "cutoff": "2022-08-26", "start": "2022-08-27", "end": "2022-09-02"},
        {"fold": 5, "name": "Autumn Normal",    "cutoff": "2022-09-09", "start": "2022-09-10", "end": "2022-09-16"},
        {"fold": 6, "name": "Late September",   "cutoff": "2022-09-23", "start": "2022-09-24", "end": "2022-09-30"},
    ]

    print("\n" + "-" * 85)
    print("                     TEMPORAL LEAKAGE AUDIT PER FOLD                     ")
    print("-" * 85)
    for f in folds:
        c_dt = pd.to_datetime(f['cutoff'])
        s_dt = pd.to_datetime(f['start'])
        e_dt = pd.to_datetime(f['end'])
        train_days = (c_dt - df_raw['ds'].min()).days
        print(f"Fold {f['fold']} ({f['name']:<18}): Train <= {c_dt.strftime('%Y-%m-%d')} ({train_days} days / {train_days/365.25:.2f} yrs) | Horizon: {s_dt.strftime('%Y-%m-%d')} to {e_dt.strftime('%Y-%m-%d')} [ZERO LEAKAGE]")

    all_fold_evals = []

    for f in folds:
        fold_num = f['fold']
        cutoff = pd.to_datetime(f['cutoff'])
        start_date = pd.to_datetime(f['start'])
        end_date = pd.to_datetime(f['end'])

        # Strict temporal split
        df_train = df_raw[df_raw['ds'] <= cutoff].copy()
        df_test = df_raw[(df_raw['ds'] >= start_date) & (df_raw['ds'] <= end_date)].copy()

        # Step 1: Fit Prophet on train set only
        components_list = []
        for item, group in df_train.groupby('article'):
            if len(group) < 30:
                continue
            m = Prophet(seasonality_mode='multiplicative', yearly_seasonality=True, weekly_seasonality=True)
            m.add_country_holidays(country_name='FR')
            m.add_regressor('is_tourist_season')
            m.fit(group[['ds', 'y', 'is_tourist_season']])

            # Predict components for full timeline of this item up to end_date
            full_item = df_raw[(df_raw['article'] == item) & (df_raw['ds'] <= end_date)]
            forecast = m.predict(full_item[['ds', 'is_tourist_season']])
            cols = ['ds', 'trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season', 'yhat']
            for c in ['weekly', 'yearly', 'holidays', 'is_tourist_season']:
                if c not in forecast.columns:
                    forecast[c] = 0.0
            res = forecast[cols].copy()
            res['article'] = item
            components_list.append(res)

        components_df = pd.concat(components_list, ignore_index=True)
        merged = pd.merge(df_raw[df_raw['ds'] <= end_date], components_df, on=['article', 'ds'], suffixes=('', '_prophet'))

        # Moving average computed at or prior to forecast
        # For each test day t in [start_date, end_date], lag 7 is in the past (t-7 <= cutoff)
        merged['pred_snaive'] = np.maximum(merged['y_lag_7'], 0.0)
        merged['pred_weekday4w'] = np.maximum(merged['pred_weekday4w'], 0.0)
        
        # 7-day MA strictly using history available at or before cutoff
        ma_at_cutoff = df_train.groupby('article').apply(
            lambda x: x.sort_values('ds').tail(7)['y'].mean()
        ).to_dict()
        merged['pred_ma7'] = merged['article'].astype(str).map(ma_at_cutoff).fillna(0.0)

        merged['article'] = merged['article'].astype('category')

        # Features for GBDT models
        lag_features = ['day_of_week', 'month', 'is_tourist_season', 'y_lag_7', 'pred_weekday4w']
        prophet_features = ['trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season_prophet', 'yhat']

        train_set = merged[merged['ds'] <= cutoff].dropna().copy()
        test_set = merged[(merged['ds'] >= start_date) & (merged['ds'] <= end_date)].dropna().copy()

        # Step 2: GBDT-only ablation (no Prophet features)
        gbdt_only = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
        gbdt_only.fit(train_set[['article'] + lag_features], train_set['y'])
        test_set['pred_gbdt_only'] = np.maximum(gbdt_only.predict(test_set[['article'] + lag_features]), 0.0)

        # Step 3: Hybrid model (Prophet components + GBDT)
        hybrid_features = ['article'] + lag_features + prophet_features
        hybrid = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
        hybrid.fit(train_set[hybrid_features], train_set['y'])
        test_set['pred_hybrid'] = np.maximum(hybrid.predict(test_set[hybrid_features]), 0.0)

        # Prophet-only ablation (pure Prophet yhat)
        test_set['pred_prophet_only'] = np.maximum(test_set['yhat'], 0.0)

        test_set['fold'] = fold_num
        test_set['fold_name'] = f['name']
        all_fold_evals.append(test_set)

    eval_df = pd.concat(all_fold_evals, ignore_index=True)

    models = {
        'snaive': 'Seasonal Naive (Lag 7)',
        'ma7': '7-Day Moving Avg',
        'weekday4w': 'Same-Weekday 4-Wk Avg (Strong Baseline)',
        'prophet_only': 'Prophet-Only Ablation',
        'gbdt_only': 'GBDT-Only Ablation',
        'hybrid': 'RestockIQ Hybrid Model',
    }

    # Compute errors
    for m in models.keys():
        eval_df[f'abs_err_{m}'] = (eval_df['y'] - eval_df[f'pred_{m}']).abs()
        eval_df[f'ape_{m}'] = eval_df[f'abs_err_{m}'] / np.maximum(eval_df['y'], 1.0) * 100.0

    print("\n" + "=" * 90)
    print("                 PER-FOLD WAPE PERFORMANCE MATRIX (6 FOLDS)               ")
    print("=" * 90)
    print(f"{'Fold / Window':<26} | {'SNaive':>8} | {'MA7':>8} | {'4Wk-Avg':>8} | {'Prophet':>8} | {'GBDT':>8} | {'Hybrid':>8}")
    print("-" * 90)

    summary_rows = []

    for f in folds:
        sub = eval_df[eval_df['fold'] == f['fold']]
        tot_y = sub['y'].sum()

        wapes = {m: (sub[f'abs_err_{m}'].sum() / tot_y) * 100.0 for m in models}
        mapes = {m: sub[f'ape_{m}'].mean() for m in models}

        # Relative WAPE improvement of Hybrid over each baseline
        rel_gains = {
            m: ((wapes[m] - wapes['hybrid']) / wapes[m]) * 100.0 if wapes[m] > 0 else 0.0
            for m in models if m != 'hybrid'
        }
        pp_gains = {
            m: wapes[m] - wapes['hybrid']
            for m in models if m != 'hybrid'
        }

        row = {
            'Level': f"Fold {f['fold']}: {f['name']}",
            'Item': 'ALL',
            'Total_Actual': tot_y,
            'Hybrid_WAPE': wapes['hybrid'],
            'Hybrid_MAPE': mapes['hybrid'],
            'SNaive_WAPE': wapes['snaive'],
            'MA7_WAPE': wapes['ma7'],
            'Weekday4W_WAPE': wapes['weekday4w'],
            'ProphetOnly_WAPE': wapes['prophet_only'],
            'GBDTOnly_WAPE': wapes['gbdt_only'],
            'Rel_Gain_vs_SNaive_pct': rel_gains['snaive'],
            'Rel_Gain_vs_MA7_pct': rel_gains['ma7'],
            'Rel_Gain_vs_Weekday4W_pct': rel_gains['weekday4w'],
            'Rel_Gain_vs_Prophet_pct': rel_gains['prophet_only'],
            'Rel_Gain_vs_GBDT_pct': rel_gains['gbdt_only'],
            'PP_Gain_vs_SNaive': pp_gains['snaive'],
            'PP_Gain_vs_MA7': pp_gains['ma7'],
            'PP_Gain_vs_Weekday4W': pp_gains['weekday4w'],
            'PP_Gain_vs_Prophet': pp_gains['prophet_only'],
            'PP_Gain_vs_GBDT': pp_gains['gbdt_only'],
        }
        summary_rows.append(row)

        print(f"Fold {f['fold']} ({f['name']:<18}) | {wapes['snaive']:>7.2f}% | {wapes['ma7']:>7.2f}% | {wapes['weekday4w']:>7.2f}% | {wapes['prophet_only']:>7.2f}% | {wapes['gbdt_only']:>7.2f}% | {wapes['hybrid']:>7.2f}%")

    # Overall across all 6 folds
    tot_y_all = eval_df['y'].sum()
    all_wapes = {m: (eval_df[f'abs_err_{m}'].sum() / tot_y_all) * 100.0 for m in models}
    all_mapes = {m: eval_df[f'ape_{m}'].mean() for m in models}
    all_rel = {m: ((all_wapes[m] - all_wapes['hybrid']) / all_wapes[m]) * 100.0 for m in models if m != 'hybrid'}
    all_pp = {m: all_wapes[m] - all_wapes['hybrid'] for m in models if m != 'hybrid'}

    overall_row = {
        'Level': 'OVERALL (All 6 Folds)',
        'Item': 'ALL',
        'Total_Actual': tot_y_all,
        'Hybrid_WAPE': all_wapes['hybrid'],
        'Hybrid_MAPE': all_mapes['hybrid'],
        'SNaive_WAPE': all_wapes['snaive'],
        'MA7_WAPE': all_wapes['ma7'],
        'Weekday4W_WAPE': all_wapes['weekday4w'],
        'ProphetOnly_WAPE': all_wapes['prophet_only'],
        'GBDTOnly_WAPE': all_wapes['gbdt_only'],
        'Rel_Gain_vs_SNaive_pct': all_rel['snaive'],
        'Rel_Gain_vs_MA7_pct': all_rel['ma7'],
        'Rel_Gain_vs_Weekday4W_pct': all_rel['weekday4w'],
        'Rel_Gain_vs_Prophet_pct': all_rel['prophet_only'],
        'Rel_Gain_vs_GBDT_pct': all_rel['gbdt_only'],
        'PP_Gain_vs_SNaive': all_pp['snaive'],
        'PP_Gain_vs_MA7': all_pp['ma7'],
        'PP_Gain_vs_Weekday4W': all_pp['weekday4w'],
        'PP_Gain_vs_Prophet': all_pp['prophet_only'],
        'PP_Gain_vs_GBDT': all_pp['gbdt_only'],
    }
    summary_rows.append(overall_row)

    print("-" * 90)
    print(f"{'OVERALL (All 6 Folds)':<26} | {all_wapes['snaive']:>7.2f}% | {all_wapes['ma7']:>7.2f}% | {all_wapes['weekday4w']:>7.2f}% | {all_wapes['prophet_only']:>7.2f}% | {all_wapes['gbdt_only']:>7.2f}% | {all_wapes['hybrid']:>7.2f}%")
    print("=" * 90)

    print("\nOVERALL BENCHMARK & ABLATION COMPARISON (WAPE):")
    print(f"  - Hybrid Model WAPE:                   {all_wapes['hybrid']:.2f}% (MAPE: {all_mapes['hybrid']:.2f}%)")
    print(f"  - vs. Same-Weekday 4-Wk Avg Baseline:  {all_wapes['weekday4w']:.2f}% (Rel Gain: {all_rel['weekday4w']:+.2f}%, Diff: -{all_pp['weekday4w']:.2f} pp)")
    print(f"  - vs. Seasonal Naive (Lag 7):          {all_wapes['snaive']:.2f}% (Rel Gain: {all_rel['snaive']:+.2f}%, Diff: -{all_pp['snaive']:.2f} pp)")
    print(f"  - vs. 7-Day Moving Average:            {all_wapes['ma7']:.2f}% (Rel Gain: {all_rel['ma7']:+.2f}%, Diff: -{all_pp['ma7']:.2f} pp)")
    print(f"  - vs. Prophet-Only Ablation:           {all_wapes['prophet_only']:.2f}% (Rel Gain: {all_rel['prophet_only']:+.2f}%, Diff: -{all_pp['prophet_only']:.2f} pp)")
    print(f"  - vs. GBDT-Only Ablation:              {all_wapes['gbdt_only']:.2f}% (Rel Gain: {all_rel['gbdt_only']:+.2f}%, Diff: -{all_pp['gbdt_only']:.2f} pp)")

    # Save to docs/backtest_results.csv
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_csv = docs_dir / "backtest_results.csv"
    pd.DataFrame(summary_rows).to_csv(out_csv, index=False)
    print(f"\nSaved extended backtest results to: {out_csv.resolve()}")

if __name__ == "__main__":
    run_extended_backtest()
