import pandas as pd 
import numpy as np 
from sklearn.metrics import mean_absolute_error,mean_absolute_percentage_error,mean_squared_error
from prophet import Prophet 
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split 


df = pd.read_csv("data/processed/processed_rossmann.csv")


df_subset=df[["ds","y"]]
df_store = df[df['Store'] == 1].copy()

df_subset = df_store[["ds", "y"]].copy()

df_subset['ds'] = pd.to_datetime(df_subset['ds'])
limit_date = df_subset['ds'].max() - pd.Timedelta(days=30)
train_data = df_subset[df_subset['ds'] < limit_date]
test_data = df_subset[df_subset['ds'] >= limit_date]

model = Prophet(changepoint_prior_scale=0.01)

# model = Prophet()

model.fit(df_subset);

# model.fit(train_data)

forecast = model.predict(test_data)

forecast_subset= forecast[['ds','yhat', 'yhat_lower', 'yhat_upper']]

# print(forecast_subset.head())

mse = mean_squared_error(test_data['y'], forecast_subset['yhat'])
print(mse)

rmse = np.sqrt(mse)
print(f"RMSE: {rmse}")

mae = mean_absolute_error(test_data['y'], forecast_subset['yhat'])
print(mae)

mape = mean_absolute_percentage_error(test_data['y'], forecast_subset['yhat'])
print(mape)

fig1 = model.plot(forecast)
fig1.savefig('rossmann_forecast.png')

fig2 = model.plot_components(forecast)
fig2.savefig('rossmann_components.png')
