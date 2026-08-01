import pandas as pd 
import numpy as np 
from sklearn.metrics import mean_absolute_error,mean_absolute_percentage_error,mean_squared_error
from prophet import Prophet 
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split 


df = pd.read_csv("data/processed/processed_rossmann.csv")


df_subset=df[["ds","y"]]

df_subset['ds'] = pd.to_datetime(df_subset['ds'])

model = Prophet()

model.fit(df_subset);


