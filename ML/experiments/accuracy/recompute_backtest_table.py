"""
Recompute seasonal naive, 4-week same-weekday average and MA7 with calendar alignment.
Rebuild every derived column in docs/backtest_results.csv.
"""
import pandas as pd, numpy as np
from pathlib import Path
from prophet import Prophet
from sklearn.ensemble import HistGradientBoostingRegressor
import warnings
warnings.filterwarnings('ignore')

FOLDS_6 = [
    {'fold': 1, 'name': 'Early Summer Ramp', 'cutoff': '2022-07-15', 'start': '2022-07-16', 'end': '2022-07-22'},
    {'fold': 2, 'name': 'Mid-Summer Peak',   'cutoff': '2022-07-29', 'start': '2022-07-30', 'end': '2022-08-05'},
    {'fold': 3, 'name': 'August Holiday',   'cutoff': '2022-08-12', 'start': '2022-08-13', 'end': '2022-08-19'},
    {'fold': 4, 'name': 'Late Summer Turn', 'cutoff': '2022-08-26', 'start': '2022-08-27', 'end': '2022-09-02'},
    {'fold': 5, 'name': 'Autumn Normal',    'cutoff': '2022-09-09', 'start': '2022-09-10', 'end': '2022-09-16'},
    {'fold': 6, 'name': 'Late September',   'cutoff': '2022-09-23', 'start': '2022-09-24', 'end': '2022-09-30'},
]

df = pd.read_csv('e:/CAP/ML/data/processed/primary_items.csv')
df['ds'] = pd.to_datetime(df['ds'])
df = df.sort_values(['article', 'ds']).reset_index(drop=True)
df['day_of_week'] = df['ds'].dt.dayofweek
df['month'] = df['ds'].dt.month
df['is_tourist_season'] = df['month'].isin([7, 8]).astype(int)

lookup = df.set_index(['article', 'ds'])['y'].to_dict()

# 1. Calendar-aligned Seasonal Naive: y(ds - 7d), if closed search previous same-weekdays
def get_snaive(art, d):
    for k in [1, 2, 3, 4, 5]:
        val = lookup.get((art, d - pd.Timedelta(days=7*k)))
        if val is not None and not np.isnan(val):
            return val
    return 0.0

# 2. Calendar-aligned 4-week weekday average (closure days excluded from denominator)
def get_weekday4w(art, d):
    vals = []
    for k in [1, 2, 3, 4]:
        v = lookup.get((art, d - pd.Timedelta(days=7*k)))
        if v is not None and not np.isnan(v):
            vals.append(v)
    return np.mean(vals) if len(vals) > 0 else 0.0

df['pred_snaive'] = [get_snaive(a, d) for a, d in zip(df['article'], df['ds'])]
df['pred_weekday4w'] = [get_weekday4w(a, d) for a, d in zip(df['article'], df['ds'])]

for k in [1, 2, 3, 4]:
    df[f'y_lag_{7*k}_cal'] = [lookup.get((art, d - pd.Timedelta(days=7*k)), np.nan) for art, d in zip(df['article'], df['ds'])]

eval_records = []
prophet_cols = ['trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season_prophet', 'yhat']
lag_feats = ['day_of_week', 'month', 'is_tourist_season', 'y_lag_7_cal', 'pred_weekday4w']

for f in FOLDS_6:
    cutoff = pd.to_datetime(f['cutoff'])
    s_date = pd.to_datetime(f['start'])
    e_date = pd.to_datetime(f['end'])
    f_num = f['fold']
    
    tr = df[df['ds'] <= cutoff].copy()
    
    p_list = []
    for item, group in tr.groupby('article'):
        if len(group) < 30: continue
        m = Prophet(seasonality_mode='multiplicative', yearly_seasonality=True, weekly_seasonality=True)
        m.add_country_holidays(country_name='FR')
        m.add_regressor('is_tourist_season')
        m.fit(group[['ds', 'y', 'is_tourist_season']])
        full_item = df[(df['article'] == item) & (df['ds'] <= e_date)]
        fc = m.predict(full_item[['ds', 'is_tourist_season']])
        for c in ['trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season', 'yhat']:
            if c not in fc.columns: fc[c] = 0.0
        r = fc[['ds', 'trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season', 'yhat']].copy()
        r['article'] = item
        p_list.append(r)
        
    df_p = pd.concat(p_list, ignore_index=True)
    merged = pd.merge(df[df['ds'] <= e_date], df_p, on=['article', 'ds'], suffixes=('', '_prophet'))
    merged['article_cat'] = merged['article'].astype('category')
    
    tr_set = merged[merged['ds'] <= cutoff].dropna(subset=['article_cat'] + lag_feats + prophet_cols + ['y']).copy()
    te_set = merged[(merged['ds'] >= s_date) & (merged['ds'] <= e_date)].copy()
    
    # GBDT-only
    gbdt_only = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
    gbdt_only.fit(tr_set[['article_cat'] + lag_feats], tr_set['y'])
    te_set['pred_gbdt_only'] = np.maximum(gbdt_only.predict(te_set[['article_cat'] + lag_feats]), 0.0)
    
    # Hybrid
    gbdt_hy = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
    gbdt_hy.fit(tr_set[['article_cat'] + lag_feats + prophet_cols], tr_set['y'])
    te_set['pred_hybrid'] = np.maximum(gbdt_hy.predict(te_set[['article_cat'] + lag_feats + prophet_cols]), 0.0)
    te_set['pred_prophet_only'] = np.maximum(te_set['yhat'], 0.0)
    
    ma7_dict = tr.groupby('article').apply(lambda x: x.sort_values('ds').tail(7)['y'].mean(), include_groups=False).to_dict()
    te_set['pred_ma7'] = te_set['article'].map(ma7_dict).fillna(0.0)
    
    te_set['fold'] = f_num
    te_set['fold_name'] = f['name']
    eval_records.append(te_set)

full_eval = pd.concat(eval_records, ignore_index=True)

# Build rows
res_rows = []
models = ['hybrid', 'snaive', 'ma7', 'weekday4w', 'prophet_only', 'gbdt_only']

for f in FOLDS_6:
    sub = full_eval[full_eval['fold'] == f['fold']]
    tot_y = sub['y'].sum()
    wapes = {m: (np.sum(np.abs(sub['y'] - sub[f'pred_{m}'])) / tot_y) * 100.0 for m in models}
    mapes = {m: np.mean(np.abs(sub['y'] - sub[f'pred_{m}']) / np.maximum(sub['y'], 1.0)) * 100.0 for m in models}
    
    rel_gains = {m: ((wapes[m] - wapes['hybrid']) / wapes[m]) * 100.0 if wapes[m] > 0 else 0.0 for m in models if m != 'hybrid'}
    pp_gains  = {m: wapes[m] - wapes['hybrid'] for m in models if m != 'hybrid'}
    
    row = {
        'Level': f"Fold {f['fold']}: {f['name']}",
        'Version': 'Corrected (Calendar-Aligned Lags & Baselines)',
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
    res_rows.append(row)

# Overall
tot_y_all = full_eval['y'].sum()
wapes_all = {m: (np.sum(np.abs(full_eval['y'] - full_eval[f'pred_{m}'])) / tot_y_all) * 100.0 for m in models}
mapes_all = {m: np.mean(np.abs(full_eval['y'] - full_eval[f'pred_{m}']) / np.maximum(full_eval['y'], 1.0)) * 100.0 for m in models}
rel_gains_all = {m: ((wapes_all[m] - wapes_all['hybrid']) / wapes_all[m]) * 100.0 if wapes_all[m] > 0 else 0.0 for m in models if m != 'hybrid'}
pp_gains_all  = {m: wapes_all[m] - wapes_all['hybrid'] for m in models if m != 'hybrid'}

row_ov = {
    'Level': 'OVERALL (All 6 Folds)',
    'Version': 'Corrected (Calendar-Aligned Lags & Baselines)',
    'Item': 'ALL',
    'Total_Actual': tot_y_all,
    'Hybrid_WAPE': wapes_all['hybrid'],
    'Hybrid_MAPE': mapes_all['hybrid'],
    'SNaive_WAPE': wapes_all['snaive'],
    'MA7_WAPE': wapes_all['ma7'],
    'Weekday4W_WAPE': wapes_all['weekday4w'],
    'ProphetOnly_WAPE': wapes_all['prophet_only'],
    'GBDTOnly_WAPE': wapes_all['gbdt_only'],
    'Rel_Gain_vs_SNaive_pct': rel_gains_all['snaive'],
    'Rel_Gain_vs_MA7_pct': rel_gains_all['ma7'],
    'Rel_Gain_vs_Weekday4W_pct': rel_gains_all['weekday4w'],
    'Rel_Gain_vs_Prophet_pct': rel_gains_all['prophet_only'],
    'Rel_Gain_vs_GBDT_pct': rel_gains_all['gbdt_only'],
    'PP_Gain_vs_SNaive': pp_gains_all['snaive'],
    'PP_Gain_vs_MA7': pp_gains_all['ma7'],
    'PP_Gain_vs_Weekday4W': pp_gains_all['weekday4w'],
    'PP_Gain_vs_Prophet': pp_gains_all['prophet_only'],
    'PP_Gain_vs_GBDT': pp_gains_all['gbdt_only'],
}
res_rows.append(row_ov)

df_corr = pd.DataFrame(res_rows)

# Read original file to print diff
old_path = Path('e:/CAP/docs/backtest_results.csv')
old_df = pd.read_csv(old_path)

# Retain original rows
orig_rows = old_df[old_df['Version'].str.contains('Original')].copy()

# Combine
final_df = pd.concat([orig_rows, df_corr], ignore_index=True)
final_df.to_csv(old_path, index=False)
print("Updated backtest_results.csv successfully.")

print("\n--- DIFF OF CORRECTED ROWS (PREVIOUS VS FULLY CALENDAR-ALIGNED) ---")
prev_corr = old_df[old_df['Version'].str.contains('Corrected')].set_index('Level')
new_corr = df_corr.set_index('Level')

for metric in ['Hybrid_WAPE', 'Hybrid_MAPE', 'SNaive_WAPE', 'Weekday4W_WAPE', 'MA7_WAPE', 'PP_Gain_vs_SNaive', 'PP_Gain_vs_Weekday4W', 'PP_Gain_vs_Prophet']:
    print(f"\nMetric: {metric}")
    for idx in new_corr.index:
        p_val = prev_corr.loc[idx, metric] if idx in prev_corr.index and metric in prev_corr.columns else np.nan
        n_val = new_corr.loc[idx, metric]
        diff = n_val - p_val
        print(f"  {idx:<28} | Prev: {p_val:>8.2f}% | New: {n_val:>8.2f}% | Diff: {diff:>+7.2f} pp")
