import pandas as pd 
import numpy as np 
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import itertools
import logging
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

df = pd.read_csv('data/processed/processed_bakery.csv')
df_subset = df[['ds', 'y']].copy()
df_subset['ds'] = pd.to_datetime(df_subset['ds'])

# --- STEP 4: GRID SEARCH ON BAKERY DATA ---
print('Starting Grid Search on Bakery Data...')
param_grid = {  
    'changepoint_prior_scale': [0.01, 0.05, 0.1, 0.5],
    'seasonality_prior_scale': [0.01, 0.1, 1.0, 10.0],
}

# Generate all combinations of parameters
all_params = [dict(zip(param_grid.keys(), v)) for v in itertools.product(*param_grid.values())]
rmses = []

for params in all_params:
    m = Prophet(**params)
    m.fit(df_subset)
    
    # Cross validate
    df_cv = cross_validation(m, initial='180 days', period='30 days', horizon='30 days')
    df_p = performance_metrics(df_cv, rolling_window=1)
    
    rmses.append(df_p['rmse'].values[0])

# Find the best parameters
tuning_results = pd.DataFrame(all_params)
tuning_results['rmse'] = rmses

best_params = all_params[np.argmin(rmses)]
print('\n==================================')
print('GRID SEARCH COMPLETE')
print(f'Best parameters: {best_params}')
print(f'Minimum Cross-Validated RMSE: {min(rmses):.2f}')
print('==================================')
