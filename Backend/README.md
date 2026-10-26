# RestockIQ Backend Service (`Backend/`)

The **RestockIQ Backend** is a high-performance, asynchronous REST API built with **FastAPI**, **Motor** (async MongoDB driver), and **Gemini 2.5 Flash LLM**. It acts as the secure read-layer and business logic coordinator between MongoDB Atlas and the Flutter mobile app.

---

## Directory Overview

```
Backend/
├── README.md                      # This index and API architecture documentation
├── main.py                        # FastAPI application entrypoint and route handlers
├── requirements.txt               # Pinned Python backend dependencies
├── Dockerfile                     # Container definition for Render cloud deployment
├── .dockerignore                  # Docker build exclude rules
├── .env.example                   # Environment variable template
├── ATLAS_SECURITY_GUIDE.md        # MongoDB Atlas network security and IP whitelist guide
├── learning_notes.md              # Engineering diary covering multi-tenancy, JWT, and rate limiting
├── services/                      # Application service layers
│   └── llm_service.py             # Gemini LLM integration for daily briefings and chat assistant
├── test_backend_unit.py           # Offline unit & security test suite (executed in CI)
├── test_rate_limiter.py           # Multi-IP rate limiter test harness (slowapi)
├── test_tenant_isolation.py       # Multi-tenant data segregation test harness
├── test_mongo.py                  # Atlas connection verification script
└── verify_*.py                    # Operational smoke test scripts (Steps 1–5, LLM, E2E)
    ├── verify_step1.py            # Verifies raw sales ingestion endpoint
    ├── verify_step2.py            # Verifies daily sales aggregation rollup
    ├── verify_step4.py            # Verifies forecast recommendations fetch
    ├── verify_step5.py            # Verifies end-of-day waste and inventory logging
    ├── verify_llm.py              # Verifies Gemini LLM briefing & chat generation
    └── verify_e2e.py              # Simulates full end-to-end user journey
```

---

## Component Catalog & Responsibilities

| File / Component | Purpose & Description | Context / Lifecycle |
| :--- | :--- | :--- |
| **[`main.py`](file:///e:/CAP/Backend/main.py)** | Core FastAPI application. Configures CORS, JWT bearer authentication, multi-tenant isolation filters (`tenant_id`), rate limiting (`slowapi`), and API v1 endpoints (`/api/v1/auth`, `/api/v1/inventory`, `/api/v1/forecast`, `/api/v1/assistant`). | Runs locally via Uvicorn or in Docker container on Render. |
| **[`services/llm_service.py`](file:///e:/CAP/Backend/services/llm_service.py)** | Interfaces with Google Gemini 2.5 Flash via `google-genai`. Generates non-technical morning restock briefings and answers conversational questions about inventory without performing arithmetic calculations (anti-hallucination design). | Invoked by `/api/v1/assistant/briefing` and `/api/v1/assistant/chat`. |
| **[`test_backend_unit.py`](file:///e:/CAP/Backend/test_backend_unit.py)** | Unit test suite verifying Pydantic request constraints (empty query and length bounds), client IP rate limiter isolation, and tenant segregation. | Automated via [`.github/workflows/ci.yml`](file:///e:/CAP/.github/workflows/ci.yml). |
| **[`test_rate_limiter.py`](file:///e:/CAP/Backend/test_rate_limiter.py)** | Validates that client rate limiting tracks distinct IP addresses independently behind proxy headers (`X-Forwarded-For`). | Imported by `test_backend_unit.py`. |
| **[`test_tenant_isolation.py`](file:///e:/CAP/Backend/test_tenant_isolation.py)** | Validates that queries for tenant A strictly never leak documents belonging to tenant B. | Imported by `test_backend_unit.py`. |
| **[`verify_*.py`](file:///e:/CAP/Backend/)** | Operational verification scripts simulating HTTP API requests against a running backend instance to validate database transitions step-by-step. | Used during staging and smoke verification. |
| **[`Dockerfile`](file:///e:/CAP/Backend/Dockerfile)** | Multi-stage Docker build utilizing `python:3.10-slim`, installing dependencies, and running Uvicorn on port 8000. | Deployed automatically by Render via [`render.yaml`](file:///e:/CAP/render.yaml). |

---

## Environment Variables

| Variable | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `MONGODB_URI` | Yes | MongoDB Atlas connection string | `mongodb+srv://<user>:<password>@cluster.mongodb.net/restockiq` |
| `JWT_SECRET` | Yes | Secret key for signing HS256 auth tokens | *(Cryptographically random 32+ bytes)* |
| `GEMINI_API_KEY` | Optional | Google Gemini API key for assistant features | *(API key from Google AI Studio)* |
| `GEMINI_MODEL` | Optional | Model identifier (defaults to `gemini-2.5-flash`) | `gemini-2.5-flash` |
| `ALLOWED_ORIGINS`| Yes | Comma-separated list of allowed CORS domains | `https://restockiq.com,http://localhost:3000` |
| `ALLOW_DEMO_SEED`| No | Enables demo database seeding endpoint | `false` |
