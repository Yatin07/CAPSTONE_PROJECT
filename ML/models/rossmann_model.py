import pandas as pd 
import numpy as np 
from sklearn.metrics import mean_absolute_error,mean_absolute_percentage_error,mean_squared_error
from prophet import Prophet 
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/processed_rossmann.csv")

# 1. Create our empty bucket
store_metrics = {}

# 2. Start the loop for Stores 1, 2, and 3
for store_id in [1, 2, 3]:
    print(f"Training model for Store {store_id}...")
    
    # Filter the dataframe
    df_store = df[df['Store'] == store_id].copy()
    
    # Add SchoolHoliday and Promo. (Removed is_weekend to stop multicollinearity)
    df_subset = df_store[["ds", "y", "Promo", "SchoolHoliday"]].copy()
    df_subset['ds'] = pd.to_datetime(df_subset['ds'])
    
    limit_date = df_subset['ds'].max() - pd.Timedelta(days=30)
    train_data = df_subset[df_subset['ds'] < limit_date]
    test_data = df_subset[df_subset['ds'] >= limit_date]
    
    # We increase changepoint_prior_scale slightly to let it adapt to trends better
    model = Prophet(changepoint_prior_scale=0.05)
    
    # ACCURACY BOOST 1: Add built-in German holidays! (Rossmann is a German store)
    model.add_country_holidays(country_name='DE')
    
    # ACCURACY BOOST 2: Add our external regressors
    model.add_regressor('Promo')
    model.add_regressor('SchoolHoliday')
    
    model.fit(train_data)
    
    forecast = model.predict(test_data)
    forecast_subset = forecast[['ds','yhat']]
    
    mse = mean_squared_error(test_data['y'], forecast_subset['yhat'])
    rmse = np.sqrt(mse)
    
    store_metrics[store_id] = rmse

print("\nFinal Results for all 3 stores (RMSE):")
for store_id, error in store_metrics.items():
    print(f"Store {store_id}: {error:.2f}")
