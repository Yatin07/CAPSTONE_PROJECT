import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')

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

split_date = pd.to_datetime('2022-07-01')

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

def q90(x):
    return x.quantile(0.90)
cat_priors = df_train.groupby(['category', 'day_of_week'])['y'].apply(q90).reset_index(name='p90_vol')

def tsb_forecast(series, alpha=0.2, beta=0.2):
    n = len(series)
    z = np.zeros(n)
    p = np.zeros(n)
    non_zero = series[series > 0]
    if len(non_zero) == 0:
        return 0.0
    z[0] = non_zero[0]
    p[0] = len(non_zero) / n
    for t in range(1, n):
        if series[t] > 0:
            z[t] = alpha * series[t] + (1 - alpha) * z[t-1]
            p[t] = beta * 1 + (1 - beta) * p[t-1]
        else:
            z[t] = z[t-1]
            p[t] = beta * 0 + (1 - beta) * p[t-1]
    return p[-1] * z[-1]

results = []
THRESHOLD = 0.05

for article in df_filled['article'].unique():
    cat = df_train[df_train['article'] == article]['category'].iloc[0]
    item_train = df_train[df_train['article'] == article].sort_values('ds')
    item_test = df_test[df_test['article'] == article].sort_values('ds')
    
    if len(item_test) == 0 or len(item_train) == 0:
        continue
        
    train_y = item_train['y'].values
    tsb_pred = tsb_forecast(train_y)
    
    cat_prior_map = cat_priors[cat_priors['category'] == cat].set_index('day_of_week')['p90_vol'].to_dict()
    
    actuals = item_test['y'].values
    dows = item_test['day_of_week'].values
    prior_preds = np.array([cat_prior_map.get(d, 0) for d in dows])
    tsb_preds = np.full(len(actuals), tsb_pred)
    
    mae_tsb = np.mean(np.abs(actuals - tsb_preds))
    mae_prior = np.mean(np.abs(actuals - prior_preds))
    
    diff = mae_prior - mae_tsb # positive means TSB has lower MAE (better)
    
    if diff > THRESHOLD:
        status = 'TSB_WIN'
    elif diff < -THRESHOLD:
        status = 'TSB_LOSS'
    else:
        status = 'TIE'
        
    results.append({
        'article': article,
        'category': cat,
        'mae_tsb': mae_tsb,
        'mae_prior': mae_prior,
        'diff': diff,
        'status': status
    })

res_df = pd.DataFrame(results)

print("=== Win/Loss using 0.05 Threshold ===")
counts = res_df['status'].value_counts()
print(f"TSB Meaningful Wins: {counts.get('TSB_WIN', 0)}")
print(f"Meaningful Ties (diff <= 0.05): {counts.get('TIE', 0)}")
print(f"TSB Meaningful Losses: {counts.get('TSB_LOSS', 0)}")

