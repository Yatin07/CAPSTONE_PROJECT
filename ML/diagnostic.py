import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation
import logging

logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

# 1. Regime Shift Check (Monthly Averages)
df = pd.read_csv('E:/CAP/ML/data/processed/primary_items.csv')
df['ds'] = pd.to_datetime(df['ds'])

trad_bag = df[df['article'] == 'TRADITIONAL BAGUETTE'].copy()
trad_bag['month_year'] = trad_bag['ds'].dt.to_period('M')
monthly_avg = trad_bag.groupby('month_year')['y'].mean()

print('--- TRADITIONAL BAGUETTE MONTHLY AVERAGES (Regime Shift Check) ---')
for month, avg in monthly_avg.items():
    print(f'{month}: {avg:.1f} units/day')
print('-' * 60)

# 2. Test Multiplicative Seasonality
top_items = ['TRADITIONAL BAGUETTE', 'CROISSANT', 'BAGUETTE']
print('\n--- TESTING MULTIPLICATIVE SEASONALITY ---')

for item in top_items:
    df_item = df[df['article'] == item].copy()
    
    model = Prophet(
        changepoint_prior_scale=0.05, 
        seasonality_prior_scale=0.1,
        seasonality_mode='multiplicative'
    )
    model.add_country_holidays(country_name='FR')
    model.fit(df_item)
    
    df_cv = cross_validation(model, initial='180 days', period='30 days', horizon='30 days', disable_tqdm=True)
    
    df_cv['residual'] = df_cv['y'] - df_cv['yhat']
    wape = (df_cv['residual'].abs().sum() / df_cv['y'].sum()) * 100
    
    numerator = 2 * df_cv['residual'].abs()
    denominator = df_cv['y'].abs() + df_cv['yhat'].abs()
    smape_vals = np.where(denominator == 0, 0, numerator / denominator)
    smape = smape_vals.mean() * 100
    
    print(f'[{item}] Multiplicative WAPE: {wape:.2f}% | SMAPE: {smape:.2f}%')
