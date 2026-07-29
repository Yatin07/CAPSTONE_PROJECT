import pandas as pd 
import numpy as np 
from prophet import Prophet

df = pd.read_csv("data/processed/processed_bakery.csv")

df_subset = df[["ds", "y"]].copy()


# print(df_subset.head())

df_subset['ds'] = pd.to_datetime(df_subset['ds'])

limit_date = df_subset['ds'].max() - pd.Timedelta(days=30)
train_data = df_subset[df_subset['ds'] < limit_date]
test_data = df_subset[df_subset['ds'] >= limit_date]

# print(train_data)
# print(test_data)

model = Prophet()
model.fit(train_data)

forecast = model.predict(test_data)

forecast_subset= forecast[['ds','yhat', 'yhat_lower', 'yhat_upper']]

print(forecast_subset.head())
