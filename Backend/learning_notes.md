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
6.  **Pre-Seeded Credentials:**
    *   `admin@test.com` / `123456` (Pre-filled in Flutter frontend)
    *   `admin@admin.com` / `123456`
    *   `manager@cafe.com` / `password123`

---

## 7. Developer Experience (DX) & Security Hygiene

To enable frictionless testing inside Android Studio while safeguarding cloud credentials:

*   **Flutter Auto-Fill:** The `LoginScreen` controllers initialize with `admin@test.com` and `123456`, allowing single-tap login during emulator testing.
*   **One-Tap Demo Bypass:** Added an outlined `Demo Login (Skip Auth)` button directly beneath the login form to bypass authentication screens during UI work.
*   **Root Security Hygiene:** Created a centralized root `.gitignore` to prevent any accidental exposure of `.env` database connection strings, Python compiled bytecode (`__pycache__/`, `*.pyc`), and IDE files. Untracked previously cached bytecode from Git history.

