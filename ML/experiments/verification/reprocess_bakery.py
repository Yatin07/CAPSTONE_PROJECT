import pandas as pd
import numpy as np
import os

print('Loading raw Bakery data...')
raw_path = 'E:/CAP/ML/data/raw/Bakery sales.csv'
df = pd.read_csv(raw_path)

# 1. Clean the European unit_price column
df['unit_price'] = df['unit_price'].astype(str).str.replace(' €', '').str.replace(',', '.').astype(float)

# 2. Group by date AND article to sum the quantity
df_grouped = df.groupby(['date', 'article']).agg({'Quantity': 'sum', 'unit_price': 'mean'}).reset_index()

# Rename for Prophet consistency
df_grouped.rename(columns={'date': 'ds', 'Quantity': 'y'}, inplace=True)
df_grouped['ds'] = pd.to_datetime(df_grouped['ds'])

# 3. Calculate Item Coverage
total_days = df_grouped['ds'].nunique()
item_days = df_grouped.groupby('article')['ds'].nunique()
coverage = item_days / total_days

# 4. Split into Primary (>=70%) and Sparse (<70%)
primary_articles = coverage[coverage >= 0.70].index
sparse_articles = coverage[coverage < 0.70].index

df_primary = df_grouped[df_grouped['article'].isin(primary_articles)]
df_sparse = df_grouped[df_grouped['article'].isin(sparse_articles)]

# 5. Save to the processed folder
primary_out = 'E:/CAP/ML/data/processed/primary_items.csv'
sparse_out = 'E:/CAP/ML/data/processed/sparse_items.csv'

df_primary.to_csv(primary_out, index=False)
df_sparse.to_csv(sparse_out, index=False)

print('\nData Processing Complete!')
print(f'Primary Items (>=70% coverage): {len(primary_articles)} items -> Saved to {primary_out}')
print(f'Sparse Items (<70% coverage): {len(sparse_articles)} items -> Saved to {sparse_out}')
