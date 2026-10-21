import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation
import logging

logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

df = pd.read_csv('E:/CAP/ML/data/processed/primary_items.csv')
df['ds'] = pd.to_datetime(df['ds'])
df['is_tourist_season'] = df['ds'].dt.month.isin([7, 8])

df_item = df[df['article'] == 'TRADITIONAL BAGUETTE'].copy()

model = Prophet(
    changepoint_prior_scale=0.05, 
    seasonality_prior_scale=0.1,
    seasonality_mode='multiplicative'
)
model.add_country_holidays(country_name='FR')
model.add_regressor('is_tourist_season')
model.fit(df_item)

df_cv = cross_validation(model, initial='365 days', period='30 days', horizon='30 days', disable_tqdm=True)

df_cv['residual'] = df_cv['y'] - df_cv['yhat']
df_cv['cutoff_date'] = df_cv['cutoff'].dt.date

cutoff_groups = df_cv.groupby('cutoff_date')
for cutoff, group in cutoff_groups:
    wape = (group['residual'].abs().sum() / group['y'].sum()) * 100
    mean_y = group['y'].mean()
    print(f"Cutoff {cutoff}: WAPE = {wape:>6.2f}% (Mean Daily Volume = {mean_y:>5.1f})")
