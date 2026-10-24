# RestockIQ - Weather Feature Experiment Report

**Location:** Guerande, 44350, France
**Coordinates (Open-Meteo geocoding):** lat=47.3283, lon=-2.4293
**Data range:** 2021-01-01 to 2022-09-30
**Run date:** 2026-10-24
**Decision:** **REJECT**

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
| Folds | 6 rolling-origin 28-day test windows |
| KEEP threshold | WAPE improvement >= 0.5 pp AND wins >= 4/6 AND 95% CI excludes 0 |
| Closure days | Excluded (y=0 removed - DEF-008 fix) |
| Terminology | train/serve mismatch (not data leakage) |

---

## Results

### WAPE per Fold (%)

model  average     hybrid  hybrid_weather  prophet_only  prophet_weather
fold                                                                    
1      46.1552  1697.4709       2132.9398     1696.4317        2132.2808
2      42.7330    70.6766         69.3265       71.0111          69.7423
3      42.6836    47.0711         54.8749       46.9257          54.6469
4      57.0374    55.1689         52.7157       54.4590          52.6899

### Mean WAPE Across Folds

| Model | Mean WAPE (%) |
|---|---|
| average | 47.1523 |
| prophet_only | 467.2069 |
| hybrid | 467.5969 |
| prophet_weather | 577.3400 |
| hybrid_weather | 577.4642 |

---

## Decision Criteria

| Criterion | Required | Actual | Pass? |
|---|---|---|---|
| WAPE improvement | >= 0.5 pp | -530.1877 pp | FAIL |
| Fold wins | >= 4/6 | 1/4 | FAIL |
| Bootstrap 95% CI excludes 0 | CI_lo > 0 | [-530.1877, -530.1877] | FAIL |

**Best no-weather:** `average` WAPE 47.1523%
**Best weather:** `prophet_weather` WAPE 577.3400%

---

## Waste Simulation (Newsvendor Proxy)

```
          model  mean_WAPE_%  implied_waste_rate  implied_shortage_rate                             note
   prophet_only     467.2069            2.336034               2.336034 newsvendor proxy: 0.5 x WAPE/100
         hybrid     467.5969            2.337984               2.337984 newsvendor proxy: 0.5 x WAPE/100
prophet_weather     577.3400            2.886700               2.886700 newsvendor proxy: 0.5 x WAPE/100
 hybrid_weather     577.4642            2.887321               2.887321 newsvendor proxy: 0.5 x WAPE/100
        average      47.1523            0.235761               0.235761 newsvendor proxy: 0.5 x WAPE/100
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
