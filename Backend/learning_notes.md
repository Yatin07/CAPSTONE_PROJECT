# Backend Engineering: Learning Notes & Architectural Decisions

This document acts as a continuous audit of the engineering decisions made during the Backend Phase of the RestockIQ project. It explains *why* certain architectural choices were made and documents the progress of the FastAPI + MongoDB integration.

---

## 1. The Database Pivot: MongoDB Atlas vs. Firebase Firestore
During our ML planning phase, we initially considered Firebase Firestore. However, upon rigorous auditing before writing code, we locked in **MongoDB Atlas** as the master database. 

**Why did we make this pivot?**
1.  **Firebase is retained for Auth only:** Handling user identity via Firebase Auth is industry-standard and highly secure. We use it strictly to generate JWT tokens.
2.  **Data Structure:** Firestore is a NoSQL document store that becomes prohibitively expensive and difficult to query when running complex aggregations (like grabbing 3 months of historical sales across 100 items for a Prophet ML job). MongoDB handles large, structured time-series data and bulk reads much more efficiently, which is critical for our nightly ML batch jobs.

## 2. API Contract & Payload Formatting Decisions
Before writing the mock API, we ran an alignment audit against the Flutter UI expectations and made strict decisions about the data shape:

*   **The `confidence_interval` Issue:** Facebook Prophet natively outputs upper and lower bounds. However, our locked ML pipeline feeds Prophet's features into a globally pooled XGBoost regressor. XGBoost is a point-estimate model, meaning it outputs one specific number, not a range. Instead of "faking" a confidence interval, we explicitly set this field to `null` across all items to maintain data integrity.
*   **The `unit` Field:** We discovered the frontend expected a `unit` string (like "Units", "LBS", "GAL"). Instead of hardcoding the UI to assume everything is sold by count, we formally added this to the MongoDB schema. This prevents technical debt when the bakery wants to sell flour by weight.
*   **The `description` Field:** The UI expects a natural language explanation per item on the dashboard. Because integrating the OpenAI/Gemini LLM is slated for Phase 3, we opted to serve a hardcoded `"LLM analysis pending"` placeholder. This unblocks the frontend team completely without leaking fake or misleading data during demo testing.

## 3. The Shift to Direct Production-Grade Architecture
Initially, we considered a "Mock-First" strategy to unblock the frontend and planned to use Firebase for Auth. However, we have made a definitive pivot:
**Total Control & Single Source of Truth:**
1. **No Mocks:** We are bypassing dummy data entirely. The backend is being built directly to production standards. The frontend (Flutter running in Android Studio) will connect directly to real, live FastAPI endpoints querying real MongoDB collections from Day 1.
2. **MongoDB as the Single Source of Truth:** We officially dropped Firebase Auth. MongoDB is now handling *everything* — user authentication (via custom JWTs), item inventory, and ML forecasts. This centralizes our entire data ecosystem into one robust NoSQL environment, giving us total architectural control without third-party dependencies.

---

## 4. Step 1 Implementation: Production FastAPI + Motor + JWT Auth

We completed and verified the core infrastructure for Step 1 of the Backend Integration Plan:

*   **Async Driver with Motor:** Replaced standard synchronous PyMongo with `motor.motor_asyncio.AsyncIOMotorClient`. Because FastAPI is an async ASGI framework, using Motor prevents database I/O from blocking the server event loop during concurrent requests.
*   **Resilient Startup Lifecycle:** Configured non-blocking ping checks in the `@app.on_event("startup")` handler using explicit 5-second connection timeouts (`serverSelectionTimeoutMS=5000`). If cloud network or VPN issues occur, the server logs a warning and boots cleanly instead of crashing or hanging indefinitely.
*   **Cryptographic Password Hashing:** Implemented `passlib` with `bcrypt`. Passwords are automatically salted and hashed before entering MongoDB. Plaintext passwords never touch persistence.
*   **Stateless JWT Security:** Generated 7-day expiration JSON Web Tokens using `python-jose` (HS256). Protected endpoints use FastAPI's `HTTPBearer` dependency injection (`get_current_user`), decoding the token, verifying the signature, and hydrating the user context directly from the Atlas `users` collection.
*   **Database-Level Unique Indexing:** Startup lifecycle automatically ensures a unique index on `db.users.email`, preventing race-condition duplicate account registrations at the database engine layer.

---

## 5. Cloud Diagnostics & Network Engineering (MongoDB Atlas)

During deployment and testing on Windows via mobile hotspot, we diagnosed and resolved network-level hurdles:

*   **Symptom:** `ServerSelectionTimeoutError: No replica set members found yet` on port 27017, with ping attempts timing out.
*   **Root Cause Analysis:** When switching internet networks (e.g., from campus/dorm Wi-Fi to a phone hotspot), the client machine was assigned a new public IP (`115.242.138.74`). MongoDB Atlas strictly rejects all TCP handshakes from unlisted IPs.
*   **Resolution:** Configured MongoDB Atlas Network Access with `0.0.0.0/0` ("Allow Access From Anywhere"). Confirmed TCP connectivity with PowerShell `Test-NetConnection` and validated the connection via Motor:
    ```json
    SUCCESS: MongoDB Atlas Ping Result: {"ok": 1}
    ```

---

## 6. End-to-End Verification on Live MongoDB Atlas

We confirmed 100% functionality against the live cloud database using end-to-end automated scripts (`verify_step1.py`):

1.  **`GET /api/v1/health`** $\rightarrow$ `200 OK`
    *   Response: `{"status": "ok", "db": "connected"}`
2.  **`POST /api/v1/auth/register`** $\rightarrow$ `201 Created`
    *   Payload: `name`, `email`, `password`, `role`.
    *   Result: Salted bcrypt hash stored in Atlas `users` collection, returned signed JWT.
3.  **`POST /api/v1/auth/login`** $\rightarrow$ `200 OK`
    *   Result: Validated bcrypt hash and returned authenticated bearer token.
4.  **`POST /api/v1/items` (JWT Protected)** $\rightarrow$ `201 Created`
    *   Payload: Item details (`name`, `category`, `unit`, `currentStock`, `isPerishable`, `price`).
    *   Result: Stored with `owner_id` relational link to the logged-in user, initialized cold-start fields for future ML ingestion.
5.  **`GET /api/v1/items` (JWT Protected)** $\rightarrow$ `200 OK`
    *   Result: Fetched persisted inventory items from Atlas filtered by `owner_id`.
6.  **Walkthrough Accounts:**
    *   Walkthrough test accounts (configured via `.env` or local test runners) are used for automated test suites.
    *   All passwords in production must be cryptographically hashed using bcrypt.

---

## 7. Developer Experience (DX) & Security Hygiene

To enable frictionless testing inside Android Studio while safeguarding cloud credentials:

*   **Flutter Development Mode:** In debug mode, the `LoginScreen` can pre-fill testing fields for swift emulator verification.
*   **One-Tap Demo Bypass:** Added an outlined `Demo Login (Skip Auth)` button directly beneath the login form to bypass authentication screens during UI work.
*   **Root Security Hygiene:** Centralized root `.gitignore` strictly prevents exposure of `.env` connection strings, Python bytecode, credentials, and IDE metadata.

---

## 8. Step 2 Architecture: The ML Read Layer & Inventory Lifecycle

We implemented and verified the fast read-layer endpoints required by the Flutter dashboard and item deep-dive screens:

*   **`GET /api/v1/forecasts/today`:** Queries the user's items and joins with the latest precomputed forecast in `db.forecasts`. Computes dynamic inventory metrics on the fly:
    $$\text{restockQuantity} = \max(0, \text{predictedDemand} + \text{safetyStock} - \text{currentStock})$$
    $$\text{stockProgress} = \text{clamp}\left(\frac{\text{currentStock}}{\max(1, \text{predictedDemand} + \text{safetyStock})}, 0.0, 1.0\right)$$
    Generates a natural-language operational summary (e.g., `"5 of 6 items require restocking today"`).
*   **Point-Estimate Constraint:** Adheres strictly to the architectural lock: `confidence_interval = None` across all items, preventing faked uncertainty bounds.
*   **`GET /api/v1/forecasts/{item_id}`:** Serves deep-dive item data, including full 7-day historical sales and 7-day forecast series for Flutter's `SalesForecastChart` widget.
*   **One-Tap Restock (`POST /api/v1/items/{item_id}/restock`):** Increases `currentStock` in Atlas and records an audit event, instantly resetting the calculated `restockQuantity`.
*   **Automated Verification:** Verified via `verify_step2.py` with all 6 tests passing.

---

## 9. Steps 3 & 4: Two-Tier Machine Learning Engine (`batch_forecast.py`)

We integrated the offline ML forecasting engine directly with MongoDB Atlas:

*   **Offline Batch Execution:** Designed to run as a nightly batch runner (`ML/batch_forecast.py`), isolating intensive ML feature extraction and regression from the real-time API event loop.
*   **Tier 1 (Primary Items):** Evaluates high-volume daily staples (Croissants, Baguettes, Pain au Chocolat, Milk) against 19,418 historical bakery sales records. Decomposes structural trend/seasonality with Prophet (including French holidays and tourist season multipliers) and refines point estimates using a pooled `HistGradientBoostingRegressor` on lag features (`y_lag_1`, `y_lag_7`, `y_rolling_7_mean`).
*   **Tier 2 (Sparse Items & Cold Start):** Solves the new-product cold-start dilemma using Teunter-Syntetos-Babai (TSB) intermittent demand estimation combined with credibility shrinkage:
    $$W = \frac{n}{n + 14}$$
    $$\hat{y} = W \cdot \hat{y}_{\text{TSB}} + (1 - W) \cdot \text{Prior}_{p90}$$
    When $n = 0$ days of history, $W = 0$, guaranteeing the forecast **strictly equals the category 90th percentile prior** (`category_priors_percentiles.json`).
*   **Automated Verification:** Verified via `verify_step4.py` — created a new item (`Artisan Sourdough Loaf`, $n=0$), executed the batch runner, and confirmed its predicted demand matched the Sunday prior ($10$ units) exactly.

---

## 10. Step 5: Waste Action Engine & Intraday Velocity Tracking

We constructed the real-time perishable inventory protection engine:

*   **Intraday POS Sales Stream (`POST /api/v1/sales/intraday`):** Allows POS terminals or staff to record sales events throughout the day, decrementing inventory and incrementing `intradaySales`.
*   **Velocity Tracking (`sales_pace_ratio`):** Compares actual sales volume against expected sales for the elapsed business hours (8:00 AM to 8:00 PM):
    $$\text{sales\_pace\_ratio} = \frac{\text{actualSold}}{\max(1.0, \text{predictedDemand} \times \text{elapsedFraction})}$$
*   **Dynamic Risk Tiers & Static Discount Mappings:**
    *   $\text{sales\_pace\_ratio} < 0.35 \implies$ **Critical** (assigned locked static $30\%$ discount or flagged for donation).
    *   $\text{sales\_pace\_ratio} < 0.70 \implies$ **Low Pace** (assigned locked static $20\%$ discount).
    *   $\text{sales\_pace\_ratio} \ge 0.70 \implies$ Normal pace (no alert required).
*   **Mitigation Actions:** Provides dedicated endpoints to apply discounts (`/apply-discount`), flag items for charity pickup (`/flag-donation`), or dismiss alerts (`/dismiss`).
*   **Automated Verification:** Verified via `verify_step5.py` with all 7 tests passing.

---

## 11. Step 6: Master End-to-End Integration Audit

The entire 6-step integration plan was executed and verified live via `Backend/verify_e2e.py` on the active mobile hotspot:
*   Cloud Atlas Heartbeat $\rightarrow$ Authenticated JWT $\rightarrow$ Catalog Query $\rightarrow$ Unified ML Batch Job $\rightarrow$ Main Dashboard Read $\rightarrow$ Item Deep-Dive $\rightarrow$ One-Tap Restock $\rightarrow$ Intraday POS Logging $\rightarrow$ Waste Action Engine.
*   **All 6 steps in `ML/Backend_Integration_Plan.md` are 100% complete, verified, and committed.**


