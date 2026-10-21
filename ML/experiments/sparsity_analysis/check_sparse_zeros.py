import pandas as pd
import json

df = pd.read_csv('E:/CAP/ML/data/processed/sparse_items.csv')
with open('E:/CAP/ML/data/processed/sparse_categories.json', 'r') as f:
    categories = json.load(f)

item_to_category = {}
for cat, items in categories.items():
    for item in items:
        item_to_category[item] = cat

df['category'] = df['article'].map(item_to_category)
df = df[~df['category'].isin(['Holiday Specialty', 'Data Artifacts (Drop)'])]
df['ds'] = pd.to_datetime(df['ds'])
df['day_of_week'] = df['ds'].dt.dayofweek

print(df.head())
print("\nDoes dataframe have explicit zeros?", (df['y'] == 0).sum())
