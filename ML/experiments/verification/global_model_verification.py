import pandas as pd
import numpy as np
from prophet import Prophet
import holidays
from sklearn.ensemble import HistGradientBoostingRegressor
import warnings
import sys
import logging

logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

df_orig = pd.read_csv('E:/CAP/ML/data/processed/primary_items.csv')
df_orig['ds'] = pd.to_datetime(df_orig['ds'])
df_orig = df_orig.sort_values(['article', 'ds']).reset_index(drop=True)

df_orig['day_of_week'] = df_orig['ds'].dt.dayofweek
df_orig['month'] = df_orig['ds'].dt.month
df_orig['is_tourist_season'] = df_orig['month'].isin([7, 8]).astype(int)

df_orig['y_lag_1'] = df_orig.groupby('article')['y'].shift(1)
df_orig['y_lag_7'] = df_orig.groupby('article')['y'].shift(7)
df_orig['y_rolling_7_mean'] = df_orig.groupby('article')['y_lag_1'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
df_orig = df_orig.dropna().reset_index(drop=True)

splits = ['2022-06-01', '2022-05-01']

for split_date in splits:
    print(f"\n{'='*50}\nRUNNING FOR SPLIT: {split_date}\n{'='*50}", file=sys.stderr)
    df = df_orig.copy()
    
    components_list = []
    print("Running Prophet on training split...", file=sys.stderr)
    for item, group in df.groupby('article'):
        train_group = group[group['ds'] < split_date]
        if len(train_group) < 30:
            continue
            
        m = Prophet(seasonality_mode='multiplicative')
        m.add_country_holidays(country_name='FR')
        m.add_regressor('is_tourist_season')
        
        m.fit(train_group[['ds', 'y', 'is_tourist_season']])
        
        forecast = m.predict(group[['ds', 'is_tourist_season']])
        
        cols_to_keep = ['ds', 'trend', 'weekly', 'yearly', 'is_tourist_season', 'holidays', 'yhat']
        for col in ['weekly', 'yearly', 'holidays', 'is_tourist_season']:
            if col not in forecast.columns:
                forecast[col] = 0
                
        res = forecast[cols_to_keep].copy()
        res['article'] = item
        components_list.append(res)
        
    components_df = pd.concat(components_list, ignore_index=True)
    df_merged = pd.merge(df, components_df, on=['article', 'ds'], suffixes=('', '_prophet'))
    df_merged['article'] = df_merged['article'].astype('category')
    
    train_df = df_merged[df_merged['ds'] < split_date].copy()
    test_df = df_merged[df_merged['ds'] >= split_date].copy()
    
    features = [
        'article', 'day_of_week', 'month', 'is_tourist_season', 
        'y_lag_1', 'y_lag_7', 'y_rolling_7_mean',
        'trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season_prophet'
    ]
    target = 'y'
    
    print("Training global HistGradientBoostingRegressor...", file=sys.stderr)
    model = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
    model.fit(train_df[features], train_df[target])
    
    test_df['y_pred_global'] = model.predict(test_df[features])
    test_df['y_pred_global'] = np.maximum(test_df['y_pred_global'], 0)
    
    total_y = test_df['y'].sum()
    total_prophet_err = (test_df['y'] - test_df['yhat']).abs().sum()
    total_global_err = (test_df['y'] - test_df['y_pred_global']).abs().sum()
    
    weighted_prophet = (total_prophet_err / total_y) * 100
    weighted_global = (total_global_err / total_y) * 100
    
    print(f"\n--- RESULTS FOR SPLIT {split_date} ---")
    print(f"Volume-Weighted Prophet WAPE (Out-of-sample):  {weighted_prophet:.2f}%")
    print(f"Volume-Weighted Global Model WAPE:             {weighted_global:.2f}%")
    
    if split_date == '2022-06-01':
        results = []
        for item in test_df['article'].unique():
            item_df = test_df[test_df['article'] == item]
            sum_y = item_df['y'].sum()
            if sum_y == 0: continue
            
            p_wape = ((item_df['y'] - item_df['yhat']).abs().sum() / sum_y) * 100
            g_wape = ((item_df['y'] - item_df['y_pred_global']).abs().sum() / sum_y) * 100
            mean_vol = item_df['y'].mean()
            
            results.append({
                'Item': item,
                'Vol': mean_vol,
                'Prophet WAPE': p_wape,
                'Global WAPE': g_wape,
                'Delta': p_wape - g_wape
            })
            
        res_df = pd.DataFrame(results).sort_values('Vol', ascending=False)
        print("\n| Item | Mean Daily Vol | Prophet WAPE | Global Model WAPE | Delta |")
        print("| :--- | :--- | :--- | :--- | :--- |")
        for _, r in res_df.iterrows():
            d_str = f"**+{r['Delta']:.1f}%**" if r['Delta'] > 0 else f"{r['Delta']:.1f}%"
            print(f"| {r['Item']} | {r['Vol']:.1f} | {r['Prophet WAPE']:.1f}% | {r['Global WAPE']:.1f}% | {d_str} |")
