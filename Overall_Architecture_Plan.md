# RestockIQ: Overall Development & Architecture Plan

This document outlines the end-to-end development roadmap for the RestockIQ system, spanning the Machine Learning engine, Backend API, LLM integration, and Mobile Frontend.

## 1. Machine Learning Core (The Brain)
*Ref: `e:\CAP\ML\ML_Development_Plan.md`*
*   **Engine:** Prophet + XGBoost hybrid architecture to capture seasonality and correct residuals.
*   **Inventory Simulator:** A required step to generate "Current Inventory" states and measure waste vs. stockouts over time.
*   **Adaptive Branching:** 3-phase progressive routing (Category Prior → Blended → Full Hybrid) based on item history depth.
*   **Waste Action Engine:** Intraday logic to flag slow-moving stock for discounts (calibrated via elasticity data) or donation.
*   **Validation:** Strict chronological holdout testing, including a final isolated generalization test on an Indian dataset.

## 2. Backend API & LLM Narrator (The Bridge)
*   **Framework:** FastAPI (Python) to seamlessly wrap the ML models and Pandas logic.
*   **Endpoints:**
    *   `POST /forecast`: Accepts daily inputs (item_id, current_inventory, actual_sales_so_far).
    *   Returns JSON: `{restock_qty, predicted_demand, waste_action}`.
*   **LLM Narrator Integration:**
    *   Takes the hard mathematical output and generates a plain-text, non-technical recommendation.
    *   *Example input:* `item: croissant, restock_qty: 15, waste_risk: high, recommend: 20% discount`.
    *   *LLM Output:* "Order 15 croissants for tomorrow. Today's croissants are selling slowly; consider a 20% discount to clear inventory."
    *   *Constraint:* The LLM does **no math**; it acts strictly as a text translator to prevent hallucinations.

## 3. Mobile Frontend (The Interface)
*   **Framework:** Flutter (Dart) for zero-install, cross-platform mobile delivery.
*   **Target User:** Non-technical cafe/bakery owners.
*   **Core UI:**
    *   **Login/Auth:** single shop, 2 roles — Owner and Manager/Employee, permissions differ (e.g. only Owner manages staff accounts).
    *   **Item Setup:** add/edit menu items, mark each as perishable or non-perishable (this flag drives the Inventory Simulator and Waste Action Engine logic).
    *   **Dashboard:** today's restock recommendations per item, cold-start confidence badge (e.g. "Learning your patterns — Day 5/14"), LLM plain-language daily summary.
    *   **Inventory Input:** system-calculated leftover pre-filled automatically, with manual override; perishable items auto-reset to 0 and are not manually editable.
    *   **Item Detail/Forecast View:** predicted demand, restock formula shown as labeled components (Predicted + Safety Stock − Current Stock = Restock Qty), LLM narrator explanation, 7-day actual vs. predicted trend.
    *   **Waste Alerts:** flagged items with recommended action (discount % or donate/staff-meal), reasoning shown on tap.
    *   **Settings:** manage items, manage staff/roles (Owner-only), notification toggle.

## 4. Database & Infrastructure
*   **Database:** Firebase / Supabase. *(Pending confirmation from backend lead before implementation).*
*   **Storage:** 
    *   User profiles, store metadata.
    *   Historical sales logs (ingested from CSV initially, built for POS integration later).
*   **Hosting:** Render or AWS (Standard CPU, 8GB RAM). No GPU instances required due to Prophet/XGBoost efficiency. *(Pending confirmation from backend lead before implementation).*

## 5. System Integration & End-to-End Testing
*   **Data Flow Test:** Ensure data successfully travels: `Flutter App → FastAPI → ML Pipeline (Simulator + Hybrid) → LLM Narrator → FastAPI → Flutter App`.
*   **Load Testing:** Verify the API can handle batch item updates (e.g., closing out a 50-item menu at the end of the day).

---
**Next Immediate Action:** Begin Phase 1 (Hybrid Engine) & Phase 3 (Inventory Simulator) inside the `ML` module, as the backend and frontend cannot be built until the core forecasting math is proven.
