import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')

# 1. Load data
df = pd.read_csv('E:/CAP/ML/data/processed/sparse_items.csv')
df['ds'] = pd.to_datetime(df['ds'])

with open('E:/CAP/ML/data/processed/sparse_categories.json', 'r') as f:
    categories = json.load(f)

item_to_category = {}
for cat, items in categories.items():
    for item in items:
        item_to_category[item] = cat

df['category'] = df['article'].map(item_to_category)
valid_cats = ['Breads & Baguettes', 'Viennoiserie', 'Patisserie / Desserts', 'Savory Food / Lunch', 'Beverages & Sweets']
df = df[df['category'].isin(valid_cats)]

# Define train/test split (same as primary items, test from 2022-07-01)
split_date = pd.to_datetime('2022-07-01')

# Prepare full continuous series with zeros
min_date = df['ds'].min()
max_date = df['ds'].max()
all_dates = pd.date_range(min_date, max_date, freq='D')

reindexed_list = []
for article, group in df.groupby('article'):
    cat = group['category'].iloc[0]
    group = group.set_index('ds').reindex(all_dates)
    group['article'] = article
    group['category'] = cat
    group['y'] = group['y'].fillna(0)
    group = group.rename_axis('ds').reset_index()
    reindexed_list.append(group)

df_filled = pd.concat(reindexed_list, ignore_index=True)
df_filled['day_of_week'] = df_filled['ds'].dt.dayofweek

df_train = df_filled[df_filled['ds'] < split_date]
df_test = df_filled[df_filled['ds'] >= split_date]

# Calculate Category Priors on Train
def q90(x):
    return x.quantile(0.90)

cat_priors = df_train.groupby(['category', 'day_of_week'])['y'].apply(q90).reset_index(name='p90_vol')

def tsb_forecast(series, alpha=0.1, beta=0.1):
    # series is a 1D numpy array of historical daily sales (including 0s)
    n = len(series)
    
    # Initialize
    z = np.zeros(n) # Demand size
    p = np.zeros(n) # Probability of demand
    
    # Initial values (simple heuristics)
    non_zero = series[series > 0]
    if len(non_zero) == 0:
        return 0.0 # No demand ever
        
    z[0] = non_zero[0]
    p[0] = len(non_zero) / n
    
    for t in range(1, n):
        if series[t] > 0:
            z[t] = alpha * series[t] + (1 - alpha) * z[t-1]
            p[t] = beta * 1 + (1 - beta) * p[t-1]
        else:
            z[t] = z[t-1]
            p[t] = beta * 0 + (1 - beta) * p[t-1]
            
    # Forecast for next period is P * Z
    return p[-1] * z[-1]

# Backtest
results = []

for article in df_filled['article'].unique():
    cat = df_train[df_train['article'] == article]['category'].iloc[0]
    item_train = df_train[df_train['article'] == article].sort_values('ds')
    item_test = df_test[df_test['article'] == article].sort_values('ds')
    
    if len(item_test) == 0 or len(item_train) == 0:
        continue
        
    # Get TSB forecast based on train
    train_y = item_train['y'].values
    # Predict a flat TSB rate for the test period
    tsb_pred = tsb_forecast(train_y, alpha=0.2, beta=0.2)
    
    # Get Category Prior for the test period
    cat_prior_map = cat_priors[cat_priors['category'] == cat].set_index('day_of_week')['p90_vol'].to_dict()
    
    actuals = item_test['y'].values
    dows = item_test['day_of_week'].values
    prior_preds = np.array([cat_prior_map.get(d, 0) for d in dows])
    tsb_preds = np.full(len(actuals), tsb_pred)
    
    mae_tsb = np.mean(np.abs(actuals - tsb_preds))
    mae_prior = np.mean(np.abs(actuals - prior_preds))
    
    sum_actual = np.sum(actuals)
    
    results.append({
        'article': article,
        'category': cat,
        'sum_actual': sum_actual,
        'mae_tsb': mae_tsb,
        'mae_prior': mae_prior,
        'sum_abs_err_tsb': np.sum(np.abs(actuals - tsb_preds)),
        'sum_abs_err_prior': np.sum(np.abs(actuals - prior_preds))
    })

res_df = pd.DataFrame(results)
total_actual = res_df['sum_actual'].sum()
wape_tsb = res_df['sum_abs_err_tsb'].sum() / total_actual
wape_prior = res_df['sum_abs_err_prior'].sum() / total_actual

print("=== Sparse Item Backtest (Test Period: July - Sept 2022) ===")
print(f"Total Test Actuals (Sparse Items): {total_actual}")
print(f"\nGlobal WAPE - TSB Method: {wape_tsb:.2%}")
print(f"Global WAPE - Category 90th Percentile: {wape_prior:.2%}")

print("\nAverage MAE per item - TSB: {:.4f}".format(res_df['mae_tsb'].mean()))
print("Average MAE per item - Prior: {:.4f}".format(res_df['mae_prior'].mean()))

# Number of items where TSB beats Prior
beats = (res_df['mae_tsb'] < res_df['mae_prior']).sum()
print(f"\nTSB improved accuracy on {beats} out of {len(res_df)} items.")
