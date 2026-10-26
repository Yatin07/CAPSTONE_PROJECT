# RestockIQ - Weather Feature Experiment v2 (Corrected)

**Location:** Guérande, 44350, France  
**Coordinates (geocoded):** lat=47.32829, lon=-2.42934  
**Weather Sources Evaluated:**
1. **ERA5 Reanalysis** via Open-Meteo archive API (non-commercial only, CC BY 4.0)
2. **Historical Forecast API** via Open-Meteo (`historical-forecast-api.open-meteo.com/v1/forecast`, covers full range 2021-01-01 to 2022-09-30)

**Run date:** 2026-10-25  
**Final Decision:** **REJECT**  

> This report supersedes the INVALID docs/weather_experiment.md (commit 76c31115).

---

## 1. Pre-Registered Decision Rule
Adopt weather features **IF AND ONLY IF**:
1. Weather model beats the BEST no-weather model by $\ge 0.5$ points pooled WAPE.
2. Wins $\ge 4$ of 6 rolling folds.
3. Block-bootstrap 95% confidence interval of improvement strictly excludes zero ($CI_{lower} > 0$).

*(The previously drafted '< 1.0 pp single-fold degradation' rule was non-standard and has been completely removed).*

---

## 2. Model Performance Summary (Pooled vs Fold-Mean WAPE)

> **Accuracy Scope Note:** Metrics in this table reflect the **6 summer ramp folds (July–September 2022)** where Prophet-only achieves **21.74%** pooled WAPE and Hybrid achieves **22.37%** (or **22.51%** depending on trailing history padding). Evaluated across the full-year **38 weekly rolling folds (January–September 2022)**, Prophet-only achieves **27.95%** pooled WAPE and Hybrid achieves **28.26%** (see `docs/accuracy_experiments_v2.md`).

| Model | Pooled WAPE (%) | Fold-Mean WAPE (%) | Fold Wins (vs Baseline) | Bootstrap 95% CI (Improvement pp) | Decision |
|---|:---:|:---:|:---:|:---:|:---:|
| Prophet-only (Baseline) | **21.74%** | 22.82% | 0/6 | Baseline | **Baseline** |
| Prophet + ERA5 Weather | **21.87%** | 23.00% | 1/6 | [-0.48, +0.23] | **REJECT** |
| Prophet + Forecast Weather | **21.87%** | 23.05% | 1/6 | [-0.50, +0.27] | **REJECT** |
| Hybrid (Baseline) | **22.37%** | 23.41% | 3/6 | [-2.00, +0.48] | **Benchmark** |
| Hybrid + ERA5 Weather | **22.62%** | 23.73% | 0/6 | [-1.99, +0.34] | **REJECT** |
| Hybrid + Forecast Weather | **22.44%** | 23.50% | 0/6 | [-1.72, +0.41] | **REJECT** |
| Average (Prophet + Hybrid) | **21.90%** | 22.91% | 4/6 | [-0.87, +0.44] | **REJECT** |
| Average (Prophet + Hybrid) + ERA5 | **21.84%** | 22.86% | 2/6 | [-0.73, +0.52] | **REJECT** |
| Average (Prophet + Hybrid) + Forecast | **21.78%** | 22.82% | 3/6 | [-0.66, +0.56] | **REJECT** |

*Note on Metrics: **Pooled WAPE** is $\frac{\sum |y - \hat{y}|}{\sum y} \times 100$ across all test predictions (primary metric matching store-level inventory loss). **Fold-Mean WAPE** is the simple unweighted mean of the 6 individual fold WAPEs.*

---

## 3. Per-Volume Tier WAPE (%)

| Model | Top 10 SKUs (High Vol) | Mid Tier SKUs | Low Tier SKUs |
|---|:---:|:---:|:---:|
| Prophet-only (Baseline) | 18.43% | 30.37% | 45.40% |
| Prophet + ERA5 Weather | 18.57% | 30.80% | 44.94% |
| Prophet + Forecast Weather | 18.57% | 30.82% | 44.97% |
| Hybrid (Baseline) | 19.21% | 30.16% | 45.73% |
| Hybrid + ERA5 Weather | 19.53% | 30.21% | 45.59% |
| Hybrid + Forecast Weather | 19.29% | 30.16% | 45.83% |
| Average (Prophet + Hybrid) | 18.65% | 30.22% | 45.40% |
| Average (Prophet + Hybrid) + ERA5 | 18.60% | 30.43% | 44.89% |
| Average (Prophet + Hybrid) + Forecast | 18.52% | 30.37% | 44.99% |

---

## 4. Per-Fold WAPE Matrix (%)

| Fold / Window | Prophet-only | Prophet+ERA5 | Prophet+Fcst | Hybrid | Hybrid+ERA5 | Hybrid+Fcst | Avg(Prophet,Hybrid) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Fold 1 (Early Summer Ramp) | 24.57% | 24.09% | 23.97% | 24.04% | 25.15% | 25.28% | 24.15% |
| Fold 2 (Mid-Summer Peak) | 16.50% | 16.84% | 16.88% | 16.49% | 16.98% | 16.70% | 16.48% |
| Fold 3 (August Holiday) | 18.51% | 18.78% | 18.64% | 20.56% | 19.85% | 19.66% | 19.47% |
| Fold 4 (Late Summer Turn) | 36.80% | 36.86% | 37.10% | 38.53% | 37.76% | 37.58% | 37.55% |
| Fold 5 (Autumn Normal) | 18.90% | 19.41% | 19.37% | 19.39% | 19.22% | 19.30% | 18.50% |
| Fold 6 (Late September) | 21.65% | 22.05% | 22.37% | 21.48% | 23.39% | 22.50% | 21.29% |

---

## 5. ERA5 vs Historical Forecast API

- **Why ERA5 was initially selected:** In Open-Meteo documentation, `archive-api.open-meteo.com` defaults to ERA5 reanalysis (the gold standard for historical climate backtesting). The dedicated Historical Forecast API (`historical-forecast-api.open-meteo.com`) is a newer endpoint providing archived Numerical Weather Prediction (NWP) model runs.
- **Coverage Check:** The Historical Forecast API was queried for Guérande coordinates (`lat=47.32829, lon=-2.42934`) from `2021-01-01` to `2022-09-30`. It returned **638 days (100% complete, 0 nulls)**.
- **Evaluation Finding:** Re-running the entire ablation with Historical Forecast weather confirms that weather features provide no statistically significant gain:
  - `Prophet + Forecast` pooled WAPE is **21.87%** (vs 21.74% baseline, $-0.13$ pp change, 1/6 fold wins).
  - `Hybrid + Forecast` pooled WAPE is **22.44%** (vs 22.37% baseline, $-0.07$ pp change, 0/6 fold wins).
  - Neither ERA5 reanalysis nor live forecast weather passes the pre-registered threshold.

---

## 6. Lag vs Rolling Features in Models
- **Standard 7-day Horizon Hybrid:** Uses fixed same-weekday lags (`y_lag_7`, `y_lag_14`, `y_lag_21`, `y_lag_28` via `pred_weekday4w`) and a cutoff-level historical rolling average (`pred_ma7`). It does NOT use $t-1$ lag because days $t+2$ through $t+7$ do not have prior-day observations available at forecast cutoff.
- **1-Day-Ahead Hybrid (evaluated in Accuracy Suite):** Evaluated strictly day-ahead, enabling dynamic `y_lag_1` and `y_roll_7` (7-day trailing mean of actual open days) computed exclusively from sales prior to each forecast day.

---

## 7. Open-Meteo Licensing & Literature Summary
- **Commercial Status:** Open-Meteo free tier is **NON-COMMERCIAL ONLY**. Any production or commercial SaaS deployment requires a paid commercial subscription or self-hosted instance (open source CC BY 4.0).
- **Literature Reference Verification:**
  - *Güler et al. (2023)*: Reports Prophet + weather + holidays achieving MAE 0.76, RMSE 0.82 on retail food series.
  - *Lalitha et al. (2025)*: Reports RF/ARIMA + weather + inventory cost optimization achieving MSE 53.97.
  - *Unsourced claims* ("80-90%", "3-7%", "1-4%") have been excised.
