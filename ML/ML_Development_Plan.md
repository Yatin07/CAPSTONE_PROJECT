# RestockIQ: Machine Learning Development Plan (Corrected)

This supersedes the initial draft. Structural issues fixed: missing inventory source, a pre-decided result target, invented cold-start thresholds, and two missing modules (waste action engine, India holdout). See changelog at bottom for exact diffs.

## Phase 1: Prophet + XGBoost Hybrid Engine
*   **Base Prophet Training** — train on historical `y` (sales) per dataset to capture trend + weekly seasonality; generate in-sample `yhat`.
*   **Residual Calculation** — `Residual = Actual Sales (y) − Prophet Prediction (yhat)`.
*   **XGBoost Training** — target = `Residual`; features = `lag_1`, `lag_7`, `rolling_7day_avg`, `day_of_week`, `is_weekend`, `month`, `promo` (Rossmann only), `is_holiday`.
*   **Hybrid Inference** — `Forecast = Prophet_Prediction + XGBoost_Predicted_Residual`.

## Phase 2: Holiday Feature Integration (weather dropped — see note)
*   **Holiday flags** — per-dataset-correct calendars, not one generic call:
    *   French Bakery → `holidays.France()`
    *   Rossmann → `holidays.Germany()` (or use Rossmann's native StateHoliday/SchoolHoliday columns if present — check first, real data beats a library guess)
    *   Store Sales Price Elasticity → `holidays.UnitedStates()` (confirm country from dataset docs first)
*   **Feature merge** into `processed_bakery.csv`, `processed_rossmann.csv`, etc.
*   **Weather** — do NOT commit to this until feasibility is checked. Requires confirmed store geolocation in each dataset. If location data isn't precise/available, drop this feature rather than pulling mismatched weather data. Check this first; don't build assuming it'll work.

## Phase 3: Inventory Simulator 
*No dataset has real "current inventory on hand" — this must be simulated before the restock formula can be tested at all.*
*   **Day 1:** `current_inventory = 0`.
*   **Each day:** `restock_qty = max(0, predicted_demand + safety_stock − current_inventory)`.
*   **After the day:** `leftover = max(0, current_inventory + restock_qty − actual_sales)`.
*   **Perishable flag:** if perishable, leftover → 0 next day (thrown away); if non-perishable, leftover carries forward as next day's `current_inventory`.
*   **Output:** total demand, total sales, total restock ordered, total waste — this becomes the backtest proof that restock logic prevents compounding over-ordering.

## Phase 4: Adaptive Cold-Start Branching 
*Use the already-agreed 3-phase progressive-confidence model — not invented thresholds:*
*   **Day 1–13:** category-level prior (e.g., category moving average) — insufficient history for Prophet/XGBoost to be reliable.
*   **Day 14–30:** blended forecast (weighted mix of category prior and emerging item-level Prophet signal).
*   **Day 30+:** fully user-trained Prophet+XGBoost hybrid. 
*   *Note: This routing logic replaces the previous history > 30 days / zero_sales_ratio < 40% branch — those numbers weren't part of the agreed design and shouldn't silently override it.*

## Phase 5: Deterministic Restock Logic Layer
*   **Safety stock** — `1.65 * std_dev(demand)` as the dynamic buffer.
*   **Final equation** — `Restock_Qty = Max(0, (Hybrid_Predicted_Demand + Safety_Stock) − Current_Inventory)`, where `Current_Inventory` comes from the Phase 3 simulator, not assumed.
*   **Validation** — confirm `Restock_Qty` correctly drops to 0 when simulated leftover inventory is high.

## Phase 6: Waste Action Engine 
*Sits alongside Phase 5, same day — addresses stock that's already sitting unsold, not just next-day ordering.*
*   `sales_pace_ratio = actual_sales_so_far / predicted_demand_so_far`.
*   If `sales_pace_ratio < 0.6` (tune this threshold): flag item for a waste action.
*   **Perishable + low pace, earlier in day:** recommend discount %, calibrated using the Store Sales Price Elasticity dataset (repurposed here as discount-to-demand-lift calibration source — not just another forecasting dataset).
*   **Perishable + very low pace, late in day:** recommend donate/staff-meal instead of discount.
*   **Non-perishable + low pace:** no action — already handled correctly by the simulator's carry-forward logic.
*   **Output:** `{waste_risk, recommended_action, discount_pct}`.

## Phase 7: Evaluation & Benchmarking
*   **Metrics** — RMSE, MAE, MAPE, computed identically across:
    *   Model A: Standalone XGBoost
    *   Model B: Standalone Prophet (current baseline)
    *   Model C: Custom Hybrid
*   **Time-series split only** — no random shuffling; last 15–20% chronologically as test set, per dataset.
*   **Report the actual result, whatever it is.** No pre-set target percentage — the improvement (or lack of it) over Model B is measured, not decided in advance. If Model C underperforms on any dataset, report that honestly; it's still a valid, defensible finding.

## Phase 8: Final Holdout Validation — Indian Dataset
*Separate from Phases 1–7. Purpose: test generalization of a model trained on non-Indian data, not train on India.*
*   **Inspect candidate** (e.g. `abuhumzakhan/store-data`) for: true daily granularity, food-category relevance, 1+ year continuity, sufficient volume per series.
*   **Do not touch this dataset during training/tuning** — any influence on the model before this step invalidates it as a generalization test.
*   **Normalize metrics** (MAPE, not raw RMSE/MAE) before comparing across currencies (₹ vs €/$).
*   **Report the generalization gap honestly** — expected to underperform vs. same-market test splits. Note what India-specific fine-tuning (e.g., `holidays.India()`, already supported by Prophet natively) would do to close that gap in a real deployment, without claiming deployment-readiness now.

## Phase 9: API Preparation
*   **Modularize** — wrap the full pipeline (hybrid model + simulator + restock logic + waste action engine) into a clean class (e.g. `RestockIQ_Engine`).
*   **Serialize** — save trained models as `.pkl/.json`.
*   **Expose `predict()`** — input `{"item_id": 101, "current_inventory": 12}` → output `{"restock_qty": 5, "predicted_demand": 15, "waste_action": {"risk": "low", "action": "none"}}`. (Weather field dropped unless Phase 2 feasibility check passes.)

---
### Changelog vs. Original Draft
*   Added Phase 3 (Inventory Simulator) — was missing; Phase 4/5 restock formula had no real source for Current_Inventory.
*   Added Phase 6 (Waste Action Engine) — was missing entirely.
*   Added Phase 8 (India holdout validation) — was missing entirely.
*   Fixed Phase 2 — holiday calendars must be per-dataset-correct (FR/DE/US), not generic; weather ingestion gated behind a feasibility check, not assumed.
*   Fixed cold-start branching — replaced invented thresholds with the already-agreed 3-phase design.
*   Removed pre-set "12-18% MAPE improvement" target and "prove X fails" framing — evaluation reports actual results, not a predetermined narrative.

**Next immediate action:** Phase 1 (hybrid engine) + Phase 3 (inventory simulator) — same as before, since the simulator was always required before restock logic could be tested.
