# RestockIQ: Physical Phone Field Verification Runbook

This document defines the authoritative, consistent 13-step operational protocol for conducting an end-to-end field verification test of the RestockIQ mobile application (`RestockIQ-debug.apk` or Flutter debug session) on a physical Android smartphone.

It covers two operational execution targets:
- **Target A: Local Development Backend** with `adb reverse tcp:8000 tcp:8000` (connected to `restockiq_staging`).
- **Target B: Cloud Staging Backend** deployed on Render (`https://restockiq-backend.onrender.com/api/v1`).

> [!IMPORTANT]
> **Branch & Database Safety Rule**: All tests must be executed strictly against git branch `fix/integrity-v1`. Never run this protocol against production database `restockiq` or production tag `v1.0-submission`. The target database is strictly `restockiq_staging`.

---

## 1. Prerequisites & Environment Setup

### 1.1 Physical Device Requirements
1. Android smartphone running Android 8.0 (API 26) or higher.
2. **USB Debugging** enabled under *Settings > Developer Options*.
3. USB data cable connecting the phone to the development PC.
4. Verify device detection:
   ```powershell
   adb devices
   ```
   *Expected Output*: Device ID listed with status `device` (e.g., `d7a5b32e    device`).

### 1.2 Development Machine Setup (Local Target A)
1. USB reverse port forwarding:
   ```powershell
   adb reverse tcp:8000 tcp:8000
   ```
2. Start the local backend pointing to staging:
   ```powershell
   Set-Location -Path "E:\CAP"
   $env:MONGODB_DB = "restockiq_staging"
   $env:STORE_TIMEZONE = "Asia/Kolkata"
   $env:STORE_OPEN_HOUR = "8.0"
   $env:STORE_CLOSE_HOUR = "20.0"
   $env:PORT = "8000"
   $env:GEMINI_MODEL = "gemini-3.5-flash"
   & "Backend\venv\Scripts\python.exe" -m uvicorn Backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 1.3 Cloud Target Setup (Render Target B)
When testing against the deployed Render cloud environment:
- No USB cable or `adb reverse` required.
- The app defaults to `https://restockiq-backend.onrender.com/api/v1` on physical devices.
- Cold start note: If the free-tier Render web service has spun down, the app displays a prominent `"Waking up server..."` banner with a 40-second timeout until the container activates.

---

## 2. Server Selection in App

1. On the **Login Screen**, locate the server selector chip at the bottom.
2. Tap the chip to choose your environment:
   - For **Localhost (PC USB)**: Select `Localhost (127.0.0.1:8000)`.
   - For **Cloud (Render)**: Select `Cloud (Render onrender.com)`.
3. Toast message confirms active target.

---

## 3. The 13-Step Verification Protocol

Execute each step sequentially on the physical smartphone and verify against the expected behavior:

| Step # | Step Name | Operational Action on Device | Expected Result | Badge Status |
|:---:|---|---|---|:---:|
| **1** | **User Registration** | Tap *Don't have an account? Sign Up*.<br>Enter Name, unique Email (`phone_test_N@staging.restockiq.com`), and Password (`Pass@1234`). Tap *Create Account*. | Account created with HTTP 201. JWT issued and stored in SecureStorage. App automatically routes to **Interactive Tour Screen**. | **LIVE** |
| **2** | **Demo Sandbox Walkthrough** | Walk through the 7 interactive tour steps:<br>1. Dashboard & Maturity Chips<br>2. Waste Mitigation (10% discount / 20% bundle)<br>3. Item Detail & Restock Formula<br>4. Mid-Day Check & Simulated Clock (Tap *Simulate 14:30 Clock*)<br>5. Closing Routine & Learning Loop<br>6. Executive AI Briefing & Chat<br>7. Start My Real Store | Top displays `DEMO TOUR` badge. Clock simulation triggers 14:30 local time. Replayed 60-day dataset active in shadow tenant without touching live store. | **DEMO TOUR** |
| **3** | **Demo Sandbox Exit & Purge** | On Step 7, tap *Start My Store*. Confirmation dialog appears: *"Starting your store will delete all sample bakery data. Ready to proceed?"* Tap *Start My Store*. | Calls `DELETE /api/v1/demo`. Shadow documents completely purged. App transitions to **Store Setup Screen** with 0 items. | **DEMO** $\rightarrow$ **LIVE** |
| **4** | **Store Operating Profile Setup** | On *Store Setup Screen*, verify Store Name (`Artisan Bakery`), Operating Hours (`08:00` to `20:00`), Timezone (`Asia/Kolkata`), Currency (`₹`). Tap *Save & Continue*. | Profile saved to MongoDB staging via `PATCH /api/v1/me`. `onboarding_completed` set to `true`. App navigates to Catalog Setup. | **LIVE** |
| **5** | **Add 3 Items (Cold-Start Priors)** | Add 3 items in Catalog Setup:<br>1. *Artisan Sourdough Baguette* (Bakery, 30 on hand, ₹45, perishable)<br>2. *Golden Butter Croissant* (Bakery, 25 on hand, ₹65, perishable)<br>3. *Whole Farm Milk* (Dairy, 20 on hand, ₹60, perishable) | Each item created with immediate pure-Python category prior forecast. Displays `Learning (0/7 days)` maturity chip. Zero crash, zero pending wait. | **LIVE** |
| **6** | **Day 1 Closing Count** | In *Check-In* tab (Closing Count), record leftover units:<br>- Baguette: 5 left<br>- Croissant: 3 left<br>- Milk: 4 left.<br>Tap *Confirm Closing Stock*. | Sold units derived accurately: `Sold = Opening + Restock - Leftover`. Perishables flagged as waste. Confirmation locks inputs. | **LIVE** |
| **7** | **Missing Day 2 Detection** | Open *Yesterday Review* tab on morning of Day 3 before recording Day 2. | Missed closing count correctly detected: status shows `missing`, label shows `no data`, `soldUnits` is `None` (never falsely reported as 0). | **LIVE** |
| **8** | **Day 2 Backfill & Day 3 Closing** | In *Check-In*, select Day 2 date picker and backfill leftover units. Then record Day 3 evening count. | Backfill processed cleanly. Idempotency verified: re-submitting backfill produces identical state with zero duplicate records. | **LIVE** |
| **9** | **Yesterday Review Routine** | Open *Yesterday Review* tab. | Displays authoritative sell-through percentages (e.g. `Croissants: 90.0% sell-through (High)`). Validated against backend calculations. | **LIVE** |
| **10** | **Mid-Day Pace & Waste Alerts** | In *Check-In*, open *Mid-Day Check* tab. Record 28 remaining for Baguette (low sales velocity). Navigate to *Alerts* tab. | Low pace alert triggered: displays **Suggest 10% Discount** and **Apply 20% Bundle**. Tap action $\rightarrow$ state updates. **Audit**: Zero charity donation buttons exist. | **LIVE** |
| **11** | **Executive AI Briefing & Chat** | Return to *Dashboard*. Inspect top **Executive AI Briefing** card. Tap *Ask RestockIQ Assistant*.<br>Query: *"Why is Baguette critical today?"* | Briefing renders verified metrics without hallucinations. Assistant answers within 15 queries/day limit. Coherence check: restock held to 0 for critical items. | **LIVE** |
| **12** | **Second-User Isolation** | From Settings, tap *Log Out*. Register a second user (`owner_beta@staging.restockiq.com`). Navigate to Dashboard. | User B sees an empty store (0 items). Cross-tenant requests to User A's items return HTTP 404. Absolute isolation verified. | **LIVE** |
| **13** | **Logout & Re-Login Re-Entry** | Log out of User B and sign back in as User A (`phone_test_N@staging.restockiq.com`). | App authenticates in < 1s and opens **directly to Main Dashboard**. Because `onboarding_completed: true` is persisted, the tour is **NEVER** shown again. | **LIVE** |

---

## 4. Verification Sign-Off Checklist

Before signing off on physical hardware:
- [ ] Backend terminal confirmed `[DB] Connected to database: restockiq_staging`.
- [ ] Zero requests touched production database `restockiq`.
- [ ] USB port forwarding (`adb reverse tcp:8000 tcp:8000`) or Render HTTPS endpoint maintained stable connectivity.
- [ ] All 13 test steps executed on the physical smartphone.
- [ ] Screenshots captured for each key view according to `docs/blackbook_assets/PHONE_SCREENSHOT_CHECKLIST.md`.
