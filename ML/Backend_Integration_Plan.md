# Backend Integration Plan (FastAPI + MongoDB)

This document dictates the strict sequential build plan to construct the FastAPI backend and MongoDB database, and wire them to both the Flutter frontend and the Python ML Engine.

---

## 🔒 Core Architectural Locks (Alignment Audit Results)

Before writing any code, we aligned the backend architecture precisely with the UI expectations and ML realities:

- **Database:** **MongoDB Atlas (Cloud)** is the master database. Stores items, sales, inventory state, and forecasts.
- **Auth:** **Firebase Auth** (JWTs are verified by FastAPI). No data is stored in Firestore.
- **ML Execution:** **Nightly Python Batch Job**. The FastAPI layer does NOT run ML inference on the fly; it acts as an ultra-fast read-layer for precomputed JSON in MongoDB.
- **API Payload & Contract Fixes:**
  - `unit` is formally added to the item schema (e.g., "Units", "LBS") rather than being hardcoded.
  - `description` (LLM rationale) sits on the individual item object. It will default to `"LLM analysis pending"` to safely unblock the frontend.
  - `confidence_interval` is explicitly **`null`** for both primary and sparse items. The locked pooled XGBoost pipeline is a point-estimate regressor and does not produce real bounds. We will not fake them.
  - `discount_pct` in waste alerts is a **hardcoded static mapping** (e.g., 10%, 20%) based on risk tier. True price elasticity modeling is deferred.
  - `isNew=true` (or $n=0$ history) properly tags new items for the TSB sparse cold-start engine based on their category.

---

## 🚀 Sequential Build Plan

This build plan is ordered strictly by dependency. A step cannot start until the previous step is verified.

### Step 1: MongoDB Scaffolding & FastAPI Mocks (Unblock Chinmay)
*   **What gets built:** A MongoDB Atlas cluster (free tier), basic database schemas (`sales`, `items`, `inventory`, `forecasts`), and a FastAPI shell with mock endpoints returning hardcoded JSON matching the Flutter contract exactly.
*   **Depends on:** Nothing.
*   **Verification:** FastAPI serves the mock JSON locally via Swagger/cURL.
*   **Unblocks:** **Chinmay (Frontend)**. He can immediately wire the Flutter HTTP calls to these endpoints and finish all UI state management.

### Step 2: FastAPI to MongoDB CRUD (The Operations Layer)
*   **What gets built:** The actual MongoDB connection (`motor` or `pymongo`) inside FastAPI. The mock endpoints are replaced with real MongoDB reads/writes. Specifically, `POST /api/v1/items` is wired up.
*   **Depends on:** Step 1.
*   **Verification:** We can successfully create an item via API, and it appears in MongoDB Atlas. We can fetch it back via `GET`.
*   **Unblocks:** The ML Engine. We now have a real database to read history from and write forecasts to.

### Step 3: ML Batch Job - Primary Items (Prophet + XGBoost)
*   **What gets built:** A standalone Python script (`batch_forecast.py`). It ports the locked Primary Item ML pipeline (Prophet feature extraction + pooled `HistGradientBoostingRegressor`), reads yesterday's sales from MongoDB, and writes the forecast objects to the `forecasts` collection.
*   **Depends on:** Step 2.
*   **Verification:** Run the script locally; verify the `forecasts` collection in Atlas populates with correct point estimates.

### Step 4: ML Batch Job - Sparse Items & Cold Start (TSB + Category Prior)
*   **What gets built:** The batch script is extended to include the Sparse Tier logic. Implements the $W = n/(n+k)$ credibility weighting against the `category_priors.json` 90th percentile.
*   **Depends on:** Step 3.
*   **Verification:** Create a new item (0 days history) in MongoDB. Run the script. Verify it outputs a forecast strictly equal to the category 90th percentile prior.

### Step 5: The Waste Action Engine
*   **What gets built:** A fast rule-engine endpoint (`/api/v1/waste-alerts`). Calculates `sales_pace_ratio` using intraday sales vs. the daily forecast, assigning a hardcoded `discount_pct` based on the calculated risk tier.
*   **Depends on:** Step 4 (requires the daily forecast to exist to calculate the pace).
*   **Verification:** Insert dummy intraday sales for an item; verify the endpoint flags it if sales are suspiciously slow.

### Step 6: End-to-End Test
*   **What gets built:** The final demo state.
*   **Depends on:** Step 1-5.
*   **Verification:** Load the real bakery dataset into the MongoDB Atlas cluster. Run the ML Batch Job. Fire up the Flutter app and visually verify the dashboard, item details, and waste alerts populate correctly with the real backend.
