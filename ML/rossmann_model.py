import pandas as pd 
import numpy as np 
from sklearn.metrics import mean_absolute_error,mean_absolute_percentage_error,mean_squared_error
from prophet import Prophet 
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split 


df = pd.read_csv("data/processed/processed_rossmann.csv")


# 1. Create our empty bucket
store_metrics = {}

# 2. Start the loop for Stores 1, 2, and 3
for store_id in [1, 2, 3]:
    
    # Notice the INDENTATION (Tab). Everything here runs 3 times!
    print(f"Training model for Store {store_id}...")
    
    # 3. Filter the dataframe using our loop variable `store_id`
    df_store = df[df['Store'] == store_id].copy()
    
    # --- THIS IS YOUR LOGIC FROM BEFORE, INDENTED ---
    df_subset = df_store[["ds", "y"]].copy()
    df_subset['ds'] = pd.to_datetime(df_subset['ds'])
    
    limit_date = df_subset['ds'].max() - pd.Timedelta(days=30)
    train_data = df_subset[df_subset['ds'] < limit_date]
    test_data = df_subset[df_subset['ds'] >= limit_date]
    
    model = Prophet(changepoint_prior_scale=0.01)
    model.fit(train_data)
    
    forecast = model.predict(test_data)
    forecast_subset = forecast[['ds','yhat']]
    
    mse = mean_squared_error(test_data['y'], forecast_subset['yhat'])
    rmse = np.sqrt(mse)
    # ------------------------------------------------
    
    # 4. Save the RMSE we calculated into our bucket!
    store_metrics[store_id] = rmse

# 5. The loop is over! This is NO LONGER INDENTED.
print("\nFinal Results for all 3 stores (RMSE):")
print(store_metrics)
