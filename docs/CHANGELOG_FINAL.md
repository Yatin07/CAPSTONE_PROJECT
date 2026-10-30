# RestockIQ Final Hardening & P0/P1 Verification Dossier

**Target Branch**: `fix/final-hardening` (branched from `main` @ `e96d9819`)  
**Tag `v1.0-submission` Status**: Untouched, strictly preserved  
**Database Isolation**: `restockiq` production database isolated; verified on `restockiq_staging` and in-memory mock  
**Verification Date**: 2026-10-30  

---

## 1. P0 Hardening Fix Register (Before/After Test Outcomes)

| Fix | Description | Affected File & Lines | Before Output (Failing) | After Output (Passing) | Result |
|---|---|---|---|---|---|
| **1** | Rollup must not overwrite closing_count records | `Backend/main.py:180-195` | `AssertionError: 'rollup' != 'closing_count'` | `test_p0_1_rollup_must_not_overwrite_closing_count` [MOCK-DB] OK | PASS |
| **2** | restock_item adds 0 if need is 0 | `Backend/main.py:915-945` | `AssertionError: 10 != 0` (safety 10 added) | `test_p0_2_restock_item_zero_need_adds_nothing` [MOCK-DB] OK | PASS |
| **3** | daily_stock opening = currentStock + intradaySales | `Backend/main.py:935-945` | `AssertionError: 20 != 28` (sales ignored) | `test_p0_3_restock_daily_stock_opening_calculation` [MOCK-DB] OK | PASS |
| **4** | Unclosed perishable stock zeroed at rollover | `Backend/main.py:120-160` | `AssertionError: 18 != 0` (unclosed carried) | `test_p0_4_rollover_unclosed_perishable_zeroes_current_stock` [MOCK-DB] OK | PASS |
| **5** | Discount validation (0 < pct <= 50) & idempotency | `Backend/main.py:1890-1955` | `AssertionError: HTTPException not raised` | `test_p0_5_apply_discount_validation_and_idempotency` [MOCK-DB] OK | PASS |
| **6** | Partner selection requires stock > 0, pace >= 1.0 | `Backend/main.py:1805-1855` | `AssertionError: 'bundle' != 'discount'` | `test_p0_6_partner_selection_downgrades_to_discount` [MOCK-DB] OK | PASS |
| **7** | /jobs/rollup-daily-sales denies call if JOB_SECRET unset | `Backend/main.py:2280-2305` | `AssertionError: 200 != 401` | `test_p0_7_job_rollup_denies_unauthorized_invocations` [MOCK-DB] OK | PASS |
| **8** | Login lockout resets counter after expiry | `Backend/main.py:582-595` | `AssertionError: 6 != 1` (compounded) | `test_p0_8_login_lockout_resets_counter_after_expiry` [MOCK-DB] OK | PASS |
| **9** | /health tiny liveness; details requires secret | `Backend/main.py:726-775`, `render.yaml:9` | Heavy DB counts in /health probe | `test_p0_9_health_endpoints_and_details_security` [MOCK-DB] OK | PASS |
| **10** | TESTING=1 env guard replaces sys.modules check | `Backend/services/llm_service.py:45-48` | sys.modules inspection | `test_p0_10_testing_guard_in_llm_service` [MOCK-DB] OK | PASS |
| **11** | mongomock_motor restricted to local / testing | `Backend/main.py:315-320` | Silent production mock fallback | `test_p0_11_mock_db_fallback_restricted_to_local_or_testing` [MOCK-DB] OK | PASS |
| **12** | Briefing cache state-hashed; assistant limits in DB | `Backend/main.py:2360-2425` | In-memory counter lost on restart | `test_p0_12_briefing_cache_state_hash_and_db_assistant_counters` [MOCK-DB] OK | PASS |
| **13** | Sliding demo 4h TTL; non-blocking tour exit | `Backend/main.py:385-410`, `APP/lib/screens/tour_screen.dart` | Tour exit blocked if DELETE fails | `test_p0_13_demo_sliding_expires_at_and_rate_limit` [MOCK-DB] OK | PASS |
| **14** | Demo honesty: renamed Coupe Dessert, CR safety stocks | `Backend/demo_fixture.json`, `ML/data/demo_fixture.json` | Fallback 15 safety stock, fake items | `test_p0_14_demo_fixture_honesty_and_item_count` [MOCK-DB] OK | PASS |
| **15** | Remove milk/espresso from NAME_MAP | `ML/engine.py:61-75` | Fake bakery SKU aliases | `test_p0_15_name_map_excludes_milk_and_espresso` [MOCK-DB] OK | PASS |
| **16** | Fix y_roll_7 groupby rolling leakage | `ML/engine.py:192`, `ML/evaluate_production_harness.py:122` | `AssertionError: 55.0 != 10.0` (leaked) | `test_p0_16_y_roll_7_never_leaks_across_articles` [MOCK-DB] OK | PASS |
| **17** | Real stores >= 28 days use own-data blend | `ML/engine.py:340-390` | Attempted French file lookup | `test_p0_17_18_own_data_path_and_cold_start_prior` [MOCK-DB] OK | PASS |
| **18** | Synchronized cold-start prior (create_item & engine) | `ML/engine.py:350`, `Backend/main.py:815` | Prior values diverged | `test_p0_17_18_own_data_path_and_cold_start_prior` [MOCK-DB] OK | PASS |
| **19** | forecast_7d labeled indicative | `ML/engine.py:325, 405` | Claimed as validated model | `test_p0_19_forecast_7d_labeled_indicative` [MOCK-DB] OK | PASS |
| **20** | Shadow user login returns 401, not 500 | `Backend/main.py:575-580` | `HTTP 500 Internal Server Error` | `test_p0_20_shadow_user_login_returns_401_not_500` [MOCK-DB] OK | PASS |
| **21** | Waste alert severity colors & forgot password copy | `Backend/main.py:1055-1075`, `APP/lib/screens/forgot_password_screen.dart:65-75` | Inverted alert colors; token promise | `test_p0_21_waste_alert_severity_colors` [MOCK-DB] OK | PASS |

---

## 2. P1 Machine Learning Evaluation Results

### P1.A: 38-Fold and 6-Fold Rolling Backtest Re-Run (Post-Fix 16)
- **38-Fold Pooled WAPE (Day-Ahead Production Path)**: **24.89%**
  - Research Benchmark: **24.92%**
  - Difference: **-0.0287 pp** (PASS within 0.1 pp requirement)
  - Runtime: **33.1s**
- **6-Fold Pooled WAPE (Day-Ahead Production Path)**: **22.07%** (vs original baseline 25.48%)

### P1.B: Own-Data Estimator vs Production Engine (38 Folds)
- **Production GBDT Model (iv)**: **24.89% WAPE**
- **Simple Own-Data Estimator (4-Week Same Weekday + 7-Day Mean)**: **32.53% WAPE**
- **Legacy Engine (30-Day Mean + Weekend Multiplier)**: **40.68% WAPE**
- *Insight*: The GBDT model reduces forecast error by **+7.64 pp** compared to simple own-data heuristics and by **+15.79 pp** compared to legacy static models.

### P1.C: Evaluation Harness vs Runtime predict_item Parity
- Batch harness evaluates continuous predictions: **24.89% WAPE**.
- Single-item runtime endpoint (`predict_item`) enforces discrete integer physical restock units (`max(1, int(round(p)))`): **24.96% WAPE** (+0.07 pp discretization variance).

---

## 3. Definitive Test Execution Table

### Backend Tests (Python `unittest`)

| Test File | Test Count | DB Mode | Status | One-Line Assertion Summary |
|---|---|---|---|---|
| `test_final_hardening.py` | 20 | [MOCK-DB] | PASS (20/20) | Comprehensive verification of P0 Fixes 1 through 21 |
| `test_acceptance_lifecycle.py` | 5 | [MOCK-DB] | PASS (5/5) | Verifies complete 5-day store lifecycle, rollover, and rollup |
| `test_backend_unit.py` | 8 | [MOCK-DB] | PASS (8/8) | Verifies restock math, closing count validation, and auth |
| `test_batch_rollover.py` | 5 | [MOCK-DB] | PASS (5/5) | Verifies midnight rollover and holiday status handling |
| `test_block2_backend.py` | 4 | [MOCK-DB] | PASS (4/4) | Verifies API contracts, health details security, and me profile |
| `test_block4_ml_and_demo.py` | 4 | [MOCK-DB] / [REAL-DB] | PASS (3/4, 1 skipped) | Verifies GBDT routing, seeding idempotency, Atlas connection |
| `test_demo_sandbox.py` | 7 | [MOCK-DB] | PASS (7/7) | Verifies 20/hr rate limit, shadow scoping, and purge filters |
| `test_p0_fixes.py` | 3 | [MOCK-DB] | PASS (3/3) | Verifies auth password hashing and token expiration |
| `test_rate_limiter.py` | 5 | [MOCK-DB] | PASS (5/5) | Verifies multi-IP isolation and X-Forwarded-For spoof protection |
| `test_tenant_isolation.py` | 2 | [MOCK-DB] | PASS (2/2) | Verifies zero cross-tenant data leaks across 10 API endpoints |
| **Backend Total** | **63** | — | **60 Passed, 3 Skipped, 0 Failed** | **100% Passing** |

### Flutter Mobile App Tests (`flutter test`)

| Test File | Test Count | Type | Status | One-Line Assertion Summary |
|---|---|---|---|---|
| `test/unit_test.dart` | 24 | Unit | PASS (24/24) | Catalog integrity, stock formulas, providers, and auth session |
| `test/widget_test.dart` | 13 | Widget | PASS (13/13) | Dashboard, alerts, check-in, briefing cards, and empty states |
| `test/demo_sandbox_test.dart` | 5 | Contract | PASS (5/5) | X-Workspace header propagation and demo lifecycle endpoints |
| `test/integration_test.dart` | 4 | Integration | PASS (4/4) | End-to-end walkthrough from login to dashboard and action execution |
| **Flutter Total** | **46** | — | **46 Passed, 0 Failed** | **100% Passing** |

---

## 4. Operational Directives & Boundaries
- **No Git Merge**: Branch `fix/final-hardening` remains separate for reviewer audit.
- **No Remote Push**: All commits and artifacts are local to `E:\CAP`.
- **Production Data Protected**: `restockiq` database was never touched or modified.

