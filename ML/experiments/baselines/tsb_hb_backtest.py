import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')
from scipy.special import digamma

# Load Data
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

# Reindex
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

# Calculate Empirical Bayes Priors per Category
# Probability: Beta(alpha, beta)
# Size (Log-Normal): Normal(mu0, sigma0^2) on the log of non-zero sales
cat_priors = {}

for cat in valid_cats:
    cat_train = df_train[df_train['category'] == cat]
    
    # 1. Probability prior (Beta)
    # Estimate alpha, beta from the distribution of item-level probabilities
    item_probs = cat_train.groupby('article').apply(lambda g: (g['y'] > 0).mean())
    mean_p = item_probs.mean()
    var_p = item_probs.var()
    
    if var_p == 0 or np.isnan(var_p):
        alpha_p = 1.0
        beta_p = 1.0
    else:
        # Method of moments for Beta
        temp = (mean_p * (1 - mean_p) / var_p) - 1
        if temp > 0:
            alpha_p = mean_p * temp
            beta_p = (1 - mean_p) * temp
        else:
            alpha_p = 1.0
            beta_p = 1.0
            
    # 2. Size prior (Log-Normal -> Normal on logs)
    non_zero = cat_train[cat_train['y'] > 0]['y']
    if len(non_zero) > 0:
        log_y = np.log(non_zero)
        mu0 = log_y.mean()
        sigma0 = log_y.std()
        if np.isnan(sigma0) or sigma0 == 0:
            sigma0 = 1.0
    else:
        mu0 = 0.0
        sigma0 = 1.0
        
    cat_priors[cat] = {
        'alpha': alpha_p, 'beta': beta_p,
        'mu0': mu0, 'sigma0': sigma0, 'var0': sigma0**2
    }

# 3. Old TSB function for comparison
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

def q90(x):
    return x.quantile(0.90)
old_cat_priors = df_train.groupby(['category', 'day_of_week'])['y'].apply(q90).reset_index(name='p90_vol')

results = []
THRESHOLD = 0.05

for article in df_filled['article'].unique():
    cat = df_train[df_train['article'] == article]['category'].iloc[0]
    item_train = df_train[df_train['article'] == article].sort_values('ds')
    item_test = df_test[df_test['article'] == article].sort_values('ds')
    
    if len(item_test) == 0 or len(item_train) == 0:
        continue
        
    train_y = item_train['y'].values
    actuals = item_test['y'].values
    
    # ---------------------------
    # TSB + Blend (Old Approach)
    # ---------------------------
    tsb_pred = tsb_forecast(train_y)
    old_cat_prior_map = old_cat_priors[old_cat_priors['category'] == cat].set_index('day_of_week')['p90_vol'].to_dict()
    dows = item_test['day_of_week'].values
    # Credibility weighting: W = n / (n + 14)
    n = len(train_y)
    W = n / (n + 14.0)
    
    old_preds = []
    for d in dows:
        prior = old_cat_prior_map.get(d, 0)
        old_preds.append((W * tsb_pred) + ((1 - W) * prior))
    old_preds = np.array(old_preds)
    
    # ---------------------------
    # TSB-HB (Empirical Bayes)
    # ---------------------------
    prior_params = cat_priors[cat]
    alpha_p = prior_params['alpha']
    beta_p = prior_params['beta']
    mu0 = prior_params['mu0']
    var0 = prior_params['var0']
    
    # Posterior for Probability (Beta-Binomial)
    sales_days = (train_y > 0).sum()
    zero_days = len(train_y) - sales_days
    
    post_alpha = alpha_p + sales_days
    post_beta = beta_p + zero_days
    expected_p = post_alpha / (post_alpha + post_beta)
    
    # Posterior for Size (Log-Normal conjugate normal on log values)
    non_zero_train = train_y[train_y > 0]
    if len(non_zero_train) > 0:
        log_y = np.log(non_zero_train)
        n_size = len(log_y)
        mean_log_y = log_y.mean()
        var_y = log_y.var()
        if np.isnan(var_y) or var_y == 0:
            var_y = 1.0 # fallback
            
        # conjugate normal update
        post_var = 1.0 / ((1.0 / var0) + (n_size / var_y))
        post_mu = post_var * ((mu0 / var0) + ((n_size * mean_log_y) / var_y))
        
        # Expected value of log-normal = exp(mu + sigma^2 / 2)
        expected_size = np.exp(post_mu + post_var / 2.0)
    else:
        expected_size = np.exp(mu0 + var0 / 2.0)
        
    tsb_hb_pred = expected_p * expected_size
    hb_preds = np.full(len(actuals), tsb_hb_pred)
    
    # ---------------------------
    # Evaluate
    # ---------------------------
    mae_old = np.mean(np.abs(actuals - old_preds))
    mae_hb = np.mean(np.abs(actuals - hb_preds))
    
    diff = mae_old - mae_hb # positive means HB is better
    
    if diff > THRESHOLD:
        status = 'HB_WIN'
    elif diff < -THRESHOLD:
        status = 'HB_LOSS'
    else:
        status = 'TIE'
        
    results.append({
        'article': article,
        'category': cat,
        'mae_old': mae_old,
        'mae_hb': mae_hb,
        'diff': diff,
        'status': status
    })

res_df = pd.DataFrame(results)

print("=== TSB-HB vs Old Blend (Test: July - Sept 2022) ===")
print("Global MAE - Old Blend: {:.4f}".format(res_df['mae_old'].mean()))
print("Global MAE - TSB-HB: {:.4f}".format(res_df['mae_hb'].mean()))

counts = res_df['status'].value_counts()
print(f"\nTSB-HB Meaningful Wins: {counts.get('HB_WIN', 0)}")
print(f"Meaningful Ties (diff <= 0.05): {counts.get('TIE', 0)}")
print(f"Old Blend Meaningful Wins (HB_LOSS): {counts.get('HB_LOSS', 0)}")
