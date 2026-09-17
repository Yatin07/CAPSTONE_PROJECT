import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

df = pd.read_csv('E:/CAP/ML/data/processed/bakery_residuals.csv')
df['ds'] = pd.to_datetime(df['ds'])
df = df.sort_values(['article', 'ds'])

# 1. Yes, lags are safely grouped by article!
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
split_date = '2022-06-01'

results = []

for item in df['article'].unique():
    item_df = df[df['article'] == item].copy()
    
    train_df = item_df[item_df['ds'] < split_date].copy()
    test_df = item_df[item_df['ds'] >= split_date].copy()
    
    # Track test rows
    test_rows = len(test_df)
    
    if len(train_df) < 50 or test_rows < 10:
        continue
        
    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    model = HistGradientBoostingRegressor(learning_rate=0.05, max_iter=100, max_depth=4, random_state=42)
    model.fit(X_train, y_train)
    
    test_df['predicted_residual'] = model.predict(X_test)
    test_df['final_yhat'] = np.maximum(test_df['yhat'] + test_df['predicted_residual'], 0)
    
    sum_y = test_df['y'].sum()
    if sum_y > 0:
        prophet_wape = (test_df['residual'].abs().sum() / sum_y) * 100
        ensemble_error = (test_df['y'] - test_df['final_yhat']).abs().sum()
        ensemble_wape = (ensemble_error / sum_y) * 100
        
        results.append({
            'Item': item,
            'Test_Rows': test_rows,
            'Mean_Vol': test_df['y'].mean(),
            'Prophet_WAPE': prophet_wape,
            'Ensemble_WAPE': ensemble_wape,
            'Delta': prophet_wape - ensemble_wape
        })

res_df = pd.DataFrame(results)
res_df = res_df.sort_values('Mean_Vol', ascending=False)

print("\n--- FULL 35-ITEM RESULTS (Sorted by Volume) ---")
print(f"{'Item':<25} | {'TestRows':>8} | {'MeanVol':>8} | {'Prophet%':>10} | {'EnsWAPE%':>10} | {'Delta':>8}")
print("-" * 80)
for _, row in res_df.iterrows():
    print(f"{row['Item']:<25} | {row['Test_Rows']:>8} | {row['Mean_Vol']:>8.1f} | {row['Prophet_WAPE']:>9.1f}% | {row['Ensemble_WAPE']:>9.1f}% | {row['Delta']:>7.1f}%")

avg_prophet = res_df['Prophet_WAPE'].mean()
avg_ensemble = res_df['Ensemble_WAPE'].mean()

print(f"\nOVERALL AVERAGE (Unweighted):")
print(f"Prophet: {avg_prophet:.1f}% | Ensemble: {avg_ensemble:.1f}%")
