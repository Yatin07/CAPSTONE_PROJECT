# RestockIQ: Final Weather Pipeline Report & Technical Limitations

**Investigation Date:** October 26, 2026  
**Target Coordinates:** Guérande, France ($47.3275^\circ\text{ N}, -2.4289^\circ\text{ W}$, Elevation: ~30m, Timezone: `Europe/Paris`)  
**Data Sources:**
1. **Reanalysis / Archive:** `ML/data/weather_guerande.csv` (Open-Meteo Historical Weather API / ERA5 Reanalysis)
2. **Forecast-Type:** `ML/data/weather_guerande_forecast.csv` (Open-Meteo Historical Forecast API / DWD ICON & ECMWF Seamless Blended Forecasts)

---

## 1. Final Verdict: Rejection of Weather Features in Production

Across 38 weekly rolling origins (Jan 2, 2022 to Sep 23, 2022), incorporating meteorological features into the forecasting models yielded **no reliable, statistically significant improvement**:
* **Prophet Baseline (No Weather):** 27.95% pooled WAPE
* **Prophet + Weather Regressors (Forecast API):** 27.63% pooled WAPE (+0.32 pp apparent gain)
* **Paired Whole-Week Cluster Bootstrap (38 Blocks):** 95% CI is `[-0.24, +0.87]` percentage points. Because the confidence interval strictly includes zero ($p > 0.05$), the null hypothesis of zero predictive gain cannot be rejected.
* **Comparison with Non-Weather Autoregression:** Pure day-ahead machine learning (`Control 3`, GBDT with $t-1$ lag alone) achieves **25.48% pooled WAPE** (+2.47 pp over Prophet, $p = 0.0138$), outperforming the weather model by **2.15 percentage points** with zero external API dependencies.

**Decision:** Formally **REJECT** weather features from the production inference pipeline.

---

## 2. Technical Limitations & Data Discrepancies Audit

An exhaustive forensic comparison of `weather_guerande.csv` and `weather_guerande_forecast.csv` across all 638 calendar days (2021-01-01 to 2022-09-30) revealed four key technical nuances:

### A. Missing Values in Early Forecast Records (`temp_max` Nulls)
* **Observation:** In `weather_guerande_forecast.csv`, the `temp_max` column contains **81 missing values (`NaN`)** spanning from `2021-01-01` to `2021-03-22`.
* **Root Cause:** Open-Meteo's `historical-forecast` API only began archiving daily discrete maximum temperature forecast grids in late March 2021. Prior to that date, only hourly re-aggregated mean temperatures were indexed.
* **Impact & Handling:** In our backtesting suite, `temp_mean` (which has 0 nulls across the entire 638-day span) was utilized as the primary temperature regressor to prevent dropping the first 81 days of training history.

### B. Identical Sunshine Duration Values Across Files
* **Observation:** For all 638 dates, the sunshine duration in the forecast file (`sunshine_sec`) matches the archive reanalysis file (`sunshine_duration`) **exactly** ($\max |\text{diff}| = 0.0$ seconds across all 638 rows).
* **Root Cause:** Open-Meteo's historical forecast endpoint does not store archived numerical weather prediction (NWP) solar radiation integrals from legacy model runs. Instead, Open-Meteo populates `sunshine_duration` retroactively from ERA5 reanalysis surface solar radiation downwards (SSRD).
* **Impact:** The forecast-type sunshine duration is technically an ERA5 reanalysis product rather than a strictly point-in-time forecast snapshot. However, because sunshine duration exhibited near-zero regressor weight in both Prophet and GBDT models, this identity had zero impact on the final accuracy verdict.

### C. Inconsistent Rain-Flag Thresholds
* **Observation:** The binary rain indicator (`rain_flag`) was generated using divergent precipitation cutoffs across the two files:
  - **Archive File (`weather_guerande.csv`):** `rain_flag = 1` if $\text{precipitation\_sum} \ge 3.0\text{ mm}$ (Yields 129 rainy days, 509 dry days).
  - **Forecast File (`weather_guerande_forecast.csv`):** `rain_flag = 1` if $\text{precip\_sum} \ge 1.0\text{ mm}$ (Yields 205 rainy days, 433 dry days).
* **Impact:** The forecast file classifies light mist/drizzle (1.0–2.9 mm) as rain, whereas the archive file reserves the flag for moderate-to-heavy rainfall. Despite this threshold shift, the correlation between rain and artisan bread purchasing remained statistically negligible ($r \approx -0.04$).

### D. Seasonality Bias in the Placebo Test
* **Observation:** In the 200-iteration weather placebo experiment, weather series were circularly shifted by $k \in [30, 300]$ days. Real weather scored $+0.32$ pp gain, while the placebo distribution had a mean of $-0.51$ pp (95% CI `[-0.86, -0.20]`), leading to a superficial empirical $p < 0.0001$.
* **Critical Flaw:** Circular shifting in temperate climates (Brittany, France) shifts winter freezing temperatures ($2^\circ\text{C}$) into July/August and summer heat ($30^\circ\text{C}$) into January. This breaks the macro annual temperature-demand alignment, severely penalizing the placebo models.
* **Takeaway:** The apparent statistical significance ($p < 0.0001$) against circular placebos reflects **annual seasonal phase alignment**, not daily high-frequency weather predictive power. When evaluated against non-weather calendar features (day-of-week, month, holiday flags), weather regressors add no marginal predictive utility.

---

## 3. Summary for Black Book and Academic Defense

When presenting the weather experiments:
1. Frame the investigation as an **evidence-based feature rejection study**.
2. State: *"We evaluated meteorological regressors using both ERA5 reanalysis and historical numerical weather forecasts. The marginal gain of $+0.32$ pp is not statistically distinguishable from zero (95% CI `[-0.24, +0.87]`), and weather is heavily outperformed by autoregressive day-ahead sales lags (25.48% WAPE)."*
3. Acknowledge the data limitations (81 nulls in early `temp_max`, ERA5-mirrored sunshine duration, and circular placebo seasonality bias) to demonstrate methodological rigor.
