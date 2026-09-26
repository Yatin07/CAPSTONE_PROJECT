import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import logging

logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

df = pd.read_csv('data/processed/primary_items.csv')
df['ds'] = pd.to_datetime(df['ds'])

# Add the tourist season flag (July and August)
df['is_tourist_season'] = df['ds'].dt.month.isin([7, 8])

all_residuals = []
unique_items = df['article'].unique()

print(f"Starting Prophet training (Multiplicative + Tourist Season + 365d initial) for {len(unique_items)} items...")

for item in unique_items:
    try:
        # print(f"Processing: {item}")
        
        df_item = df[df['article'] == item].copy()
        
        model = Prophet(
            changepoint_prior_scale=0.05, 
            seasonality_prior_scale=0.1,
            seasonality_mode='multiplicative'
        )
        model.add_country_holidays(country_name='FR')
        
        # Claude is right: Prophet should handle known patterns. 
        # A regressor acts as a perfect mathematical step-change (multiplier) for the tourist block.
        model.add_regressor('is_tourist_season')
        
        model.fit(df_item)
        
        # 365 days initial window so Prophet has seen 1 full cycle
        df_cv = cross_validation(model, initial='365 days', period='30 days', horizon='30 days', disable_tqdm=True)
        
        df_cv['residual'] = df_cv['y'] - df_cv['yhat']
        df_cv['article'] = item
        
        df_cv_clean = df_cv[['ds', 'article', 'y', 'yhat', 'residual']]
        all_residuals.append(df_cv_clean)
        
    except Exception as e:
        print(f"[{item}] FAILED: {str(e)}")
        continue

if all_residuals:
    final_residuals_df = pd.concat(all_residuals, ignore_index=True)
    final_residuals_df.to_csv('data/processed/bakery_residuals.csv', index=False)
    print(f"\nSuccess! Out-of-fold residuals saved to data/processed/bakery_residuals.csv for {len(all_residuals)} items.")
else:
    print("\nError: No residuals were generated.")
