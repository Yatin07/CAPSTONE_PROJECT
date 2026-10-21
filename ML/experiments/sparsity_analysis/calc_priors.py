import pandas as pd
import json

# 1. Load data and categories
df = pd.read_csv('E:/CAP/ML/data/processed/sparse_items.csv')
df['ds'] = pd.to_datetime(df['ds'])

with open('E:/CAP/ML/data/processed/sparse_categories.json', 'r') as f:
    categories = json.load(f)

item_to_category = {}
for cat, items in categories.items():
    for item in items:
        item_to_category[item] = cat

df['category'] = df['article'].map(item_to_category)

# Filter out Artifacts and Holidays
valid_cats = ['Breads & Baguettes', 'Viennoiserie', 'Patisserie / Desserts', 'Savory Food / Lunch', 'Beverages & Sweets']
df = df[df['category'].isin(valid_cats)]

# 2. Reindex to fill implicit zeros
# Find global date range
min_date = df['ds'].min()
max_date = df['ds'].max()
all_dates = pd.date_range(min_date, max_date, freq='D')

reindexed_list = []
for article, group in df.groupby('article'):
    cat = group['category'].iloc[0]
    # Set index to ds, reindex to all_dates
    group = group.set_index('ds').reindex(all_dates)
    group['article'] = article
    group['category'] = cat
    group['y'] = group['y'].fillna(0)
    group = group.rename_axis('ds').reset_index()
    reindexed_list.append(group)

df_filled = pd.concat(reindexed_list, ignore_index=True)
df_filled['day_of_week'] = df_filled['ds'].dt.dayofweek

# 3. Calculate Item-level Day-of-Week Averages
# How much does ITEM X sell on average on a Monday?
item_dow = df_filled.groupby(['category', 'article', 'day_of_week'])['y'].mean().reset_index()
item_dow.rename(columns={'y': 'item_mean_vol'}, inplace=True)

# 4. Calculate Category-level Day-of-Week Priors
# What is the average and std of those item-level averages?
cat_dow = item_dow.groupby(['category', 'day_of_week']).agg(
    cat_mean_vol=('item_mean_vol', 'mean'),
    cat_std_vol=('item_mean_vol', 'std'),
    item_count=('article', 'nunique')
).reset_index()

# Map day_of_week to names
dow_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
cat_dow['Day'] = cat_dow['day_of_week'].map(dow_map)

# Print results grouped by category
print("=== Category Day-of-Week Priors ===")
for cat in valid_cats:
    subset = cat_dow[cat_dow['category'] == cat]
    item_count = subset['item_count'].iloc[0]
    print(f"\n--- {cat} (Items: {item_count}) ---")
    print(f"{'Day':<5} | {'Mean Vol':<10} | {'Std Vol':<10}")
    print("-" * 32)
    for _, row in subset.iterrows():
        print(f"{row['Day']:<5} | {row['cat_mean_vol']:<10.2f} | {row['cat_std_vol']:<10.2f}")

# Save to JSON
final_priors = {}
for cat in valid_cats:
    final_priors[cat] = {}
    subset = cat_dow[cat_dow['category'] == cat]
    for _, row in subset.iterrows():
        final_priors[cat][row['day_of_week']] = {
            'mean': round(row['cat_mean_vol'], 3),
            'std': round(row['cat_std_vol'], 3)
        }

with open('E:/CAP/ML/data/processed/category_priors.json', 'w') as f:
    json.dump(final_priors, f, indent=4)

print("\nSaved to category_priors.json")
