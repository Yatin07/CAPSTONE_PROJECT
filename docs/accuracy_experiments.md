# RestockIQ - Pre-Registered Accuracy Experiments Report

**Dataset:** `ML/data/processed/primary_items.csv` (35 SKUs, Guérande bakery proxy dataset)  
**Evaluation Protocol:** 6 Rolling-Origin Temporal Folds (cutoff dates `2022-07-15` through `2022-09-23`)  
**Baseline to Beat:** Prophet-only (Pooled WAPE = **21.74%**)  
**Pre-Registered Decision Rule:**  
KEEP only if pooled WAPE improves by $\ge 0.5$ points, wins $\ge 4$ of 6 folds, and the block-bootstrap 95% CI strictly excludes zero ($CI_{lower} > 0$). Otherwise **REJECT**.

---

## 1. Executive Summary & Decision Table

| Experiment | Model Description | Pooled WAPE (%) | Fold-Mean WAPE (%) | Fold Wins (vs Baseline) | Bootstrap 95% CI (Improvement pp) | Pre-Registered Decision |
|---|---|:---:|:---:|:---:|:---:|:---:|
| prophet_only | Prophet-only (Verified Baseline) | **21.74%** | 22.82% | 0/6 | Baseline | **REJECT** |
| hybrid_7d | Hybrid (7-day horizon comparison) | **22.37%** | 23.41% | 3/6 | [-2.00, +0.48] | **REJECT** |
| model_a_day_ahead | Model A: 1-Day-Ahead Hybrid | **21.59%** | 22.42% | 4/6 | [-1.31, +1.53] | **REJECT** |
| model_b_calendar | Model B: Prophet + Enhanced Calendar | **21.50%** | 22.94% | 3/6 | [-0.53, +0.85] | **REJECT** |
| model_c_tier_routing | Model C: Tier Routing (Prophet/Hybrid) | **21.74%** | 22.83% | 2/6 | [-0.03, +0.03] | **REJECT** |
| model_d_ensemble_avg | Model D1: Simple Ensemble (50/50 Avg) | **21.90%** | 22.91% | 4/6 | [-0.87, +0.44] | **REJECT** |
| model_d_ensemble_wt | Model D2: Weighted Ensemble (Train-fit Wt) | **21.74%** | 22.82% | 0/6 | [+0.00, +0.00] | **REJECT** |

---

## 2. Per-Fold Performance Breakdown (WAPE %)

| Fold / Window | Prophet-only (Base) | Hybrid (7d Horizon) | Model A (1d-Ahead Hybrid) | Model B (Prophet+Cal) | Model C (Tier Routing) | Model D1 (50/50 Ensemble) | Model D2 (Weighted Ens) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Fold 1 (Early Summer Ramp) | 24.57% | 24.04% | 21.99% | 24.50% | 24.57% | 24.15% | 24.57% |
| Fold 2 (Mid-Summer Peak) | 16.50% | 16.49% | 16.34% | 16.19% | 16.44% | 16.48% | 16.50% |
| Fold 3 (August Holiday) | 18.51% | 20.56% | 21.33% | 16.68% | 18.51% | 19.47% | 18.51% |
| Fold 4 (Late Summer Turn) | 36.80% | 38.53% | 33.47% | 39.41% | 36.96% | 37.55% | 36.80% |
| Fold 5 (Autumn Normal) | 18.90% | 19.39% | 20.29% | 18.92% | 18.83% | 18.50% | 18.90% |
| Fold 6 (Late September) | 21.65% | 21.48% | 21.08% | 21.96% | 21.65% | 21.29% | 21.65% |

---

## 3. Per-Volume Tier WAPE (%)

| Model | Top 10 SKUs (High Vol) | Mid Tier SKUs | Low Tier SKUs |
|---|:---:|:---:|:---:|
| Prophet-only (Verified Baseline) | 18.43% | 30.37% | 45.40% |
| Hybrid (7-day horizon comparison) | 19.21% | 30.16% | 45.73% |
| Model A: 1-Day-Ahead Hybrid | 18.33% | 29.93% | 45.15% |
| Model B: Prophet + Enhanced Calendar | 18.15% | 30.45% | 45.13% |
| Model C: Tier Routing (Prophet/Hybrid) | 18.43% | 30.46% | 45.21% |
| Model D1: Simple Ensemble (50/50 Avg) | 18.65% | 30.22% | 45.40% |
| Model D2: Weighted Ensemble (Train-fit Wt) | 18.43% | 30.37% | 45.40% |

---

## 4. Experiment-by-Experiment Analysis

### Experiment A: 1-Day-Ahead Evaluation
- **Methodology:** Rather than assuming static 7-day horizon features, daily store re-ordering operates day-ahead. For each test day $t$, actual sales up to $t-1$ are ingested to compute `y_lag_1`, `y_lag_7`, and `rolling_7` mean prior to making predictions.
- **Results:**
  - Old 7-Day Horizon Hybrid: **23.43%** pooled WAPE.
  - 1-Day-Ahead Hybrid: **21.59%** pooled WAPE (Fold wins: 4/6 vs Prophet baseline).
- **Decision:** **REJECT**. Day-ahead evaluation demonstrates substantial improvement over the 7-day batch horizon, showing that recent lag information is a primary driver of GBDT performance.

### Experiment B: Calendar Features for Prophet
- **Features Tested:**
  1. Public holiday windows: `lower_window = -1`, `upper_window = +1` around French statutory holidays.
  2. Bridge days ("ponts"): e.g. Ascension Friday.
  3. Official French School Holidays: Zone B (Académie de Nantes, covering Guérande) from `data.education.gouv.fr`.
- **Source Citation:** `VERIFIED (data.education.gouv.fr: fr-en-calendrier-scolaire, Nantes Academy / Zone B)`.
- **Results:** Pooled WAPE = **21.50%** vs baseline 21.74% (Improvement: +0.24 pp, 3/6 wins).
- **Decision:** **REJECT**.

### Experiment C: Tier Routing
- **Methodology:** Time-based validation inside each fold's training history (last 28 days of training set). For each volume tier (Top 10, Mid, Low), the model with lower inner validation WAPE is selected, with zero test leakage.
- **Results:** Pooled WAPE = **21.74%** (2/6 wins).
- **Decision:** **REJECT**.

### Experiment D: Simple & Weighted Ensembles
- **Methodology:**
  - Model D1 (Equal weight): $0.5 \times \text{Prophet} + 0.5 \times \text{Hybrid}$.
  - Model D2 (Trained weight): $w \times \text{Prophet} + (1-w) \times \text{Hybrid}$, where $w$ is optimized via 1D grid search on the inner validation window.
- **Results:**
  - Simple 50/50 Ensemble: **21.90%** pooled WAPE (4/6 wins).
  - Weighted Ensemble: **21.74%** pooled WAPE (0/6 wins).
- **Decision:** **REJECT** / **REJECT**.

---

## 5. Limitations
1. **Single Store Dataset:** The data originates from a single artisan French bakery. Store-specific patterns (local weekly opening schedules, neighborhood foot traffic) may not generalize to multi-store chain operations.
2. **Short History Horizon (1.7 Years):** The series spans 2021-01-02 to 2022-09-30 (~600 open trading days). Training windows of 1.5 years capture only one full seasonal cycle, limiting the degrees of freedom for estimating higher-order yearly Fourier terms.
3. **ERA5 vs Forecast Weather Discrepancy:** ERA5 is an atmospheric reanalysis product using post-event observations, whereas operational forecasting relies on 1-7 day numerical weather forecasts subject to forecast error. However, testing both ERA5 and the Open-Meteo Historical Forecast API confirmed that neither yields a statistically significant accuracy gain.
