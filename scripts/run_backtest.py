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

def run_backtest():
    print("=" * 80)
    print("      RESTOCKIQ: ROLLING-ORIGIN BACKTEST (HYBRID VS NAIVE BASELINES)    ")
    print("=" * 80)

    # 1. Load data
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

    # 4 Rolling origin cutoffs (each 7-day test horizon)
    folds = [
        {"fold": 1, "cutoff": "2022-09-02", "start": "2022-09-03", "end": "2022-09-09"},
        {"fold": 2, "cutoff": "2022-09-09", "start": "2022-09-10", "end": "2022-09-16"},
        {"fold": 3, "cutoff": "2022-09-16", "start": "2022-09-17", "end": "2022-09-23"},
        {"fold": 4, "cutoff": "2022-09-23", "start": "2022-09-24", "end": "2022-09-30"},
    ]

    all_test_predictions = []

    for fold_info in folds:
        fold_num = fold_info["fold"]
        cutoff = pd.to_datetime(fold_info["cutoff"])
        start_date = pd.to_datetime(fold_info["start"])
        end_date = pd.to_datetime(fold_info["end"])

        print(f"\n--- Running Fold {fold_num}/4 | Cutoff: {cutoff.strftime('%Y-%m-%d')} | Horizon: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ---")

        # Split train and test
        df_train_raw = df_raw[df_raw['ds'] <= cutoff].copy()
        df_test_raw = df_raw[(df_raw['ds'] >= start_date) & (df_raw['ds'] <= end_date)].copy()

        # Step A: Fit Prophet per item on train data
        components_list = []
        unique_articles = df_raw['article'].unique()

        for item in unique_articles:
            train_item = df_train_raw[df_train_raw['article'] == item]
            if len(train_item) < 30:
                continue

            full_item = df_raw[df_raw['article'] == item]

            m = Prophet(seasonality_mode='multiplicative', yearly_seasonality=True, weekly_seasonality=True)
            m.add_country_holidays(country_name='FR')
            m.add_regressor('is_tourist_season')
            m.fit(train_item[['ds', 'y', 'is_tourist_season']])

            forecast = m.predict(full_item[['ds', 'is_tourist_season']])

            cols = ['ds', 'trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season', 'yhat']
            for c in ['weekly', 'yearly', 'holidays', 'is_tourist_season']:
                if c not in forecast.columns:
                    forecast[c] = 0.0

            res = forecast[cols].copy()
            res['article'] = item
            components_list.append(res)

        components_df = pd.concat(components_list, ignore_index=True)

        # Merge components with raw data
        df_merged = pd.merge(df_raw, components_df, on=['article', 'ds'], suffixes=('', '_prophet'))

        # Build lag features using only historical values
        df_merged['y_lag_1'] = df_merged.groupby('article')['y'].shift(1)
        df_merged['y_lag_7'] = df_merged.groupby('article')['y'].shift(7)
        df_merged['y_rolling_7_mean'] = df_merged.groupby('article')['y_lag_1'].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )

        df_merged['article'] = df_merged['article'].astype('category')

        # Split into train and test
        train_df = df_merged[df_merged['ds'] <= cutoff].dropna().copy()
        test_df = df_merged[(df_merged['ds'] >= start_date) & (df_merged['ds'] <= end_date)].dropna().copy()

        features = [
            'article', 'day_of_week', 'month', 'is_tourist_season',
            'y_lag_1', 'y_lag_7', 'y_rolling_7_mean',
            'trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season_prophet'
        ]
        target = 'y'

        # Fit global gradient boosting model
        model = HistGradientBoostingRegressor(
            categorical_features=[0],
            learning_rate=0.05,
            max_iter=200,
            max_depth=6,
            random_state=42
        )
        model.fit(train_df[features], train_df[target])

        # Generate predictions
        test_df['pred_hybrid'] = np.maximum(model.predict(test_df[features]), 0.0)
        test_df['pred_snaive'] = np.maximum(test_df['y_lag_7'], 0.0)
        test_df['pred_ma7'] = np.maximum(test_df['y_rolling_7_mean'], 0.0)
        test_df['fold'] = fold_num

        all_test_predictions.append(test_df[['fold', 'ds', 'article', 'y', 'pred_hybrid', 'pred_snaive', 'pred_ma7']])

    # Combine all folds
    eval_df = pd.concat(all_test_predictions, ignore_index=True)

    # Calculate absolute errors and percentage errors
    for m in ['hybrid', 'snaive', 'ma7']:
        eval_df[f'abs_err_{m}'] = (eval_df['y'] - eval_df[f'pred_{m}']).abs()
        # Non-zero safe MAPE calculation
        eval_df[f'ape_{m}'] = eval_df[f'abs_err_{m}'] / np.maximum(eval_df['y'], 1.0) * 100.0

    # Summary per fold
    print("\n" + "=" * 80)
    print("                       PER-FOLD PERFORMANCE SUMMARY                       ")
    print("=" * 80)
    print(f"{'Fold':<6} | {'Hybrid WAPE':>12} | {'SNaive WAPE':>12} | {'MA7 WAPE':>12} | {'Hybrid MAPE':>12} | {'SNaive MAPE':>12} | {'MA7 MAPE':>12}")
    print("-" * 88)

    fold_metrics = []
    for f in range(1, 5):
        sub = eval_df[eval_df['fold'] == f]
        tot_y = sub['y'].sum()

        wape_h = (sub['abs_err_hybrid'].sum() / tot_y) * 100.0
        wape_s = (sub['abs_err_snaive'].sum() / tot_y) * 100.0
        wape_m = (sub['abs_err_ma7'].sum() / tot_y) * 100.0

        mape_h = sub['ape_hybrid'].mean()
        mape_s = sub['ape_snaive'].mean()
        mape_m = sub['ape_ma7'].mean()

        fold_metrics.append({
            'Level': f'Fold {f}',
            'Item': 'ALL',
            'Total_Actual': tot_y,
            'Hybrid_WAPE': wape_h,
            'SNaive_WAPE': wape_s,
            'MA7_WAPE': wape_m,
            'Hybrid_MAPE': mape_h,
            'SNaive_MAPE': mape_s,
            'MA7_MAPE': mape_m,
            'WAPE_Gain_vs_SNaive': wape_s - wape_h,
            'WAPE_Gain_vs_MA7': wape_m - wape_h
        })

        print(f"Fold {f:<2} | {wape_h:>11.2f}% | {wape_s:>11.2f}% | {wape_m:>11.2f}% | {mape_h:>11.2f}% | {mape_s:>11.2f}% | {mape_m:>11.2f}%")

    # Overall across all folds
    tot_y_all = eval_df['y'].sum()
    overall_wape_h = (eval_df['abs_err_hybrid'].sum() / tot_y_all) * 100.0
    overall_wape_s = (eval_df['abs_err_snaive'].sum() / tot_y_all) * 100.0
    overall_wape_m = (eval_df['abs_err_ma7'].sum() / tot_y_all) * 100.0

    overall_mape_h = eval_df['ape_hybrid'].mean()
    overall_mape_s = eval_df['ape_snaive'].mean()
    overall_mape_m = eval_df['ape_ma7'].mean()

    fold_metrics.append({
        'Level': 'Overall (All Folds)',
        'Item': 'ALL',
        'Total_Actual': tot_y_all,
        'Hybrid_WAPE': overall_wape_h,
        'SNaive_WAPE': overall_wape_s,
        'MA7_WAPE': overall_wape_m,
        'Hybrid_MAPE': overall_mape_h,
        'SNaive_MAPE': overall_mape_s,
        'MA7_MAPE': overall_mape_m,
        'WAPE_Gain_vs_SNaive': overall_wape_s - overall_wape_h,
        'WAPE_Gain_vs_MA7': overall_wape_m - overall_wape_h
    })

    print("-" * 88)
    print(f"{'OVERALL':<6} | {overall_wape_h:>11.2f}% | {overall_wape_s:>11.2f}% | {overall_wape_m:>11.2f}% | {overall_mape_h:>11.2f}% | {overall_mape_s:>11.2f}% | {overall_mape_m:>11.2f}%")
    print(f"\nNet Architecture Gain: -{overall_wape_s - overall_wape_h:.2f}% WAPE vs Seasonal Naive, -{overall_wape_m - overall_wape_h:.2f}% WAPE vs 7-day MA")

    # Top 10 items performance
    print("\n" + "=" * 80)
    print("                     TOP 10 ITEMS PERFORMANCE (ALL FOLDS)                 ")
    print("=" * 80)
    print(f"{'Item':<24} | {'Volume':>7} | {'Hybrid WAPE':>12} | {'SNaive WAPE':>12} | {'MA7 WAPE':>12} | {'Hybrid Gain':>12}")
    print("-" * 88)

    top_items = eval_df.groupby('article')['y'].sum().sort_values(ascending=False).head(10).index

    item_metrics = []
    for item in top_items:
        sub_i = eval_df[eval_df['article'] == item]
        item_y = sub_i['y'].sum()

        w_h = (sub_i['abs_err_hybrid'].sum() / item_y) * 100.0
        w_s = (sub_i['abs_err_snaive'].sum() / item_y) * 100.0
        w_m = (sub_i['abs_err_ma7'].sum() / item_y) * 100.0

        m_h = sub_i['ape_hybrid'].mean()
        m_s = sub_i['ape_snaive'].mean()
        m_m = sub_i['ape_ma7'].mean()

        gain_s = w_s - w_h

        item_metrics.append({
            'Level': 'Item Top 10',
            'Item': item,
            'Total_Actual': item_y,
            'Hybrid_WAPE': w_h,
            'SNaive_WAPE': w_s,
            'MA7_WAPE': w_m,
            'Hybrid_MAPE': m_h,
            'SNaive_MAPE': m_s,
            'MA7_MAPE': m_m,
            'WAPE_Gain_vs_SNaive': gain_s,
            'WAPE_Gain_vs_MA7': w_m - w_h
        })

        print(f"{item:<24} | {item_y:>7.0f} | {w_h:>11.2f}% | {w_s:>11.2f}% | {w_m:>11.2f}% | {gain_s:>+11.2f}%")

    # Save to docs/backtest_results.csv
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_csv = docs_dir / "backtest_results.csv"

    all_summary_rows = fold_metrics + item_metrics
    summary_df = pd.DataFrame(all_summary_rows)
    summary_df.to_csv(out_csv, index=False)
    print(f"\nSaved backtest results to: {out_csv.resolve()}")

if __name__ == "__main__":
    run_backtest()
