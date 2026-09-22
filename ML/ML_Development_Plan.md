# RestockIQ: Machine Learning Development Plan & Architecture Rationale

*This document serves as the definitive roadmap and evidence-based justification for the RestockIQ ML architecture. It supersedes all previous drafts.*

---

## The 9-Phase Execution Plan

### Phase 1: Prophet Decomposition + Pooled Global Gradient-Boosting Engine (M5 Architecture)
*   **Base Prophet Training (Per Item)** — train on historical `y` (sales) per item using strict out-of-sample discipline. Extract structural components: `trend`, `weekly`, `yearly`, `is_tourist_season`, `holidays`.
*   **Data Pooling** — combine all 35 primary items into a single long-format dataset, assigning `article` as a categorical feature.
*   **Global XGBoost Training** — target = `y` (actual sales, NOT residuals); features = `article`, `lag_1`, `lag_7`, `rolling_7day_avg`, plus Prophet's extracted components (`trend`, `weekly`, `is_tourist_season`, etc.).
*   **Inference** — the single globally-trained XGBoost model predicts the final sales figure for all items.

### Phase 2: Holiday Feature Integration
*   **Holiday flags** — per-dataset-correct calendars, not one generic call:
    *   French Bakery → `holidays.France()`
    *   Rossmann → `holidays.Germany()` (or use Rossmann's native StateHoliday/SchoolHoliday columns if present — real data beats a library guess).
    *   Store Sales Price Elasticity → `holidays.UnitedStates()` (confirm country from dataset docs first).
*   **Feature merge** into `processed_bakery.csv`, `processed_rossmann.csv`, etc.
*   **Weather (Dropped until verified):** Do NOT commit to this until feasibility is checked. Requires confirmed store geolocation in each dataset. If location data isn't precise/available, drop this feature rather than pulling mismatched weather data.

### Phase 3: Inventory Simulator (Pre-requisite for Phase 5)
*No dataset has real "current inventory on hand" — this must be simulated before the restock formula can be tested.*
*   **Day 1:** `current_inventory = 0`.
*   **Each day:** `restock_qty = max(0, predicted_demand + safety_stock − current_inventory)`.
*   **After the day:** `leftover = max(0, current_inventory + restock_qty − actual_sales)`.
*   **Perishable flag:** if perishable, `leftover → 0` next day (thrown away); if non-perishable, leftover carries forward as next day's `current_inventory`.
*   **Output:** total demand, total sales, total restock ordered, total waste — this becomes the backtest proof that restock logic prevents compounding over-ordering.

### Phase 4: Adaptive Cold-Start Branching (Sparse Items)
*Use a 3-phase progressive-confidence model designed for zero-inflated retail data:*
*   **Day 1–13:** Category-Day Prior (90th Percentile). Instead of `mean + std` (which breaks on skewed sparse data), use the 90th percentile of historical category sales for that specific day of the week. 
    *   *Design Consideration (The "Zero-Forever" Trap):* For highly sparse categories where the 90th percentile is 0, the system must enforce a minimal trial-stocking heuristic (e.g., forcing a floor of 1 unit every 2-3 days) to prevent a self-fulfilling prophecy where an item never sells because it is never stocked.
*   **Day 14–30:** Bayesian Credibility Weighting. Blend the category prior with the item's emerging history using $W = n / (n + k)$, where $n$ is the number of days of item history.
    *   *The Constant $k$:* $k$ is derived per category based on its historical variance. Noisier categories receive a higher $k$, meaning they require more real-world days before the item's own noisy data is trusted over the category prior.
*   **Day 30+:** Fully item-driven. The item graduates to the standard Prophet Decomposition + Pooled Global XGBoost pipeline.

### Phase 5: Deterministic Restock Logic Layer
*   **Safety stock** — `1.65 * std_dev(demand)` as the dynamic buffer.
*   **Final equation** — `Restock_Qty = Max(0, (Hybrid_Predicted_Demand + Safety_Stock) − Current_Inventory)`, where `Current_Inventory` comes from the Phase 3 simulator.
*   **Validation** — confirm `Restock_Qty` correctly drops to 0 when simulated leftover inventory is high.

### Phase 6: Waste Action Engine (Intraday Intervention)
*Sits alongside Phase 5, same day — addresses stock that's already sitting unsold.*
*   `sales_pace_ratio = actual_sales_so_far / predicted_demand_so_far`.
*   If `sales_pace_ratio < 0.6` (tune this threshold): flag item for a waste action.
*   **Perishable + moderate shortfall (pace 0.4–0.6):** recommend moderate discount (~20%), calibrated using the Store Sales Price Elasticity dataset (repurposed here as discount-to-demand-lift calibration source).
*   **Perishable + severe shortfall (pace < 0.25, late in day):** recommend steep discount (50–70%) and/or bundling with other slow-moving items into one discounted "surplus bundle." *Never recommend donation* — real surplus-food platforms (e.g. Too Good To Go) always sell at a deep discount rather than giving product away, keeping every action revenue-positive.
*   **Non-perishable + low pace:** no action — already handled correctly by the simulator's carry-forward logic.
*   **Output:** `{waste_risk, recommended_action: none/moderate_discount/steep_discount_bundle, discount_pct}`.

### Phase 7: Evaluation & Benchmarking
*   **Metrics** — RMSE, MAE, MAPE, computed identically across:
    *   Model A: Standalone Prophet (current baseline)
    *   Model B: Pooled Global XGBoost with Prophet Features
*   **Time-series split only** — no random shuffling; last 15–20% chronologically as test set, per dataset.
*   **Report the actual result.** No pre-set target percentage — the improvement (or lack of it) over Model A is measured, not decided in advance. If Model B underperforms on any dataset, report that honestly.

### Phase 8: Final Holdout Validation — Indian Dataset
*Separate from Phases 1–7. Purpose: test generalization of a model trained on non-Indian data.*
*   **Inspect candidate** (e.g. `abuhumzakhan/store-data`) for: true daily granularity, food-category relevance, 1+ year continuity, sufficient volume per series.
*   **Do not touch this dataset during training/tuning** — any influence on the model before this step invalidates it as a generalization test.
*   **Normalize metrics** (MAPE, not raw RMSE/MAE) before comparing across currencies.
*   **Report the generalization gap honestly** — expected to underperform vs. same-market test splits. Note what India-specific fine-tuning (e.g., `holidays.India()`) would do to close that gap in a real deployment.

### Phase 9: API Preparation
*   **Modularize** — wrap the full pipeline (hybrid model + simulator + restock logic + waste action engine) into a clean class (`RestockIQ_Engine`).
*   **Serialize** — save trained models as `.pkl/.json`.
*   **Expose predict()** — input `{"item_id": 101, "current_inventory": 12}` → output `{"restock_qty": 5, "predicted_demand": 15, "waste_action": {"risk": "low", "action": "none"}}`.

---

## Part A: Actual Waste-Reduction Mechanism (Evidence-Backed)
The original framing ("if it doesn't sell, the system learns and orders less next time") only prevents compounding waste over multiple days. It does nothing about the food that is already sitting unsold today. 

Dynamic/markdown pricing on perishables — reducing price as the item approaches its waste point — is a well-documented, proven waste-reduction lever:
*   A **UC San Diego** study found dynamic pricing of perishables could reduce grocery food waste by roughly 21% or more.
*   **Wasteless** (a commercial dynamic-pricing vendor) reported pilot results of a 32.8% reduction in food waste and a 6.3% revenue increase.
*   Academic work (**ScienceDirect, 2022**) found that roughly 40% of fresh product is wasted before reaching consumers when pricing isn't responsive, and that a staged markdown strategy measurably reduces this.

**Takeaway:** Markdown/discount timing, triggered by inventory-vs-demand pace, is the standard, evidence-backed second lever alongside forecasting. Forecasting tells you how much to order; a waste-action layer tells you what to do with what's already sitting there.

*Honest caveat to document:* We don't have real markdown-response data for the bakery/Rossmann sales datasets. The elasticity dataset gives a defensible way to estimate discount-to-demand-lift, but this is a modeled estimate, not observed ground truth for specific SKUs.

---

## Part B: Model Accuracy Roadmap
1. **Feature Engineering & Architecture:** A per-item XGBoost residual hybrid fails due to data starvation (overfitting noise on sparse 500-row histories). The correct architecture leverages the M5 Walmart competition winning strategy: extracting Prophet's trend/seasonality components as features, then training **one pooled global gradient-boosting model** across all items simultaneously. This enables robust cross-item learning and allows XGBoost's short-term lags to successfully damp Prophet's occasional mathematical overshoots on low-volume items.
2. **India-Specific Calendar:** Prophet supports India natively (`model.add_country_holidays(country_name='IN')`). However, adding this to French/German data is scientifically wrong. The India holiday layer is a *deployment-readiness feature*, not a training-data feature. Document it as: "the system is built to support Indian festival/holiday effects when deployed on real Indian café data".
3. **Model/Ensemble Technique:** Use time-series cross-validation (walk-forward), never random k-fold (which leaks future data). Tune XGBoost hyperparameters via Bayesian optimization (e.g., Optuna) rather than manual guessing.

---

## Part C: Final Pipeline Validation on an Indian Dataset
Our training datasets (FR/DE/US contexts) are what the model is built and tuned on. An Indian dataset should be used *only* as a final, untouched holdout test to answer one question: does a model built on non-Indian data generalize to an Indian retail context? 

**Selection Criteria for Holdout Dataset:**
1. **True daily granularity:** A genuine date-per-row per item, not just scattered transaction timestamps.
2. **Continuity:** 1+ year of unbroken history per series.
3. **Food-category relevance:** Filterable to food/perishable categories.
4. **Sufficient volume:** Aggregated daily numbers aren't mostly zero-inflated noise.
5. **No leakage risk:** Does not overlap with training data.

*If no suitable public Indian daily-demand dataset exists at food-SKU granularity, the honest and defensible conclusion is to document that as a finding, not a failure. Fabricating fit is worse than reporting a gap.*

---
**Sources:**
*   [Salon: Dynamic pricing in supermarkets](https://www.salon.com/2022/01/10/can-dynamic-pricing-reduce-waste-in-supermarkets_partner/)
*   [RetailWire: Dynamic pricing reducing food waste](https://retailwire.com/discussion/can-dynamic-pricing-reduce-food-waste-at-grocers/)
*   [ScienceDirect: Dynamic Pricing for perishables](https://www.sciencedirect.com/science/article/pii/S0959652622007016)
*   [EIT Food: Wasteless dynamic pricing algorithm](https://www.eitfood.eu/blog/start-up-wasteless-tackles-food-waste-at-supermarkets-with-dynamic-pricing-algorithm)
*   [Prophet+XGBoost Implementation](https://subh700.github.io/prophet_xgboost.html)
*   [MDPI: Prophet-BO-XGBoost Load Forecasting](https://www.mdpi.com)
