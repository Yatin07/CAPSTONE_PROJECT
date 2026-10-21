# RestockIQ Machine Learning Engine (`ML/`)

This directory houses the core demand forecasting models, automated batch inference pipeline, and experimental evaluation benches for **RestockIQ**.

---

## Directory Overview

```
ML/
├── README.md                      # This index and architecture documentation
├── batch_forecast.py              # Production nightly batch inference engine (CI/CD)
├── requirements.txt               # Python ML package dependencies
├── ML_Development_Plan.md         # Formal forecasting architecture specification
├── Backend_Integration_Plan.md    # Blueprint for MongoDB schema & FastAPI sync
├── learning_notes.md              # Exhaustive engineering log of all trials & falsifications
├── models/                        # Production forecasting model implementations
│   ├── bakery_model.py            # Primary bakery Prophet + GBDT model definition
│   ├── rossmann_model.py          # Benchmark retail model implementation
│   └── xgboost_model.py           # Gradient-boosted regressor wrapper
├── data/                          # Dataset junction mirror (raw and processed data)
│   ├── raw/                       # Historical sales datasets
│   └── processed/                 # Cleaned primary and sparse item daily rollups
└── experiments/                   # Diagnostic scripts, baselines, grid search, and plots
    ├── README.md                  # Catalog of all experimental and verification scripts
    ├── grid_search/               # Hyperparameter search pipelines and tuning logs
    ├── baselines/                 # Seasonal Naive, Moving Average, and TSB backtests
    ├── sparsity_analysis/         # Intermittent demand, zero-inflation, and prior math
    ├── verification/              # Holdout date checks, GBDT table generators, diagnostics
    └── plots/                     # Trend/seasonal decomposition and forecast visual plots
```

---

## Production Core Components

| Component | Role | Trigger / Lifecycle |
| :--- | :--- | :--- |
| **[`batch_forecast.py`](file:///e:/CAP/ML/batch_forecast.py)** | Main production inference script. Connects to MongoDB Atlas, loads historical primary item reference (`primary_items.csv`), fits Prophet decompositions, applies calibrated priors for sparse articles, calculates safety stock, and writes pre-computed forecast documents to `forecasts` collection. | Triggered nightly at 02:00 UTC via [`.github/workflows/nightly-forecast.yml`](file:///e:/CAP/.github/workflows/nightly-forecast.yml), or manually on-demand. |
| **[`requirements.txt`](file:///e:/CAP/ML/requirements.txt)** | Minimal pinned dependencies (`prophet`, `scikit-learn`, `pandas`, `pymongo[srv]`, `python-dotenv`). | Used in CI and container setup. |
| **[`models/bakery_model.py`](file:///e:/CAP/ML/models/bakery_model.py)** | Dual-tier primary model logic combining structural seasonality and gradient boosting. | Loaded by batch forecasting engine. |
| **[`ML_Development_Plan.md`](file:///e:/CAP/ML/ML_Development_Plan.md)** | Theoretical basis for hybrid decomposition and adaptive item routing. | Architecture reference. |
| **[`Backend_Integration_Plan.md`](file:///e:/CAP/ML/Backend_Integration_Plan.md)** | Schema contract between batch predictions and FastAPI read endpoints. | API integration reference. |
| **[`learning_notes.md`](file:///e:/CAP/ML/learning_notes.md)** | Complete chronological laboratory notebook documenting experimental trials, falsifications, and locked hyperparameters. | Audit & verification reference. |

---

> [!TIP]
> To inspect benchmark scripts, TSB loss landscapes, and hyperparameter tuning results, see [`ML/experiments/README.md`](file:///e:/CAP/ML/experiments/README.md).
