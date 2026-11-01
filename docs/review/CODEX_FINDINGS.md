# RestockIQ independent read-only audit

Audit target: working tree at `fix/final-pass`, HEAD `60b90d26f9def2fccb383107a95b8b926c43c4e3` (2026-11-01 local date). `main` ref is `66537a32694d4c53f9fa85f9c4272eda63f1b80c`; `feat/adaptive-forecast` is `3106597fe286124b31f2622131e18700b4dd4319`. Adaptive backend files compared were identical between `main` and this HEAD; no branch checkout was done. At audit start, tracked files were modified and many assets untracked; final status showed only `docs/review/` untracked. I did not run a command intended to revert those entries; their disappearance is unexplained. Exactly this report file was added by this task. No database writes and no production network calls were made.

**Evidence convention:** line numbers refer to the final working tree and are given with concrete snippets. “COULD NOT VERIFY” means the required proof was not obtained, not that the issue is absent. The earlier status listed edits to `APP/lib/screens/inventory_checkin_screen.dart`, `Backend/services/llm_service.py`, and docs; final status no longer does. The LLM guard was additionally checked with `git show HEAD:Backend/services/llm_service.py`.

## 0. Summary

| Severity | Findings |
|---|---:|
| Critical | 0 confirmed |
| High | 6 confirmed |
| Medium | 11 confirmed |
| Low | 1 confirmed |
| Unverified / refuted suspects | See sections 3–5 |

**Top 10 demo risks:** (1) registration installs sample data; (2) demo can silently switch to local samples on server failure; (3) API fabricates chart points when forecast series are absent; (4) start limit is 20/hour, not five; (5) purge omits assistant-usage rows; (6) tour continues after delete failure; (7) default demo password in seed script; (8) lockout can be induced against a victim; (9) negative sale quantities and forecast overrides accepted; (10) requested mutation checks remain unrun.

**GO / NO-GO:** **NO-GO for presenting this as a single-path server-backed demo or enabling adaptive forecasts on Render** until the demo fallback/cleanup and rate limit are corrected, the production flag and forecast writer policy are validated, the isolated mutation checks pass, and staging-only tests complete. The current Render config explicitly selects legacy mode (`render.yaml:29-32`).

### Findings index

| ID | Severity | Demo-impact | Area | Location | Problem | Confidence | Effort |
|---|---|:---:|---|---|---|---|:---:|
| C-001 | High | Y | Demo | `APP/lib/screens/tour_screen.dart:152-174` | Server demo failure switches to local fixture repository | High | S |
| C-002 | High | Y | Demo | `Backend/main.py:4403-4417` | Demo limiter allows 20 starts/hour | High | S |
| C-003 | Medium | Y | Demo | `Backend/main.py:4317-4341` | Demo purge leaves assistant-usage rows until TTL | High | S |
| C-004 | Medium | Y | Demo | `APP/lib/screens/tour_screen.dart:251-267` | Tour can exit after DELETE failure | High | S |
| C-005 | High | N | Forecast/ops | `render.yaml:29-32` | Render selects legacy, not adaptive forecast | High | S |
| C-006 | High | Y | Forecast/API | `Backend/main.py:2840-2855` | API fabricates chart points if stored forecast series are absent | High | S |
| C-007 | High | Y | Security/demo | `scripts/seed_demo_store.py:115-123` | Source contains fallback demo password | High | S |
| C-008 | High | N | Validation | `Backend/main.py:1248-1282`, `3697-3711` | PUT accepts forecast overrides; intraday accepts nonpositive quantities | High | S |
| C-009 | Medium | Y | Onboarding | `APP/lib/screens/register_screen.dart:64-90` | Successful registration binds SampleRepository before tour starts | High | S |
| C-010 | Medium | N | Tests | `Backend/test_acceptance_lifecycle.py:17`; `ML/batch_forecast.py:64` | Importing tests initializes Mongo client at module import | High | S |
| C-011 | Medium | N | Data integrity | `Backend/main.py:808-816`, `886-914` | Index creation failures are logged and boot continues | High | S |
| C-012 | Medium | Y | Operations | `Backend/main.py:1410-1422`, `1500-1548` | Lockout state combines persistent and process-local counters | High | M |
| C-013 | Medium | Y | Data integrity | `Backend/main.py:4159-4179`, `4235-4255` | Discount/bundle guard is read-then-write, not atomic | High | S |
| C-014 | Medium | Y | Data integrity | `Backend/main.py:3711-3761` | Concurrent intraday taps use read-then-write totals | Med | M |
| C-015 | Low | Y | Currency | `Backend/main.py:4181-4189` | Discount response formats price with `$` regardless of profile currency | High | S |
| C-016 | Medium | N | Flutter/session | `APP/lib/services/api_service.dart:253-271` | SharedPreferences stores user ID, name and role alongside login token | High | S |
| C-017 | Medium | Y | Demo/TTL | `Backend/main.py:1030-1044` | Sliding expiry extends users/items but not all tenant child documents | High | S |
| C-018 | Medium | Y | Workspace isolation | `Backend/main.py:4879-4953` | Rollup route ignores X-Workspace and JWT call is scoped to live owner | High | S |

## 1. Backend route inventory

Route table is derived from FastAPI decorators and handler bodies in `Backend/main.py`. `get_workspace_user` is the tenant-aware dependency; `get_current_user` authenticates the real account but does not select the workspace. Collection lists are direct handler references; helper calls may touch additional collections. `owner filter` identifies whether the handler’s visible query is explicitly tenant scoped.

| Method | Path | Auth dependency | Workspace dependency | Collections touched | Owner filter / location |
|---|---|---|---|---|---|
| POST | `/api/v1/auth/register` | none | no | users | unique email, `main.py:1344-1385` |
| POST | `/api/v1/auth/login` | none | no | users | normalized email, `main.py:1424-1578` |
| GET | `/api/v1/me` | `get_current_user` via wrapper | yes | users (read) | `_id=current_user`, `main.py:1596-1610` |
| PATCH | `/api/v1/me` | `get_current_user` via wrapper | yes | users | `_id=current_user`, `main.py:1632-1702` |
| GET | `/health`, `/api/v1/health` | none | no | none | no DB access, `main.py:1736-1752` |
| GET | `/health/details`, `/api/v1/health/details` | job-secret header | no | users/items/forecasts/daily_stock | global counts/latest forecast, `main.py:1762-1818` |
| POST | `/api/v1/items` | `get_current_user` via wrapper | yes | items/forecasts | owner on inserts, `main.py:1866-2006` |
| GET | `/api/v1/items` | `get_current_user` via wrapper | yes | items | `owner_id`, `main.py:2064-2080` |
| PUT | `/api/v1/items/{item_id}` | `get_current_user` via wrapper | yes | items | `owner_id`, `main.py:2114-2178` |
| DELETE | `/api/v1/items/{item_id}` | `get_current_user` via wrapper | yes | items/forecasts | `owner_id`, `main.py:2212-2224` |
| POST | `/api/v1/items/{item_id}/restock` | `get_current_user` via wrapper | yes | items/daily_stock | `owner_id`, `main.py:2230-2318` |
| GET | `/api/v1/forecasts/today` | `get_current_user` via wrapper | yes | items/forecasts/daily_sales | owner filters, `main.py:2538-2750` |
| GET | `/api/v1/forecasts/{item_id}` | `get_current_user` via wrapper | yes | items/forecasts/daily_sales | owner filters, `main.py:2764-2890` |
| POST | `/api/v1/closing-count` | `get_current_user` via wrapper | yes | items/daily_stock/daily_sales | owner filters, `main.py:2976-3290` |
| POST | `/api/v1/midday-count` | `get_current_user` via wrapper | yes | items/daily_stock/forecasts | owner filters, `main.py:3315-3485` |
| GET | `/api/v1/review/yesterday` | `get_current_user` via wrapper | yes | items/daily_stock | owner filters, `main.py:3509-3680` |
| POST | `/api/v1/sales/intraday` | `get_current_user` via wrapper | yes | items/intraday_sales | owner filters, `main.py:3697-3775` |
| GET | `/api/v1/waste-alerts` | `get_current_user` via wrapper | yes | items/forecasts | owner filters; helper evaluates partner candidates, `main.py:3789-4103` |
| POST | `/api/v1/waste-alerts/{item_id}/apply-discount` | `get_current_user` via wrapper | yes | items | owner filter, `main.py:4119-4193` |
| POST | `/api/v1/waste-alerts/{item_id}/apply-bundle` | `get_current_user` via wrapper | yes | items | owner filter, `main.py:4201-4267` |
| POST | `/api/v1/waste-alerts/{item_id}/dismiss` | `get_current_user` via wrapper | yes | items | owner filter, `main.py:4275-4295` |
| POST | `/api/v1/demo/start` | `get_current_user` | no (creates shadow itself) | users/items/forecasts/daily_sales/daily_stock | shadow ID filters, `main.py:4385-4790` |
| POST | `/api/v1/demo/reset` | `get_current_user` | no (shadow helper) | indirect purge/seed | shadow ID, `main.py:4813-4823` |
| DELETE | `/api/v1/demo` | `get_current_user` | no (shadow helper) | indirect purge | shadow ID, `main.py:4827-4845` |
| POST | `/api/v1/demo/clock` | `get_current_user` | no (explicit shadow lookup) | users | shadow ID, `main.py:4849-4873` |
| POST | `/api/v1/jobs/rollup-daily-sales` | bearer JWT or job secret | no | intraday_sales/daily_sales | owner-scoped for JWT, all tenants with valid secret, `main.py:4879-4955` |
| GET | `/api/v1/briefing/today` | `get_current_user` via wrapper | yes | items; alerts via helper | owner, `main.py:4995-5109` |
| POST | `/api/v1/assistant/chat` | chat limiter + current user | yes | items/assistant_usage; alerts via helper | owner, `main.py:5117-5227` |

`startup_db`/`shutdown_db` are lifecycle hooks, not HTTP routes (`main.py:742-744`, `920`). No other route decorator was found in `Backend/main.py` by AST enumeration.

## 2. Detailed findings

### C-001 — High — demo can silently become an offline mock

**Evidence:** `APP/lib/screens/tour_screen.dart:152-174`: authenticated path calls `startDemo()` then installs `LiveRepository()`; unauthenticated or caught-error path calls `_useSampleFallback()`, which installs `SampleRepository()`.
**Reproduction:** `flutter test --no-pub` includes `Tour flow with SampleRepository renders DEMO TOUR badge and walkthrough steps`; all tests passed. It demonstrates mock tour coverage, not backend parity.
**Impact:** Presenter can complete a tour against local sample behavior instead of the server shadow store. **Minimal fix:** show a retry/error screen for server start failure; reserve SampleRepository for explicit test-only usage. **Proof test:** force `startDemo()` to fail and assert no sample repo is installed.

### C-002 — High — demo start rate differs from stated policy

**Evidence:** `Backend/main.py:4407-4417`: `if len(DEMO_START_RATE_LIMITS[user_id]) >= 20:` then returns “maximum 20 sandbox creations per hour.”
**Reproduction:** not safely load-tested; direct branch condition confirms threshold 20. **Impact:** demo creation can be retried four times the apparent limit; state is process-local. **Minimal fix:** change the enforced threshold/message to the desired value and centralize it if multiple workers are used. **Proof test:** 5th/6th attempt boundary across two workers.

### C-003 — Medium — demo purge omits assistant usage

**Evidence:** `Backend/main.py:4317-4341` deletes user, items, stock, sales, forecasts and alerts only; assistant writes `assistant_usage` at `main.py:5203-5211` with shadow `owner_id` and expiry.
**Reproduction:** code path comparison; no DB writes performed. **Impact:** deleted demo leaves query-count data until TTL (two days). **Minimal fix:** add `db.assistant_usage.delete_many(filter_dict)` to purge and report count. **Proof test:** seed one shadow usage row, purge, assert zero remain while live-owner row remains.

### C-004 — Medium — demo exit proceeds despite server deletion error

**Evidence:** `APP/lib/screens/tour_screen.dart:251-267`: `exitDemo()` is caught, workspace set null, and navigation continues with notice that TTL will clean up.
**Reproduction:** Flutter source behavior; no explicit failing-delete test was found (`COULD NOT VERIFY` comprehensive test inventory). **Impact:** user returns to live mode while shadow records persist. **Minimal fix:** keep demo workspace active and offer retry until DELETE succeeds, or explicitly present deferred cleanup. **Proof test:** mock DELETE 500 and assert user cannot enter the live setup flow silently.

### C-005 — High — adaptive is not selected in Render config

**Evidence:** `render.yaml:29-32` sets `ENGINE=legacy` and `FORECAST_MODE=legacy`; adaptive helper exits unless env is `adaptive` (`Backend/main.py:281-285`).
**Reproduction:** config values read directly; no production URL called. **Impact:** switching feature on in code alone does not use it in deployment. **Minimal fix:** set the Render variable to `adaptive` only after the explicit GO conditions pass. **Proof test:** deployment config assertion plus staging forecast response containing `engine=adaptive-v1`.

### C-006 — High — forecast endpoint fabricates chart series

**Evidence:** `Backend/main.py:2840-2855`: `base = max(5, predicted_demand)` and each chart point is computed from `base * (0.85 + (i * 0.04))` / `base * (0.95 + ((i % 3) * 0.05))`.
**Reproduction:** inspected fallback branch; no live request. **Impact:** a live store can see invented chart values. **Minimal fix:** return empty series plus an unavailable state. **Proof test:** missing stored series produce no synthetic values in response or UI.

### C-007 — High — source has a fallback demo password

**Evidence:** `scripts/seed_demo_store.py:115-123`: `raw_password = demo_password or os.getenv("DEMO_PASSWORD", "DemoStorePass2026!")`.
**Reproduction:** source inspection; password value is a code default, not a live login attempt. **Impact:** if the seeding script is run without an explicit secret, it creates a predictable demo account. **Minimal fix:** require `DEMO_PASSWORD` and fail if missing; rotate any account created from the default. **Proof test:** invocation without password exits before connecting or inserting.

### C-008 — High — forecast overrides and negative sales are accepted

**Evidence:** `Backend/main.py:1256-1266` accepts client-set `currentStock`, `predictedDemand`, `safetyStock`, and `riskLevel`; `1278-1282` accepts unbounded `quantity`; `3709-3711` subtracts it from stock and adds it to sales.
**Reproduction:** request model lacks positive-quantity constraint and excludes none of those fields; no request sent. **Impact:** negative sales increase stock and reduce sales; clients can override forecasts. **Minimal fix:** reject engine-owned fields and require `quantity >= 1`. **Proof test:** invalid bodies return 422 and leave data unchanged.

### C-009 — Medium — registration binds sample data before server tour

**Evidence:** `APP/lib/screens/register_screen.dart:64-90` installs `SampleRepository()` after server registration, then routes to `TourScreen`.
**Reproduction:** direct code path; no account created. **Impact:** sample data is selected before sandbox startup succeeds. **Minimal fix:** bind the demo repository only after successful `startDemo()`. **Proof test:** force start failure and assert no sample inventory is shown.

### C-010 — Medium — test import constructs a Mongo client

**Evidence:** `Backend/test_acceptance_lifecycle.py:17` imports `batch_forecast`; `ML/batch_forecast.py:64` invokes `init_db()` at module import; `main.py:58-65` requires URI config.
**Reproduction:** unittest output emitted `ResourceWarning: Unclosed MongoClient opened at ... batch_forecast.py ... init_db()`. URI was overridden to localhost port 1; Atlas unavailable tests skip. **Impact:** test discovery has connection side effects and warns about an unclosed client. **Minimal fix:** move DB initialization behind `main`/explicit function call and inject a mock in tests. **Proof test:** import module with no URI and assert no client construction.

### C-011 — Medium — required indexes fail open

**Evidence:** `Backend/main.py:808-816` catches index errors and only logs; unique indexes for daily sales, stock, forecasts and items are requested at `main.py:886-914`.
**Reproduction:** no database write/test; catch block establishes boot behavior. **Impact:** duplicate writes/races can persist if uniqueness indexes are absent. **Minimal fix:** fail production startup for required unique-index failures; retain warning-only behavior only for optional indexes. **Proof test:** mock `create_index` raising for a required index and assert startup aborts.

### C-012 — Medium — lockout is not one shared counter

**Evidence:** `Backend/main.py:1410-1416` defines process-local `ACCOUNT_LOCKOUTS`; failures are counted in memory and database at `main.py:1500-1548`; expiry resets both paths at `main.py:1446-1474`.
**Reproduction:** lockout test coverage exists, but multi-process behavior not exercised. **Impact:** a restart or another worker may have different lock state; targeted victim lockout can be triggered by repeated bad logins (the IP limiter is separate). **Minimal fix:** persist the authoritative counter and make failure increments atomic; add per-account abuse controls. **Proof test:** restart/two-worker simulation and attacker rate boundary.

### C-013 — Medium — action idempotency races under simultaneous taps

**Evidence:** discount reads `discountApplied` then updates later without that condition in update predicate (`Backend/main.py:4141-4179`); bundle has same structure (`main.py:4223-4255`).
**Reproduction:** no concurrent DB experiment. Sequential duplicate calls reject; concurrent read-then-write can both pass. **Impact:** duplicate action semantics can race; price compounding is possible only if concurrent requests both compute from an already-updated value in a particular interleaving. **Minimal fix:** atomically update with `discountApplied != true` and require `matched_count == 1`; do likewise for bundle. **Proof test:** concurrent requests yield exactly one success.

### C-014 — Medium — concurrent sale taps can lose totals

**Evidence:** `Backend/main.py:3709-3711` computes counters from a previously read item; `3747-3761` writes absolute values after inserting an event.
**Reproduction:** no concurrency test run. **Impact:** overlapping writes may diverge item counters from event records. **Minimal fix:** atomic increments with stock-floor enforcement. **Proof test:** concurrent sales reconcile item totals with all inserted events.

### C-015 — Low — dollar sign is fixed in a backend message

**Evidence:** `Backend/main.py:4181-4189` formats `New price: ${discounted_price}` while user currency is stored/read from profile (`main.py:1616`, `1716`).
**Reproduction:** code inspection; no action executed. **Impact:** non-dollar stores see a misleading message. **Minimal fix:** use the profile currency symbol in the response. **Proof test:** account currency `₹` returns `₹`.

### C-016 — Medium — local session stores more than the login token

**Evidence:** `APP/lib/services/api_service.dart:253-261` persists `auth_token`, `auth_user_id`, `auth_user_name`, and `auth_user_role` in SharedPreferences.
**Reproduction:** direct source path; no device data inspected. **Impact:** violates a token-only local-storage requirement and retains profile identifiers/name. **Minimal fix:** persist only token and fetch profile after auto-login. **Proof test:** inspect preferences after login and confirm only token remains.

### Refuted suspect — nightly shadow/adaptive overwrite guards

**Evidence:** `ML/batch_forecast.py:316` excludes owners matching `^shadow_`; lines `375-394` skip an existing adaptive forecast. Workflow cron: `.github/workflows/nightly-forecast.yml:1-5`.
**Reproduction:** code inspection; batch not run. **Impact:** inspected code excludes shadow owners and adaptive forecast docs. **Minimal fix:** none indicated. **Proof test:** add explicit shadow exclusion to the existing adaptive-overwrite test.

### C-017 — Medium — shadow sliding expiry does not renew every child row

**Evidence:** `Backend/main.py:1030-1044` updates shadow user and `items`; created sales/stock/forecast documents carry their then-current `expiresAt` (`main.py:3102-3130`, `3168-3170`, `347-348`).
**Reproduction:** source comparison; no DB used. **Impact:** long active demos may lose TTL-indexed child records at an older expiry even as item/user expiry slides. **Minimal fix:** renew `expiresAt` for all shadow collections on activity or use a single tenant expiry policy. **Proof test:** advance TTL clock during active session and verify all demo records survive together.

### C-018 — Medium — rollup endpoint does not honor demo workspace header

**Evidence:** `Backend/main.py:4879-4953` has no `get_workspace_user`; on bearer auth it sets scope from JWT `sub` and calls `rollup_daily_sales` for that owner (`4923-4926`, `4953`).
**Reproduction:** code path; endpoint not called. **Impact:** a request carrying `X-Workspace: demo` still rolls up the authenticated live account's intraday events. **Minimal fix:** reject workspace header on this route or resolve demo workspace before selecting owner. **Proof test:** with both live/demo events, JWT plus demo header rolls only shadow rows or rejects request.

## 3. Known-suspect answers (1–25)

1. **rollup overwrites closing_count — FIXED.** `Backend/main.py:592-600` skips an existing source `closing_count`; writes are owner/item/date upserts at `604-622`. Route invoker is `/api/v1/jobs/rollup-daily-sales` (`4877-4955`) and nightly script/workflow is separate.
2. **restock at zero need adds stock — FIXED.** `main.py:2248-2268` computes `max(0, demand+safety-currentStock)` and returns added 0 when need is zero.
3. **opening stock ignores prior intraday sales — NOT A BUG for this code path.** `main.py:2292-2306` records `currentStock + intradaySales` on first daily-stock insert, reconstructing pre-tap opening quantity if intradaySales is the sold count.
4. **Unclosed perishable stale stock carried — FIXED with fragility.** `main.py:442-480` zeros currentStock if prior day stock absent/unclosed; DB exceptions are swallowed, so failure case remains unsure.
5. **Discount/bundle repeated compounding, cap, original price — PARTLY FIXED.** `main.py:4121-4127`, `4141-4179`, `4203-4255` validate `(0,50]`, reject sequential repeats; rollover restores `originalPrice`/clears promo at `410-439`, `484-510`. Concurrent guard is non-atomic (C-013).
6. **Partner ignores stock, pace, alerts — NOT A BUG.** `main.py:3945-3987` requires positive stock, excludes active alert, then requires pace >=1.0.
7. **Job passes if JOB_SECRET unset/no header — NOT A BUG.** `main.py:4901-4943` rejects missing credentials; when no secret header, valid bearer JWT is required and scoped.
8. **Lockout counter not reset after expiry — NOT A BUG when expiry is observed.** `main.py:1446-1474` resets both counters; distributed-worker state remains a concern (C-012).
9. **Health expensive/public — PARTLY NOT A BUG.** `/health` is public but liveness-only, no DB counts (`main.py:1736-1752`); `/health/details` is secret-protected and does counts (`1758-1818`), with a global latest-forecast lookup (`1814`). Render health path is `/health` (`render.yaml:9`).
10. **unittest sys.modules guard — NOT A BUG in HEAD.** `git show HEAD:Backend/services/llm_service.py` shows `if os.getenv("TESTING") == "1"`, not a `sys.modules` check; live Gemini is allowed when not testing if configured.
11. **mongomock production fallback — NOT A BUG by condition.** `main.py:774-802` permits it only for `ENVIRONMENT=local` or `TESTING=1`; `mongomock-motor` is in `Backend/requirements.txt`.
12. **in-memory counters/cache/lockouts — CONFIRMED.** Login state `main.py:1410-1416`; briefing cache `4977-4987` (key includes state hash at `5055-5065`); assistant quota normally DB-backed but falls back to process memory at `5163-5223`; demo-start limiter `1004`, `4407-4419`.
13. **demo expiry/rate/exit — PARTLY PRESENT.** User/item expiry slides four hours at `1030-1044`, but child docs retain older expiry (C-017); rate actually 20/hour (`4403-4417`); exit proceeds on failed DELETE (`tour_screen.dart:251-267`).
14. **NAME_MAP / fixture honesty — CONFIRMED missing aliases, fixture content COULD NOT VERIFY.** `ML/engine.py:71-85` does not map “whole milk” or “espresso”; three tracked fixture copies exist: `Backend/data/demo_fixture.json`, `Backend/demo_fixture.json`, `ML/data/demo_fixture.json`.
15. **groupby rolling crosses article — NOT A BUG.** `ML/engine.py:201` uses `groupby("article").transform(lambda s: s.shift(1).rolling(...))`, so rolling is performed per article.
16. **legacy real path reads French dataset — CONFIRMED conditionally.** `ML/engine.py:367-413` uses own-data blend at 28+ days for non-replayed mapped/unmapped conditions; fallback/reference branch builds `art_df` from `historical_ref` at `400-413`. API may instead serve stored forecasts; Render says legacy (`render.yaml:29-32`).
17. **two cold-start sources — CONFIRMED.** `Backend/main.py:1902-1913` reads `constants.CATEGORY_PRIORS` (Bakery safety 7 in `Backend/constants.py:8-15`); adaptive n=0 uses 25% of 24 (=6) at `Backend/adaptive_forecast.py:170-180`. If adaptive refresh errors, create-item fallback inserts the other safety value (`main.py:1971-1990`).
18. **forecast_7d uses heuristic multipliers — CONFIRMED in ML engine; user-facing label unsure.** `ML/engine.py:334-335`, `429-430` uses `1.15` for selected weekdays and `0.95` otherwise, tagged `type: indicative`; Flutter presentation label was not verified.
19. **forgot-password promises email token — COULD NOT VERIFY.** Screen source needs direct inspection; no claim is made from QA docs.
20. **shadow login 500 / batch shadow — NOT A BUG in inspected code.** `main.py:1438-1443` rejects shadow accounts with 401; `ML/batch_forecast.py:316` excludes shadow owner IDs.
21. **currency/severity colors — PARTLY PRESENT.** alert colors are red/amber in `main.py:2404-2436`; discount text hardcodes `$` at `4185` (C-015). A full widget color rendering check was not done.
22. **briefing/assistant demo vs live — NOT A BUG for data selection.** Both use `get_workspace_user` and query by `owner_id` (`main.py:4995-5017`, `5117-5131`); demo uses shadow workspace when header is set.
23. **route bypasses workspace while demo header sent — CONFIRMED for rollup route.** `/api/v1/jobs/rollup-daily-sales` ignores workspace header and uses live JWT `sub` (`main.py:4917-4953`); demo-management routes use authenticated real user intentionally.
24. **account lockout abused against victim — CONFIRMED weakness.** Login limiter is process/IP-based (`main.py:638-726`, `1422`) while failed attempts increment victim’s persistent count (`1510-1526`), so attacker can cause lockout by targeting known email. No account-neutral response/secondary verification observed.
25. **QA_LOG/DEFECTS stale claims — COULD NOT VERIFY exhaustively.** Docs are not evidence by instruction; all listed claims require item-by-item code and repro. Current worktree has a pre-existing modified `docs/final/DEFECTS.md`, so HEAD version must be inspected separately before a final claim.

## 4. Refuted / false-positive log

- Restock zero-need fallback stock: false positive; returns 0 (suspect 2).
- Opening stock losing tap sales: false positive for the current formula, assuming `intradaySales` is accumulated sold quantity (suspect 3).
- Rollup overwriting verified closing-count row: false positive; explicit skip (suspect 1).
- `/health` running repeated Mongo counts: false positive; `/health` itself is liveness-only (suspect 9).
- JOB_SECRET unset means unauthenticated job access: false positive; valid bearer token is still required (suspect 7).
- Password lock counter fails to reset when expiry is observed by that worker: false positive (suspect 8).
- Sequential discount/bundle taps compound without bounds: false positive; sequential repeat rejected and percentage capped. Concurrent race remains (suspect 5).
- Partner picker can select zero stock or an item with an active alert: false positive in inspected branch (suspect 6).
- Shadow account can log in and cause server 500: false positive; explicit 401 guard (suspect 20).
- Dart `StateError` is invalid: false positive; `flutter analyze` and `flutter test` succeed.
- Nightly batch overwrites shadow/adaptive forecast documents: false positive for inspected filters (`ML/batch_forecast.py:316`, `375-394`).
- APKs are committed: false positive; they are present on disk, but `git ls-files RestockIQ-debug.apk RestockIQ-latest.apk` returned no paths.

## 5. Not reviewed / limits

- **Mutation testing:** not performed. The requested eight mutations were not applied because the checkout began with pre-existing modifications and the request also limits edits to one report file. No mutation catch-rate claim is made. Use an isolated disposable checkout/worktree, mutate each behavior, run the named tests, and restore that isolated checkout; do not use `git checkout` on the user's checkout.
- **Backend tests:** with `PYTHONDONTWRITEBYTECODE=1`, `TESTING=1`, `ENVIRONMENT=local`, dummy `JWT_SECRET`, and both Mongo URIs set to `mongodb://127.0.0.1:1/read_only_audit`: `python -B -m pytest -q` output ended `91 passed, 4 skipped, 4 warnings in 62.97s`; `python -B -m unittest discover -s . -p 'test*.py' -q` output `Ran 78 tests in 54.650s` / `OK (skipped=4)`. Staging Atlas tests skipped; mock seeding used `mock_staging` (in-memory). Tests emit unclosed MongoClient warnings because `ML/batch_forecast.py:64` initializes on import.
- **Flutter checks:** `flutter analyze` output `No issues found! (ran in 22.1s)`; `flutter test --no-pub` output `00:19 +46: All tests passed!`. Test HTTP guards logged attempted requests to the configured app host but threw `BLOCKED` before any socket call; no production request was sent.
- **Database:** no database connection/write; staging tests skipped because Atlas on port 27017 was unreachable.
- **Secret history:** a broad `git log -G` search found historical commits with connection/config/password-pattern changes; values were not printed. Exhaustive secret scanning across all historical blobs was not completed. Do not treat absence of printed matches as proof of clean history. `.live_credentials.local` and `Backend/.env` exist in the workspace; their values were not read. `Backend/.env.example` has placeholders.
- **Repo hygiene:** `git ls-files` confirms three tracked `demo_fixture.json` copies and root `IEEEtran.cls`/`.bst`; APKs are present in the workspace inventory but were not listed by `git ls-files`. Full duplicate-content/hash and dead-code audit was not completed. Numerous untracked academic-review assets and scratch scripts were pre-existing and preserved.
- **ML leakage, exact NAME_MAP, groupby rolling boundary, all Flutter JSON key mismatches, all error/loading states, long-text overflow, every HTTP-500 path, all input bounds/NoSQL injection possibilities, comprehensive route helper-query ownership, and every docs claim:** not exhaustively proven. These are not represented as verified-safe.
- **Docker build, 512-MB peak RSS, cold start, concurrency races, actual deployment settings and nightly job against staging:** not run. Requirements show no pandas/numpy/sklearn in the API requirements (`Backend/requirements.txt`); ML batch has a separate workflow dependency set. Memory conclusion remains unverified empirically.
- **Tracked HEAD vs working tree:** audit began with listed local edits and tests ran against that worktree state; at final status the tracked changes were no longer present, with only this report directory untracked. I did not run reset/checkout commands. Cause is **COULD NOT VERIFY**; inspect user state before subsequent work.

## 6. Docs and claims checked against code

- **README.md:16 — false:** claims Firebase Auth; the mobile client calls FastAPI auth endpoints (`APP/lib/services/api_service.dart:151-216`) and the backend creates JWTs (`Backend/main.py:1392-1396`, `1576-1580`).
- **README.md:32-34, 84-86 — unsupported for current shipped path:** claims Prophet decomposition + pooled GBDT and about 22.75% WAPE; `render.yaml:29-32` selects `ENGINE=legacy` and `FORECAST_MODE=legacy`, and the audited engine source is candidate ML/TSB logic rather than a demonstrated live Prophet service. Accuracy figures were not reproduced in this audit.
- **README.md:40 — contradicted by code:** says the prior is category p90; `Backend/adaptive_forecast.py:110-126` prefers p50/median, then mean, p80, p90; category fallback is fixed values at `34-49`.
- **README.md:58 — arithmetic inconsistency:** displayed seasonal-naive waste 46,044 vs model 40,954 is 5,090 fewer; displayed stockouts 1,345 vs 979 is 366 fewer, but cited historical experimental provenance and resulting margin cannot be reproduced here. Mark performance conclusion unverified.
- **docs/qa/APP_BEHAVIOR_GUIDE.md:97-100 — unsupported/false:** describes secure storage of profile documents, local providers serving latest cached store data, offline indicator and auto-sync. `APP/lib/services/api_service.dart:265-271` stores token and profile metadata in SharedPreferences, while API calls remain network backed and provider sample fallback is fixture data (`APP/lib/repositories/app_repository.dart:196-206`), not a synchronized cache. No offline queue/sync implementation was established.
- **docs/ENGINEERING_NOTES.md claims:** the notes contain historical fix/acceptance assertions. They were not accepted as proof; only current code and the tests actually run were used. Full statement-by-statement crosswalk is COULD NOT VERIFY.
- **docs/qa/QA_LOG.md claims:** screenshots/manual acceptance claims cannot be independently validated from repository code. No physical-device run was performed; treat all un-reproduced observations as unverified.
- **Other README claims:** “ultra-fast read-layer/no on-the-fly inference” is contradicted when `FORECAST_MODE=adaptive`, where API endpoints call `refresh_item_forecast` and run `forecast_item` (`Backend/main.py:278-318`, `2538-2580`).

## 7. Fix plan (severity × demo impact ÷ effort)

### Batch 1 — security and data integrity

1. Remove the default demo password and rotate any account that could have used it (C-007).
2. Make discount/bundle “not applied” checks atomic (C-013); verify closing-count idempotency and simultaneous restock with a staging-only concurrency test.
3. Make required unique-index failures fatal in production startup (C-011).
4. Address victim lockout abuse and move lockout/rate state to shared persistence (C-012; suspect 24).
5. Add assistant-usage purge for shadow tenant and verify all TTL/purge filters (C-003).

### Batch 2 — forecasting and daily logic

1. Confirm target deployment forecast mode and prove forecast endpoint provenance before enabling adaptive mode (C-005).
2. In an isolated workspace, complete the eight requested forecast/security/data mutations and report each test’s failure result.
3. Verify concurrent intraday write behavior using mongomock and staging-only tests (C-014); retain the batch shadow/adaptive guards noted in Section 4.
4. Prove date cutoff, groupby-by-article rolling features, priors, NAME_MAP and legacy/French-data conditions from code and reproducible examples.

### Batch 3 — app and demo flow

1. Do not silently switch to local sample data if server demo start fails (C-001).
2. Require successful demo cleanup or clearly block live transition until cleanup is confirmed (C-004).
3. Replace generated chart values with a no-data state (C-008); verify session/cache clearing and all error states.
4. Fix currency-specific action text (C-015); test action double taps and long explanation/name rendering.
5. Confirm demo rate limit and test route header/workspace behavior (C-002).

### Batch 4 — docs and claims

1. Reconcile README, QA guide/log, engineering notes, deploy docs, and claims registers against actual code and fresh eval outputs.
2. Remove unproven accuracy/model/confidence/endpoint/test-count claims; explicitly label indicative forecasts and sample-only tour behavior.
3. Audit historical secrets without displaying values, rotate exposed credentials, and establish release provenance for the untracked APK artifacts.

