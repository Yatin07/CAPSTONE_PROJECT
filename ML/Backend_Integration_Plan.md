# Machine Learning -> Backend Integration Plan

This document outlines the requirements and action plan for integrating our standalone Prophet Machine Learning models into a production-ready **FastAPI** backend, which will serve the Flutter frontend.

---

## 📂 1. ML Model Paths
We have successfully developed two baseline models using Facebook Prophet. These scripts currently live here:
*   **Single-Item Model (Bakery):** `e:\CAP\ML\models\bakery_model.py`
*   **Multi-Store/Multi-Item Loop (Rossmann):** `e:\CAP\ML\models\rossmann_model.py`

*Note: Currently, these are standalone scripts that read from CSVs. They must be refactored into callable functions.*

---

## 🎯 2. Backend Needs & Requirements
To bridge the gap between these ML scripts and the Flutter app, the Backend Team must fulfill the following technical requirements:

1.  **Framework:** Python FastAPI. (Chosen because it runs natively with our Python Prophet models).
2.  **Database SDK:** `firebase-admin` (Python). FastAPI must read historical sales data from Firestore (not CSVs) and write the forecasted numbers back to Firestore.
3.  **Deployment:** (Future) The FastAPI app will need to be hosted on a service like Google Cloud Run or Render.

---

## 🚀 3. Step-by-Step Action Plan (What to do now)

The backend team should follow this exact sequence to ensure the frontend team is never blocked.

### Phase 1: Unblock the Frontend (MOCK DATA)
*   **Task:** Setup the FastAPI shell and create a `GET /api/forecast/{item_id}` endpoint.
*   **Action:** Do **NOT** run the Prophet models yet. Just return a hardcoded JSON string (e.g., `{"item": "Croissant", "forecasted_demand": 15}`).
*   **Why:** The frontend needs the API contract immediately so they can build the UI.

### Phase 2: Refactor the ML Scripts
*   **Task:** Convert the logic inside `bakery_model.py` and `rossmann_model.py` into reusable functions.
*   **Action:** 
    *   Instead of `pd.read_csv`, the function must accept a Pandas DataFrame passed from Firestore.
    *   Example signature: `def generate_forecast(historical_data: pd.DataFrame, days_ahead: int = 1) -> float:`

### Phase 3: Connect FastAPI to Prophet (REAL DATA)
*   **Task:** Update the `/forecast` endpoint to run the real ML model.
*   **Action:** When the endpoint is hit, FastAPI should:
    1. Fetch the last 30+ days of sales for that item from Firestore.
    2. Convert it into a Pandas DataFrame (`ds`, `y`).
    3. Pass it to the refactored Prophet function.
    4. Return the predicted `yhat` to the Flutter app.

### Phase 4: The LLM "Brain" (Postponed for later)
*   **Task:** Generate plain-text advice.
*   **Action:** Once Prophet is working, integrate the OpenAI or Gemini API. Feed the Prophet forecast and historical context into the LLM and ask it to return a 2-sentence summary (e.g., "Demand is up today. Restock 15 items.").
