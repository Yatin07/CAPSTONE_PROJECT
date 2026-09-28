import pandas as pd
import numpy as np
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

df_orig['y_lag_7'] = df_orig.groupby('article')['y'].shift(7)
df_orig['y_lag_1'] = df_orig.groupby('article')['y'].shift(1)
df_orig['y_rolling_7_mean'] = df_orig.groupby('article')['y_lag_1'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
df_orig = df_orig.dropna().reset_index(drop=True)

# We already have the Prophet residuals in bakery_residuals.csv or we can just load the previous Prophet output.
# Actually I'll just re-run the fast XGBoost part for June split if I can load Prophet components from df_orig.
# Wait, Prophet features were in global_model_verification.py, they are computed on the fly. Let's just paste the fixed Prophet script.

from prophet import Prophet
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

# Ensure mapping works by keeping article as str for mapping
std_devs = df_merged[df_merged['ds'] < split_date].groupby('article')['y'].std().fillna(0).to_dict()

df_merged['article'] = df_merged['article'].astype('category')

train_df = df_merged[df_merged['ds'] < split_date].copy()
test_df = df_merged[df_merged['ds'] >= split_date].copy()

features = ['article', 'day_of_week', 'month', 'is_tourist_season', 'y_lag_1', 'y_lag_7', 'y_rolling_7_mean', 'trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season_prophet']
target = 'y'

model = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
model.fit(train_df[features], train_df[target])

test_df['y_pred_global'] = model.predict(test_df[features])
test_df['y_pred_global'] = np.maximum(test_df['y_pred_global'], 0)

# FIX: Map correctly using strings and convert to float
test_df['safety_stock'] = test_df['article'].astype(str).map(std_devs).astype(float) * 1.65

test_df['restock_model'] = np.maximum(0, test_df['y_pred_global'] + test_df['safety_stock']).round()
test_df['restock_snaive'] = np.maximum(0, test_df['y_lag_7'] + test_df['safety_stock']).round()
test_df['restock_ma7'] = np.maximum(0, test_df['y_rolling_7_mean'] + test_df['safety_stock']).round()

def simulate(forecast_col):
    sales = np.minimum(test_df['y'], test_df[forecast_col])
    waste = test_df[forecast_col] - sales
    stockouts = (test_df['y'] > test_df[forecast_col]).astype(int)
    return waste.sum(), stockouts.sum()

waste_model, so_model = simulate('restock_model')
waste_snaive, so_snaive = simulate('restock_snaive')
waste_ma7, so_ma7 = simulate('restock_ma7')

print("\n--- SIMULATION RESULTS (June-Sept 2022) ---")
print(f"Total Actual Sales (Demand): {test_df['y'].sum():.0f}")
print("1. Our Model (Prophet+XGB + Safety Stock)")
print(f"   Total Waste: {waste_model:.0f} units")
print(f"   Stockout Days: {so_model} days")

print("2. Seasonal Naive + Safety Stock")
print(f"   Total Waste: {waste_snaive:.0f} units")
print(f"   Stockout Days: {so_snaive} days")

print("3. 7-Day MA + Safety Stock")
print(f"   Total Waste: {waste_ma7:.0f} units")
print(f"   Stockout Days: {so_ma7} days")
