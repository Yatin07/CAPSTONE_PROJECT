# RestockIQ — Production Deployment Runbook

> [!WARNING]
> **READ-ONLY EXECUTION POLICY**: Do NOT execute deployment commands without explicit user confirmation.
> Target production database: `restockiq` (MongoDB Atlas production cluster).
> Staging database: `restockiq_staging`.
> Base rollback target: Commit `74ccc0a` (`v1.0-submission` base).

---

## Pre-Deployment Readiness Checklist

Before initiating production deployment:
- [x] All P0 integrity fixes merged and tested on branch `fix/integrity-v1`.
- [x] Local physical phone verification completed (`docs/PHONE_TEST_RUNBOOK.md`).
- [x] `flutter analyze` reports **0 issues**.
- [x] `flutter test` reports **43/43 PASSED**.
- [x] Backend unit & tenant isolation test suites **PASSED** (`test_backend_unit.py`, `test_p0_fixes.py`).
- [x] cron-job.org keep-alive monitor operational and logging `200 OK` pings.

---

## 1. Render Environment Variables Configuration

Log in to the [Render Dashboard](https://dashboard.render.com/) $\rightarrow$ select service **`restockiq-backend`** $\rightarrow$ **Environment**.

Configure the following production environment variables:

| Variable Key | Required Value | Purpose |
|---|---|---|
| `STORE_TIMEZONE` | `Asia/Kolkata` | Store-local operational timezone for intraday boundaries |
| `STORE_OPEN_HOUR` | `8.0` | Store opening hour (08:00 AM local) |
| `STORE_CLOSE_HOUR` | `20.0` | Store closing hour (08:00 PM local) |
| `ENGINE` | `legacy` | Production forecasting engine (`legacy` benchmark or `gbdt`) |
| `COGS_RATIO` | `0.4` | Cost of goods sold ratio for Newsvendor critical fractile |
| `MONGODB_DB` | `restockiq` | **Production** database name (isolated from staging) |
| `MONGO_URI` | *(Concealed secret)* | MongoDB Atlas production connection string |
| `JWT_SECRET` | *(Concealed secret)* | Production JWT signing secret (>= 32 chars) |
| `GEMINI_API_KEY` | *(Concealed secret)* | Google AI Studio Gemini API key |
| `GEMINI_MODEL` | `gemini-3.5-flash` | Primary Gemini model (quota-resilient, standard tier) |
| `ALLOWED_ORIGINS` | `https://restockiq.com,https://app.restockiq.com` | Production CORS allowlist |
| `ALLOW_DEMO_SEED` | `false` | Block runtime demo seed backdoors in production |

---

## 2. Render Blueprint (`render.yaml`) Synchronization

### Must `render.yaml` change?
**YES.** The repository Blueprint at `render.yaml` has been updated with the verified model ID and operational defaults:

```yaml
services:
  - type: web
    name: restockiq-backend
    runtime: docker
    dockerfilePath: ./Backend/Dockerfile
    dockerContext: ./Backend
    plan: free
    region: oregon
    healthCheckPath: /health
    envVars:
      - key: MONGO_URI
        sync: false
      - key: JWT_SECRET
        generateValue: true
      - key: GEMINI_API_KEY
        sync: false
      - key: GEMINI_MODEL
        value: gemini-3.5-flash
      - key: STORE_TIMEZONE
        value: Asia/Kolkata
      - key: STORE_OPEN_HOUR
        value: "8.0"
      - key: STORE_CLOSE_HOUR
        value: "20.0"
      - key: COGS_RATIO
        value: "0.4"
      - key: ENGINE
        value: legacy
      - key: MONGODB_DB
        value: restockiq
      - key: ALLOWED_ORIGINS
        value: "https://restockiq.com,https://app.restockiq.com"
      - key: ALLOW_DEMO_SEED
        value: "false"
```

If Render is configured via Blueprint Sync, apply the Blueprint changes in the dashboard.

---

## 3. Merge to Main (Production Release)

> [!CAUTION]
> Execute merge strictly when ready. Never rebase or force-push over `v1.0-submission` (`fa546e0a33bbf502e4395a190901fc5718d012b2`).

### Merge Command Sequence
```bash
# 1. Ensure fix/integrity-v1 working tree is clean
git status

# 2. Check out main
git checkout main

# 3. Fast-forward merge or merge-commit from fix/integrity-v1
git merge fix/integrity-v1 --no-ff -m "release: production integrity v1.0 deployment"

# 4. Push to remote main (triggers Render deploy if Auto-Deploy is active)
git push origin main
```

---

## 4. Verify Production Deployment via `/health`

Once Render finishes building the Docker image (typically 2 to 3 minutes):

### Health Check Command
```bash
curl -fsS https://restockiq-backend.onrender.com/health | jq .
```

### Expected Output
```json
{
  "status": "ok",
  "database": "connected",
  "RENDER_GIT_COMMIT": "<new-commit-hash>",
  "store_timezone": "Asia/Kolkata",
  "llm_configured": true,
  "counts": {
    "users": ...,
    "items": ...,
    "forecasts": ...,
    "daily_stock": ...
  }
}
```

**Verification criteria**:
1. `status` must be `"ok"`.
2. `database` must be `"connected"`.
3. `RENDER_GIT_COMMIT` must match your newly merged `main` commit SHA.
4. `llm_configured` must be `true`.

---

## 5. Seed Demo Store in Production (`--reset` Scoped to Demo Owner)

> [!IMPORTANT]
> **Tenant Isolation Verification**: The demo seeding script targets `demo_manager@restockiq.com` only.
> File reference: `scripts/seed_demo_store.py:95-105`:
> ```python
> db.items.delete_many({"owner_id": user_id})
> db.daily_stock.delete_many({"owner_id": user_id})
> db.daily_sales.delete_many({"owner_id": user_id})
> db.forecasts.delete_many({"owner_id": user_id})
> ```
> Every mutation strictly filters by `{"owner_id": user_id}`. It is **mathematically impossible** for this script to delete or alter any real user's catalog items, routines, or sales records.

### Execution Command
```powershell
# Set production MongoDB URI and target database
$env:MONGODB_URI = "<PROD_MONGODB_ATLAS_URI>"
$env:DEMO_PASSWORD = "<SECURE_DEMO_PASSWORD>"
$env:STORE_TIMEZONE = "Asia/Kolkata"

# Run seed with --reset scoped exclusively to demo_manager@restockiq.com
& "E:\CAP\Backend\venv\Scripts\python.exe" "E:\CAP\scripts\seed_demo_store.py" --db restockiq --reset
```

### Expected Output
```text
[SEED] Target Database: restockiq
[SEED] Demo Account: demo_manager@restockiq.com
[SEED] Password: [PROTECTED / CONCEALED]
[SEED] Existing user found (<user_id>). Purging prior demo records for idempotency...
[SUCCESS] Seeded demo store in 'restockiq':
  - User: demo_manager@restockiq.com (owner_id=<user_id>)
  - Items created: 7 (Traditional Baguette, Croissant, Pain au Chocolat, ...)
  - Daily sales inserted: 420
  - Daily stock inserted: 420
  - Flags: replayed_dataset=True on store and items
```

---

## 6. GitHub Actions Nightly ML Batch Forecast Workflow

### A. Set Repository Secret
In GitHub $\rightarrow$ **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions**:
* Add/Verify Secret: `MONGODB_URI` = `<PROD_MONGODB_ATLAS_URI>`

### B. Trigger Nightly Workflow Manually
In GitHub $\rightarrow$ **Actions** $\rightarrow$ **Nightly ML Batch Forecast** $\rightarrow$ **Run workflow**:
* Branch: `main`
* `dry_run`: `false`
* `engine`: `legacy` (default)
* Click **Run workflow**.

Verify execution logs:
* Step `Run Nightly Batch Forecasting` completes with exit code 0.
* Output shows `[BATCH [LIVE]] Processing <n> items for forecast date: <today> using ENGINE=legacy`.
* `db.forecasts` contains updated predictions for all items.

### C. Requirements for Switching to `gbdt` Engine
If changing the workflow input `engine` from `legacy` to `gbdt`:
1. **Dependencies (`ML/requirements.txt`)**:
   Ensure `scikit-learn>=1.3.0` and `scipy>=1.10.0` are present (already included).
2. **Environment Variables**:
   Workflow `env:` block must supply `COGS_RATIO: "0.4"` (or custom store ratio) for Newsvendor safety stock computation.
3. **Historical Data Prerequisite**:
   Items must have $\ge 28$ days of historical daily sales recorded to activate the `HistGradientBoostingRegressor` model (items with $< 28$ days automatically fall back to TSB/benchmark shrinkage without failure).

---

## 7. Turn Auto-Deploy OFF (Deployment Freeze)

To prevent accidental redeployments during defense presentation:
1. In the **Render Dashboard** $\rightarrow$ **restockiq-backend** $\rightarrow$ **Settings**.
2. Scroll to **Auto-Deploy**.
3. Toggle from **Yes** to **No**.
4. Confirm: Status displays *"Auto-Deploy: Off"*.

---

## 8. cron-job.org Health Check & Keep-Alive Monitoring

Verify that external keep-alive monitoring is active:
1. Open [cron-job.org Console](https://console.cron-job.org/jobs).
2. Inspect job **RestockIQ Backend Keep-Alive** (Job ID: `8748949`).
3. Verify:
   * Target URL: `https://restockiq-backend.onrender.com/health`
   * Schedule: `*/14 * * * *` (Every 14 minutes)
   * Execution History: Last 10 executions must report **`200 OK`** with duration $\le 1.5$ seconds.

---

## 9. Rollback Runbook (Zero-Downtime Rollback to `74ccc0a`)

If an unexpected production incident occurs:

### Immediate Rollback Procedure
1. In the **Render Dashboard** $\rightarrow$ **restockiq-backend** $\rightarrow$ **Events**.
2. Locate the deployment for commit **`74ccc0a`** (or click **Manual Deploy** $\rightarrow$ **Deploy a specific commit**).
3. Enter Commit SHA: `74ccc0a8` (or `74ccc0a`).
4. Click **Deploy**.
5. Render spins up the previous container and performs zero-downtime health check cutover.

### CLI Rollback via Git (Alternative)
```bash
# Revert main branch to 74ccc0a
git checkout main
git reset --hard 74ccc0a8
git push origin main --force-with-lease
```

### Verify Rollback
```bash
curl -fsS https://restockiq-backend.onrender.com/health | jq .RENDER_GIT_COMMIT
# Expected output: "74ccc0a"
```
