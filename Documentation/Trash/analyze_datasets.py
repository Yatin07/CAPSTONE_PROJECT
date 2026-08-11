import os
import pandas as pd
import numpy as np
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

data_dir = r"c:\Users\yatin\Downloads\CAP\ML\data\raw"

print(f"Analyzing files in {data_dir}\n" + "="*50)

if not os.path.exists(data_dir):
    print("Directory does not exist.")
    exit()

files = os.listdir(data_dir)
if not files:
    print("Folder is empty.")
    exit()

for f in files:
    if f.startswith('.'):
        continue
    file_path = os.path.join(data_dir, f)
    print(f"\n\n{'='*50}\n--- Analyzing {f} ---")
    try:
        if f.endswith('.csv'):
            df = pd.read_csv(file_path, low_memory=False)
        elif f.endswith('.parquet'):
            df = pd.read_parquet(file_path)
        else:
            print(f"Skipping non-CSV/Parquet file: {f}")
            continue
    except Exception as e:
        print(f"Failed to load {f}: {e}")
        continue
        
    print(f"Row count: {len(df)}")
    print("\nColumn names and dtypes:")
    for col in df.columns:
        print(f"  {col}: {df[col].dtype}")
        
    print("\nMissing values (%):")
    missing_pct = (df.isnull().sum() / len(df)) * 100
    has_missing = False
    for col, pct in missing_pct.items():
        if pct > 0:
            print(f"  {col}: {pct:.2f}%")
            has_missing = True
    if not has_missing:
        print("  None")
        
    # Date columns
    date_cols = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        elif df[col].dtype == 'object':
            first_valid = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            from datetime import date
            if isinstance(first_valid, date):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    date_cols.append(col)
                except:
                    pass
            elif isinstance(first_valid, str):
                # Try to parse if it looks like a date
                if any(c.isdigit() for c in first_valid) and ('-' in first_valid or '/' in first_valid):
                    try:
                        # sample conversion first
                        sample_parsed = pd.to_datetime(df[col].dropna().head(100), errors='coerce')
                        if sample_parsed.notnull().mean() > 0.5: # mostly dates
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            date_cols.append(col)
                    except:
                        pass

    if not date_cols:
        print("\nNo date columns identified.")
        print("Verdict: NOT USABLE FOR TRAINING \u2014 missing real dates")
        continue
        
    print("\nDate column ranges:")
    max_duration = timedelta(0)
    best_date_col = None
    for col in date_cols:
        min_date = df[col].min()
        max_date = df[col].max()
        print(f"  {col}: {min_date} to {max_date}")
        duration = max_date - min_date
        if pd.notnull(duration) and duration > max_duration:
            max_duration = duration
            best_date_col = col

    print("\nGranularity check:")
    if best_date_col is None:
        print("Verdict: NOT USABLE FOR TRAINING \u2014 missing real dates")
        continue
        
    date_counts = df[best_date_col].dt.date.value_counts()
    mean_rows_per_date = date_counts.mean()
    
    if mean_rows_per_date > 1.5:
        print("  Multiple rows per date detected (transaction-level or multiple entities/stores).")
    else:
        print("  One row per date (on average).")
        
    unique_dates = np.sort(df[best_date_col].dt.date.dropna().unique())
    is_daily = False
    if len(unique_dates) > 1:
        diffs = pd.Series(unique_dates).diff().dt.days.dropna()
        median_diff = diffs.median()
        if median_diff == 1:
            print("  Granularity is daily.")
            is_daily = True
        elif median_diff == 7:
            print("  Granularity is weekly.")
        else:
            print(f"  Granularity is ~{median_diff} days.")
    else:
        print("  Static snapshot (only one date).")
        print("Verdict: NOT USABLE FOR TRAINING \u2014 static snapshot")
        continue
    
    if max_duration.days >= 547:
        if is_daily or mean_rows_per_date > 1.5: 
            print("\nVerdict: USABLE FOR PROPHET TRAINING")
        else:
            print(f"\nVerdict: NOT USABLE FOR TRAINING \u2014 granularity is not daily (median diff: {median_diff})")
    else:
        print(f"\nVerdict: NOT USABLE FOR TRAINING \u2014 too short (history is {max_duration.days} days, need >= 547)")
