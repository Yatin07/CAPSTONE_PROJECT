import pandas as pd
import numpy as np
from prophet import Prophet
import holidays
from sklearn.ensemble import HistGradientBoostingRegressor
import warnings
import sys

warnings.filterwarnings('ignore')

# 1. Load Data
df = pd.read_csv('E:/CAP/ML/data/processed/primary_items.csv')
df['ds'] = pd.to_datetime(df['ds'])
df = df.sort_values(['article', 'ds']).reset_index(drop=True)

# Generate basic features
df['day_of_week'] = df['ds'].dt.dayofweek
df['month'] = df['ds'].dt.month
df['is_tourist_season'] = df['month'].isin([7, 8]).astype(int)

# Lag features per item
df['y_lag_1'] = df.groupby('article')['y'].shift(1)
df['y_lag_7'] = df.groupby('article')['y'].shift(7)
df['y_rolling_7_mean'] = df.groupby('article')['y_lag_1'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())

df = df.dropna().reset_index(drop=True)

# 2 & 3. Run Prophet per item and extract components
print("Running Prophet to extract components...", file=sys.stderr)
components_list = []
for item, group in df.groupby('article'):
    m = Prophet(seasonality_mode='multiplicative')
    m.add_country_holidays(country_name='FR')
    m.add_regressor('is_tourist_season')
    
    # Fit Prophet
    m.fit(group[['ds', 'y', 'is_tourist_season']])
    
    # Predict to get components
    forecast = m.predict(group[['ds', 'is_tourist_season']])
    
    # Extract components (trend, yearly, weekly, is_tourist_season, holidays)
    cols_to_keep = ['ds', 'trend', 'weekly', 'yearly', 'is_tourist_season', 'holidays', 'yhat']
    # If yearly or holidays don't exist, fill with 0
    for col in ['weekly', 'yearly', 'holidays', 'is_tourist_season']:
        if col not in forecast.columns:
            forecast[col] = 0
            
    res = forecast[cols_to_keep].copy()
    res['article'] = group['article'].iloc[0]
    components_list.append(res)

components_df = pd.concat(components_list, ignore_index=True)

# Merge back
df_merged = pd.merge(df, components_df, on=['article', 'ds'], suffixes=('', '_prophet'))

# Ensure categorical for HistGradientBoostingRegressor
df_merged['article'] = df_merged['article'].astype('category')

# 4. Train/Test Split
train_df = df_merged[df_merged['ds'] < '2022-06-01'].copy()
test_df = df_merged[df_merged['ds'] >= '2022-06-01'].copy()

features = [
    'article', 'day_of_week', 'month', 'is_tourist_season', 
    'y_lag_1', 'y_lag_7', 'y_rolling_7_mean',
    'trend', 'weekly', 'yearly', 'holidays', 'is_tourist_season_prophet'
]
target = 'y'

# 5. Train Global Model
print("Training global HistGradientBoostingRegressor...", file=sys.stderr)
model = HistGradientBoostingRegressor(categorical_features=[0], learning_rate=0.05, max_iter=200, max_depth=6, random_state=42)
model.fit(train_df[features], train_df[target])

# Predict
test_df['y_pred_global'] = model.predict(test_df[features])
test_df['y_pred_global'] = np.maximum(test_df['y_pred_global'], 0) # No negative sales

# 6. Compute WAPE
results = []
for item in test_df['article'].unique():
    item_df = test_df[test_df['article'] == item]
    sum_y = item_df['y'].sum()
    if sum_y == 0:
        continue
        
    prophet_error = (item_df['y'] - item_df['yhat']).abs().sum()
    prophet_wape = (prophet_error / sum_y) * 100
    
    global_error = (item_df['y'] - item_df['y_pred_global']).abs().sum()
    global_wape = (global_error / sum_y) * 100
    
    mean_vol = item_df['y'].mean()
    test_rows = len(item_df)
    
    results.append({
        'Item': item,
        'Test Rows': test_rows,
        'Mean Daily Vol': mean_vol,
        'Prophet WAPE': prophet_wape,
        'Global Model WAPE': global_wape,
        'Delta': prophet_wape - global_wape
    })

res_df = pd.DataFrame(results)
res_df = res_df.sort_values('Mean Daily Vol', ascending=False)

# Overall WAPE (Volume weighted)
total_y = test_df['y'].sum()
total_prophet_err = (test_df['y'] - test_df['yhat']).abs().sum()
total_global_err = (test_df['y'] - test_df['y_pred_global']).abs().sum()

weighted_prophet = (total_prophet_err / total_y) * 100
weighted_global = (total_global_err / total_y) * 100

print(f"Volume-Weighted Prophet WAPE:  {weighted_prophet:.2f}%")
print(f"Volume-Weighted Global Model WAPE: {weighted_global:.2f}%")

print("\n| Item | Test Rows | Mean Daily Vol | Prophet WAPE | Global Model WAPE | Delta (Improvement) |")
print("| :--- | :--- | :--- | :--- | :--- | :--- |")
for _, r in res_df.iterrows():
    delta_str = f"**+{r['Delta']:.1f}%**" if r['Delta'] > 0 else f"{r['Delta']:.1f}%"
    print(f"| {r['Item']} | {int(r['Test Rows'])} | {r['Mean Daily Vol']:.1f} | {r['Prophet WAPE']:.1f}% | {r['Global Model WAPE']:.1f}% | {delta_str} |")
