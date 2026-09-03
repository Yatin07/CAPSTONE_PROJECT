import pandas as pd 
import numpy as np 
from prophet import Prophet 
from prophet.diagnostics import cross_validation, performance_metrics
import logging
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

df = pd.read_csv('data/processed/processed_rossmann.csv')

# STEP 2 FIX: Filter out 0 sales (closed days)
df = df[df['y'] > 0]

store_metrics = {}

for store_id in [1, 2, 3]:
    print(f'Training and Cross-Validating Store {store_id}...')
    df_store = df[df['Store'] == store_id].copy()
    
    df_subset = df_store[['ds', 'y', 'Promo', 'SchoolHoliday']].copy()
    df_subset['ds'] = pd.to_datetime(df_subset['ds'])
    
    model = Prophet(changepoint_prior_scale=0.05)
    model.add_country_holidays(country_name='DE')
    model.add_regressor('Promo')
    model.add_regressor('SchoolHoliday')
    
    # Train on the FULL dataset for this store
    model.fit(df_subset)
    
    # STEP 3: Cross Validation
    df_cv = cross_validation(model, initial='365 days', period='60 days', horizon='30 days')
    df_p = performance_metrics(df_cv, rolling_window=1)
    
    rmse = df_p['rmse'].values[0]
    store_metrics[store_id] = rmse

print('\nFinal Results for all 3 stores (Cross-Validated RMSE):')
for store_id, error in store_metrics.items():
    print(f'Store {store_id}: {error:.2f}')
