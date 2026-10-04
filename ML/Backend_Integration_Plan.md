# Backend Integration Plan (FastAPI + MongoDB)

This document dictates the strict sequential build plan to construct the FastAPI backend and MongoDB database, and wire them to both the Flutter frontend and the Python ML Engine.

---

## 🔒 Core Architectural Locks (Alignment Audit Results)

Before writing any code, we aligned the backend architecture precisely with the UI expectations and ML realities:

- **Database & Auth:** **MongoDB Atlas (Cloud)** is the master database for everything. It stores user credentials (passwords hashed), roles, items, sales, inventory state, and forecasts. There is no Firebase; FastAPI handles native JWT authentication.
- **ML Execution:** **Nightly Python Batch Job**. The FastAPI layer does NOT run ML inference on the fly; it acts as an ultra-fast read-layer for precomputed JSON in MongoDB.
- **API Payload & Contract Fixes:**
  - `unit` is formally added to the item schema (e.g., "Units", "LBS") rather than being hardcoded.
  - `description` (LLM rationale) sits on the individual item object. It will default to `"LLM analysis pending"` to safely unblock the frontend.
  - `confidence_interval` is explicitly **`null`** for both primary and sparse items. The locked pooled XGBoost pipeline is a point-estimate regressor and does not produce real bounds. We will not fake them.
  - `discount_pct` in waste alerts is a **hardcoded static mapping** (e.g., 10%, 20%) based on risk tier. True price elasticity modeling is deferred.
  - `isNew=true` (or $n=0$ history) properly tags new items for the TSB sparse cold-start engine based on their category.

---

## 🚀 Sequential Build Plan (Status: 100% Complete)

This build plan is ordered strictly by dependency. A step cannot start until the previous step is verified.

### ✅ Step 1: MongoDB Operations & Native Auth (Production Grade) — [COMPLETED & VERIFIED]
*   **What was built:** Production `motor` async MongoDB Atlas connection, `users` collection with salted `bcrypt` password hashes, JWT generation/verification (`python-jose`), and `items` CRUD.
*   **Verification:** Verified live via `Backend/verify_step1.py` with 200/201 response codes on Atlas.
*   **Result:** Auth and database CRUD operational.

### ✅ Step 2: The ML Read Layer — [COMPLETED & VERIFIED]
*   **What was built:** FastAPI routes (`GET /api/v1/forecasts/today`, `GET /api/v1/forecasts/{id}`, `POST /api/v1/items/{id}/restock`, `PUT /api/v1/items/{id}`) reading precomputed forecasts from Atlas, computing `restockQuantity`, `stockProgress`, and point estimates (`confidence_interval=null`).
*   **Verification:** Verified live via `Backend/verify_step2.py` (all 6 tests passed).
*   **Result:** Frontend dashboard and item detail views have live read layer.

### ✅ Step 3: ML Batch Job - Primary Items (Prophet + XGBoost) — [COMPLETED & VERIFIED]
*   **What was built:** Standalone Python engine (`ML/batch_forecast.py`) loading 19,418 historical sales records, extracting Prophet components, and generating point estimates for high-volume staples.
*   **Verification:** Executed batch job locally; verified Atlas `forecasts` and `items` collections populated.
*   **Result:** Primary items have accurate predictions.

### ✅ Step 4: ML Batch Job - Sparse Items & Cold Start (TSB + Category Prior) — [COMPLETED & VERIFIED]
*   **What was built:** Extended `batch_forecast.py` with Teunter-Syntetos-Babai (TSB) estimator and $W = n / (n + 14)$ credibility shrinkage against empirical category 90th percentile priors (`category_priors_percentiles.json`).
*   **Verification:** Verified live via `Backend/verify_step4.py` — a new item with $n=0$ days history yielded predicted demand strictly equal to the category 90th percentile prior.
*   **Result:** Zero cold-start failures.

### ✅ Step 5: The Waste Action Engine — [COMPLETED & VERIFIED]
*   **What was built:** Real-time rule-engine endpoint (`GET /api/v1/waste-alerts`), intraday POS event logging (`POST /api/v1/sales/intraday`), and mitigation endpoints (`apply-discount`, `flag-donation`, `dismiss`). Calculates `sales_pace_ratio` and assigns locked static discounts (20%/30%).
*   **Verification:** Verified live via `Backend/verify_step5.py` (all 7 tests passed).
*   **Result:** Intraday slow-moving stock actively mitigated.

### ✅ Step 6: End-to-End Master Integration Test — [COMPLETED & VERIFIED]
*   **What was built:** Master integration runner `Backend/verify_e2e.py` testing the complete chain from cloud Atlas health to auth, catalog inspection, batch forecasting, dashboard reads, one-tap restock, intraday POS events, and waste mitigation.
*   **Verification:** Verified live via `Backend/verify_e2e.py` on active hotspot network.
*   **Result:** Complete system verified end-to-end.

