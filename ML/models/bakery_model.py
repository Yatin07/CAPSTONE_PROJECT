import pandas as pd 
import numpy as np 
from sklearn.metrics import mean_squared_error,mean_absolute_error,mean_absolute_percentage_error 
import matplotlib.pyplot as plt
from prophet import Prophet

df = pd.read_csv("data/processed/processed_bakery.csv")

df_subset = df[["ds", "y"]].copy()
# df_subset = df[["ds", "y", "is_weekend"]].copy()

# print(df_subset.head())

df_subset['ds'] = pd.to_datetime(df_subset['ds'])

limit_date = df_subset['ds'].max() - pd.Timedelta(days=30)
train_data = df_subset[df_subset['ds'] < limit_date]
test_data = df_subset[df_subset['ds'] >= limit_date]

# print(train_data)
# print(test_data)

# model = Prophet()
model = Prophet(changepoint_prior_scale=0.01)

# model.add_regressor('is_weekend')
model.fit(train_data)

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
fig1.savefig('bakery_forecast.png')

fig2 = model.plot_components(forecast)
fig2.savefig('bakery_components.png')
