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

