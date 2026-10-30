# RestockIQ: Formal Claims Register & Documentation Audit

**Audit Timestamp:** 2026-10-31T04:10:00+05:30  
**Repository Branch:** `fix/final-pass`  
**Evaluator:** Antigravity Autonomous Verification Harness  

---

## Claims Audit Matrix

| Source Document | Claim / Statement | Verdict | Evidence & Technical Bounds |
| :--- | :--- | :--- | :--- |
| `docs/qa/APP_BEHAVIOR_GUIDE.md` | "Adaptive Mode runs an automated per-store model tournament backtesting 5 candidate algorithms (last, ewma, ma7, swd, blend) over rolling historical windows." | **SAFE TO SAY** | Implemented verbatim in `Backend/adaptive_forecast.py:222-272`. Candidates evaluated on rolling window $m = \min(14, n-3)$. |
| `docs/qa/APP_BEHAVIOR_GUIDE.md` | "A candidate must achieve $\ge 5\%$ lower MAE than the robust 7-day average (ma7) to unseat it." | **SAFE TO SAY** | Implemented in `Backend/adaptive_forecast.py:267-272`. Verified by unit test `test_five_percent_margin_rule_sub_five_retains_ma7` and mutation testing. |
| `docs/qa/APP_BEHAVIOR_GUIDE.md` | "By design, point forecasts are generated; confidence_interval field is set to null." | **SAFE TO SAY** | `Backend/main.py:333` explicitly returns `"confidence_interval": None` in forecast payload. |
| `docs/qa/APP_BEHAVIOR_GUIDE.md` | "Critical Pace Alert flags when Pace Ratio < 0.35; Low Pace flags when 0.35 <= Pace Ratio < 0.70." | **SAFE TO SAY** | Implemented in `Backend/main.py:2480-2505` and verified across daytime and overnight operating windows. |
| `docs/qa/APP_BEHAVIOR_GUIDE.md` | "When an item has an active waste alert, restock quantity is held to 0 to prevent compounding waste." | **SAFE TO SAY** | Enforced in `Backend/main.py:2620-2628` and verified by `test_p0_fixes.py`. |
| `README.md:16` | "Tech Stack: Flutter, Dart, Firebase Auth." | **DO NOT SAY** | **False.** System uses custom JWT authentication via FastAPI (`/api/v1/auth/login`) backed by MongoDB users collection and bcrypt. Firebase Auth is not present. |
| `README.md:34` | "Achieves a ~22.75% WAPE on out-of-sample data, beating 7-Day Moving Averages by ~9 points." | **SAY WITH CAVEAT** | **Single-store dataset specific.** Derived from offline cross-validation on 35 SKUs of the French bakery dataset. On rolling real-store evaluations, WAPE is 31.70% (n=28..60) and 35.87% overall. |
| `README.md:58` | "RestockIQ reduces 5,090 units of food waste and cuts 366 stockout units compared to seasonal naive." | **SAY WITH CAVEAT** | Supported by the 90-day static replay simulation in `docs/simulation_report.md` on the historical French bakery dataset. Cannot guarantee identical percentage gains for arbitrary new stores without history. |
| `docs/ADAPTIVE_FORECAST.md` | "Zero external dependencies: runs with pure Python standard library (no pandas, numpy, or sklearn in API process)." | **SAFE TO SAY** | Verified: `Backend/adaptive_forecast.py` imports only `math`, `datetime`, `statistics.NormalDist`, `typing`. Benchmark per call: 0.096 ms. |
| `docs/qa/APP_BEHAVIOR_GUIDE.md` | "Offline local providers serve latest cached store state with session persistence across app kills." | **SAFE TO SAY** | Handled via `SharedPreferences` in `APP/lib/services/storage_service.dart`. Verified on physical device relaunch. |
