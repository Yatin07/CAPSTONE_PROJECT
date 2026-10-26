# RestockIQ - 38-Fold Weekly Rolling Accuracy Report (High-Power Suite)

**Dataset:** `ML/data/processed/primary_items.csv` (35 SKUs, Guérande bakery proxy dataset)  
**Evaluation Protocol:** 38 Weekly Rolling-Origin Temporal Folds (cutoff dates `2022-01-02` through `2022-09-23`)  
**Forecast Horizon:** 7 days per fold (consecutive out-of-sample trading days)  
**Execution Runtime:** 803.9 seconds (13.40 minutes) parallelized across 16 CPU cores  
**Pre-Registered Decision Rule:**  
KEEP only if pooled WAPE improves by $\ge 0.5$ points, wins $\ge 60\%$ of folds ($\ge 23/38$), and the block-bootstrap 95% CI strictly excludes zero ($CI_{lower} > 0$). Otherwise **REJECT**.

---

## 1. Executive Summary & Decision Table

> **Side-by-Side Accuracy Scale Comparison:**
> - **6 Summer Ramp Folds (July–September 2022, Peak Season):** Prophet-only = **21.74%** pooled WAPE, Canonical Hybrid = **22.37%** (or **22.51%** without trailing padding).
> - **38 Weekly Rolling Folds (January–September 2022, Full Year):** Prophet-only = **27.95%** pooled WAPE, Canonical Hybrid = **28.26%**, Model A (1-Day-Ahead Hybrid) = **26.06%**, Model B (Prophet+Calendar) = **26.55%**.

### A. Overall (All 38 Rolling Folds: ~266 Out-of-Sample Days)
| Model | Pooled WAPE (%) | Fold-Mean WAPE (%) | Fold Wins | Win % | Bootstrap 95% CI (Improvement pp) | Pre-Registered Decision |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Prophet-only (Baseline) | **27.95%** | 30.19% | 0/38 | 0.0% | Baseline | **Baseline** |
| Hybrid (Corrected) | **28.26%** | 30.16% | 19/38 | 50.0% | [-0.87, +0.27] | **REJECT** |
| 1-Day-Ahead Hybrid (Model A) | **26.06%** | 27.83% | 29/38 | 76.3% | [+1.17, +2.64] | **KEEP** |
| Prophet + Enhanced Calendar (Model B) | **26.55%** | 28.27% | 25/38 | 65.8% | [+0.70, +2.12] | **KEEP** |
| Prophet + Weather (Forecast API) | **27.63%** | 30.04% | 24/38 | 63.2% | [+0.00, +0.64] | **REJECT** |

### B. Split by Training History Horizon
#### 1. Folds with $\ge 540$ Calendar Days Training History (14 Folds, Peak Season June–Sept 2022)
| Model | Pooled WAPE (%) | Fold-Mean WAPE (%) | Fold Wins | Win % | Bootstrap 95% CI | Decision |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Prophet-only (Baseline) | **23.53%** | 24.49% | 0/13 | 0.0% | Baseline | **Baseline** |
| Hybrid (Corrected) | **24.33%** | 25.29% | 5/13 | 38.5% | [-1.82, +0.15] | **REJECT** |
| 1-Day-Ahead Hybrid (Model A) | **22.32%** | 22.99% | 9/13 | 69.2% | [+0.13, +2.26] | **KEEP** |
| Prophet + Enhanced Calendar (Model B) | **22.87%** | 24.01% | 8/13 | 61.5% | [+0.24, +1.09] | **KEEP** |
| Prophet + Weather (Forecast API) | **22.55%** | 23.70% | 11/13 | 84.6% | [+0.53, +1.40] | **KEEP** |

#### 2. Folds with $< 540$ Calendar Days Training History (24 Folds, 365–539 Days, Jan–June 2022)
| Model | Pooled WAPE (%) | Fold-Mean WAPE (%) | Fold Wins | Win % | Bootstrap 95% CI | Decision |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Prophet-only (Baseline) | **32.26%** | 33.15% | 0/25 | 0.0% | Baseline | **Baseline** |
| Hybrid (Corrected) | **32.08%** | 32.68% | 14/25 | 56.0% | [-0.57, +0.91] | **REJECT** |
| 1-Day-Ahead Hybrid (Model A) | **29.70%** | 30.35% | 20/25 | 80.0% | [+1.71, +3.49] | **KEEP** |
| Prophet + Enhanced Calendar (Model B) | **30.13%** | 30.48% | 17/25 | 68.0% | [+0.85, +3.51] | **KEEP** |
| Prophet + Weather (Forecast API) | **32.58%** | 33.34% | 13/25 | 52.0% | [-0.67, +0.03] | **REJECT** |

---

## 2. Statistical Methodology & Bootstrap Parameters
- **Resampling Method:** Block bootstrap resampling 7-day blocks (matching the forecast horizon) with replacement, 2,000 draws.
- **Block size:** 7 consecutive daily predictions per SKU.
- **Number of blocks ($n_{blocks}$):** ~1,200 blocks covering 266 distinct out-of-sample days and 8,600+ individual test SKU-days.
- **Handling of Closure Days in `lag_1`:**
  - The series operates on open trading days.
  - When the bakery is closed (e.g. Wednesday), Thursday's `lag_1` pulls **Tuesday's observed demand** (the most recent open trading day).
  - *Operational Justification:* In fresh artisan baking, using the last operating day's sales correctly captures the underlying operational volume rather than inserting a false 0.0, which would distort Thursday morning prep orders.

---

## 3. Analysis & Key Takeaways
1. **Model A (1-Day-Ahead Hybrid):** Demonstrates consistent outperformance across the 38-week timeline compared to the 7-day horizon models, reducing pooled WAPE by incorporating actual prior-day demand.
2. **Prophet-only Robustness:** Prophet-only remains a formidable baseline across diverse seasons, requiring no lag feature updates for multi-day horizons.
3. **Weather Rejection Reconfirmed:** Even across 38 weekly folds, Open-Meteo Historical Forecast weather yields no statistically significant gain, reconfirming the decision to **REJECT** weather features.

---

## 4. Limitations
1. **Single artisan store:** Proxy dataset from one French bakery; findings should be verified when onboarding multi-store retail chains.
2. **History length (1.7 years):** Folds in early 2022 trained on ~1 year of data, limiting seasonal Fourier term resolution.
3. **Point estimates only:** Production API serves strictly point forecasts without widening interval complexity.
