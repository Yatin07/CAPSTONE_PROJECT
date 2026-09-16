import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import logging

logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

# 1. Load the new item-level primary dataset
df = pd.read_csv('data/processed/primary_items.csv')
df['ds'] = pd.to_datetime(df['ds'])

all_residuals = []

# 2. Loop through all 35 primary items
unique_items = df['article'].unique()

print(f'Starting Prophet training and Out-of-Fold residual generation for {len(unique_items)} items...')

for item in unique_items:
    try:
        print(f'\nProcessing: {item}')
        
        # Filter for just this item
        df_item = df[df['article'] == item].copy()
        
        # Initialize the model (using baseline defaults since full tuning is pending)
        model = Prophet(changepoint_prior_scale=0.05, seasonality_prior_scale=0.1)
        model.add_country_holidays(country_name="FR")
        model.fit(df_item)
        
        # 3. Generate OUT-OF-FOLD predictions
        df_cv = cross_validation(model, initial='180 days', period='30 days', horizon='30 days', disable_tqdm=True)
        
        # Calculate metrics for logging
        df_p = performance_metrics(df_cv, rolling_window=1)
        rmse = df_p['rmse'].values[0]
        mae = df_p['mae'].values[0]
        print(f'[{item}] Success - RMSE: {rmse:.2f} | MAE: {mae:.2f}')
        
        # Calculate the true out-of-fold residual
        df_cv['residual'] = df_cv['y'] - df_cv['yhat']
        df_cv['article'] = item
        
        # Keep only the columns we need for XGBoost
        df_cv_clean = df_cv[['ds', 'article', 'y', 'yhat', 'residual']]
        all_residuals.append(df_cv_clean)
        
    except Exception as e:
        print(f'[{item}] FAILED: {str(e)}')
        continue

# 4. Combine all items into one massive dataset
if all_residuals:
    final_residuals_df = pd.concat(all_residuals, ignore_index=True)
    final_residuals_df.to_csv('data/processed/bakery_residuals.csv', index=False)
    print(f'\nSuccess! Out-of-fold residuals saved to data/processed/bakery_residuals.csv for {len(all_residuals)} items.')
else:
    print('\nError: No residuals were generated.')
