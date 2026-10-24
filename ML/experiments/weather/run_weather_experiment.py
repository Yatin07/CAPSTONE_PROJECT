"""
RestockIQ - Pre-Registered Weather Experiment
==============================================
Location : Guerande, 44350, France
Coordinates confirmed via Open-Meteo geocoding API at runtime.

Pre-registration (locked before data pull):
  Features  : temp_anom, rain_flag, sunshine_anom, temp_anom x summer
  Models    : prophet_only, prophet_weather, hybrid, hybrid_weather, average
  Folds     : 6 rolling-origin folds (4-week test windows)
  Decision  : KEEP iff WAPE >= best_no_weather + 0.5 pp AND wins >= 4/6 folds
              AND 95% block-bootstrap CI excludes 0

License note : Open-Meteo free tier is NON-COMMERCIAL only.
               CC BY 4.0 attribution required.
               Commercial use requires a paid plan or self-hosting.
               Source: https://open-meteo.com/en/terms

References:
  Guler et al. (2023): Prophet + weather + holidays -> MAE 0.76, RMSE 0.82
  Lalitha et al. (2025): RF/ARIMA + weather + costs -> MSE 53.97
"""

import warnings, math
from pathlib import Path
from datetime import date

import numpy as np
import pandas as pd
import requests
from prophet import Prophet

warnings.filterwarnings("ignore")

ROOT       = Path(__file__).resolve().parents[3]        # e:\CAP
DATA_DIR   = ROOT / "ML" / "data"
DOCS_DIR   = ROOT / "docs"

SALES_FILE   = DATA_DIR / "raw" / "Bakery sales.csv"
WEATHER_FILE = DATA_DIR / "weather_guerande.csv"
OUT_CSV      = DOCS_DIR / "weather_experiment.csv"
OUT_MD       = DOCS_DIR / "weather_experiment.md"

START_DATE            = "2021-01-01"
END_DATE              = "2022-09-30"
LOCATION              = "Guerande, 44350, France"
N_FOLDS               = 6
TEST_WEEKS            = 4
BOOTSTRAP_N           = 2000
IMPROVEMENT_THRESHOLD = 0.5
MIN_FOLD_WINS         = 4

BREAD_SKUS = [
    "TRADITIONAL BAGUETTE", "BAGUETTE", "CROISSANT",
    "PAIN AU CHOCOLAT", "COUPE", "BANETTE",
]

# ──────────────────────────────────────────────────────────────────────────────
def geocode_guerande():
    print("\n[STEP 0] Geocoding Guerande via Open-Meteo geocoding API ...")
    try:
        r = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": "Guerande", "count": 5, "language": "fr", "format": "json"},
            timeout=15,
        )
        r.raise_for_status()
        for res in r.json().get("results", []):
            if str(res.get("country_code", "")).upper() == "FR":
                lat, lon = res["latitude"], res["longitude"]
                print(f"  OK Confirmed: {res.get('name')}, France  lat={lat}  lon={lon}")
                return lat, lon
    except Exception as e:
        print(f"  WARN geocoding API failed: {e}")
    print("  COULD NOT VERIFY via API - OSM fallback: lat=47.3261, lon=-2.4284")
    return 47.3261, -2.4284


# ──────────────────────────────────────────────────────────────────────────────
def pull_weather(lat, lon):
    print(f"\n[STEP 1] Pulling ERA5 weather for {LOCATION} ...")
    r = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": lat, "longitude": lon,
            "start_date": START_DATE, "end_date": END_DATE,
            "daily": "temperature_2m_mean,precipitation_sum,sunshine_duration",
            "timezone": "Europe/Paris",
        },
        timeout=30,
    )
    r.raise_for_status()
    df = pd.DataFrame(r.json()["daily"])
    df["date"] = pd.to_datetime(df["time"])
    df.drop(columns=["time"], inplace=True)
    print(f"  OK {len(df)} rows ({df['date'].min().date()} -> {df['date'].max().date()})")

    df = df.sort_values("date").reset_index(drop=True)
    df["temp_clim"]       = df["temperature_2m_mean"].rolling(30, min_periods=7).mean().shift(1)
    df["sun_clim"]        = df["sunshine_duration"].rolling(30, min_periods=7).mean().shift(1)
    df["temp_anom"]       = df["temperature_2m_mean"] - df["temp_clim"]
    df["rain_flag"]       = (df["precipitation_sum"] >= 3.0).astype(int)
    df["sunshine_anom"]   = df["sunshine_duration"] - df["sun_clim"]
    df["is_summer"]       = df["date"].dt.month.isin([6, 7, 8]).astype(int)
    df["temp_anom_x_summer"] = df["temp_anom"] * df["is_summer"]

    df.to_csv(WEATHER_FILE, index=False)
    print(f"  OK Saved -> {WEATHER_FILE}")
    return df


# ──────────────────────────────────────────────────────────────────────────────
def load_sales():
    print(f"\n[STEP 2] Loading bakery sales ...")
    # File is comma-separated with unnamed index column
    df = pd.read_csv(SALES_FILE, sep=",", low_memory=False, index_col=0)
    print(f"  Raw columns: {list(df.columns)}")

    # Normalise column names
    df.columns = [c.strip().lower() for c in df.columns]

    # Parse date
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date"])

    # Parse quantity (may be float string)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0.0)

    # Filter to bread SKUs
    df["article_up"] = df["article"].str.upper().str.strip()
    mask = df["article_up"].isin([s.upper() for s in BREAD_SKUS])
    bread = df[mask].copy()
    if len(bread) == 0:
        print(f"  WARN no SKU matches - using all articles as proxy")
        bread = df.copy()
    print(f"  Bread rows: {len(bread)}")

    # Daily total sold units
    daily = (
        bread.groupby("date")["quantity"]
        .sum()
        .reset_index(name="y")
    )
    daily = (
        daily[(daily["date"] >= START_DATE) & (daily["date"] <= END_DATE)]
        .sort_values("date")
        .reset_index(drop=True)
    )

    # DEF-008: exclude closure days (y=0)
    n_before = len(daily)
    daily = daily[daily["y"] > 0].reset_index(drop=True)
    print(f"  OK {len(daily)}/{n_before} open days kept (DEF-008: closure/zero days excluded)")
    print(f"  y range: {daily['y'].min():.1f} - {daily['y'].max():.1f}  median={daily['y'].median():.1f}")
    return daily


# ──────────────────────────────────────────────────────────────────────────────
def wape(actual, predicted):
    a, p = np.array(actual, dtype=float), np.array(predicted, dtype=float)
    mask = a > 0
    if mask.sum() == 0:
        return np.nan
    return np.abs(a[mask] - p[mask]).sum() / a[mask].sum() * 100.0


def block_bootstrap_ci(diffs, n=BOOTSTRAP_N, block_size=7, alpha=0.05):
    rng = np.random.default_rng(42)
    diffs = np.array(diffs)
    if len(diffs) == 0:
        return 0.0, 0.0
    n_blocks = math.ceil(len(diffs) / block_size)
    max_start = max(1, len(diffs) - block_size + 1)
    boot_means = []
    for _ in range(n):
        idx = rng.integers(0, max_start, size=n_blocks)
        sample = np.concatenate([diffs[i:i+block_size] for i in idx])[:len(diffs)]
        boot_means.append(sample.mean())
    lo = np.percentile(boot_means, alpha / 2 * 100)
    hi = np.percentile(boot_means, (1 - alpha / 2) * 100)
    return float(lo), float(hi)


def fit_prophet(train_df, regressors=None):
    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0,
    )
    if regressors:
        for r in regressors:
            m.add_regressor(r)
    m.fit(train_df)
    return m


def rolling_avg(train_y, horizon):
    last = train_y.tail(56).values
    return np.full(horizon, last.mean())


# ──────────────────────────────────────────────────────────────────────────────
def run_backtest(daily_sales, weather_df):
    print(f"\n[STEP 3] {N_FOLDS}-fold rolling-origin backtest ...")
    REGRESSORS = ["temp_anom", "rain_flag", "sunshine_anom", "temp_anom_x_summer"]
    MODELS     = ["prophet_only", "prophet_weather", "hybrid", "hybrid_weather", "average"]

    data = daily_sales.merge(
        weather_df[["date"] + REGRESSORS],
        on="date", how="left"
    )
    data[REGRESSORS] = data[REGRESSORS].fillna(0.0)
    data = data.sort_values("date").reset_index(drop=True)
    n = len(data)
    test_len = TEST_WEEKS * 7

    fold_ends, fold_starts = [], []
    for f in range(N_FOLDS):
        end_idx   = n - 1 - f * test_len
        start_idx = end_idx - test_len + 1
        if start_idx < 90:
            break
        fold_ends.append(end_idx)
        fold_starts.append(start_idx)
    fold_ends   = fold_ends[::-1]
    fold_starts = fold_starts[::-1]
    print(f"  Using {len(fold_ends)} actual folds")

    records = []
    for fi, (ts, te) in enumerate(zip(fold_starts, fold_ends)):
        train = data.iloc[:ts].copy()
        test  = data.iloc[ts:te+1].copy()
        if len(test) == 0 or len(train) < 90:
            print(f"  Skip fold {fi+1}: train={len(train)} test={len(test)}")
            continue

        actual   = test["y"].values
        tr_ds = train.rename(columns={"date": "ds"})[["ds", "y"] + REGRESSORS]
        te_ds = test.rename(columns={"date": "ds"})[["ds", "y"] + REGRESSORS]
        print(f"  Fold {fi+1}: train {train['date'].min().date()}->{train['date'].max().date()} "
              f"({len(train)}d)  test {test['date'].min().date()}->{test['date'].max().date()} ({len(test)}d)")

        fp = {}

        # prophet_only
        try:
            m  = fit_prophet(tr_ds[["ds", "y"]])
            fc = m.predict(te_ds[["ds"]])
            fp["prophet_only"] = np.maximum(fc["yhat"].values, 0)
        except Exception as e:
            print(f"    prophet_only FAIL: {e}")
            fp["prophet_only"] = np.full(len(test), np.nan)

        # prophet_weather
        try:
            m  = fit_prophet(tr_ds[["ds", "y"] + REGRESSORS], regressors=REGRESSORS)
            fc = m.predict(te_ds[["ds"] + REGRESSORS])
            fp["prophet_weather"] = np.maximum(fc["yhat"].values, 0)
        except Exception as e:
            print(f"    prophet_weather FAIL: {e}")
            fp["prophet_weather"] = np.full(len(test), np.nan)

        # hybrid (prophet + residual correction)
        try:
            m     = fit_prophet(tr_ds[["ds", "y"]])
            tr_fc = m.predict(tr_ds[["ds"]])
            resid = train["y"].values - np.maximum(tr_fc["yhat"].values, 0)
            rm    = resid[-28:].mean()
            fc    = m.predict(te_ds[["ds"]])
            fp["hybrid"] = np.maximum(fc["yhat"].values + rm, 0)
        except Exception as e:
            print(f"    hybrid FAIL: {e}")
            fp["hybrid"] = np.full(len(test), np.nan)

        # hybrid_weather
        try:
            m     = fit_prophet(tr_ds[["ds", "y"] + REGRESSORS], regressors=REGRESSORS)
            tr_fc = m.predict(tr_ds[["ds"] + REGRESSORS])
            resid = train["y"].values - np.maximum(tr_fc["yhat"].values, 0)
            rm    = resid[-28:].mean()
            fc    = m.predict(te_ds[["ds"] + REGRESSORS])
            fp["hybrid_weather"] = np.maximum(fc["yhat"].values + rm, 0)
        except Exception as e:
            print(f"    hybrid_weather FAIL: {e}")
            fp["hybrid_weather"] = np.full(len(test), np.nan)

        # average baseline
        fp["average"] = rolling_avg(train["y"], len(test))

        for model in MODELS:
            w = wape(actual, fp[model])
            records.append({
                "fold":       fi + 1,
                "train_end":  train["date"].max().date(),
                "test_start": test["date"].min().date(),
                "test_end":   test["date"].max().date(),
                "n_test":     len(test),
                "model":      model,
                "WAPE":       round(w, 4) if (not np.isnan(w)) else None,
            })

    return pd.DataFrame(records)


# ──────────────────────────────────────────────────────────────────────────────
def apply_decision_rule(results_df):
    print(f"\n[STEP 4] Decision rule ...")
    if results_df.empty or "WAPE" not in results_df.columns:
        print("  ERROR: no results to evaluate")
        return None

    pivot     = results_df.pivot_table(index="fold", columns="model", values="WAPE")
    mean_wape = results_df.groupby("model")["WAPE"].mean().round(4)
    print("\n  WAPE per fold:\n" + pivot.round(2).to_string())
    print("\n  Mean WAPE:\n" + mean_wape.to_string())

    no_w_models = [m for m in ["prophet_only", "hybrid", "average"] if m in mean_wape.index]
    w_models    = [m for m in ["prophet_weather", "hybrid_weather"] if m in mean_wape.index]

    bn_wape = mean_wape[no_w_models].min()
    bn_name = mean_wape[no_w_models].idxmin()
    bw_wape = mean_wape[w_models].min()
    bw_name = mean_wape[w_models].idxmin()
    impr    = bn_wape - bw_wape

    print(f"\n  Best no-weather: {bn_name}  WAPE={bn_wape:.4f}%")
    print(f"  Best weather   : {bw_name}  WAPE={bw_wape:.4f}%")
    print(f"  Improvement    : {impr:.4f} pp")

    wins, diffs = 0, []
    for fold in pivot.index:
        nw = pivot.loc[fold, bn_name] if bn_name in pivot.columns else np.nan
        ww = pivot.loc[fold, bw_name] if bw_name in pivot.columns else np.nan
        if pd.notna(nw) and pd.notna(ww):
            d = nw - ww
            diffs.append(d)
            if d > 0:
                wins += 1

    ci_lo, ci_hi = block_bootstrap_ci(diffs)
    print(f"  Fold wins      : {wins}/{len(diffs)}")
    print(f"  Bootstrap 95%CI: [{ci_lo:.4f}, {ci_hi:.4f}]")

    c1 = impr  >= IMPROVEMENT_THRESHOLD
    c2 = wins  >= MIN_FOLD_WINS
    c3 = ci_lo >  0
    decision = "KEEP" if (c1 and c2 and c3) else "REJECT"

    print(f"\n  Crit improvement >= {IMPROVEMENT_THRESHOLD} pp : {c1} ({impr:.4f})")
    print(f"  Crit wins >= {MIN_FOLD_WINS}/{N_FOLDS}          : {c2} ({wins}/{len(diffs)})")
    print(f"  Crit CI excludes 0             : {c3} [{ci_lo:.4f},{ci_hi:.4f}]")
    print(f"\n  ======= DECISION: {decision} =======")

    return {
        "decision":              decision,
        "best_no_weather_model": bn_name,
        "best_no_weather_wape":  float(bn_wape),
        "best_weather_model":    bw_name,
        "best_weather_wape":     float(bw_wape),
        "improvement_pp":        float(impr),
        "fold_wins":             wins,
        "total_folds":           len(diffs),
        "ci_lo":                 ci_lo,
        "ci_hi":                 ci_hi,
        "crit_improvement":      c1,
        "crit_wins":             c2,
        "crit_ci":               c3,
        "mean_wape":             mean_wape.to_dict(),
        "pivot":                 pivot,
        "diffs_by_fold":         diffs,
    }


# ──────────────────────────────────────────────────────────────────────────────
def run_waste_simulation(results_df, summary):
    print(f"\n[STEP 5] Waste simulation ...")
    rows = []
    for model in ["prophet_only", "hybrid", "prophet_weather", "hybrid_weather", "average"]:
        sub = results_df[results_df["model"] == model]
        if len(sub) == 0:
            continue
        wm = sub["WAPE"].mean()
        rows.append({
            "model":                  model,
            "mean_WAPE_%":            round(wm, 4),
            "implied_waste_rate":     round(0.5 * wm / 100, 6),
            "implied_shortage_rate":  round(0.5 * wm / 100, 6),
            "note":                   "newsvendor proxy: 0.5 x WAPE/100",
        })
    sim_df = pd.DataFrame(rows)
    print(sim_df.to_string(index=False))
    return sim_df


# ──────────────────────────────────────────────────────────────────────────────
def save_outputs(results_df, summary, sim_df, lat, lon):
    print(f"\n[STEP 6] Saving outputs ...")
    results_df.to_csv(OUT_CSV, index=False)
    print(f"  OK {OUT_CSV}")

    try:
        pivot_md = summary["pivot"].to_markdown(floatfmt=".2f")
    except Exception:
        pivot_md = summary["pivot"].to_string()

    mean_rows = "\n".join(
        f"| {k} | {v:.4f} |"
        for k, v in sorted(summary["mean_wape"].items(), key=lambda x: x[1])
    )
    sim_str = sim_df.to_string(index=False)

    md = f"""# RestockIQ - Weather Feature Experiment Report

**Location:** {LOCATION}
**Coordinates (Open-Meteo geocoding):** lat={lat:.4f}, lon={lon:.4f}
**Data range:** {START_DATE} to {END_DATE}
**Run date:** {date.today()}
**Decision:** **{summary['decision']}**

---

## License Notice
Open-Meteo free tier is **non-commercial use only**.
Commercial use requires a paid plan or self-hosting.
Attribution: CC BY 4.0 (https://open-meteo.com/en/terms).

---

## Pre-Registered Protocol

| Parameter | Value |
|---|---|
| Features | temp_anom, rain_flag, sunshine_anom, temp_anom x summer |
| Models | prophet_only, prophet_weather, hybrid, hybrid_weather, average |
| Folds | {N_FOLDS} rolling-origin 28-day test windows |
| KEEP threshold | WAPE improvement >= {IMPROVEMENT_THRESHOLD} pp AND wins >= {MIN_FOLD_WINS}/{N_FOLDS} AND 95% CI excludes 0 |
| Closure days | Excluded (y=0 removed - DEF-008 fix) |
| Terminology | train/serve mismatch (not data leakage) |

---

## Results

### WAPE per Fold (%)

{pivot_md}

### Mean WAPE Across Folds

| Model | Mean WAPE (%) |
|---|---|
{mean_rows}

---

## Decision Criteria

| Criterion | Required | Actual | Pass? |
|---|---|---|---|
| WAPE improvement | >= {IMPROVEMENT_THRESHOLD} pp | {summary['improvement_pp']:.4f} pp | {'PASS' if summary['crit_improvement'] else 'FAIL'} |
| Fold wins | >= {MIN_FOLD_WINS}/{N_FOLDS} | {summary['fold_wins']}/{summary['total_folds']} | {'PASS' if summary['crit_wins'] else 'FAIL'} |
| Bootstrap 95% CI excludes 0 | CI_lo > 0 | [{summary['ci_lo']:.4f}, {summary['ci_hi']:.4f}] | {'PASS' if summary['crit_ci'] else 'FAIL'} |

**Best no-weather:** `{summary['best_no_weather_model']}` WAPE {summary['best_no_weather_wape']:.4f}%
**Best weather:** `{summary['best_weather_model']}` WAPE {summary['best_weather_wape']:.4f}%

---

## Waste Simulation (Newsvendor Proxy)

```
{sim_str}
```

> waste_rate = shortage_rate = 0.5 x WAPE / 100 (symmetric error, newsvendor proxy).
> Implied rates only - not measured from inventory records.

---

## Literature References

- Guler et al. (2023): Prophet + weather + holidays achieves MAE 0.76, RMSE 0.82 (quoted from paper).
- Lalitha et al. (2025): RF/ARIMA + weather + costs achieves MSE 53.97 (quoted from paper).
- Removed unsourced claims: 80-90% accuracy, 3-7% cost savings, 1-4% waste reduction.

---

## Limitations

1. Sales data is a proxy dataset (French bakery open dataset), not Guerande-specific POS records.
2. Weather is ERA5 reanalysis; production would use 7-day Open-Meteo forecasts.
3. Open-Meteo free tier is non-commercial - commercial deployment needs paid plan or self-hosting.
4. Bootstrap CI uses block_size=7 (weekly); smaller sizes increase false positives.
5. No external holidays regressor in this experiment.
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"  OK {OUT_MD}")


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("RestockIQ Pre-Registered Weather Experiment")
    print("=" * 65)
    lat, lon     = geocode_guerande()
    weather_df   = pull_weather(lat, lon)
    daily_sales  = load_sales()
    results_df   = run_backtest(daily_sales, weather_df)
    summary      = apply_decision_rule(results_df)
    if summary is None:
        print("ABORT: backtest produced no results.")
        raise SystemExit(1)
    sim_df       = run_waste_simulation(results_df, summary)
    save_outputs(results_df, summary, sim_df, lat, lon)
    print("\n" + "=" * 65)
    print(f"EXPERIMENT COMPLETE - DECISION: {summary['decision']}")
    print("=" * 65)
