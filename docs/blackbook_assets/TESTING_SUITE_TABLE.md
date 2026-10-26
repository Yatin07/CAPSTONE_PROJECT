# RestockIQ: Software Testing & Verification Suite Table

**Total Automated Tests:** 55 Tests across all tiers  
**Pass Rate:** **100% (55 / 55 Passed)**  
**Target Environments:** Physical Mobile Device (Xiaomi Redmi Note 10 Pro / Android 13 / ARM64), Android Emulator, FastAPI Localhost, Render Cloud (`https://restockiq-backend.onrender.com`)

---

## 1. Testing Tier Summary

| Testing Level | Scope / Target File | Test Count | Pass Rate | Execution Command | Key Invariants Verified |
|---|---|:---:|:---:|---|---|
| **Tier 1: Front-End Unit Tests** | `APP/test/unit_test.dart` | 21 | **100% (21/21)** | `flutter test test/unit_test.dart` | Master 5-item catalog consistency, restock formula `max(0, pred + safety - current)`, pricing, provider CRUD operations, grounded assistant fallback. |
| **Tier 2: Widget & UI Tests** | `APP/test/widget_test.dart` | 15 | **100% (15/15)** | `flutter test test/widget_test.dart` | Screen rendering, Material 3 theming, login form validation, stepper interaction, waste alert card rendering. |
| **Tier 3: Front-End Integration Tests** | `APP/test/integration_test.dart` | 8 | **100% (8/8)** | `flutter test test/integration_test.dart` | End-to-end mobile user journey: login &rarr; dashboard &rarr; item detail forecast inspection &rarr; inventory check-in &rarr; waste alert dismissal. |
| **Tier 4: Back-End Unit & Contract Tests** | `Backend/test_backend_unit.py` | 7 | **100% (7/7)** | `python test_backend_unit.py` | Boundary value analysis on query inputs (0, 1, 500, 501 chars), decision table evaluation (10/10 operational rules), rate limiter sliding window. |
| **Tier 5: Multi-Tenant Security Tests** | `Backend/test_tenant_isolation.py` | 4 | **100% (4/4)** | `python test_tenant_isolation.py` | Cross-tenant data isolation: ensures tenant A cannot read, update, restock, or delete tenant B's items or forecasts (returns 404/empty). |

---

## 2. Detailed Front-End Unit Tests (`APP/test/unit_test.dart`)

| Test ID | Test Description | Input Conditions | Expected Output | Status |
|:---:|---|---|---|:---:|
| `UT-01` | Inventory catalog initializes with master 5 items | App cold-boot | Catalog contains exactly 5 items (Croissants, Baguettes, Pain au Chocolat, Milk, Espresso) | **PASS** |
| `UT-02` | Perishable flags accurately defined | Item model instantiation | Baguette, Croissant, Pain au Chocolat, Milk = `isPerishable: true`; Espresso = `false` | **PASS** |
| `UT-03` | Item pricing and baseline stocks adhere to business rules | Catalog initialization | Baguette: $2.80 (8 units), Croissant: $3.50 (30 units), Milk: $4.50 (4 GAL) | **PASS** |
| `UT-04` | Restock formula clamps negative order values to 0 | Predicted: 39, Safety: 15, Stock: 60 | Formula: $\max(0, 39 + 15 - 60) = 0$ (no negative orders) | **PASS** |
| `UT-05` | Restock formula computes accurate replenishment orders | Predicted: 39, Safety: 15, Stock: 8 | Formula: $\max(0, 39 + 15 - 8) = 46$ units | **PASS** |
| `UT-06` | InventoryProvider CRUD preserves local state integrity | Add item "Sourdough", delete item | Item count increments to 6, decrements back to 5 | **PASS** |
| `UT-07` | Waste alerts catalog matches master inventory | Load waste alerts | Alerts contain only Traditional Baguette and Whole Milk | **PASS** |
| `UT-08` | Traditional Baguette triggers 20% discount action | `applyPrimaryAction('2')` | Discount price: $2.24; returns confirmation text | **PASS** |
| `UT-09` | Dismiss and reset lifecycle behaves correctly | `dismissAlert('2')` | Alert card hidden from active view; `isDismissed: true` | **PASS** |
| `UT-10` | Stock check catalog matches 5 master inventory SKUs | Open stock check screen | Exactly 5 items rendered with matching current stock | **PASS** |
| `UT-11` | Perishables lock manual edits while non-perishables permit override | Edit inventory stepper | Milk locked to daily reset; Espresso permits manual text entry | **PASS** |
| `UT-12` | Confirming stock updates `isConfirmed` state | Tap confirm stock | State transitions to confirmed; timestamp saved | **PASS** |
| `UT-13` | Default base URL targets production Render cloud | Inspect `ApiService.defaultBaseUrl` | Returns `https://restockiq-backend.onrender.com/api/v1` | **PASS** |
| `UT-14` | Walkthrough login activates session without blocking | Login probe timeout | Session establishes `< 1` second; `isAuthenticated = true` | **PASS** |
| `UT-15` | AI Assistant returns grounded answer for Baguette queries | Query: "What is the discount on baguette?" | Contextual answer referencing 40% pace, 8 units, 20% markdown | **PASS** |
| `UT-16` | AI Assistant returns grounded answer for Milk queries | Query: "How much milk is left?" | Contextual answer referencing 4 GAL, safety stock 19 GAL | **PASS** |
| `UT-17` | AI Assistant returns grounded answer for Croissant queries | Query: "Tell me about croissants" | Contextual answer referencing normal pace (80 predicted) | **PASS** |
| `UT-18` | AI Assistant returns grounded answer for Espresso queries | Query: "Espresso beans status" | Contextual answer referencing 20 LBS non-perishable stock | **PASS** |
| `UT-19` | AI Assistant returns active alerts overview | Query: "What alerts are active?" | Returns summary of Baguette and Milk warnings | **PASS** |
| `UT-20` | AI Assistant never returns null or "Could not reach assistant" | Offline / timeout fallback | Returns grounded deterministic operational guidance | **PASS** |
| `UT-21` | Invariant check: all forecast items lack confidence intervals | Inspect `/forecasts/today` | `confidence_interval == null` for 100% of items | **PASS** |

---

## 3. Back-End Security & API Integrity Tests (`Backend/test_backend_unit.py`)

| Test ID | Test Category | Target / Method | Evaluation Criteria | Result |
|:---:|---|---|---|:---:|
| `BT-01` | **EP & BVA** | Input validation on query length | Boundaries tested at 0, 1, 500, 501 characters. 0 and 501 rejected (HTTP 422); 1 and 500 accepted. | **PASS** |
| `BT-02` | **Decision Table** | `evaluate_waste_alert_tier()` | 10/10 operational rules validated across perishable flags, stock levels, and sales pace thresholds. | **PASS** |
| `BT-03` | **LLM Zero-Math Invariant** | Gemini Briefing Generation | 100% of numbers in output text trace directly to input database fields; zero invented arithmetic. | **PASS** |
| `BT-04` | **Multi-Tenant Isolation** | Item CRUD & Forecasts | Requests from User A targeting User B's resources return HTTP 404 (Hidden); zero data leakage. | **PASS** |
| `BT-05` | **Sliding-Window Rate Limiter** | `login_limiter` (10 req/min) | 10 consecutive requests accepted; 11th request receives HTTP 429 Too Many Requests with `Retry-After`. | **PASS** |
| `BT-06` | **Proxy Header Protection** | Spoofed `X-Forwarded-For` | Right-most reverse proxy IP is parsed; injected client IPs share the same counter and cannot bypass limits. | **PASS** |
| `BT-07` | **State Transition Audit** | Waste Alert Lifecycle | Validated all 7 valid state transitions ($S_0 \to S_1 \to S_2 \to S_3 \to S_4 \to S_5$) in item lifecycle. | **PASS** |
