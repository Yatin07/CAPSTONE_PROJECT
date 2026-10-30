# RestockIQ Physical Device QA - Defects Found

This document records all functional, UI, validation, and schema defects discovered during the end-to-end QA execution on the physical Xiaomi Redmi Note 10 Pro over USB.

---

### DEFECT-001: Mid-Day Pace Submission Fails with HTTP 422 Unprocessable Entity

- **Severity**: High (Core routine broken in production UI)
- **Status**: Open (Strict read-only QA run; source not modified)
- **Component**: Mobile Flutter Client -> Backend API Integration
- **File**: `APP/lib/providers/stock_check_provider.dart:272`
- **Reproduction Steps**:
  1. Log into a store with active items (e.g. Croissant, Coffee Beans).
  2. Navigate to `Check-In` -> `Mid-Day Pace` tab.
  3. Enter remaining unit counts (e.g., Croissant = 10).
  4. Tap `Calculate Mid-Day Pace`.
  5. UI does not update or show pace calculation; logcat reports HTTP 422.
- **Evidence / Logcat Excerpt**:
  ```text
  10-30 16:59:36.238 10384 10384 I flutter : [Midday] Error: Exception: [
    {type: missing, loc: [body, counts, 0, remaining], msg: Field required, input: {item_id: 6ae4787208e6725befc70625, remaining_count: 10}},
    {type: missing, loc: [body, counts, 1, remaining], msg: Field required, input: {item_id: 6ae4799d08e6725befc70627, remaining_count: 20}},
    {type: missing, loc: [body, counts, 2, remaining], msg: Field required, input: {item_id: 6ae479d408e6725befc70629, remaining_count: 10}}
  ]
  ```
- **Root Cause**:
  In `APP/lib/providers/stock_check_provider.dart` line 272:
  ```dart
  final countsPayload = remainingCounts.entries.map((entry) {
    return {
      'item_id': entry.key,
      'remaining_count': entry.value, // <-- Bug: backend schema expects 'remaining'
    };
  }).toList();
  ```
  The backend FastAPI Pydantic schema `MiddayCountItem` expects the field name `remaining`, but the Flutter provider sends `remaining_count`.
- **Recommended Fix**:
  Change `'remaining_count': entry.value` to `'remaining': entry.value` in `stock_check_provider.dart:272`.
- **Screenshots**: `43_midday_check.png`, `43c_midday_result.png`.

---

### DEFECT-002: Briefing Fetch Timeout (15s) Under Heavy Network/Cold-Start Latency

- **Severity**: Medium
- **Status**: Open
- **Component**: Mobile API Client (`ApiService.fetchTodayBriefing`)
- **Reproduction Steps**:
  1. Open app during initial login or force-refresh dashboard when cloud LLM generation is cold.
  2. Observe Flutter logcat.
- **Evidence / Logcat Excerpt**:
  ```text
  10-30 16:39:01.450 10384 10384 I flutter : [API] Attempt 1/3 error: TimeoutException after 0:00:15.000000: Future not completed
  10-30 16:39:18.460 10384 10384 I flutter : [API] Attempt 2/3 error: TimeoutException after 0:00:15.000000: Future not completed
  10-30 16:39:37.463 10384 10384 I flutter : [API] Attempt 3/3 error: TimeoutException after 0:00:15.000000: Future not completed
  10-30 16:39:37.463 10384 10384 I flutter : [API] fetchTodayBriefing error: TimeoutException after 0:00:15.000000: Future not completed
  ```
- **Root Cause**:
  `fetchTodayBriefing` has a strict 15.0s client timeout. When Render cloud is waking up or Gemini API takes >15s to synthesize the executive briefing, the client aborts and retries 3 times before falling back to cached briefing.
- **Recommended Fix**:
  Increase timeout for AI synthesis endpoints (e.g., briefing and conversational QA) to 25s, or show a progress indicator specifically notifying the user that Gemini is synthesizing fresh store insights.
- **Screenshots**: `44_session_persisted.png`.

---

### DEFECT-003: Registration Rejects RFC 2606 Test Domains (`.test`, `.example`) with HTTP 422

- **Severity**: Low
- **Status**: Known limitation / validation design
- **Component**: Backend Auth Service (`Backend/app/routers/auth.py`)
- **Reproduction Steps**:
  1. Attempt to register an account with email `user@restockiq.test`.
  2. Backend returns HTTP 422: `The part after the @-sign is a special-use or reserved name that cannot be used with email.`
- **Root Cause**:
  FastAPI route uses Pydantic's `EmailStr` with `email-validator`, which performs strict DNS and special-use TLD rejection.
- **Workaround / Fix**:
  Use valid public domain suffixes (e.g. `user@restockiq.com`) for all staging, automated testing, and QA accounts.
- **Screenshots**: `08_register_fill.png`.

---

### DEFECT-004: Catalog Item Lowercase Preservation on Display

- **Severity**: Low (Cosmetic)
- **Status**: Open
- **Component**: Mobile UI Card Rendering
- **Reproduction Steps**:
  1. Add an item with all lowercase name (e.g. `whole milk`).
  2. View inventory list and yesterday review.
  3. The card displays `whole milk` rather than Title Case `Whole Milk`.
- **Root Cause**:
  Card widget renders `item.name` directly without `.toTitleCase()` in some list views, while other screens apply `.toTitleCase()`.
- **Recommended Fix**:
  Standardize on `item.name.toTitleCase()` across all card components.
- **Screenshots**: `35_inventory_list_scrolled.png`, `42_yesterday_review.png`.

