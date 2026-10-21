import pandas as pd
df = pd.read_csv('E:/CAP/ML/data/processed/sparse_items.csv')
print("Columns in sparse_items.csv:", df.columns.tolist())
articles = df['article'].unique().tolist()
print("\nNumber of unique sparse items:", len(articles))
print("\nUnique sparse items:")
for a in sorted(articles):
    print("- " + str(a))
