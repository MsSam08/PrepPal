# PrepPal ML API — Team Handoff Guide
**Version:** 3.0.0 | **Data Science Lead:** Euodia Sam

---

## Who Reads What

| Team Member | Role | Read This Section |
|---|---|---|
| Queen Kuje | Backend Lead | Integration Guide, Endpoints, Request/Response |
| Precious Nwabueze | DevOps Lead | Deployment, Environment Variables, Health Check |
| Christiana Kyebambo | Mobile App Lead | Endpoints, Request/Response examples |
| Belinda Mahachi | Product Lead | How it works, Success metrics |
| Everyone | All | Run Order (first-time setup) |

---

## How It Works (Non-Technical Summary)

The AI model was trained on 6 months of sales data across 3 business types (Restaurant, Cafe, Bakery) and 15 menu items. Given information about an item, the date, weather, and whether it's a holiday — it predicts how many customers will want that item. The API wraps this model so the backend and mobile app can get predictions through simple HTTP calls.

---

## First-Time Setup (Run Once)

```bash
# 1. Set your environment variable (see .env.example for your OS)
export PREPPAL_DATA_DIR=/path/to/your/data

# 2. Install dependencies
pip install -r requirements.txt

# 3. Validate source data
python data_validation.py

# 4. Generate features
python feature_engineering.py

# 5. Train the model (takes a few minutes)
python model_training_and_ensemble.py

# 6. Start the API
uvicorn api:app --host 0.0.0.0 --port 8000

# 7. Run smoke tests (in another terminal)
bash api_tests.sh

# 8. Run unit tests
python -m pytest tests.py -v
```

---

## Environment Variable (CRITICAL — Every Team Member)

**The single most important thing to get right.**

Every Python script reads your data folder from an environment variable called `PREPPAL_DATA_DIR`.

```bash
# Windows (Euodia):
set PREPPAL_DATA_DIR=C:\Users\euodi\Projects\PrepPal

# Mac/Linux (teammates):
export PREPPAL_DATA_DIR=/path/to/preppal

# Server (Precious — DevOps):
# Set in deployment config / docker-compose / CI environment
PREPPAL_DATA_DIR=/app/data
```

If this is not set, every script will immediately crash with a clear error message telling you what to do.

---

## API Endpoints (PRD Section 3.5 — All Required)

**Base URL:** `http://your-server:8000`
**Docs (interactive):** `http://your-server:8000/docs`

### GET /api/health
Health check. Precious uses this to verify the API is running before routing traffic.

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2025-12-01T10:30:00"
}
```

If `model_loaded` is `false`, the API is running but the model failed to load. Check `model_error` in the response.

---

### POST /api/predict
Tomorrow's demand for one item.

**Request:**
```json
{
  "item_name": "Jollof Rice",
  "business_type": "Restaurant",
  "date": "2025-12-01",
  "price": 50,
  "shelf_life_hours": 4,
  "weather": "Clear",
  "is_holiday": 0
}
```

**Response:**
```json
{
  "success": true,
  "fallback": false,
  "date": "2025-12-01",
  "predicted_demand": 42,
  "recommended_quantity": 44,
  "confidence": "High",
  "confidence_score": 0.85,
  "explanation": "Based on: weekend uplift, 7-day rolling avg (41)",
  "is_new_item": false
}
```

**Field notes:**
- `business_type`: must be exactly `"Restaurant"`, `"Cafe"`, or `"Bakery"`
- `weather`: `"Clear"` or `"Rainy"`
- `is_holiday`: `0` or `1`
- `is_new_item`: `true` means the item wasn't in training data — still works, features are estimated
- `fallback`: if `true`, the model was unavailable and this is the last cached forecast

---

### POST /api/predict-week
7-day forecast for one item.

**Request:**
```json
{
  "item_name": "Espresso",
  "business_type": "Cafe",
  "price": 25,
  "shelf_life_hours": 0.5,
  "starting_date": "2025-12-01",
  "weather_forecast": ["Clear","Clear","Rainy","Clear","Clear","Clear","Rainy"],
  "holiday_flags": [0,0,0,0,0,0,0]
}
```

**Response:**
```json
{
  "success": true,
  "fallback": false,
  "forecast": [
    {
      "date": "2025-12-01",
      "day_name": "Monday",
      "day_number": 1,
      "predicted_demand": 48,
      "recommended_quantity": 50,
      "confidence": "High",
      "confidence_score": 0.85,
      "weather": "Clear",
      "is_holiday": "No",
      "is_new_item": false,
      "explanation": "Based on: Monday peak, 7-day rolling avg (46)"
    }
  ]
}
```

Confidence degrades from 0.85 (day 1) to 0.55 (day 7). This is intentional — further predictions are less certain.

---

### POST /api/risk-alert
Classify overproduction risk. Dashboard uses this for color coding.

**Request:**
```json
{
  "predicted_demand": 42,
  "planned_quantity": 60
}
```

**Response:**
```json
{
  "success": true,
  "risk_level": "HIGH",
  "waste_percentage": 30.0,
  "expected_waste": 18,
  "message": "High waste risk — strongly recommend reducing quantity",
  "color": "red"
}
```

| `risk_level` | `color` | When |
|---|---|---|
| `HIGH` | `red` | Planned > 15% above predicted |
| `MEDIUM` | `yellow` | Planned 5–15% above predicted |
| `LOW` | `green` | Planned within 5% of predicted |

---

### POST /api/recommend
Smart quantity recommendation.

**Request:**
```json
{
  "predicted_demand": 40,
  "current_plan": 55
}
```

**Response:**
```json
{
  "success": true,
  "recommended_quantity": 42,
  "action": "REDUCE by 13 units",
  "reason": "to avoid waste",
  "explanation": "Predicted demand: 40 units, with 5% safety buffer → 42 units"
}
```

---

### POST /api/accuracy
Model performance metrics. PRD Section 3.5 requirement.

**Request:**
```json
{
  "n_recent": 7
}
```

Optional filters: `"item_name"`, `"business_type"`

**Response:**
```json
{
  "success": true,
  "period": "Last 7 evaluations",
  "avg_mape": 8.12,
  "avg_mae": 3.21,
  "avg_r2": 0.891,
  "degraded": false,
  "alert_message": null,
  "target_mape": 20.0,
  "meets_target": true,
  "history": [...]
}
```

If `degraded` is `true` (MAPE > 25%), the backend should surface an alert. Trigger `/api/retrain`.

---

### POST /api/retrain
Trigger model retraining with new sales data. Runs in the background.

**Request:**
```json
{
  "new_data_path": "/app/data/new_sales_january.csv"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Retraining started in background. Check /api/health and /api/accuracy for updates.",
  "data_path": "/app/data/new_sales_january.csv"
}
```

The new CSV must be on the same server as the API (not a URL). The file is validated, features are engineered, and the model is retrained. The new model is only deployed if it outperforms the current one.

---

## Error Handling

**Validation errors (422):** Bad request format. Example: wrong business type.
```json
{
  "detail": [{"loc": ["body","business_type"], "msg": "Input should be 'Restaurant', 'Cafe' or 'Bakery'"}]
}
```

**Server errors (500):** Something went wrong in the model. Includes traceback for debugging.
```json
{
  "success": false,
  "error": "description of what went wrong",
  "traceback": "..."
}
```

**Fallback (200 with `fallback: true`):** AI temporarily unavailable, returning last cached forecast.

---

## Files in This Package

| File | Purpose | Run by |
|---|---|---|
| `eda_analysis.py` | Exploratory data analysis | Euodia (once) |
| `data_validation.py` | Validate source CSVs | Euodia (once) |
| `feature_engineering.py` | Build features + encoders | Euodia (once, or after data update) |
| `model_training_and_ensemble.py` | Train final model | Euodia (once, or after feature changes) |
| `forecasting.py` | 7-day forecast engine | Imported by api.py |
| `api.py` | FastAPI — all endpoints | Precious (deploy), Queen (integrate) |
| `monitoring.py` | Track model accuracy | Backend calls after daily sales |
| `validation.py` | Validate upload CSVs | Called by retrain.py |
| `retrain.py` | Retrain model | Called by /api/retrain |
| `tests.py` | Unit tests | Everyone — run before deploying |
| `hyperparameter_tuning.py` | Optional model optimization | Euodia (optional, post-MVP) |
| `requirements.txt` | Python dependencies | Everyone |
| `.env.example` | Environment setup guide | Everyone |
| `api_tests.sh` | API smoke tests | Queen, Precious |

---

## Data Files Required in PREPPAL_DATA_DIR

| File | Created By |
|---|---|
| `restaurant_sales_dataset.csv` | Euodia (already done) |
| `cafe_bakery_sales_dataset.csv` | Euodia (already done) |
| `processed_data_with_features_v3.csv` | `feature_engineering.py` |
| `category_label_encoder.pkl` | `feature_engineering.py` |
| `business_label_encoder.pkl` | `feature_engineering.py` |
| `final_model_v3.pkl` | `model_training_and_ensemble.py` |
| `model_metrics.json` | `monitoring.py` (auto-created) |

---

## Deployment Notes (Precious — DevOps)

```bash
# Docker environment variable
environment:
  - PREPPAL_DATA_DIR=/app/data

# Start command
uvicorn api:app --host 0.0.0.0 --port 8000

# Health check endpoint for load balancer
GET /api/health

# The API is stateless except for model files in PREPPAL_DATA_DIR.
# Mount the data directory as a persistent volume.
```

---

## Backend Integration Notes (Queen — Backend)

- Call `/api/predict` to get tomorrow's forecast per item
- Call `/api/predict-week` when user requests the weekly view
- Call `/api/risk-alert` to determine dashboard color coding
- Call `/api/recommend` when user wants a quantity suggestion
- Call `/api/accuracy` to display model performance to admin users
- Call `/api/retrain` when new validated sales data is available
- Always check `success` field before using the response
- Check `fallback` field — if `true`, show a "using cached data" notice to the user
- Check `/api/health` on startup and surface status to admin dashboard

---

## PRD Compliance Summary

| PRD Requirement | Status | Endpoint/File |
|---|---|---|
| Tomorrow's demand forecast | ✅ | POST /api/predict |
| 7-day forecast | ✅ | POST /api/predict-week |
| Confidence scores | ✅ | Both predict endpoints |
| Prediction per item | ✅ | All endpoints |
| Smart recommendations | ✅ | POST /api/recommend |
| Explanation / explainability | ✅ | `explanation` field in responses |
| Overproduction risk detection | ✅ | POST /api/risk-alert |
| Color coding (Red/Yellow/Green) | ✅ | `color` field in risk-alert |
| Forecast accuracy monitoring | ✅ | POST /api/accuracy |
| Model retraining | ✅ | POST /api/retrain |
| AI fallback when unavailable | ✅ | `fallback` field + cached response |
| Data validation | ✅ | validation.py + retrain.py |
| Health check | ✅ | GET /api/health |
| Predictions within 10 seconds | ✅ | Typical response < 1 second |
| Bias/drift detection | ✅ | monitoring.py (alerts when MAPE > 25%) |