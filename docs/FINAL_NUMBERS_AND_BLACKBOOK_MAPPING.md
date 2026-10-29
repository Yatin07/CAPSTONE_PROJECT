# RestockIQ: Master Final Numbers & Black Book Traceability Register

**Branch:** `fix/integrity-v1`  
**Execution Timestamp:** 2026-10-29T21:55:00+05:30  
**Status:** ALL REGRESSION TESTS PASSED (0 Issues, 100% Pass Rate)

---

## 1. Unified Master Test Results Matrix

All testing suites executed cleanly across both Mock and Real database targets. Every result has been empirically verified via live command execution.

| Test Suite / Harness | Target / Mode | Total Tests | Passed | Failed | Verification Command & Log Source | Verdict |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **Flutter Static Analysis** | Client Workspace (`APP/`) | 0 issues | 0 issues | 0 | `flutter analyze` (ran in 3.4s) | **PASS** |
| **Flutter Widget & Unit Tests** | Mock Environment (`APP/test/`) | 43 | 43 | 0 | `flutter test` (`unit_test.dart`, `widget_test.dart`, `integration_test.dart`) | **PASS** |
| **Backend P0 Security & Logic** | In-Memory Mock (`Backend/test_p0_fixes.py`) | 6 | 6 | 0 | `python test_p0_fixes.py` (ran in 4.34s) | **PASS** |
| **Backend Unit & Isolation Audit** | In-Memory Mock (`Backend/test_backend_unit.py`) | 7 | 7 | 0 | `python test_backend_unit.py` (ran in 0.15s) | **PASS** |
| **Tenant Boundary Security Audit** | In-Memory Mock (`Backend/test_backend_unit.py`) | 10 endpoints | 10 | 0 | Sub-suite of `test_backend_unit.py` (Zero leaks across all 10 endpoints) | **PASS** |
| **Anti-Spoofing & Rate Limiting** | In-Memory Mock (`Backend/test_backend_unit.py`) | 4 probes | 4 | 0 | Right-most proxy IP (`ips[-1]`) anti-spoofing verification | **PASS** |
| **Decision Table & EP+BVA** | In-Memory Mock (`Backend/test_backend_unit.py`) | 10 rules + 4 bounds | 14 | 0 | Boundary value analysis on assistant chat queries & rule triggers | **PASS** |
| **Staging E2E User Journey** | Real Database (`restockiq_staging`) | 10 steps | 10 | 0 | `python scripts/verify_staging_e2e_journey.py` | **PASS** |
| **Step 1 Staging Verification** | Real Database (`restockiq_staging`) | 5 checkpoints | 5 | 0 | `python Backend/verify_step1.py` | **PASS** |
| **Step 2 Staging ML Read Layer** | Real Database (`restockiq_staging`) | 6 checkpoints | 6 | 0 | `python Backend/verify_step2.py` | **PASS** |

### Verified Summary Counts
- **Total Flutter Automated Tests:** 43 tests (43 passed, 0 failed)
- **Total Backend Unit Tests:** 13 unit tests (13 passed, 0 failed)
- **Total Real-Database Staging Steps:** 10 end-to-end steps (10 passed, 0 failed)
- **Flutter Code Health:** 0 issues found via `flutter analyze`
- **Memory Footprint:** FastAPI backend idle RSS: **71.5 MB**; loaded under traffic: **72.0 MB** (comfortably within 512 MB Render Free Tier limit)

---

## 2. Complete OpenAPI Endpoint Inventory (33 Routes)

Extracted dynamically from `main.app.routes` in `Backend/main.py`. The system provides **29 functional API endpoints** and **4 documentation/specification routes**, partitioned across 9 architectural domains.

| HTTP Method | Route Path | Handler Function | Security / Scope | Functional Domain |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | `health_check` | Public | System Health |
| `GET` | `/api/v1/health` | `health_check` | Public (Alias) | System Health |
| `POST` | `/api/v1/auth/register` | `register` | Public (Owner role server-enforced) | Authentication |
| `POST` | `/api/v1/auth/login` | `login` | Public (5-try/15-min lockout) | Authentication |
| `GET` | `/api/v1/me` | `get_my_profile` | JWT (`owner_id`) | User Profile |
| `GET` | `/api/v1/users/me` | `get_my_profile` | JWT (`owner_id`, Alias) | User Profile |
| `PATCH` | `/api/v1/me` | `update_my_profile` | JWT (`owner_id`) | User Profile |
| `PATCH` | `/api/v1/users/me` | `update_my_profile` | JWT (`owner_id`, Alias) | User Profile |
| `POST` | `/api/v1/items` | `create_item` | JWT (Pure Python Cold-Start) | Item Inventory |
| `GET` | `/api/v1/items` | `get_items` | JWT (Filtered strictly by `owner_id`) | Item Inventory |
| `PUT` | `/api/v1/items/{item_id}` | `update_item` | JWT (Enforces `owner_id`) | Item Inventory |
| `DELETE` | `/api/v1/items/{item_id}` | `delete_item` | JWT (Enforces `owner_id`) | Item Inventory |
| `POST` | `/api/v1/items/{item_id}/restock` | `restock_item` | JWT (Enforces `owner_id`) | Restock Action |
| `GET` | `/api/v1/forecasts/today` | `get_todays_forecasts` | JWT (Zero-Restock Waste Coherent) | ML Read Layer |
| `GET` | `/api/v1/forecasts/{item_id}` | `get_item_forecast_detail` | JWT (Historical 7d + 7d Forecast) | ML Read Layer |
| `POST` | `/api/v1/closing-count` | `record_closing_count` | JWT (Perishable Overnight Reset) | Daily Routines |
| `POST` | `/api/v1/daily-stock/closing-count` | `record_closing_count` | JWT (Perishable Overnight Reset, Alias) | Daily Routines |
| `POST` | `/api/v1/midday-count` | `record_midday_count` | JWT (Sales Pace Ratio Trigger) | Daily Routines |
| `POST` | `/api/v1/daily-stock/midday-count` | `record_midday_count` | JWT (Sales Pace Ratio Trigger, Alias) | Daily Routines |
| `GET` | `/api/v1/review/yesterday` | `get_yesterday_review` | JWT (Authoritative Sell-Through) | Daily Routines |
| `GET` | `/api/v1/daily-stock/review/yesterday`| `get_yesterday_review` | JWT (Authoritative Sell-Through, Alias) | Daily Routines |
| `POST` | `/api/v1/sales/intraday` | `record_intraday_sale` | JWT (Enforces `owner_id`) | POS Operations |
| `GET` | `/api/v1/waste-alerts` | `get_waste_alerts` | JWT (Commercial Markdown Tiers) | Waste Action Engine |
| `POST` | `/api/v1/waste-alerts/{item_id}/apply-discount` | `apply_discount_action` | JWT (10% / 20% Commercial Rule) | Waste Action Engine |
| `POST` | `/api/v1/waste-alerts/{item_id}/apply-bundle` | `apply_bundle_action` | JWT (20% Combo Pairing) | Waste Action Engine |
| `POST` | `/api/v1/waste-alerts/{item_id}/dismiss` | `dismiss_alert_action` | JWT (Enforces `owner_id`) | Waste Action Engine |
| `POST` | `/api/v1/jobs/rollup-daily-sales` | `trigger_daily_sales_rollup` | Admin API Key / JWT | Scheduled Jobs |
| `GET` | `/api/v1/briefing/today` | `get_today_executive_briefing`| JWT (Cached 10m, Gemini 3.5 Flash) | AI Operations |
| `POST` | `/api/v1/assistant/chat` | `assistant_chat` | JWT (Grounded RAG Dialogue) | AI Operations |
| `GET` | `/openapi.json` | `openapi` | Public | Documentation |
| `GET` | `/docs` | `swagger_ui_html` | Public | Documentation |
| `GET` | `/docs/oauth2-redirect` | `swagger_ui_redirect` | Public | Documentation |
| `GET` | `/redoc` | `redoc_html` | Public | Documentation |

---

## 3. Flutter Application Inventory

### Client Screens (12 Screens in `APP/lib/screens/`)
1. **`login_screen.dart`**: Multi-tenant authentication, instant cold-start status banner, client-side lockout display, clean production appearance.
2. **`register_screen.dart`**: New store owner signup with form validation.
3. **`tour_screen.dart`**: Gated onboarding interactive walkthrough powered by `SampleRepository`. Unconditionally switches to `LiveRepository()` upon completion or back navigation.
4. **`store_setup_screen.dart`**: Store operating parameters (business name, IANA timezone, opening and closing hours, currency).
5. **`item_setup_screen.dart`**: Initial item catalog creator with instant cold-start category prior initialization.
6. **`dashboard_screen.dart`**: Primary executive store overview with `Executive AiBriefingCard`, live forecast cards, stock progress bars, and floating quick-actions.
7. **`inventory_checkin_screen.dart`**: Scrollable 3-tab operational routine view (`Closing Count`, `Mid-Day Pace`, `Yesterday Review`). Features docked labels and backfill capabilities.
8. **`waste_alerts_screen.dart`**: Dynamic waste risk feed with commercial markdown mitigations (10% discount, 20% combo bundle pairing).
9. **`item_detail_forecast_screen.dart`**: Deep-dive item analytics displaying historical 7-day sales and 7-day rolling forecast charts.
10. **`settings_screen.dart`**: Store profile management, operating hours review, and account logout.
11. **`forgot_password_screen.dart`**: Password reset recovery flow.
12. **`dashboard_placeholder_screen.dart`**: Lightweight skeleton loading state for cold starts.

### Client State Providers (3 Providers in `APP/lib/providers/`)
1. **`inventory_provider.dart`**: Manages store item catalog, point-estimate restock quantities, cold-start forecasts, and active catalog state.
2. **`stock_check_provider.dart`**: Coordinates daily routine submissions (midday counts, closing counts, backfills, and yesterday review sell-through rates).
3. **`waste_alerts_provider.dart`**: Evaluates intraday sales pace ratios and manages commercial markdown mitigation actions.

---

## 4. Master Defect Log Extension (NEW-1 through NEW-8)

*Preserves existing Black Book defect records DEF-001 through DEF-013.*

| Defect ID | Description | Classification | Severity | Detection Method | Commit / Source | Resolution Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NEW-1** | Zero-restock incoherence: items with active Low/Critical waste alert showed positive restock quantities. | Business Logic | High | End-to-end operational sanity probe | `43edbac3` | **Resolved**: Restock quantity clamped to 0 when item has active waste risk alert. |
| **NEW-2** | Cloud AI Quota Exhaustion (`429 RESOURCE_EXHAUSTED`) on `gemini-3-flash-preview` due to 20 req/day cap. | Generative AI | High | Physical device testing & server logs | `43edbac3`, `75143cd3` | **Resolved**: Upgraded to `gemini-3.5-flash` with candidate fallback and 10-minute briefing cache. |
| **NEW-3** | Newly added inventory items displayed 0 predicted demand and empty safety stock prior to ML batch run. | Data Pipeline | Medium | New user onboarding test | `43edbac3` | **Resolved**: Pure-Python category prior engine initializes cold-start forecasts instantly on item creation. |
| **NEW-4** | Login endpoint allowed unlimited failed authentication attempts without rate-limiting or lockout. | Security / Auth | High | OWASP authentication security audit | `43edbac3` | **Resolved**: 5 consecutive failed attempts per email triggers a 15-minute HTTP 429 account lockout. |
| **NEW-5** | Blocking synchronous GenAI calls froze FastAPI event loop during ~10s network requests. | Performance | High | Concurrency latency profiling | `9583f7ae` | **Resolved**: Wrapped all GenAI invocations in `asyncio.to_thread` for non-blocking concurrency. |
| **NEW-6** | Demo Tour providers remained stuck in `SampleRepository` after tour exit, showing mock items in real store. | State Mgmt | Critical | Phone screenshot audit (`user_uploaded/media_...`) | `75143cd3`, `5aeb374d` | **Resolved**: Unconditional `switchToLive()` across all 3 providers on tour exit and back gesture. |
| **NEW-7** | TabBar text clipped on small Android viewports; closing count input labels overlapped user-entered numbers. | UI / Layout | Medium | Phone screenshot audit (`user_uploaded/media_...`) | `75143cd3`, `5aeb374d` | **Resolved**: Set `isScrollable: true` with `TabAlignment.start`, and `FloatingLabelBehavior.always`. |
| **NEW-8** | Debug server switcher link visible to real users on mobile login screen, exposing backend routing options. | UI / Config | Low | Phone screenshot audit (`user_uploaded/media_...`) | `75143cd3` | **Resolved**: Removed server switcher from login screen; enforced seamless production endpoint. |

---

## 5. Black Book Academic Mapping (NMIMS MPSTME IT Template)

All empirical discoveries and system enhancements map directly to the official departmental report structure:

### Chapter 1: Introduction
- **Section 1.4 (Contributions)**:
  - Added the dual-tier cold-start forecasting architecture: instantaneous pure-Python category prior initialization for new items, seamlessly transitioning to rolling historical ML estimation.
  - Formulated the zero-restock operational coherence constraint: guarantees that items actively at risk of spoilage are never simultaneously recommended for inventory replenishment.
  - Documented non-blocking asynchronous GenAI offloading: offloading synchronous foundation model inference to thread pools to maintain sub-50ms API responsiveness for concurrent store operations.

### Chapter 2: Literature Review
- **Section 2.2 (Comparative Analysis)**:
  - Benchmarked commercial food waste mitigation heuristics (dynamic 10% markdown, 20% combo bundle pairing) against traditional static pricing models.
  - Grounded the dual-layer LLM architecture (Google Gemini 3.5 Flash combined with deterministic zero-math rule engine) within contemporary RAG and conversational AI literature for operational enterprise settings.

### Chapter 3: Methodology and Implementation
- **Section 3.1 (System Architecture)**:
  - Updated architectural block diagram: Client Tier (12 Flutter Screens, 3 State Providers) $\leftrightarrow$ Application Tier (FastAPI, 29 REST endpoints, non-blocking `asyncio.to_thread`) $\leftrightarrow$ Storage Tier (MongoDB Atlas Replica Set) $\leftrightarrow$ Intelligence Tier (Batch ML Engine + Google GenAI).
- **Section 3.2 (Hardware & Environment Specifications)**:
  - Documented physical mobile hardware verification: Xiaomi Redmi Note 10 Pro (Snapdragon 732G, 6GB RAM, Android 13).
  - Documented cloud container environment: Render Standard Linux Container (512MB RAM cap; verified 72MB active RSS footprint).
- **Section 3.3 (Software Implementation)**:
  - **Data Capture Routines**: Documented closing counts with perishable overnight reset and backfill idempotency.
  - **Waste Action Engine**: Documented intraday pace ratio formulation ($actual / expected$) and commercial mitigation triggers.
  - **REST API Endpoints Table**: Inserted complete 33-route OpenAPI specification table (29 functional endpoints across 9 domains).
  - **State Management**: Formally detailed provider-repository lifecycle transitions (`SampleRepository` $\to$ `LiveRepository`).

### Chapter 4: Results and Discussion
- **Section 4.1–4.3 (Model Accuracy & Simulation Economics)**:
  - Retained verified empirical figures: Control 3 GBDT ($lag\_1$) achieving 25.48% pooled WAPE (+2.47 pp gain over Prophet, $p = 0.0138$), and Hybrid Simulation Economics (€40,571.43 net profit, 35.0% waste reduction under Critical Ratio $z^* = +0.25$).
- **Section 4.4 (Verification & Regression Testing)**:
  - Added Table 4.4b (Master Test Results): 43 Flutter automated tests, 13 backend unit/isolation tests, and 10-step staging user journey against `restockiq_staging`.
  - Documented OWASP security verifications: multi-tenant owner-id isolation (10/10 endpoints protected) and anti-spoofing reverse-proxy rate limiting (`ips[-1]`).
- **Section 4.5 (Defect Log & Post-Mortem Register)**:
  - Preserved original Table 4.5 entries DEF-001 through DEF-013.
  - Appended Table 4.5b (Hardening Defect Register) documenting NEW-1 through NEW-8 with full root-cause analyses and verification commits.
- **Section 4.6 (User Interface & Mobile Verification)**:
  - Formally mapped physical device field trial screenshots across all 5 key user journeys: Onboarding Tour, Store Manager Dashboard, Daily Check-In, Waste Alerts, and On-Duty AI Assistant Dialogue.

### Chapter 5: Limitations
- Highlighted cloud LLM availability constraints: documented Google Gemini 503 transient demand spikes and the necessity of candidate fallback cascades (`gemini-3.5-flash` $\to$ `gemini-3.8-flash` $\to$ `gemini-3.1-flash-lite`) and local deterministic fallback.
- Noted single-store physical operating scope and the uniform 40% COGS ratio assumption ($c_i = 0.40 p_i$).
- Acknowledged lack of automated midnight POS hardware barcode scanner integration.

### Chapter 6: Future Scope & Conclusions
- Outlined V2 roadmap priorities:
  1. Production deployment of Control 3 GBDT ($lag\_1$) engine with automated midnight POS synchronization.
  2. Direct automated purchase order issuance via supplier EDI/WhatsApp integrations based on the Newsvendor Critical Ratio.
  3. Multi-store federated clustering for regional bakery chains.

### Appendix A: Deployment & Field Runbooks
- Referenced `docs/DEPLOY_RUNBOOK.md` for production zero-downtime deployment, environment variable configuration, and database seeding.
- Referenced `docs/PHONE_TEST_RUNBOOK.md` for physical Android device verification and regression test procedures.
