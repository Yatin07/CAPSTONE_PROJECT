# RestockIQ: Machine Learning Development Plan

This document outlines the step-by-step technical roadmap for building the complete forecasting engine in the `ML/` folder. We will transition from our current standalone Prophet scripts to the full **Adaptive Hybrid Architecture** proposed in our methodology.

---

## Phase 1: The Prophet + XGBoost Hybrid Engine
Currently, we only have Prophet. We need to implement the residual-correction architecture (inspired by Kamboj et al.) to squeeze out maximum accuracy.

1. **Base Prophet Training:** 
   - Train Prophet on historical `y` (sales) to capture the trend and weekly seasonality.
   - Run Prophet over the *training data* to generate predictions (`yhat`).
2. **Residual Calculation:** 
   - Calculate the mathematical error of Prophet: `Residual = Actual Sales (y) - Prophet Prediction (yhat)`.
3. **XGBoost Training:** 
   - Train an XGBoost Regressor where the *Target* is the `Residual`, and the *Features* are external factors (Weather, Day of Week, Is_Holiday, Is_Weekend).
4. **Hybrid Inference (The Final Output):** 
   - Future Forecast = `Prophet_Prediction + XGBoost_Predicted_Residual`.

---

## Phase 2: Weather & Holiday Integration
To make XGBoost effective, we need rich external features.
1. **Weather Data Ingestion:** Write a script to pull historical daily weather (temp, precipitation) for the location of the French Bakery/Rossmann stores.
2. **Holiday Data:** Integrate the Python `holidays` library to flag public holidays as a boolean feature (`1` or `0`).
3. **Feature Merging:** Merge these regressors into our `processed_bakery.csv` and `processed_rossmann.csv` files.

---

## Phase 3: Adaptive Branching Implementation
We must build the routing logic to handle new/sparse items vs. high-volume items.
1. **Data Depth Check:** Write a Python function that counts the number of historical sales days for a given SKU.
2. **Branch A (High-Volume):** If `history > 30 days` and `zero_sales_ratio < 40%`, route the item to the Full Prophet+XGBoost Hybrid.
3. **Branch B (Cold-Start / Sparse):** If `history < 30 days`, route to a safe fallback model (e.g., Category Moving Average) to prevent AI math crashes.

---

## Phase 4: Deterministic Restock Logic Layer
We must bridge the gap between "Demand Prediction" and "Actionable Restock Quantity".
1. **Safety Stock Calculation:** Calculate the standard deviation of demand to create a dynamic safety buffer (e.g., buffer = `1.65 * std_dev`).
2. **The Final Equation:** Write a Python function that executes:
   `Restock_Qty = Max(0, (Hybrid_Predicted_Demand + Safety_Stock) - Current_Inventory)`
3. **Validation:** Run simulations ensuring that if `Current_Inventory` is high, `Restock_Qty` correctly drops to 0.

---

## Phase 5: Evaluation & Benchmarking
We must prove mathematically that our architecture works.
1. **Metric Calculation:** Calculate RMSE and MAPE for three models on the exact same test dataset:
   - Model A: Standard XGBoost (To prove Susanto's point that standard ML fails)
   - Model B: Standalone Prophet (Our current baseline)
   - Model C: Our Custom Hybrid
2. **Success Criteria:** Prove that Model C achieves a 12-18% reduction in MAPE over Model B.

---

## Phase 6: API Preparation
Once the ML logic is mathematically sound, we prepare it for the software engineers.
1. **Modularization:** Wrap the entire pipeline into a clean Python class (e.g., `RestockIQ_Engine`).
2. **Serialization:** Save the trained Prophet/XGBoost models as `.pkl` or `.json` files.
3. **Expose `predict()`:** Ensure the system takes a JSON input `{"item_id": 101, "current_inventory": 12, "weather_tomorrow": "Rain"}` and returns `{"restock_qty": 5}` for FastAPI.

---
**Next Immediate Action:** We will begin with **Phase 1 & 2**: Building the residual calculator and injecting weather/holiday features into our processed CSVs.
