# RestockIQ Deployment Checklist

This document outlines the strict procedure for deploying changes from branch `fix/integrity-v1` to staging and production environments, along with operational guards for live demo presentations.

---

## 1. Pre-Deployment Integrity Checks

Before initiating any deployment or merge:
- [ ] Confirm git branch is `fix/integrity-v1`:
  ```bash
  git branch --show-current
  ```
- [ ] Verify tag `v1.0-submission` is untouched:
  ```bash
  git show -s --format="%H %s" v1.0-submission
  # Expected: fa546e0a33bbf502e4395a190901fc5718d012b2
  ```
- [ ] Run full automated test suites locally:
  ```bash
  # Backend discovery suite (unit, tenant, timezone, acceptance tests)
  Backend\venv\Scripts\python.exe -m unittest discover -s Backend -p "test_*.py" -v
  # Flutter frontend suite (43/43 tests)
  cd APP && flutter test
  ```
- [ ] Confirm zero lint or analysis warnings:
  ```bash
  cd APP && flutter analyze
  ```

---

## 2. Git Merge Protocol (fix/integrity-v1 -> main)

Deployments to production must follow this exact non-fast-forward merge protocol:

```bash
# 1. Fetch latest remote main and switch to main
git checkout main
git pull origin main

# 2. Merge fix/integrity-v1 with explicit merge commit
git merge --no-ff fix/integrity-v1 -m "Merge fix/integrity-v1: Final Build & Integrity Verification"

# 3. Verify submission tag integrity remains intact
git show -s --format="%H %s" v1.0-submission
# Must match: fa546e0a33bbf502e4395a190901fc5718d012b2

# 4. Push to remote main
git push origin main
```

---

## 3. Render Environment Variables Configuration

Configure the following environment variables in the Render Dashboard (or Docker host) before triggering the build:

| Variable | Staging Default | Production Default | Description |
|---|---|---|---|
| `MONGO_URI` | *(Atlas URI)* | *(Atlas URI)* | MongoDB Atlas connection string. |
| `MONGODB_DB` | `restockiq_staging` | `restockiq_prod` | Targeted MongoDB database name. Ensures staging tests never touch production. |
| `ENVIRONMENT` | `staging` | `production` | Deployment environment identifier. |
| `JWT_SECRET` | *(Secret Key)* | *(Secret Key)* | Cryptographic HMAC secret for signing and verifying JWT tokens. |
| `STORE_TIMEZONE` | `Asia/Kolkata` | `Asia/Kolkata` | Store operating timezone for business-hour fraction calculations and daily rollover. Validated IANA. |
| `STORE_OPEN_HOUR` | `6.0` | `8.0` | Store opening hour in local 24-hour float format (e.g., 06:00 AM or 08:00 AM). |
| `STORE_CLOSE_HOUR` | `20.0` | `20.0` | Store closing hour in local 24-hour float format (e.g., 08:00 PM). |
| `ENGINE` | `legacy` (or `gbdt`) | `legacy` (or `gbdt`) | ML forecasting engine routing (`legacy` moving-average or `gbdt` HistGradientBoosting). |
| `COGS_RATIO` | `0.40` | `0.40` | Cost-of-goods-sold ratio for Newsvendor safety stock critical ratio calculation. |
| `DEMO_PASSWORD` | *(Secret Demo Pwd)* | *(Secret Demo Pwd)* | Password for seeded demo manager account (`demo_manager@restockiq.com`). Never committed to source. |
| `GEMINI_API_KEY` | *(Secret Key)* | *(Secret Key)* | Google Gemini GenAI key for daily briefing and assistant chat. |
| `GEMINI_MODEL` | `gemini-3-flash-preview` | `gemini-3-flash-preview` | Google Gemini model identifier. |
| `RENDER_GIT_COMMIT` | *(Render System Env)* | *(Render System Env)* | Exposed commit SHA for `/health` diagnostics. |

---

## 4. Demo Day Operational Guard (Auto-Deploy OFF)

> [!IMPORTANT]
> **TURN AUTO-DEPLOY OFF ON DEMO DAY**
> In the Render Dashboard:
> 1. Navigate to **RestockIQ Web Service** -> **Settings**.
> 2. Scroll down to **Auto-Deploy**.
> 3. Toggle Auto-Deploy to **No / OFF**.
> 
> *Rationale*: Disabling auto-deploy guarantees that any accidental push, webhook ping, or branch update cannot trigger a mid-presentation rebuild or cause unexpected cold-start downtime while the live mobile app is being demonstrated to evaluators.

---

## 5. Database Compound Unique Indexes

Before running live traffic or batch forecast jobs, verify that compound unique indexes exist in MongoDB:

```python
# daily_sales unique compound index
db.daily_sales.create_index([("owner_id", 1), ("item_id", 1), ("date", 1)], unique=True)

# daily_stock unique compound index
db.daily_stock.create_index([("owner_id", 1), ("item_id", 1), ("date", 1)], unique=True)

# items unique compound index (per owner, lowercase name)
db.items.create_index([("owner_id", 1), ("name_lower", 1)], unique=True)
```

---

## 6. Post-Deployment Verification Protocol

Verify endpoints in this exact sequence immediately after deployment:

1. **Service Liveness & Diagnostics**:
   ```bash
   curl -s https://<render-service-url>/health | jq .
   ```
   *Verify*: `"status": "ok"`, `"database": "connected"`, `"llm_configured": true`.

2. **Operating Hours & Waste Alerts**:
   ```bash
   curl -s -H "Authorization: Bearer <TOKEN>" https://<render-service-url>/api/v1/waste-alerts | jq .
   ```
   *Verify*: If outside store operating hours, returns `"store_status": "closed"` and `alerts: []`. If during open hours, returns `"store_status": "open"` with correct `sales_pace_ratio` based on elapsed business hours.

3. **Executive Daily Briefing**:
   ```bash
   curl -s -H "Authorization: Bearer <TOKEN>" https://<render-service-url>/api/v1/briefing/today | jq .
   ```
   *Verify*: Response contains `executive_summary` and `actions` (3 items). Zero hallucinated prices or quantities.

4. **On-Duty Assistant Chat**:
   ```bash
   curl -s -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
     -d '{"query": "What items require reordering today?"}' \
     https://<render-service-url>/api/v1/assistant/chat | jq .
   ```
   *Verify*: Assistant quotes verified `Restock` numbers derived from `Demand + Safety - Stock`.

---

## 7. Rollback Procedure

If any post-deploy health check fails or unexpected regressions occur:

1. **Render Dashboard Rollback**:
   In Render Dashboard -> Deploys -> Locate previous healthy deployment -> Click **Rollback to this deploy**.

2. **Git Rollback to Pre-flight Commit (`74ccc0a`)**:
   ```bash
   # Reset main to verified rollback commit 74ccc0a
   git checkout main
   git reset --hard 74ccc0a
   git push origin main --force-with-lease
   ```

3. **Restore Verified APK Backup**:
   ```bash
   # Verified pre-flight APK backup location:
   backups/RestockIQ-debug-backup.apk
   ```
