# RestockIQ: REST API Endpoint Specifications

**Base URL (Production Render):** `https://restockiq-backend.onrender.com/api/v1`  
**Authentication Scheme:** HTTP Bearer Token (`Authorization: Bearer <jwt_access_token>`)  
**Data Exchange Format:** `application/json` (UTF-8)

---

## 1. System & Authentication Endpoints

| Method | Endpoint Path | Auth Required | Request Body | Success Response | Description & Rate Limits |
|---|---|:---:|---|---|---|
| `GET` | `/health` | No | None | `200 OK`<br>`{"status": "ok", "database": {"status": "connected"}, "llm": {...}}` | Cloud service health probe and Atlas ping check. |
| `POST` | `/auth/register` | No | `{"name": "...", "email": "...", "password": "...", "role": "owner"}` | `201 Created`<br>`{"access_token": "...", "user_id": "...", "name": "...", "role": "..."}` | Registers a new retail tenant in MongoDB Atlas. |
| `POST` | `/auth/login` | No | `{"email": "...", "password": "..."}` | `200 OK`<br>`{"access_token": "...", "user_id": "...", "name": "...", "role": "..."}` | Authenticates credentials; returns HS256 JWT access token. Limited to 10 req/min per IP. |

---

## 2. Inventory & Catalog Endpoints

| Method | Endpoint Path | Auth Required | Request Body | Success Response | Description & Constraints |
|---|---|:---:|---|---|---|
| `GET` | `/items` | **Yes** | None | `200 OK`<br>`{"items": [{"id": "...", "name": "...", "currentStock": 30, ...}]}` | Retrieves all inventory items owned by the authenticated tenant. |
| `POST` | `/items` | **Yes** | `{"name": "...", "category": "Bakery", "unit": "Units", "currentStock": 15, "isPerishable": true, "price": 2.80}` | `201 Created`<br>`{"status": "created", "item_id": "...", "message": "..."}` | Adds a new inventory SKU. Relational link set to `owner_id`. |
| `PUT` | `/items/{item_id}` | **Yes** | `{"currentStock": 20, "price": 2.50}` | `200 OK`<br>`{"status": "updated", "item": {...}}` | Updates item attributes. Enforces tenant ownership isolation (returns 404 on cross-tenant ID). |
| `DELETE` | `/items/{item_id}` | **Yes** | None | `200 OK`<br>`{"status": "deleted"}` | Deletes an inventory SKU. |
| `POST` | `/items/{item_id}/restock` | **Yes** | `{"quantity": 15}` | `200 OK`<br>`{"status": "restocked", "newStock": 35}` | Increments stock on hand after baking or shipment delivery. |

---

## 3. Demand Forecasting Endpoints

| Method | Endpoint Path | Auth Required | Request Body | Success Response | Description & Constraints |
|---|---|:---:|---|---|---|
| `GET` | `/forecasts/today` | **Yes** | None | `200 OK`<br>`{"summary": "...", "total_items": 5, "action_required_count": 2, "items": [...]}` | Primary dashboard payload. Returns point estimates for today. **Invariant: `confidence_interval = null`.** |
| `GET` | `/forecasts/{item_id}` | **Yes** | None | `200 OK`<br>`{"id": "...", "name": "...", "predictedDemand": 39, "safetyStock": 15, "historical_chart": [...], "forecast_chart": [...]}` | Returns 7-day historical sales chart series and 7-day forward predicted series for time-series visualization. |

---

## 4. Intraday POS Sales & Waste Mitigation Endpoints

| Method | Endpoint Path | Auth Required | Request Body | Success Response | Description & Constraints |
|---|---|:---:|---|---|---|
| `POST` | `/sales/intraday` | **Yes** | `{"item_id": "...", "quantity": 1}` | `201 Created`<br>`{"status": "recorded", "item_id": "...", "quantity": 1}` | Logs real-time register checkout events into `intraday_sales`. |
| `GET` | `/waste-alerts` | **Yes** | None | `200 OK`<br>`{"alerts": [{"id": "...", "itemName": "...", "salesPaceRatio": 0.40, ...}], "total_alerts": 1}` | Evaluates hourly sales velocity against daily target; returns active markdown alerts for perishable stock. |
| `POST` | `/waste-alerts/{id}/apply-discount` | **Yes** | None | `200 OK`<br>`{"status": "success", "message": "Applied discount...", "newPrice": 2.24}` | Applies dynamic markdown (20%) directly to POS item price. |
| `POST` | `/waste-alerts/{id}/dismiss` | **Yes** | None | `200 OK`<br>`{"status": "dismissed"}` | Dismisses the waste warning card for the current trading shift. |

---

## 5. AI Executive Briefing & Assistant Endpoints

| Method | Endpoint Path | Auth Required | Request Body | Success Response | Description & Constraints |
|---|---|:---:|---|---|---|
| `GET` | `/briefing/today` | **Yes** | None | `200 OK`<br>`{"status": "success", "briefing": "**Executive Summary** Today's operational priority..."}` | Calls Google Gemini (`gemini-3-flash-preview`) to synthesize natural language daily briefing. Strictly grounded in verified Atlas values. |
| `POST` | `/assistant/chat` | **Yes** | `{"query": "What is the discount on baguette?"}` | `200 OK`<br>`{"status": "success", "reply": "...", "provider": "google-gemini", "model": "gemini-3-flash-preview"}` | RAG-grounded natural language Q&A for managers. Limited to 20 req/min per IP. Zero invented arithmetic. |
