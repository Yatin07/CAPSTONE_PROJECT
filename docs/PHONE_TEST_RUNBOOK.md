# RestockIQ: Physical Phone Field Verification Runbook

This document defines the exact step-by-step operational protocol for conducting an end-to-end field verification test of the RestockIQ mobile application (`RestockIQ-debug.apk` or Flutter debug session) connected to a local backend instance backed by the real Atlas staging database (`restockiq_staging`).

> [!IMPORTANT]
> **Branch Rule**: All tests must be executed strictly against git branch `fix/integrity-v1`. Never run this protocol against production database `restockiq` or production tag `v1.0-submission`.

---

## 1. Prerequisites & Environment Setup

### 1.1 Physical Device Requirements
1. Android smartphone (Android 8.0 / API 26 or higher).
2. USB Debugging enabled under **Developer Options**.
3. High-quality USB data cable connecting the smartphone to your development PC.

### 1.2 Development Machine Prerequisites
1. Android SDK Platform-Tools installed with `adb` available in `$PATH`.
2. Python virtual environment active in `Backend/venv`.
3. Valid `MONGODB_URI` configured in `Backend/.env`.

---

## 2. Exact Execution Commands

### Step A: Verify Device Connectivity
Open a terminal (PowerShell or Bash) and execute:
```powershell
adb devices
```
*Expected Output*: Exactly one physical device listed with status `device` (e.g. `d7a5b32e    device`). If listed as `unauthorized`, accept the RSA key fingerprint prompt on your phone display.

### Step B: Configure USB Reverse Port Forwarding
Reverse forward local port 8000 so that requests to `127.0.0.1:8000` on the Android device route directly over USB to the local backend on your computer:
```powershell
adb reverse tcp:8000 tcp:8000
```
*Expected Output*: `8000`

### Step C: Start the Backend Locally with Staging Database
Open a dedicated terminal window on your PC and run:
```powershell
# Set-Location to repository root
Set-Location -Path "E:\CAP"

# Set environment variables for staging database and local timezone
$env:MONGODB_DB = "restockiq_staging"
$env:STORE_TIMEZONE = "Asia/Kolkata"
$env:STORE_OPEN_HOUR = "8.0"
$env:STORE_CLOSE_HOUR = "20.0"
$env:PORT = "8000"

# Launch FastAPI server with live reload and request logging
& "Backend\venv\Scripts\python.exe" -m uvicorn Backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*Expected Output*:
```text
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
[DB] Connected to MongoDB Atlas successfully.
[DB] Connected to database: restockiq_staging
```

### Step D: How to Capture Logs
To monitor both client and server events simultaneously during the test:
1. **Physical Phone Logs (adb logcat)**:
   In a separate PowerShell window, run:
   ```powershell
   adb logcat -v time -s flutter:V RestockIQ:V *:E | Tee-Object -FilePath "docs/phone_test_logcat.log"
   ```
2. **Backend Server Logs**:
   The backend terminal window will output all incoming HTTP requests, response status codes, and execution timings in real time:
   ```text
   INFO: 127.0.0.1:51234 - "POST /api/v1/auth/register HTTP/1.1" 201 Created
   INFO: 127.0.0.1:51234 - "POST /api/v1/items HTTP/1.1" 201 Created
   INFO: 127.0.0.1:51234 - "GET /api/v1/briefing/today HTTP/1.1" 200 OK
   ```

### Step E: Launch the App on Device
In another terminal, build and run the app on the connected device:
```powershell
Set-Location -Path "E:\CAP\APP"
flutter run -d <device_id>
```

---

## 3. Server Selection in App

1. On the initial **Login Screen**, locate the server target indicator chip at the bottom:
   `Server: Localhost ⚡` or `Server: Cloud (Render) ☁️`.
2. Tap the server chip to open the **Backend Server Target** dialog.
3. Select **Localhost (PC / Web)** (`http://127.0.0.1:8000/api/v1`).
4. A toast message confirms: `Target: Localhost (127.0.0.1:8000)`.

---

## 4. End-to-End Walkthrough Procedure & Results Verification Table

Fill in this table as you execute each step on your physical device:

| Step # | Test Action | Expected Result | Actual Result (User To Fill) | Badge Status |
|:---:|---|---|---|:---:|
| **1** | **User Registration**<br>Tap *Don't have an account? Sign Up*.<br>Enter unique Name, Email (e.g., `phone_tester@restockiq.com`), and Password (`Pass@1234`). Tap *Create Account*. | Account created with HTTP 201. JWT token issued and stored in SecureStorage. App automatically routes to the first-time **Interactive Tour Screen**. | `[PENDING PHONE TEST]` | **LIVE** |
| **2** | **First-Time Tour**<br>Step through the 3 interactive tour slides: (1) ML Restock Formula, (2) Waste Mitigation Alerts, (3) Closing Stock Learning Loop. Tap *Finish Tour*. | Header displays `DEMO TOUR` badge during walkthrough. Upon finishing, `SampleRepository` unbinds and app navigates to **Store Setup Screen** (`onboarding_completed: false`). | `[PENDING PHONE TEST]` | **DEMO TOUR** $\rightarrow$ **LIVE** |
| **3** | **Replay Tour from Settings**<br>Later, navigate to Settings $\rightarrow$ tap *Replay Product Tour*. Tap back arrow $\leftarrow$. | Tour reopens cleanly with sample data and `DEMO TOUR` badge. Back arrow returns cleanly to Settings without altering store state. | `[PENDING PHONE TEST]` | **DEMO TOUR** |
| **4** | **Store Configuration**<br>On *Store Setup Screen*, verify Store Name (e.g. `Artisan Corner`), Operating Hours (`08:00` to `20:00`), Timezone (`Asia/Kolkata`), Currency (`₹`). Tap *Save & Continue*. | Profile saved to MongoDB Atlas `users` collection via `PATCH /api/v1/users/me`. App transitions to **Catalog Item Setup**. | `[PENDING PHONE TEST]` | **LIVE** |
| **5** | **Add 3 Items (Instant Cold-Start)**<br>Add 3 items:<br>1. *Traditional Baguette* (Bakery, 5 units on hand, ₹40)<br>2. *Whole Milk* (Beverage, 20 units on hand, ₹60)<br>3. *Almond Croissant* (Bakery, 2 units on hand, ₹50) | Each item receives an immediate pure-Python category-prior forecast (Bakery: 24 demand / 7 safety; Beverage: 18 demand / 5 safety) with `Learning (0/7 days)` maturity chip. No crash, no pending ML wait. | `[PENDING PHONE TEST]` | **LIVE** |
| **6** | **Day 1 Closing Count**<br>Navigate to *Check-In* tab (Tab 0: Closing Count).<br>Enter leftover physical units:<br>- Baguette: 3 left<br>- Whole Milk: 18 left<br>- Croissant: 0 left (Sold Out).<br>Tap *Confirm Closing Stock*. | Units sold and spoilage computed accurately: perishable leftovers flagged as waste; non-perishables carry over. Confirmation locks inputs. | `[PENDING PHONE TEST]` | **LIVE** |
| **7** | **Next-Day Review Routine**<br>In *Check-In* screen, switch to *Yesterday Review* tab. | Review card displays yesterday's recorded sales, waste units, and audit status (`Completed 3 of 3 items`). | `[PENDING PHONE TEST]` | **LIVE** |
| **8** | **Mid-Day Progress Check**<br>In *Check-In* screen, select *Mid-Day Check* tab.<br>Record 2 units sold for Whole Milk. | Intraday sales event recorded via `POST /api/v1/sales/intraday`. Remaining stock decrements dynamically. | `[PENDING PHONE TEST]` | **LIVE** |
| **9** | **Intraday Waste Alerts**<br>Navigate to *Alerts* tab.<br>Observe alert cards generated during business hours:<br>- Low Pace alert: 10% markdown button.<br>- Critical Expiry alert: 20% combo bundle pairing with partner SKU.<br>**CRITICAL AUDIT**: Verify **NO** donation buttons appear anywhere. | Commercial markdown and combo actions present. Tap *Apply Discount* or *Apply Bundle* $\rightarrow$ state changes to *Discount Applied* / *Bundle Active*. Zero charity donation buttons. | `[PENDING PHONE TEST]` | **LIVE** |
| **10** | **Executive AI Briefing & Coherence**<br>Return to *Dashboard*. Inspect the top **Executive AI Briefing** card. | Briefing card renders summary and 3 key actions. **COHERENCE VERIFICATION**: Items with active waste alerts show restock quantity **0** (e.g. *Waste mitigation for Whole Milk: restock held to 0*). Displays `[Deterministic Fallback Mode]` or `[Live Gemini 3 Flash]` badge. | `[PENDING PHONE TEST]` | **LIVE** |
| **11** | **Grounded Store Assistant**<br>Tap *Ask RestockIQ Assistant* button on briefing card.<br>Query: *"Should I restock Whole Milk today?"* | Grounded response answers: *"No, Whole Milk has an active waste alert with lagging sales pace. Recommended restock is 0; apply scheduled combo markdown instead."* Zero hallucination. | `[PENDING PHONE TEST]` | **LIVE** |
| **12** | **Logout & Login Re-entry**<br>Navigate to Settings $\rightarrow$ tap *Log Out*.<br>Sign back in with registered email and password. | App logs in in < 1 second. Since `onboarding_completed: true` is stored in user profile, app opens **directly to Main Dashboard**; first-time tour is **NOT** shown again. | `[PENDING PHONE TEST]` | **LIVE** |
| **13** | **Airplane Mode Resilience**<br>Turn ON phone Airplane Mode.<br>Attempt to refresh dashboard or submit stock count.<br>Turn OFF phone Airplane Mode. | App displays clear, non-blocking offline banner (`Network connection lost. Please check connection.`). App does **not** crash or freeze. Once network is toggled back on, live sync resumes immediately. | `[PENDING PHONE TEST]` | **OFFLINE** $\rightarrow$ **LIVE** |

---

## 5. Verification Sign-Off Checklist

Before considering Section 2 complete on hardware:
- [ ] Backend terminal confirmed `[DB] Connected to database: restockiq_staging`.
- [ ] No requests touched production database `restockiq`.
- [ ] `adb reverse tcp:8000 tcp:8000` maintained stable connection throughout the test.
- [ ] All 13 test steps executed on the physical smartphone.
- [ ] Screenshot captured for each key view according to `docs/blackbook_assets/PHONE_SCREENSHOT_CHECKLIST.md`.

