# RestockIQ Backend Service (`Backend/`)

The **RestockIQ Backend** is a high-performance, asynchronous REST API built with **FastAPI**, **Motor** (async MongoDB driver), and **Google Gemini GenAI** (`gemini-3.5-flash-lite`). It acts as the secure read/write layer, real-time demand forecasting engine, and business logic coordinator between MongoDB Atlas and the Flutter mobile client.

---

## 📂 Directory Structure

```
Backend/
├── main.py                        # FastAPI entrypoint, routes, lifecycle, auth & waste alerts
├── adaptive_forecast.py           # Pure-Python 5-candidate adaptive tournament engine
├── constants.py                   # System-wide operational constants & categories
├── demo_fixture.json              # Seed dataset for demo sandbox store
├── requirements.txt               # Pinned Python backend dependencies
├── Dockerfile                     # Multi-stage container for Render cloud deployment
├── .dockerignore                  # Docker build exclusions
├── .env.example                   # Environment variable template
├── openapi.json                   # OpenAPI 3.1 specification schema
├── ATLAS_SECURITY_GUIDE.md        # MongoDB Atlas network security and index guide
├── README.md                      # This backend architecture and API guide
├── services/                      # Application service layers
│   └── llm_service.py             # Gemini LLM integration with deterministic fallback
├── test_*.py                      # 13 Automated test suites (78 passing tests)
│   ├── test_adaptive_forecast.py  # Adaptive tournament & Bayesian shrinkage tests
│   ├── test_adaptive_integration.py # Zero-downtime fallback & integration tests
│   ├── test_demo_sandbox.py       # Shadow tenant isolation & sliding 4hr TTL tests
│   ├── test_p0_fixes.py           # Lockout, assistant quota, & input validation tests
│   ├── test_timezone_and_alerts.py # Store hours, overnight shifts, & waste pace tests
│   ├── test_tenant_isolation.py   # Multi-tenant cross-boundary isolation tests
│   ├── test_acceptance_lifecycle.py # EOD closing count & daily rollover idempotency
│   ├── test_final_hardening.py    # Rate limiting & proxy spoofing defenses
│   └── test_backend_unit.py       # CI master test suite
└── verify_*.py                    # Verification and benchmark scripts
    ├── verify_step1.py            # Sales ingestion smoke test
    ├── verify_step2.py            # Aggregation rollup smoke test
    ├── verify_step4.py            # Forecast recommendations smoke test
    ├── verify_step5.py            # Waste logging smoke test
    ├── verify_llm.py              # Gemini LLM briefing verification
    ├── verify_e2e.py              # End-to-end user journey simulation
    ├── measure_rss.py             # Process RSS memory & prohibited imports check
    └── check_mongo.py             # Atlas connection probe
```

---

## 🛠️ Core Components & Architecture

| Component | File | Responsibilities |
| :--- | :--- | :--- |
| **API Gateway & Routing** | [`main.py`](file:///e:/CAP/Backend/main.py) | Configures CORS, JWT bearer auth, multi-tenant isolation, inventory CRUD, closing count submissions, midday pace alerts, and demo sandbox lifecycle. |
| **Adaptive Forecasting** | [`adaptive_forecast.py`](file:///e:/CAP/Backend/adaptive_forecast.py) | Pure-Python rolling tournament evaluating 5 candidate demand models, Bayesian prior shrinkage, 5% churn margin guard, and Newsvendor safety stock. Zero heavy dependencies (no pandas/numpy in API process). |
| **GenAI Assistant** | [`services/llm_service.py`](file:///e:/CAP/Backend/services/llm_service.py) | Connects to `gemini-3.5-flash-lite`. Generates conversational daily morning restock briefings. Features deterministic rule-based zero-fail fallback when offline or quota-limited. |
| **Demo Sandbox** | [`main.py`](file:///e:/CAP/Backend/main.py#L4300) | Maps `X-Workspace: demo` requests to `shadow_{owner_id}` with a 4-hour sliding TTL index across all collections, allowing safe demonstrations without mutating live tenant data. |

---

## 🧪 Automated Testing

Run the full backend test suite from the virtual environment:

```bash
cd Backend
.\venv\Scripts\activate

# Run all 78 tests across all suites
python -B -m unittest discover -s . -p "test*.py"
```

All 78 tests run offline against `mongomock_motor` / `mongomock` with zero cloud dependencies and 100% security branch coverage.

---

## ⚙️ Environment Configuration

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `MONGODB_URI` | Yes | MongoDB Atlas connection string | `mongodb+srv://user:pass@cluster.mongodb.net/restockiq` |
| `JWT_SECRET` | Yes | Secret key for signing HS256 auth tokens | *(Random 32+ byte secret)* |
| `GEMINI_API_KEY` | Optional | Google Gemini API key for assistant features | `AIzaSy...` |
| `GEMINI_MODEL` | Optional | Model identifier (default: `gemini-3.5-flash-lite`) | `gemini-3.5-flash-lite` |
| `ALLOWED_ORIGINS`| Yes | Comma-separated CORS origins | `*` or `https://restockiq.com` |
| `FORECAST_MODE` | No | Forecasting engine (`legacy` or `adaptive`) | `legacy` |
| `JOB_SECRET` | No | Shared secret for `/health/details` & `/jobs/*` | *(Secret string)* |
