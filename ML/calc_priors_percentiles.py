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

valid_cats = ['Breads & Baguettes', 'Viennoiserie', 'Patisserie / Desserts', 'Savory Food / Lunch', 'Beverages & Sweets']
df = df[df['category'].isin(valid_cats)]

# 2. Reindex to fill implicit zeros
min_date = df['ds'].min()
max_date = df['ds'].max()
all_dates = pd.date_range(min_date, max_date, freq='D')

reindexed_list = []
for article, group in df.groupby('article'):
    cat = group['category'].iloc[0]
    group = group.set_index('ds').reindex(all_dates)
    group['article'] = article
    group['category'] = cat
    group['y'] = group['y'].fillna(0)
    group = group.rename_axis('ds').reset_index()
    reindexed_list.append(group)

df_filled = pd.concat(reindexed_list, ignore_index=True)
df_filled['day_of_week'] = df_filled['ds'].dt.dayofweek

# 3. Calculate Category-level Day-of-Week Priors using Percentiles
# Group by category and day_of_week on the raw daily observations
def q80(x):
    return x.quantile(0.80)
    
def q90(x):
    return x.quantile(0.90)

cat_dow = df_filled.groupby(['category', 'day_of_week']).agg(
    cat_mean_vol=('y', 'mean'),
    p80_vol=('y', q80),
    p90_vol=('y', q90),
    item_count=('article', 'nunique')
).reset_index()

dow_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
cat_dow['Day'] = cat_dow['day_of_week'].map(dow_map)

print("=== Category Day-of-Week Priors (Percentiles) ===")
for cat in valid_cats:
    subset = cat_dow[cat_dow['category'] == cat]
    item_count = subset['item_count'].iloc[0]
    print(f"\n--- {cat} (Items: {item_count}) ---")
    print(f"{'Day':<5} | {'Mean':<8} | {'80th pctl':<10} | {'90th pctl':<10}")
    print("-" * 45)
    for _, row in subset.iterrows():
        print(f"{row['Day']:<5} | {row['cat_mean_vol']:<8.2f} | {row['p80_vol']:<10.2f} | {row['p90_vol']:<10.2f}")

# Save to JSON
final_priors = {}
for cat in valid_cats:
    final_priors[cat] = {}
    subset = cat_dow[cat_dow['category'] == cat]
    for _, row in subset.iterrows():
        final_priors[cat][row['day_of_week']] = {
            'mean': round(row['cat_mean_vol'], 3),
            'p80': round(row['p80_vol'], 3),
            'p90': round(row['p90_vol'], 3)
        }

with open('E:/CAP/ML/data/processed/category_priors_percentiles.json', 'w') as f:
    json.dump(final_priors, f, indent=4)

print("\nSaved to category_priors_percentiles.json")
