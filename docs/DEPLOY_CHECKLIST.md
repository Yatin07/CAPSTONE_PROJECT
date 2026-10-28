# RestockIQ Deployment Checklist

This document outlines the strict procedure for deploying changes from branch `fix/integrity-v1` to staging and production environments.

---

## 1. Pre-Deployment Integrity Checks

Before initiating any deployment or merge:
- [ ] Confirm git branch is `fix/integrity-v1`.
- [ ] Verify tag `v1.0-submission` is untouched:
  ```bash
  git show -s --format="%H %s" v1.0-submission
  # Expected: fa546e0a33bbf502e4395a190901fc5718d012b2
  ```
- [ ] Run full automated test suites locally:
  ```bash
  # Backend discovery suite (all unit, tenant, timezone, acceptance tests)
  Backend\venv\Scripts\python.exe -m unittest discover -s Backend -p "test_*.py" -v
  # Flutter frontend suite (44 tests)
  cd APP && flutter test
  ```
- [ ] Confirm zero lint or analysis warnings:
  ```bash
  cd APP && flutter analyze
  ```

---

## 2. Environment Variables Configuration

Configure the following environment variables in the Render Dashboard (or Docker host) before triggering the build:

| Variable | Recommended / Default | Description |
|---|---|---|
| `MONGODB_DB` | `restockiq_prod` (or `restockiq_staging`) | Targeted MongoDB database name. Ensures staging tests never touch production. |
| `STORE_TIMEZONE` | `Asia/Kolkata` (or `UTC` / store IANA tz) | Store operating timezone for business-hour fraction calculations and daily rollover. |
| `STORE_OPEN_HOUR` | `8.0` | Store opening hour in local 24-hour time (e.g., 08:00 AM). |
| `STORE_CLOSE_HOUR` | `20.0` | Store closing hour in local 24-hour time (e.g., 08:00 PM). |
| `GEMINI_API_KEY` | *(Secret Key)* | Google Gemini GenAI key for daily briefing and assistant chat. |
| `GEMINI_MODEL` | `gemini-3-flash-preview` | Google Gemini model identifier. |
| `RENDER_GIT_COMMIT` | *(Render System Env)* | Exposed commit SHA for `/health` diagnostics. |

---

## 3. Database Indexes

Before running traffic or batch jobs, ensure compound unique indexes exist:
```python
# daily_sales unique compound index
db.daily_sales.create_index([("owner_id", 1), ("item_id", 1), ("date", 1)], unique=True)
```

---

## 4. Post-Deployment Verification Protocol

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
   curl -s -H "Authorization: Bearer <TOKEN>" https://<render-service-url>/api/v1/ai/briefing | jq .
   ```
   *Verify*: Response contains `executive_summary` and `actions` (3 items). Zero hallucinated prices or quantities.

4. **On-Duty Assistant Chat**:
   ```bash
   curl -s -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
     -d '{"message": "What items require reordering today?"}' \
     https://<render-service-url>/api/v1/ai/assistant/chat | jq .
   ```
   *Verify*: Assistant quotes verified `Restock` numbers derived from `Demand + Safety - Stock`.

---

## 5. Rollback Procedure

If any post-deploy health check fails or unexpected regressions occur:

1. **Render One-Click Rollback**:
   In Render Dashboard -> Deploys -> Locate previous healthy deployment -> Click **Rollback to this deploy**.

2. **Git Rollback (if merged)**:
   ```bash
   # Revert merge commit while preserving v1.0-submission tag
   git revert -m 1 <MERGE_COMMIT_HASH>
   git push origin main
   ```
