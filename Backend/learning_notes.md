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
