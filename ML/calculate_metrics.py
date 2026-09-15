import pandas as pd
import numpy as np

# Load residuals
df = pd.read_csv('E:/CAP/ML/data/processed/bakery_residuals.csv')

results = []

for item in df['article'].unique():
    df_item = df[df['article'] == item].copy()
    
    # Calculate metrics
    mean_y = df_item['y'].mean()
    mae = df_item['residual'].abs().mean()
    
    # WAPE: sum of absolute errors / sum of actuals
    wape = (df_item['residual'].abs().sum() / df_item['y'].sum()) * 100 if df_item['y'].sum() > 0 else np.nan
    
    # SMAPE
    numerator = 2 * df_item['residual'].abs()
    denominator = df_item['y'].abs() + df_item['yhat'].abs()
    # Avoid division by zero
    smape_vals = np.where(denominator == 0, 0, numerator / denominator)
    smape = smape_vals.mean() * 100
    
    results.append({
        'Item': item,
        'Mean_y': mean_y,
        'MAE': mae,
        'WAPE_%': wape,
        'SMAPE_%': smape
    })

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('WAPE_%', ascending=False)

print(f"{'Item':<25} | {'Mean_y':>8} | {'MAE':>8} | {'WAPE %':>8} | {'SMAPE %':>8}")
print('-' * 65)
for _, row in results_df.iterrows():
    print(f"{row['Item']:<25} | {row['Mean_y']:>8.2f} | {row['MAE']:>8.2f} | {row['WAPE_%']:>8.2f} | {row['SMAPE_%']:>8.2f}")

avg_smape = results_df['SMAPE_%'].mean()
worst_smape = results_df['SMAPE_%'].max()
worst_smape_item = results_df.loc[results_df['SMAPE_%'].idxmax(), 'Item']

avg_wape = results_df['WAPE_%'].mean()
worst_wape = results_df['WAPE_%'].max()
worst_wape_item = results_df.loc[results_df['WAPE_%'].idxmax(), 'Item']

print('\n--- SUMMARY ---')
print(f'Average SMAPE across all items: {avg_smape:.2f}%')
print(f'Worst SMAPE: {worst_smape:.2f}% ({worst_smape_item})')
print(f'Average WAPE across all items: {avg_wape:.2f}%')
print(f'Worst WAPE: {worst_wape:.2f}% ({worst_wape_item})')
