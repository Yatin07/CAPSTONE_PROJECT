import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance

df = pd.read_csv('E:/CAP/ML/data/processed/bakery_residuals.csv')
df['ds'] = pd.to_datetime(df['ds'])
df = df.sort_values(['article', 'ds'])

df['day_of_week'] = df['ds'].dt.dayofweek
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['month'] = df['ds'].dt.month
df['is_tourist_season'] = df['month'].isin([7, 8]).astype(int)

df['y_lag_1'] = df.groupby('article')['y'].shift(1)
df['y_lag_7'] = df.groupby('article')['y'].shift(7)
df['y_rolling_7_mean'] = df.groupby('article')['y'].shift(1).rolling(window=7, min_periods=1).mean()
df['residual_lag_1'] = df.groupby('article')['residual'].shift(1)

df = df.dropna().copy()
features = ['yhat', 'day_of_week', 'is_weekend', 'month', 'is_tourist_season', 'y_lag_1', 'y_lag_7', 'y_rolling_7_mean', 'residual_lag_1']
target = 'residual'

# 1. Feature Importance for Traditional Baguette
print("--- TRADITIONAL BAGUETTE: FEATURE IMPORTANCE (Split 2022-06-01) ---")
item_df = df[df['article'] == 'TRADITIONAL BAGUETTE'].copy()
train_df = item_df[item_df['ds'] < '2022-06-01']
test_df = item_df[item_df['ds'] >= '2022-06-01']

model = HistGradientBoostingRegressor(learning_rate=0.05, max_iter=100, max_depth=4, random_state=42)
model.fit(train_df[features], train_df[target])
result = permutation_importance(model, train_df[features], train_df[target], n_repeats=10, random_state=42)

for i in result.importances_mean.argsort()[::-1]:
    print(f"{features[i]:<20} : {result.importances_mean[i]:.4f}")


# 2. Split 2022-05-01 for Traditional Baguette
print("\n--- TRADITIONAL BAGUETTE: ALTERNATE SPLIT (2022-05-01) ---")
train_df2 = item_df[item_df['ds'] < '2022-05-01']
test_df2 = item_df[item_df['ds'] >= '2022-05-01']

model2 = HistGradientBoostingRegressor(learning_rate=0.05, max_iter=100, max_depth=4, random_state=42)
model2.fit(train_df2[features], train_df2[target])
test_df2_copy = test_df2.copy()
test_df2_copy['predicted_residual'] = model2.predict(test_df2_copy[features])
test_df2_copy['final_yhat'] = np.maximum(test_df2_copy['yhat'] + test_df2_copy['predicted_residual'], 0)

sum_y = test_df2_copy['y'].sum()
prophet_wape = (test_df2_copy['residual'].abs().sum() / sum_y) * 100
ensemble_error = (test_df2_copy['y'] - test_df2_copy['final_yhat']).abs().sum()
ensemble_wape = (ensemble_error / sum_y) * 100

print(f"Prophet WAPE:  {prophet_wape:.2f}%")
print(f"Ensemble WAPE: {ensemble_wape:.2f}%")
print(f"Delta:         {prophet_wape - ensemble_wape:.2f}%")


# 3. Volume-Weighted WAPE for all 35 items
print("\n--- VOLUME-WEIGHTED WAPE (All 35 Items, Split 2022-06-01) ---")
total_y = 0
total_prophet_err = 0
total_ensemble_err = 0

for item in df['article'].unique():
    item_df = df[df['article'] == item].copy()
    train_df = item_df[item_df['ds'] < '2022-06-01']
    test_df = item_df[item_df['ds'] >= '2022-06-01']
    
    if len(train_df) < 50 or len(test_df) < 10:
        continue
        
    m = HistGradientBoostingRegressor(learning_rate=0.05, max_iter=100, max_depth=4, random_state=42)
    m.fit(train_df[features], train_df[target])
    
    test_df['predicted_residual'] = m.predict(test_df[features])
    test_df['final_yhat'] = np.maximum(test_df['yhat'] + test_df['predicted_residual'], 0)
    
    total_y += test_df['y'].sum()
    total_prophet_err += test_df['residual'].abs().sum()
    total_ensemble_err += (test_df['y'] - test_df['final_yhat']).abs().sum()

weighted_prophet = (total_prophet_err / total_y) * 100
weighted_ensemble = (total_ensemble_err / total_y) * 100

print(f"Volume-Weighted Prophet WAPE:  {weighted_prophet:.2f}%")
print(f"Volume-Weighted Ensemble WAPE: {weighted_ensemble:.2f}%")
