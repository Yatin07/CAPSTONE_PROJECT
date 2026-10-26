# RestockIQ: Final Verified Empirical Results (Single Source of Truth)

**Freeze Date:** October 26, 2026  
**Status:** ALL PHASES VERIFIED & FROZEN (No provisional figures)  
**Primary Dataset:** `ML/data/processed/primary_items.csv` (Guérande French artisan bakery dataset, 35 primary SKUs, 637 calendar days, 600 operating days)  
**Evaluation Protocols:**
1. **Full-Year High-Power Backtest:** 38 weekly rolling origins (`2022-01-02` through `2022-09-23`), 7-day forecast horizon.
2. **Summer High-Demand Backtest:** 6 weekly rolling origins (`2022-07-10` through `2022-08-21`), 7-day forecast horizon.
3. **Day-Ahead Inventory & Spoilage Simulation:** 88 operating trading days (`2022-07-03` through `2022-09-30`), 68,883 units observed demand, 2,929 SKU-days.

---

## 1. Primary Model Architecture & Scope Hierarchy

* **Shipped / Production Architecture:**
  - **Prophet Engine + Multiplicative Seasonality + French Holiday Model:** Generates core structural trend and day-of-week seasonality.
  - **Pooled Gradient-Boosted Decision Tree (`HistGradientBoostingRegressor`):** Learns residual error patterns on top of Prophet estimates.
  - **Sparse-Item Engine:** Fallback rule-based logic for low-volume lines.
  - *Status:* Shipped and active in nightly batch forecasting.
* **V2 Research Architecture (Future Work / Planned EOD Sales Feed):**
  - **Control 3 (Pure Day-Ahead GBDT with $t-1$ lag):** Achieves **25.48% pooled WAPE**, outperforming Prophet baseline by +2.47 percentage points (9% relative error reduction, $p = 0.0138$).
  - *Status:* Pre-registered for V2. Cannot be shipped in V1 because the mobile client and backend currently lack an automated midnight end-of-day POS sales rollup service.

---

## 2. Accuracy Benchmark: 38 Weekly Rolling-Origin Folds (Full Suite)

* **Source File:** `docs/accuracy_experiments_v3.csv` / `ML/experiments/accuracy/run_accuracy_experiments_v3.py`  
* **Resampling:** Paired whole-week cluster bootstrap (38 blocks, 2,000 draws).  
* **Hypothesis Testing:** Exact two-sided binomial sign-tests on fold wins ($H_0: P(\text{win}) = 0.5$).  

| Model Key | Model Description | Pooled WAPE (%) | Fold-Mean WAPE (%) | Fold Wins (vs Baseline) | Win % | Gain vs Prophet (pp) | 95% Cluster CI (38 Blocks) | Decision / Framing |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `prophet_only` | **Prophet-only (Baseline Engine)** | **27.95%** | 30.19% | — | — | 0.00 pp | [Baseline] | **Baseline Benchmark** |
| `ctrl3_gbdt_no_prophet` | **Control 3: Pure Day-Ahead GBDT (No Prophet)** | **25.48%** | 26.71% | 27/38 | 71.1% | **+2.47 pp** | [+0.49, +4.76] | **V2 Discovery ($p=0.0138$, KEEP)** |
| `model_iv_ctrl3_cal` | **Model (iv): Control 3 + Enhanced Calendar in GBDT** | **24.92%** | 26.04% | 29/38 | 76.3% | **+3.03 pp** | [+1.10, +5.52] | **Ablation (At parity with Ctrl 3, CI includes 0)** |
| `model_iii_ab` | **Model (iii): Model A + Enhanced Calendar (A+B)** | **25.47%** | 27.16% | 33/38 | 86.8% | +2.48 pp | [+1.63, +3.49] | **Ablation Study** |
| `model_a_day_ahead` | **Model A: 1-Day-Ahead Hybrid** | **26.07%** | 27.85% | 28/38 | 73.7% | +1.88 pp | [+1.01, +2.89] | **Research Variant** |
| `model_b_cal` | **Model B: Prophet + Enhanced Calendar** | **26.55%** | 28.27% | 25/38 | 65.8% | +1.40 pp | [+0.16, +2.91] | **Ablation Study** |
| `canonical_hybrid` | **Canonical Hybrid (Shipped Model)** | **28.26%** | 30.82% | 18/38 | 47.4% | -0.31 pp | [-1.45, +0.82] | **Production Shipped Engine** |
| `prophet_weather` | **Prophet + Weather (Open-Meteo API)** | **27.63%** | 30.04% | 24/38 | 63.2% | +0.32 pp | [-0.24, +0.87] | **REJECTED (CI includes 0)** |
| `model_i_prophet_res_corr` | **Control (i): Prophet + Linear AR(1) Residual Corr** | **33.04%** | 35.89% | 0/38 | 0.0% | -5.09 pp | [-5.93, -4.37] | **REJECTED (Flawed formulation)** |

### Statistical Tests Summary:
1. **Control 3 vs Prophet-only ($p = 0.0138$):** Control 3 significantly outperforms Prophet baseline across 27 of 38 folds with a 95% cluster CI strictly above zero (`[+0.49, +4.76]`).
2. **Model (iv) vs Control 3 ($p = 0.0730$):** Adding explicit holiday indicators directly into the tree yields an incremental +0.56 pp gain, but the paired cluster CI (`[-0.05, +1.26]`) crosses zero ($p > 0.05$). The tree already absorbs holiday effects through autoregressive lags.
3. **Canonical Hybrid vs Prophet-only ($p = 0.87$):** On the full 38-fold year, the hybrid operates at statistical parity with Prophet-only (no significant difference).

---

## 3. Summer High-Demand Benchmark (6 Folds, July–August 2022)

* **Source File:** `docs/backtest_results.csv`  
* **Scope:** Peak tourist season in Guérande, France (Fold 1 to Fold 6, 42 trading days).  

| Model Architecture | Pooled WAPE (%) | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Relative Gain vs Naive |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Canonical Hybrid (Shipped Model)** | **22.51%** *(22.37% with trailing pad)* | 20.30% | 22.84% | 20.25% | 21.05% | 23.95% | 26.68% | **+25.9% relative gain** |
| **Prophet-only Engine** | **21.74%** | 19.82% | 22.31% | 19.98% | 20.12% | 23.36% | 24.85% | **+28.5% relative gain** |
| **Seasonal Naive (Calendar-Aligned)** | **30.39%** | 24.52% | 29.80% | 24.12% | 31.95% | 38.45% | 33.50% | Baseline |
| **4-Week Same-Weekday Average** | **32.06%** | 25.10% | 31.20% | 25.80% | 33.40% | 40.10% | 36.75% | Baseline |
| **7-Day Moving Average** | **41.63%** | 35.20% | 40.10% | 34.50% | 43.80% | 51.20% | 45.00% | Baseline |

* **Reconciliation of Historical Figures:**
  - `23.43%`: Sourced from an early uncorrected pipeline containing buggy 4-week weekday lookups. Superseded by the calendar-aligned figure **22.51%** (zero padding) / **22.37%** (trailing padding).
  - All occurrences of 23.43% in text documents have been updated.

---

## 4. Inventory Waste & Ordering Policy Simulation (Integrity Verified)

* **Source File:** `docs/ordering_policy_experiment_v3_verified.csv`  
* **Replay Window:** July 3, 2022 to September 30, 2022 (88 operating trading days).  
* **Total Demand:** Exactly **68,883 units** across 35 SKUs (2,929 SKU-days).  
* **Accounting Assertions:** Verified across 100% of rows:
  $$\text{Baked} = \text{Sold} + \text{Waste}$$
  $$\text{Sold} = \text{Demand} - \text{Stockout}$$
  $$\text{Demand} = \text{Sold} + \text{Stockout} = 68,883\text{ units (Zero Discrepancy)}$$

### Primary Results Table (Shelf Life = 1 Day, COGS = 40%)

| Ordering Policy | Model Description | Baked Units | Sold Units | Waste Units | Waste % | Stockout Units | Stockout % | Cycle Service Level | Gross Profit (€) | Demand Check |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Critical Ratio Policy ($z = +0.2533$)** | **Control 3 (GBDT lag_1, V2)** | 70,965 | 61,991 | 8,974 | 12.7% | 6,892 | 10.0% | 69.3% | **€41,635.90** | 68,883 (PASS) |
| Critical Ratio Policy ($z = +0.2533$) | **Canonical Hybrid (Shipped)** | 66,878 | 59,366 | 7,512 | 11.2% | 9,517 | 13.8% | 59.9% | **€40,571.43** | 68,883 (PASS) |
| Critical Ratio Policy ($z = +0.2533$) | **Prophet-only (Engine)** | 66,756 | 59,161 | 7,595 | 11.4% | 9,722 | 14.1% | 59.7% | **€40,401.11** | 68,883 (PASS) |
| Critical Ratio Policy ($z = +0.2533$) | **7-Day Moving Average** | 74,494 | 61,065 | 13,429 | 18.0% | 7,818 | 11.3% | 68.8% | **€38,926.17** | 68,883 (PASS) |
| Critical Ratio Policy ($z = +0.2533$) | **Seasonal Naive (Lag 7)** | 75,282 | 60,713 | 14,569 | 19.4% | 8,170 | 11.9% | 68.0% | **€37,831.73** | 68,883 (PASS) |
| Fixed $z = 0.0$ (Zero Buffer) | Control 3 (GBDT lag_1, V2) | 67,215 | 60,325 | 6,890 | 10.2% | 8,558 | 12.4% | 60.7% | €41,466.97 | 68,883 (PASS) |
| Fixed $z = 0.0$ (Zero Buffer) | Canonical Hybrid (Shipped) | 63,279 | 57,507 | 5,772 | 9.1% | 11,376 | 16.5% | 52.1% | €40,064.14 | 68,883 (PASS) |
| Fixed $z = 0.0$ (Zero Buffer) | Prophet-only (Engine) | 62,915 | 57,138 | 5,777 | 9.2% | 11,745 | 17.1% | 51.9% | €39,824.97 | 68,883 (PASS) |
| Target 80% Service Level ($z=0.8416$) | Control 3 (GBDT lag_1, V2) | 79,718 | 64,570 | 15,148 | 19.0% | 4,313 | 6.3% | 84.4% | €40,225.26 | 68,883 (PASS) |
| Target 80% Service Level ($z=0.8416$) | Canonical Hybrid (Shipped) | 75,113 | 62,740 | 12,373 | 16.5% | 6,143 | 8.9% | 75.0% | €40,432.53 | 68,883 (PASS) |
| Target 90% Service Level ($z=1.2816$) | Control 3 (GBDT lag_1, V2) | 86,303 | 65,768 | 20,535 | 23.8% | 3,115 | 4.5% | 90.0% | €38,000.84 | 68,883 (PASS) |
| Target 95% Service Level ($z=1.6449$) | Control 3 (GBDT lag_1, V2) | 91,728 | 66,511 | 25,217 | 27.5% | 2,372 | 3.4% | 93.3% | €35,796.35 | 68,883 (PASS) |
| Target 95% Service Level ($z=1.6449$) | Canonical Hybrid (Shipped) | 86,370 | 65,505 | 20,865 | 24.2% | 3,378 | 4.9% | 88.1% | €37,647.81 | 68,883 (PASS) |
| Target 95% Service Level ($z=1.6449$) | 7-Day Moving Average | 104,929 | 66,892 | 38,037 | 36.2% | 1,991 | 2.9% | 93.9% | €29,929.56 | 68,883 (PASS) |

### Explanation of Past Profit Variations:
* **The €42,752 Quote:** Originated in preliminary exploratory code that multiplied aggregated sales units by an unweighted flat retail price ($61,991 \times 1.15 \times 0.60$) and evaluated an unconstrained model.
* **Standardized Ground Truth:** Under SKU-by-SKU retail prices, exact integer order quantities, and 100% mathematical unit accounting, peak profit is **€41,635.90** for Control 3 and **€40,571.43** for Canonical Hybrid under the Critical Ratio policy ($z = +0.2533$).

---

## 5. Weather Placebo & Negative Result

* **Source File:** `docs/weather_experiment_v2.md` / `ML/experiments/accuracy/run_weather_placebo_experiment.py`  
* **Finding:** 
  - Real meteorological features yielded an apparent gain of $+0.32$ pp on Prophet.
  - 200 random circular shifts ($k \in [30, 300]$ days) produced a placebo mean of $-0.51$ pp with CI `[-0.86, -0.20]`.
  - While real weather sat above random scrambled dates ($p < 0.0001$), circular shifting breaks annual seasonality, producing an artificial baseline.
  - Crucially, Prophet + Weather (27.63%) is $-2.15$ percentage points worse than pure autoregressive day-ahead GBDT (25.48%).
  - **Verdict:** REJECT weather in production.
