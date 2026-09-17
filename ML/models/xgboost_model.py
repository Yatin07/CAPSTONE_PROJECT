import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error

print("Loading Prophet out-of-fold residuals...")
df = pd.read_csv('data/processed/bakery_residuals.csv')
df['ds'] = pd.to_datetime(df['ds'])
df = df.sort_values(['article', 'ds'])

print("Engineering Features (Lags & Calendar)...")
# Calendar features
df['day_of_week'] = df['ds'].dt.dayofweek
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['month'] = df['ds'].dt.month
df['is_tourist_season'] = df['month'].isin([7, 8]).astype(int)

# Lag features grouped by article (using shift(1) to avoid data leakage)
df['y_lag_1'] = df.groupby('article')['y'].shift(1)
df['y_lag_7'] = df.groupby('article')['y'].shift(7)
df['y_rolling_7_mean'] = df.groupby('article')['y'].shift(1).rolling(window=7, min_periods=1).mean()
df['residual_lag_1'] = df.groupby('article')['residual'].shift(1)

# Drop rows with NaNs from lags
df = df.dropna().copy()

features = ['yhat', 'day_of_week', 'is_weekend', 'month', 'is_tourist_season', 'y_lag_1', 'y_lag_7', 'y_rolling_7_mean', 'residual_lag_1']
target = 'residual'

# Train/Test Split (Temporal split to prevent leakage)
split_date = '2022-06-01'
train_df = df[df['ds'] < split_date].copy()
test_df = df[df['ds'] >= split_date].copy()

print(f"Training XGBoost on {len(train_df)} rows... (Testing on {len(test_df)} rows)")

X_train = train_df[features]
y_train = train_df[target]
X_test = test_df[features]
y_test = test_df[target]

# Train the model
model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# Predict residuals on the test set
test_df['predicted_residual'] = model.predict(X_test)

# Final ensemble prediction
test_df['final_yhat'] = test_df['yhat'] + test_df['predicted_residual']
test_df['final_yhat'] = np.maximum(test_df['final_yhat'], 0) # Prevent negatives

# Calculate WAPE for comparison
print("\n--- FINAL EVALUATION: PROPHET vs PROPHET+XGBOOST (Test Set Only) ---")
results = []
for item in test_df['article'].unique():
    item_df = test_df[test_df['article'] == item]
    
    sum_y = item_df['y'].sum()
    if sum_y == 0: continue
        
    prophet_wape = (item_df['residual'].abs().sum() / sum_y) * 100
    
    ensemble_error = (item_df['y'] - item_df['final_yhat']).abs().sum()
    ensemble_wape = (ensemble_error / sum_y) * 100
    
    results.append({
        'Item': item,
        'Prophet_WAPE': prophet_wape,
        'Ensemble_WAPE': ensemble_wape,
        'Improvement': prophet_wape - ensemble_wape
    })

res_df = pd.DataFrame(results)
res_df = res_df.sort_values('Improvement', ascending=False)

print(f"\nTop 10 Improved Items:")
print(f"{'Item':<25} | {'Prophet WAPE':>13} | {'Ensemble WAPE':>13} | {'Improvement':>12}")
print("-" * 70)
for _, row in res_df.head(10).iterrows():
    print(f"{row['Item']:<25} | {row['Prophet_WAPE']:>12.2f}% | {row['Ensemble_WAPE']:>12.2f}% | -{row['Improvement']:>11.2f}%")

avg_prophet = res_df['Prophet_WAPE'].mean()
avg_ensemble = res_df['Ensemble_WAPE'].mean()

print(f"\nOVERALL AVERAGE (All items in Test Set):")
print(f"Prophet-Only WAPE:     {avg_prophet:.2f}%")
print(f"Prophet+XGBoost WAPE:  {avg_ensemble:.2f}%")
print(f"Total Architecture Gain: -{avg_prophet - avg_ensemble:.2f}% absolute improvement")
