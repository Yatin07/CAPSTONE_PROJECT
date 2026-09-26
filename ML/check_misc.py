import pandas as pd
df = pd.read_csv('E:/CAP/ML/data/raw/Bakery sales.csv')
print("Checking items '.' and 'ARTICLE 295' in raw dataset:")
print(df[df['article'].isin(['.', 'ARTICLE 295'])].head(10))
print("\nTotal counts:")
print(df['article'].value_counts().loc[['.', 'ARTICLE 295']])
