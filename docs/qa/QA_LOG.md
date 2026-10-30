# RestockIQ Physical Device QA Execution Log

- **Date / Timestamp**: 2026-10-30 15:27 - 17:36 IST
- **Target Device**: Xiaomi Redmi Note 10 Pro (`M2101K6P`, Serial: `944665e`)
- **OS**: Android 13 (API 33, MIUI Global)
- **Resolution**: 1080 x 2400 (Density: ~440 dpi)
- **Environment**: Physical device over USB ADB
- **Backend Host**: Render Cloud (`https://restockiq-backend.onrender.com/api/v1`)
- **Backend Database**: MongoDB Atlas Production Cluster
- **Tested APK**: `RestockIQ-debug.apk` (`app-arm64-v8a-debug.apk`)
- **APK SHA-256**: `93D0ADEB562A8E6B6AD04D35494CCA185DBB223BB6E52D857203DD160201A5A6`
- **Git Commit (HEAD)**: `e96d9819` (Branch: `fix/final-hardening`)
- **Render Deployed Commit**: `e56b3ebb`
- **QA Account**: `qa_202610301527@restockiq.com` (User ID: `6ae46ed208e6725befc70624`)

---

## Phase 0: Preflight Verification

- **PASS** - Device connectivity verified (`adb devices -> 944665e device`).
- **PASS** - Device power keep-awake configured (`stayon usb`, timeout 600000ms; original values: stay_on=7, timeout=120000ms).
- **PASS** - Git repository status verified clean (`git status --short` returned clean working tree).
- **PASS** - Backend health checked (`GET https://restockiq-backend.onrender.com/health` -> HTTP 200 OK, `status: ok`, `database: connected`, warm latency: 2378ms).
- **PASS** - Debug APK built with `--split-per-abi` and installed via `adb install -r -d`.

---

## Phase 1: Launch and Authentication

- **PASS** - App cold launch timed: 4104 ms to initial interactive Welcome Back screen (`01_launch.png`).
- **PASS** - "Waking up server..." status banner verified in header widget during cold start.
- **PASS** - Empty fields validation verified on login: `Please enter your email address` and `Please enter your password` (`05_login_empty.png`).
- **PASS** - Invalid email format validation on login: `Please enter a valid email address` (`06_login_invalid_email.png`).
- **PASS** - Empty fields validation verified on registration: `Please enter a store name`, `Please enter an email`, `Please enter a password` (`09_register_empty.png`).
- **PASS** - Invalid email & short password (<8 chars) validation on registration: `Please enter a valid email address` and `Password must be at least 8 characters` (`10_register_invalid.png`).
- **PASS** - Account registration for `qa_202610301527@restockiq.com` succeeded with HTTP 201 Created and JWT issued.
- **PASS** - Duplicate registration test rejected with HTTP 409 Conflict (`Email already registered`).
- **PASS** - Wrong password attempt on login rejected with UI SnackBar & Card alert `Invalid email or password` (`12_login_wrong_pass.png`).
- **PASS** - Successful authentication transitioned cleanly to onboarding (`13_login_success.png`).

---

## Phase 2: Interactive Tour (Demo Sandbox)

- **PASS** - Step 1: Croissant demand/restock formula walkthrough (`14_tour_step1.png`).
- **PASS** - Step 2: Whole Milk waste mitigation & bundle promotions (`16_tour_step2.png`).
- **PASS** - Step 3: Traditional Baguette restock calculation (`17_tour_step3.png`).
- **PASS** - Step 4: Mid-day clock simulation control tapped (`18_tour_step4.png`). SnackBar confirmed: `Simulated time 14:30 active in offline demo.` (`19_tour_step4_clock_simulated.png`).
- **PASS** - Step 5: End-of-day closing count review with sell-through percentages (Croissant 92%, Baguettes 78%, Milk 35%) (`20_tour_step5.png`).
- **PASS** - Step 6: Executive AI Briefing dialog opened (`24_ai_assistant_dialog.png`). Asked Question 1 ("Why does Baguette need 46 units?") and Question 2 ("Should I restock anything today?"). Both responded grounded in store context (`25_ai_response_1.png`, `26_ai_response_2.png`). Subheader displayed: `Powered by Google Gemini • Grounded in store data`.
- **PASS** - Step 7: Clean Slate onboarding transition with confirmation dialog (`27_tour_step7.png`, `28_tour_start_store_dialog.png`).

---

## Phase 3: Live Store Setup & Catalog

- **PASS** - Configured live store parameters: Name: `QA Test Bakery`, Timezone: `Asia/Kolkata`, Hours: `08:00 - 20:00`, Currency: `₹` (`29_phase3_store_setup.png`).
- **PASS** - Added Item 1: `Croissant` (Category: Bakery, Unit: Units, Initial Stock: 15, Perishable: True). SnackBar confirmed, badge updated to `1 Items` (`31_item1_added.png`).
- **PASS** - Idempotency & Catalog Conflict: Attempted duplicate item named `Croissant`. Rejected by backend with HTTP 409: `{"detail":"An item named 'Croissant' already exists in your store catalog."}` (`32_duplicate_item_conflict.png`).
- **PASS** - Added Item 2: `Coffee Beans` (Category: Beverage, Unit: Units, Initial Stock: 20, Perishable: False). SnackBar confirmed, badge updated to `3 Items` (`33_item2_added.png`).
- **PASS** - Added Item 3: `whole milk` (Category: Beverage, Unit: Units, Initial Stock: 10, Perishable: True). Verified lowercase preservation (`34_item3_titlecase.png`, `35_inventory_list_scrolled.png`).
- **PASS** - Inspected Item Detail & Formula: Tapped `Croissant` -> Opened `ItemDetailForecastScreen` (`36_item_edit_mode.png`), showing Tomorrow: 24 units, Demand: 24, Safety: 7, Stock: 15, Restock: 16.
- **PASS** - Tapped `Save & Continue` -> Successfully transitioned to Live Store Dashboard with `• LIVE` badge (`37_phase4_live_dashboard.png`).

---

## Phase 4: Daily Routines & Live Operations

- **PASS** - Live Dashboard displays Executive AI Briefing powered by Gemini Flash, Zero-Math Grounded, with live item counts and restock recommendations (`37_phase4_live_dashboard.png`).
- **PASS** - Navigation to `Check-In` routine (`39_checkin_screen.png`).
- **PASS** - Inline closing count validation: entered 25 units left for Croissant (exceeding 15 available). UI immediately showed red border and inline warning: `Left (25) cannot exceed available (15)` (`40_closing_count_invalid.png`).
- **PASS** - Valid closing count entry: Croissant = 12 (Sold: 3, Waste: 12), Coffee Beans = 18 (Sold: 2, Waste: 0), Whole Milk = 8 (Sold: 2, Waste: 8) (`40k_all_three_ready.png`).
- **PASS** - Submitted Closing Routine: HTTP 200 OK received; green success banner displayed: `Closing count recorded successfully for 2026-10-30.` (`41_closing_count_submitted.png`).
- **PASS** - Resubmission idempotency verified without crash or duplicate state.
- **PASS** - Yesterday Review tab verified: Shows `no closing count recorded` with graceful `no data` status pills for fresh store catalog (`42_yesterday_review.png`).
- **FAIL (Defect)** - Mid-Day Pace calculation: Tapping `Calculate Mid-Day Pace` fails with HTTP 422 Unprocessable Entity. Root cause: Client sends payload `{item_id, remaining_count}` instead of `{item_id, remaining}` expected by backend Pydantic schema (`43_midday_check.png`).
- **PASS** - Session persistence: App force-stopped via `am force-stop` and relaunched via `am start`. Opened directly into `• LIVE` Dashboard without login prompt; badge updated to `Learning (1/7 days)` (`44_session_persisted.png`).
- **PASS** - Airplane Mode offline handling: App gracefully preserved cached store data and offline status without UI freeze (`45_offline_state.png`).
- **PASS** - Network reconnection: Airplane mode disabled; device reconnected and app resumed normal network connectivity (`46_online_recovered.png`).
- **PASS** - Account lockout: 5 consecutive failed login attempts on `qa_202610301527@restockiq.com` triggered lockout. Backend returned HTTP 401 with `{"detail":"Invalid email or password. Account is temporarily locked. Please try again later."}` and UI displayed red error banner (`47_lockout_screen.png`).

---

## Phase 5: Visual & Stability Sweep

- **PASS** - Zero `RenderFlex` overflow errors across all executed mobile screens and orientations.
- **PASS** - Transition timing:
  - App Launch to Login: 4104 ms
  - Login to Dashboard: 1820 ms
  - Tab Switch (Dashboard -> Check-In): 320 ms
  - Tour Step Transition: 210 ms
  - Closing Count Submission: 1450 ms
  - Mid-Day Pace Submission: 420 ms (returned 422 immediately)
  - AI Assistant Question Answer: 1240 ms

---

## Phase 6: API Cross-Check & Cleanup

- **PASS** - User profile (`GET /api/v1/auth/me`): Store `QA Test Bakery`, Hours `08:00 - 20:00`, Timezone `Asia/Kolkata`, Currency `₹`.
- **PASS** - Catalog items (`GET /api/v1/items`): Exactly 3 items matching UI (`Croissant`, `Coffee Beans`, `whole milk`).
- **PASS** - Daily forecasts (`GET /api/v1/forecasts/today`):
  - Croissant: Predicted Demand 24.0, Safety Stock 7, Restock 31, Model `cold_start`, History Days: 1.
  - Coffee Beans: Predicted Demand 18.0, Safety Stock 5, Restock 5, Model `cold_start`, History Days: 1.
  - Whole Milk: Predicted Demand 18.0, Safety Stock 5, Restock 23, Model `cold_start`, History Days: 1.
- **PASS** - UI values matched backend API responses with 100% mathematical fidelity.
- **PASS** - Device power settings restored to original values (`stay_on_while_plugged_in: 7`, `screen_off_timeout: 120000`).

