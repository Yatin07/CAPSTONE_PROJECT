# RestockIQ Engineering Notes

This document provides a strictly auditable, chronological record of all architectural and engineering changes introduced during the system verification and integrity upgrade cycles on branch `fix/integrity-v1`.

Every entry documents:
1. **What** changed
2. **Why** it changed
3. **Files** affected
4. **How to test**
5. **How to revert**

---

## Stage 0: Safety, Isolation, and Environment Support

### 1. Pre-Review Integrity Fixes Safety Commit
- **What**: Staged and committed pre-review fixes on dedicated branch `fix/integrity-v1` (`commit a378fdfa02e31972e6123e684773be60eae2e123`).
- **Why**: Protects `main` branch and immutable tag `v1.0-submission`. Ensures a clean baseline for reviewing and auditing prior fixes (tenant scoping on delete/read, daily rollover structure, register flow, dynamic assistant, and server switcher).
- **Files**:
  - `APP/lib/providers/inventory_provider.dart`
  - `APP/lib/providers/waste_alerts_provider.dart`
  - `APP/lib/screens/item_detail_forecast_screen.dart`
  - `APP/lib/screens/login_screen.dart`
  - `APP/lib/screens/register_screen.dart`
  - `APP/lib/services/api_service.dart`
  - `Backend/main.py`
  - `Backend/services/llm_service.py`
  - `Backend/test_batch_rollover.py`
  - `Backend/test_tenant_isolation.py`
  - `ML/batch_forecast.py`
- **How to Test**:
  ```powershell
  git status
  git log -n 1 --stat
  ```
- **How to Revert**:
  ```powershell
  git reset --hard HEAD~1
  ```

---

### 2. Backups Folder Protection and Read-Only Export Utility
- **What**: Added `backups/` to `.gitignore` and created `scripts/backup_mongodb.py` to perform read-only BSON/JSON dumps of `users`, `items`, `forecasts`, and `intraday_sales`.
- **Why**: Adheres to zero-data-loss safety protocols and ensures sensitive database records or dumps can never be accidentally staged or committed to Git.
- **Files**:
  - `.gitignore`
  - `scripts/backup_mongodb.py`
- **How to Test**:
  ```powershell
  git check-ignore backups/
  Backend\venv\Scripts\python.exe scripts/backup_mongodb.py
  ```
- **How to Revert**:
  ```powershell
  git checkout HEAD -- .gitignore
  rm scripts/backup_mongodb.py
  ```

---

### 3. Configurable Database Support (`MONGODB_DB`)
- **What**: Replaced hardcoded `"restockiq"` database strings with `os.getenv("MONGODB_DB", "restockiq")` in backend services and ML batch scripts.
- **Why**: Allows complete isolation between the production database (`restockiq`) and automated testing / staging environments (`restockiq_staging`). Prevents automated tests or experimental batches from mutating production records.
- **Files**:
  - `Backend/main.py` (Line 134)
  - `ML/batch_forecast.py` (Line 38)
  - `scripts/manage_demo_user.py` (Line 22)
  - `scripts/manage_test_users.py` (Line 25)
- **How to Test**:
  ```powershell
  $env:MONGODB_DB = "restockiq_staging"
  Backend\venv\Scripts\python.exe -m py_compile Backend/main.py ML/batch_forecast.py scripts/manage_demo_user.py scripts/manage_test_users.py
  ```
- **How to Revert**:
  ```powershell
  git checkout HEAD -- Backend/main.py ML/batch_forecast.py scripts/manage_demo_user.py scripts/manage_test_users.py
  ```

---

## Stage 1: Review Existing Fixes, Audit Integrity, and Multi-Tenant Lifecycle

### 1. Fix RenderFlex Overflow in LoginScreen
- **What**: Replaced rigid `Row` with flexible `Wrap` for the "Don't have an account? Register" link.
- **Why**: Fixes a 109px layout overflow on compact mobile viewports (width <= 364px) that broke 4 Flutter widget/integration tests.
- **Files**:
  - `APP/lib/screens/login_screen.dart` (Lines 372-397)
- **How to Test**:
  ```powershell
  flutter test
  ```
  Result: 44/44 tests passing.
- **How to Revert**:
  ```powershell
  git checkout HEAD -- APP/lib/screens/login_screen.dart
  ```

---

### 2. Live API Logical Backup for Demo Manager
- **What**: Created `scripts/logical_backup_api.py` to dump `items`, `forecasts/today`, and `waste-alerts` directly through authenticated API endpoints when direct Atlas port 27017 is blocked.
- **Why**: Provides verifiable, uncorrupted snapshots of the demo manager's live operational state into the gitignored `backups/` directory.
- **Files**:
  - `scripts/logical_backup_api.py`
  - `backups/api_items_demo_manager.json`
  - `backups/api_forecasts_today_demo_manager.json`
  - `backups/api_waste_alerts_demo_manager.json`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe scripts/logical_backup_api.py
  ```
- **How to Revert**:
  ```powershell
  rm scripts/logical_backup_api.py
  ```

---

### 3. Multi-Tenant Lifecycle Test Suite (Mock-DB & Real-DB Staging)
- **What**: Implemented `Backend/test_tenant_lifecycle_mongomock.py` covering 2 owners across items isolation, forecasts isolation, intraday sales isolation, and scoped delete cascade.
- **Why**: Proves that tenant scoping strictly isolates data and that delete operations cascade only to the deleting owner's records. Labels tests explicitly as `[MOCK-DB]` or `[REAL-DB]` (marking real-DB skipped with `NOT RUN` when Atlas port 27017 is unreachable).
- **Files**:
  - `Backend/test_tenant_lifecycle_mongomock.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -m unittest Backend/test_tenant_lifecycle_mongomock.py -v
  ```
  Result: 4 mock-DB tests passed; 1 real-DB test skipped (`NOT RUN: Atlas port 27017 unreachable`).
- **How to Revert**:
  ```powershell
  rm Backend/test_tenant_lifecycle_mongomock.py
  ```

---

## Stage 2: Correct Daily State, Lazy Rollover, and Batch Idempotency

### 1. Single Source of Truth Constants Module
- **What**: Created `Backend/constants.py` defining fallback demand (`20`), fallback safety stock (`4`), default store operating hours (`08:00` - `20:00`), and default timezone (`UTC`).
- **Why**: Eliminates magic numbers across FastAPI endpoints, ML batch forecasting, and LLM prompt constructors.
- **Files**:
  - `Backend/constants.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -c "import constants; print(constants.DEFAULT_FALLBACK_DEMAND, constants.STORE_OPEN_HOUR)"
  ```
- **How to Revert**:
  ```powershell
  rm Backend/constants.py
  ```

---

### 2. Batch Forecast Non-Mutation of Live State & Historical Invariance
- **What**: Removed intraday sales appending, price resets, and action flag wipes from `ML/batch_forecast.py`. Added `--dry-run` and `--as-of DATE` CLI flags. Made DB connection non-blocking on import. Sourced historical sales strictly from finalized `daily_sales` aggregation.
- **Why**: Guarantees that running the batch job mid-day, twice in one day, or 6 hours late never mutates live manager state or duplicates sales history.
- **Files**:
  - `ML/batch_forecast.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -m unittest Backend/test_acceptance_lifecycle.py -v
  ```
- **How to Revert**:
  ```powershell
  git checkout faf9a31a -- ML/batch_forecast.py
  ```

---

### 3. Store-Local Timezone and Lazy Daily Rollover
- **What**: Added `get_store_timezone()`, `get_store_local_now()`, and `rollover_if_new_day(item, user)` in `Backend/main.py`. Wrapped all read/write paths for items, intraday sales, and alerts.
- **Why**: Ensures that state rollover occurs at store-local midnight rather than UTC, and resets `intradaySales`, reverts promotional discounts to original prices, and clears action flags seamlessly upon the first manager access of a new calendar day.
- **Files**:
  - `Backend/main.py`
  - `Backend/test_timezone_and_alerts.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -m unittest Backend/test_timezone_and_alerts.py -v
  ```
- **How to Revert**:
  ```powershell
  git checkout faf9a31a -- Backend/main.py
  ```

---

### 4. Timezone-Aware Operating Hours Fraction and Waste Alerts
- **What**: Updated `/api/v1/waste-alerts` to calculate `elapsed_fraction = (current_hour - open_hour) / (close_hour - open_hour)`. Returns `"store_status": "closed"` with 0 alerts outside operating hours (e.g. 20:00 - 08:00).
- **Why**: Solves the UTC drift issue where stores in Asian/European timezones saw critical alerts prematurely or late at night.
- **Files**:
  - `Backend/main.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -m unittest Backend/test_timezone_and_alerts.py -v
  ```

---

### 5. daily_sales Rollup & Aggregation
- **What**: Implemented `rollup_daily_sales(target_date)` and added unique compound index `(owner_id, item_id, date)` on collection `daily_sales`.
- **Why**: Allows idempotent background or cron aggregation of intraday sales receipts into permanent historical daily sales records.
- **Files**:
  - `Backend/main.py`
  - `Backend/test_acceptance_lifecycle.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -m unittest Backend/test_acceptance_lifecycle.py -v
  ```

---

### 6. LLM Grounding Enrichment & Zero-Math Audit
- **What**: Added `recommended_restock`, `tier`, and `recommended_action` to briefing and assistant context builders in `Backend/services/llm_service.py`. Extracted `build_briefing_prompt` and `build_assistant_prompt`.
- **Why**: Allows the LLM assistant to directly quote reorder requirements and operational actions without performing hallucinated arithmetic.
- **Files**:
  - `Backend/services/llm_service.py`
  - `Backend/verify_llm.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe Backend/verify_llm.py
  ```

---

### 7. Acceptance Test Suite
- **What**: Created `Backend/test_acceptance_lifecycle.py` verifying:
  1. Batch run twice on same day leaves history unchanged.
  2. Batch run mid-day does not mutate live intradaySales or prices.
  3. Batch run 6 hours late does not merge morning sales with yesterday.
  4. Day 1 sales transition to Day 2 resets intradaySales and clears flags.
  5. `daily_sales` aggregation is 100% idempotent.
- **Files**:
  - `Backend/test_acceptance_lifecycle.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -m unittest Backend/test_acceptance_lifecycle.py -v
  ```

---

## Block 1: Pre-flight Integrity & Test Isolation

### 1. Flutter Test Network Isolation & Injectable ApiService
- **What**: Made `ApiService` injectable via an `http.Client client` parameter and singleton injection method `ApiService.setMockClient()`. Replaced all 15 raw static `http.<method>` calls with `client.<method>`. Configured `APP/test/unit_test.dart` to use `MockClient` and added an explicit test asserting that any unmocked live network call fails immediately with a `StateError`.
- **Why**: Proved that unit tests were making real live HTTP POST requests to `https://restockiq-backend.onrender.com/api/v1/auth/login`. Injecting a mock client eliminates network dependency, prevents test flakiness, protects production from test traffic, and reduces test suite execution time from 11s to 3s.
- **Files**:
  - `APP/lib/services/api_service.dart`
  - `APP/test/unit_test.dart`
- **How to Test**:
  ```powershell
  cd APP && flutter test
  ```
- **How to Revert**:
  ```powershell
  git checkout ec2009d7 -- APP/lib/services/api_service.dart APP/test/unit_test.dart
  ```

---

### 2. Render Rollback Point & Debug APK Hash Backup
- **What**: Recorded Render cloud deployment commit `74ccc0a` as the immutable rollback point. Backed up the current debug APK to `backups/RestockIQ-debug-backup.apk` with verified SHA-256 hash.
- **Why**: Protects deployment rollback and provides a verified binary baseline before beginning Block 2/3 refactors.
- **Files**:
  - `backups/RestockIQ-debug-backup.apk` (SHA-256: `A4D0056E3271B275C4BF82AA54A8228AF7A31AC6197768514514A0E1EAED4424`)
- **How to Test**:
  ```powershell
  Get-FileHash backups/RestockIQ-debug-backup.apk -Algorithm SHA256
  ```

---

### 3. Real-Database Acceptance Difference & Fix
- **What**: Executed the 5 acceptance lifecycle scenarios against MongoDB Atlas staging (`restockiq_staging`). Identified a real-vs-mock discrepancy: `batch_forecast.py` called `client.close()` inside `run_batch_job()`, which caused subsequent runs to fail on real connections with `Cannot use MongoClient after close` (which `mongomock` failed to catch). Moved `client.close()` to `if __name__ == "__main__":`.
- **Why**: Real database connection pools must stay open when functions are called programmatically across repeated batch executions.
- **Files**:
  - `ML/batch_forecast.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -m unittest Backend/test_acceptance_lifecycle.py -v
  ```
- **How to Revert**:
  ```powershell
  git checkout ec2009d7 -- ML/batch_forecast.py
  ```

---

## Block 2: Daily Operations, Data Capture, Waste Mitigations, and Backend Hardening

### 1. User Profile, Auth Hardening, and Category Constraints
- **What**: Added `GET /api/v1/me` and `PATCH /api/v1/me` (and `/api/v1/users/me`) with IANA timezone validation (`zoneinfo.ZoneInfo`). Hardened `POST /api/v1/auth/register` with rate limiting (5 req/min/IP), minimum password length (8 characters), normalized email, and strict server assignment of `role = "owner"`. Restricted item categories to `ALLOWED_CATEGORIES = ["Bakery", "Beverage", "Food", "Dessert", "Snack", "Other"]` and enforced uniqueness of `(owner_id, name_lower)` with HTTP 409 Conflict.
- **Why**: Eliminates client privilege escalation, prevents duplicate SKU registration, and ensures timezones are valid IANA identifiers before computing daily operating hours.
- **Files**:
  - `Backend/main.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -m unittest Backend/test_block2_backend.py -v
  ```

---

### 2. Daily Stock Schema, Closing Count, Midday Count & Yesterday Review
- **What**: 
  - Added `daily_stock` collection with unique index `(owner_id, item_id, date)`.
  - Created `POST /api/v1/closing-count` (and `/api/v1/daily-stock/closing-count`): validates `units_left <= openingStock + producedOrRestocked`; computes `soldUnits = available - units_left`; if perishable, sets `wasteUnits = units_left` and initializes next day opening stock to 0; if non-perishable, sets `wasteUnits = 0` and carries over `units_left` to next day opening stock; derives and upserts `daily_sales` idempotently.
  - Created `POST /api/v1/midday-count` (and `/api/v1/daily-stock/midday-count`): calculates same-day pace `sold_so_far / (forecast * elapsed_fraction)` where `elapsed_fraction = (local_hour - open) / (close - open)`.
  - Created `GET /api/v1/review/yesterday` (and `/api/v1/daily-stock/review/yesterday`): calculates sell-through `sold / available` with High (>90%), Normal (70-90%), Low (<70%), and Critical (<35%) thresholds. Unsubmitted days are labeled `"no data"`, status `"missing"`, with `soldUnits = null` (NEVER zero, excluded from training).
  - Added `daysOfData`, `maturity` (`Learning`, `Improving`, `Mature`), and `maturityLabel` to `/api/v1/forecasts/today`.
- **Why**: Implements the daily learning loop and store review routine per frozen product spec while preventing missing days from being distorted as zero-sale days.
- **Files**:
  - `Backend/main.py`
  - `Backend/test_block2_backend.py`

---

### 3. Waste Mitigation Overhaul: Combo Bundle Pairing & Elimination of Donation
- **What**: Completely removed the donation endpoint (`flag-donation`) and references across backend endpoints, LLM service, tests, and verification scripts. Added `POST /api/v1/waste-alerts/{id}/apply-bundle` with 20% combo discount pairing against high-velocity partner items (preferring complementary categories: Bakery<->Beverage, Food<->Beverage, etc.). Updated Low Pace alerts to suggest 10% promotional markdowns. Updated Gemini briefing and assistant prompts to explicitly specify bundle/discount actions and restock quantities.
- **Why**: Replaces unrealistic charity donation flows with actionable commercial combo bundling to recover revenue on slow-selling stock.
- **Files**:
  - `Backend/main.py`
  - `Backend/services/llm_service.py`
  - `Backend/test_backend_unit.py`
  - `Backend/test_tenant_isolation.py`
  - `Backend/verify_llm.py`
  - `Backend/verify_step5.py`
- **How to Test**:
  ```powershell
  Backend\venv\Scripts\python.exe -m unittest discover -s Backend -p "test_*.py" -v
  ```
- **How to Revert**:
  ```powershell
  git checkout cef3d658 -- Backend/
  ```




