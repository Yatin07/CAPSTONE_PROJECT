import pandas as pd
import numpy as np
from prophet import Prophet
import holidays
from sklearn.ensemble import HistGradientBoostingRegressor
import warnings

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

split_date = '2022-06-01'
df = df_orig.copy()

components_list = []
for item, group in df.groupby('article'):
    train_group = group[group['ds'] < split_date]
    if len(train_group) < 30: continue
    
    m = Prophet(seasonality_mode='multiplicative')
    m.add_country_holidays(country_name='FR')
    m.add_regressor('is_tourist_season')
    m.fit(train_group[['ds', 'y', 'is_tourist_season']])
    forecast = m.predict(group[['ds', 'is_tourist_season']])
    
    cols_to_keep = ['ds', 'trend', 'weekly', 'yearly', 'is_tourist_season', 'holidays', 'yhat']
    for col in ['weekly', 'yearly', 'holidays', 'is_tourist_season']:
        if col not in forecast.columns: forecast[col] = 0
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

model = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
model.fit(train_df[features], train_df[target])

test_df['y_pred_global'] = model.predict(test_df[features])
test_df['y_pred_global'] = np.maximum(test_df['y_pred_global'], 0)

brioche = test_df[test_df['article'] == 'BRIOCHE'][['ds', 'y', 'yhat', 'y_pred_global']].copy()
brioche['prophet_err'] = (brioche['y'] - brioche['yhat']).abs()
brioche['global_err'] = (brioche['y'] - brioche['y_pred_global']).abs()
brioche['diff'] = brioche['prophet_err'] - brioche['global_err'] # Positive means global is better

print("--- BRIOCHE TOP 10 LARGEST PROPHET ERRORS ---")
print(brioche.sort_values('prophet_err', ascending=False).head(10).to_string(index=False))

print("\n--- BRIOCHE SUMMARY ---")
print(f"Total Sales in Test: {brioche['y'].sum()}")
print(f"Total Prophet Abs Error: {brioche['prophet_err'].sum():.1f}")
print(f"Total Global Abs Error: {brioche['global_err'].sum():.1f}")
