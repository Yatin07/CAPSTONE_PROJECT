import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

def audit_datasets():
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        raw_dir = Path("ML/data/raw")

    print(f"Auditing directory: {raw_dir.resolve()}")
    if not raw_dir.exists():
        print(f"[ERROR] Directory {raw_dir} does not exist.")
        return

    output_lines = []
    def log(msg=""):
        print(msg)
        output_lines.append(str(msg))

    log("=" * 80)
    log("                    RESTOCKIQ: RAW DATASET AUDIT REPORT                  ")
    log("=" * 80)

    files = sorted(list(raw_dir.glob("*.*")))
    log(f"Files found in {raw_dir}:")
    for f in files:
        log(f"  - {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")
    log()

    csv_files = [f for f in files if f.suffix.lower() == ".csv"]

    for csv_file in csv_files:
        log("-" * 80)
        log(f"FILE: {csv_file.name}")
        log("-" * 80)

        try:
            # Load CSV (handle potential encoding differences)
            try:
                df = pd.read_csv(csv_file, low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(csv_file, encoding="latin1", low_memory=False)

            row_count, col_count = df.shape
            log(f"Shape: {row_count:,} rows x {col_count} columns")
            log()

            # Columns, Dtypes, and Missing %
            log("Columns & Dtypes:")
            missing_series = (df.isnull().sum() / len(df)) * 100
            for col, dtype in zip(df.columns, df.dtypes):
                pct_miss = missing_series[col]
                log(f"  - {col:<32} {str(dtype):<15} Missing: {pct_miss:>6.2f}%")
            log()

            # Date identification and range
            date_col = None
            for c in df.columns:
                c_lower = c.lower()
                if "date" in c_lower or c_lower == "ds" or "timestamp" in c_lower:
                    date_col = c
                    break

            date_min = None
            date_max = None
            date_span_days = 0
            granularity = "Unknown / Non-temporal"
            is_daily_series = False

            if date_col:
                try:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                    valid_dates = df[date_col].dropna()
                    if len(valid_dates) > 0:
                        date_min = valid_dates.min()
                        date_max = valid_dates.max()
                        date_span_days = (date_max - date_min).days
                        log(f"Detected Date Column: '{date_col}'")
                        log(f"  Min Date: {date_min.strftime('%Y-%m-%d')}")
                        log(f"  Max Date: {date_max.strftime('%Y-%m-%d')}")
                        log(f"  Span:     {date_span_days} days ({date_span_days / 365.25:.2f} years)")

                        # Granularity inspection
                        # Check entity columns (article, item, product, store)
                        entity_cols = [c for c in df.columns if any(k in c.lower() for k in ["article", "item", "product", "store", "store_id", "sku"])]
                        if entity_cols:
                            entity_col = entity_cols[0]
                            # Check duplicate dates per entity
                            dups = df.duplicated(subset=[date_col, entity_col]).sum()
                            if dups > 0:
                                granularity = f"Transaction-level / Intraday (duplicates per {entity_col}: {dups:,})"
                            else:
                                granularity = f"Regular Daily Series per {entity_col}"
                                is_daily_series = True
                        else:
                            dups = df.duplicated(subset=[date_col]).sum()
                            if dups > 0:
                                granularity = f"Multiple transactions per date (duplicates: {dups:,})"
                            else:
                                granularity = "Daily Aggregate Series"
                                is_daily_series = True
                    else:
                        log(f"Date column '{date_col}' could not be parsed into valid timestamps.")
                except Exception as ex:
                    log(f"Date parsing error on '{date_col}': {ex}")
            else:
                log("No Date column detected.")

            log(f"Granularity Assessment: {granularity}")
            log()

            # Verdict Formulation
            verdict = ""
            years = date_span_days / 365.25 if date_span_days else 0

            if "sample_submission" in csv_file.name.lower():
                verdict = "NOT USABLE FOR TRAINING - Kaggle submission template with IDs only, no historical targets."
            elif "store.csv" in csv_file.name.lower():
                verdict = "NOT USABLE FOR TRAINING - Static store metadata without time-series sales/dates."
            elif "test.csv" in csv_file.name.lower():
                verdict = "NOT USABLE FOR TRAINING - Out-of-sample evaluation feature matrix without historical ground truth."
            elif "grocery_inventory" in csv_file.name.lower():
                verdict = "NOT USABLE FOR TRAINING - Synthetic cross-sectional snapshot table lacking sequential multi-year time series."
            elif "bakery sales" in csv_file.name.lower():
                if years >= 1.5:
                    verdict = f"USABLE FOR PROPHET TRAINING (Real multi-article daily series with {years:.2f} years history: {date_min.strftime('%Y-%m-%d')} to {date_max.strftime('%Y-%m-%d')})"
                else:
                    verdict = f"NOT USABLE FOR TRAINING - Insufficient date history ({years:.2f} years < 1.5 years requirement)"
            elif "train.csv" in csv_file.name.lower() and years >= 1.5:
                verdict = f"USABLE FOR PROPHET TRAINING (Real multi-store daily series with {years:.2f} years history: {date_min.strftime('%Y-%m-%d')} to {date_max.strftime('%Y-%m-%d')})"
            else:
                if years < 1.5:
                    verdict = f"NOT USABLE FOR TRAINING - Date span is only {years:.2f} years (< 1.5 years required for reliable Prophet yearly seasonality)"
                else:
                    verdict = f"NOT USABLE FOR TRAINING - Does not meet time-series granularity prerequisites"

            log(f"VERDICT: {verdict}")
            log()

        except Exception as e:
            log(f"[LOAD ERROR] Could not process {csv_file.name}: {e}")
            log(f"VERDICT: NOT USABLE FOR TRAINING - Load failure ({e})")
            log()

    # Save output to docs/dataset_audit.txt
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_file = docs_dir / "dataset_audit.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    log(f"Report saved to: {out_file.resolve()}")

if __name__ == "__main__":
    audit_datasets()
