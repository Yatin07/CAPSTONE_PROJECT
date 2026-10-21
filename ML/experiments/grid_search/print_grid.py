import pandas as pd
res_df = pd.read_csv('E:/CAP/ML/grid_search_results.csv')
print(f"Total combinations tested: {len(res_df)}")
print("\nTop 15 Combinations:")
print(res_df.head(15).to_string())
print("\nBottom 5 Combinations (Worst):")
print(res_df.tail(5).to_string())
