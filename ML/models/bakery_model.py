import pandas as pd 
import numpy as np 
from prophet import Prophet
import matplotlib.pyplot as plt
import logging
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

print('Loading dataset...')
df = pd.read_csv('data/processed/processed_bakery.csv')
df_subset = df[['ds', 'y']].copy()
df_subset['ds'] = pd.to_datetime(df_subset['ds'])

print('Training Final Prophet Model...')
# Initialize with the winning grid-search parameters
model = Prophet(changepoint_prior_scale=0.05, seasonality_prior_scale=0.1)

# Fit on the FULL dataset (No test split, because this is our production model)
model.fit(df_subset)

# Ask Prophet to predict the past (the exact days it just trained on)
print('Generating historical predictions to find the residual errors...')
historical_forecast = model.predict(df_subset)

# Merge the actual sales (y) with the predicted sales (yhat)
df_residuals = pd.merge(df_subset, historical_forecast[['ds', 'yhat']], on='ds')

# Calculate the Residual (What Prophet missed!)
df_residuals['residual'] = df_residuals['y'] - df_residuals['yhat']

print('Prophet Model Complete! Here is a preview of the residuals:')
print(df_residuals[['ds', 'y', 'yhat', 'residual']].tail())

# Save this for the XGBoost layer
df_residuals.to_csv('data/processed/bakery_residuals.csv', index=False)
print('\nSaved residuals to data/processed/bakery_residuals.csv')
