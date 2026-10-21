# RestockIQ ML Experiments & Diagnostic Catalog (`ML/experiments/`)

This directory contains research benchmarks, hyperparameter tuning pipelines, baseline models, intermittent demand analyses, and diagnostic verification scripts developed during the evaluation of the RestockIQ forecasting engine.

---

## Catalog by Subdirectory

### 1. `grid_search/` (Hyperparameter Tuning)
| Script / Artifact | Description |
| :--- | :--- |
| **`grid_search_pipeline.py`** | Multi-process grid search evaluating combinations of Prophet changepoint prior scales (`[0.01, 0.05, 0.1, 0.3, 0.5]`), seasonality prior scales (`[0.1, 1, 10]`), and seasonality modes (`additive` vs `multiplicative`) cross-trained with gradient boosting trees. |
| **`targeted_grid.py`** | Focused fine-grained grid search around top-performing hyperparameter clusters. |
| **`print_grid.py`** | Terminal formatting utility to parse and rank results from grid search runs. |
| **`test_max_depth.py`** | Sensitivity check on tree `max_depth` to prevent over-fitting on high-volume days. |
| **`grid_search_results.csv`** | Tabulated out-of-sample metrics (WAPE, MAE) for all evaluated hyperparameter configurations. |

### 2. `baselines/` (Benchmarks & Intermittent Models)
| Script / Artifact | Description |
| :--- | :--- |
| **`naive_baselines_simulation.py`** | Implements and evaluates baseline forecasting heuristics: 7-Day Moving Average, Seasonal Naive (same weekday last week), and Historical Item Mean. |
| **`naive_baselines_simulation2.py`** | Extended evaluation of 4-Week Same-Weekday Average baseline against test period data. |
| **`calculate_metrics.py`** | Utility to calculate WAPE (Weighted Absolute Percentage Error), MAE, and RMSE across model predictions. |
| **`tsb_backtest.py`** | Backtesting implementation of the Teunter-Syntetos-Babai (TSB) method designed specifically for intermittent and lumpy demand items. |
| **`tsb_hb_backtest.py`** | Hierarchical Bayesian Credibility implementation fading between category prior percentiles and item-level TSB forecasts based on sample size $n$. |
| **`analyze_tsb_loss.py`** | Loss surface mapping over grid of $(\alpha, \beta)$ smoothing constants to identify global minimum error. |
| **`analyze_tsb_ties.py`** | Edge-case analysis of tie-breaking behavior during prolonged zero-demand streaks. |

### 3. `sparsity_analysis/` (Intermittent Demand & Priors)
| Script / Artifact | Description |
| :--- | :--- |
| **`check_sparse.py`** | Dataset profiler identifying items with average daily demand $< 10$ units to route into Tier 2. |
| **`check_sparse_zeros.py`** | Zero-demand frequency calculator measuring sparsity percentages across catalog items. |
| **`create_sparse_categories.py`** | Maps sparse menu articles into 5 domain categories (`Breads & Baguettes`, `Viennoiserie`, `Patisserie / Desserts`, `Savory Food / Lunch`, `Beverages & Sweets`). |
| **`calc_priors.py`** | Computes empirical category priors (mean and standard deviation) for cold-start initialization. |
| **`calc_priors_percentiles.py`** | Computes 90th percentile demand priors per category to prevent stockouts on intermittent articles. |
| **`brioche_check.py`** | Individual trace inspection on the `Brioche` article to audit model transitions during volatility spikes. |

### 4. `verification/` (Diagnostics & Verification)
| Script / Artifact | Description |
| :--- | :--- |
| **`diagnostic.py`** | General sanity checker confirming dataframe integrity, column naming, and date formatting. |
| **`cutoff_check.py` / `cutoff_check_2.py`** | Verifies strict chronological train/test separation to guarantee zero temporal data leakage. |
| **`check_deps.py`** | Python environment validator testing for compatible `prophet`, `cmdstanpy`, and `scikit-learn` installations. |
| **`check_misc.py`** | Helper for validating transient intermediate data structures during pipeline refactoring. |
| **`process_datasets.py`** | Pipeline that cleans raw transaction records and generates daily article sums (`ds`, `article`, `y`). |
| **`reprocess_bakery.py`** | Re-aggregates bakery sales data to incorporate tourist season indicators (`month in [7, 8]`). |
| **`update_model.py`** | Retraining script that refreshes serialized model weights and priors. |
| **`global_model.py` / `global_model_verification.py`** | Verifies the cross-article pooled `HistGradientBoostingRegressor` trained on all items simultaneously. |
| **`xgboost_verification.py` / `xgboost_full_table.py`** | Verification scripts evaluating XGBoost gradient-boosted decision tree performance across all articles. |
| **`bakery_run.log`** | Execution and convergence log captured during full bakery model fit. |

### 5. `plots/` (Visualization Artifacts)
*   **`bakery_components.png`**: Decomposition showing structural trend, weekly day-of-week seasonality, and annual tourist spikes.
*   **`bakery_forecast.png`**: Out-of-sample forecast overlay against actual bakery sales.
*   **`rossmann_components.png`**: Trend and seasonal decomposition on the Rossmann retail benchmark dataset.
*   **`rossmann_forecast.png`**: Forecast overlay on the Rossmann validation partition.
