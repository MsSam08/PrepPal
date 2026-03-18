# PrepPal: AI Food Waste Management System

> **Reducing food waste for SME food businesses by up to 85% through AI-powered demand forecasting.**

**Author:** Euodia Sam - Data Science Lead  
**Sprint Duration:** 2 weeks (February 2026)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Team & Roles](#team--roles)
3. [Technical Architecture](#technical-architecture)
4. [Quick Start](#quick-start)
5. [Implementation Journey](#implementation-journey)
6. [Model Performance](#model-performance)
7. [API Documentation](#api-documentation)
8. [Deployment Guide](#deployment-guide)
9. [Testing & Validation](#testing--validation)
10. [Business Impact](#business-impact)
11. [Troubleshooting](#troubleshooting)
12. [Project Structure](#project-structure)
13. [Contributing](#contributing)

---

## Project Overview

### The Problem

Small and medium food businesses; restaurants, cafés, and bakeries rely on guesswork when planning daily production. This leads to:

- **6–14% food waste** from consistent overproduction
- **Lost revenue** from stockouts on high-demand days
- **No affordable forecasting tools** designed for SME-scale operations

### The Solution

PrepPal is an AI-powered demand forecasting system that gives food businesses the intelligence of enterprise-grade tools at SME-friendly scale. It:

- Predicts tomorrow's demand per menu item
- Generates 7-day forecasts with calibrated confidence scores
- Recommends optimal production quantities with safety buffers
- Issues overproduction risk alerts (🔴 High / 🟡 Medium / 🟢 Low)
- Generalises to new menu items without retraining

### Key Result

**Model MAPE: 8.32%** - 58% better than the 20% PRD target.

Predictions are accurate to within ±4 units on average, enabling **85% waste reduction** in pilot testing.

---

## Team & Roles

The Data Science team owned the full ML pipeline end-to-end from exploratory data analysis through to the production API. Other team members own complementary parts of the product.

| Role | Name | Responsibility |
|------|------|----------------|
| **Data Science Lead** | Euodia Sam | ML pipeline, model training, API development, deployment |
| Backend Lead | Queen Kuje & Precious Nwabueze | API integration, database, business logic |
| Mobile App Lead | Christiana Kyebambo | iOS/Android client integration |
| DevOps Lead | Precious Nwabueze | Cloud deployment, CI/CD, monitoring |
| Product Lead | Belinda Mahachi | PRD, requirements, stakeholder management |
| Design Lead | Mutiat Sanusi | UI/UX, user flows |
| Cyber Security Lead | Margaret Macharia | Security audits, vulnerability testing |
| Mentor | Bolatito Sarumi | Project guidance|

---

## Technical Architecture

The system is structured across four layers:

```
┌─────────────────────────────────────────┐
│           User Interface Layer          │
│   Mobile App · Web Dashboard · Demo     │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│          FastAPI Backend Layer          │
│   7 REST endpoints · Pydantic · CORS    │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         ML Prediction Engine            │
│  XGBoost (34 features) · Encoders ×2   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│       Monitoring & Retraining           │
│  Daily MAPE tracking · Auto-retrain     │
└─────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| API Framework | FastAPI (async) |
| ML Model | XGBoost |
| Preprocessing | scikit-learn, pandas, numpy |
| Validation | Pydantic |
| Testing | pytest |
| Demo | Streamlit Cloud |
| Deployment | Railway / Render (production) |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/MsSam08/PrepPal.git
cd PrepPal

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
.\.venv\Scripts\Activate.ps1    # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import xgboost, fastapi; print('All dependencies installed')"
```

### Run the API

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

| URL | Purpose |
|-----|---------|
| `http://localhost:8000` | API root |
| `http://localhost:8000/docs` | Interactive Swagger docs |
| `http://localhost:8000/api/health` | Health check |

### First Prediction

```bash
curl -X POST "http://localhost:8000/api/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "item_name": "Jollof Rice",
    "business_type": "Restaurant",
    "date": "2025-12-01",
    "price": 50,
    "shelf_life_hours": 4,
    "weather": "Clear",
    "is_holiday": 0
  }'
```

**Expected response:**

```json
{
  "success": true,
  "predicted_demand": 42,
  "recommended_quantity": 44,
  "confidence": "High",
  "confidence_score": 0.85
}
```

---

## Implementation Journey

### Phase 1: Data Exploration (Days 1–2)

```bash
python eda_analysis.py
```

**Dataset:** 2,700 rows (900 restaurant + 1,800 café/bakery) over 180 consecutive days (June-November 2025).

**Key findings:**
- No missing values or quality issues
- Bakeries peak on weekends; cafés peak Monday-Friday
- Rainy weather reduces restaurant demand by ~15%
- Recent demand (last 3-7 days) is the strongest single predictor

**Outputs:** `eda_distributions.png`, `demand_timeseries.png`, `correlation_matrix.png`

---

### Phase 2: Data Validation (Day 2)

```bash
python data_validation.py
```

Seven automated checks were run across both datasets:

| Check | Result |
|-------|--------|
| Schema - all 11 columns present | Pass |
| Date format (YYYY-MM-DD) parseable | Pass |
| No negative quantities | Pass |
| Sales ≤ min(demand, supply) | Pass |
| No duplicate item-date pairs | Pass |
| No gaps in 180-day series | Pass |
| Valid categorical values | Pass |

**Output:** `validation_report.md`

---

### Phase 3: Feature Engineering (Days 3-4)

```bash
python 03_feature_engineering_FINAL.py
```

34 features were engineered across six groups:

| Feature Group | Count | Purpose |
|---------------|-------|---------|
| Time | 13 | Capture daily/weekly patterns |
| Cyclical (sin/cos) | 4 | Handle circular time (Mon→Sun wraps) |
| External | 2 | Holidays and weather effects |
| Item | 2 | Food category and preparation complexity |
| Business | 3 | Restaurant vs Café vs Bakery patterns |
| Lag | 4 | Yesterday's demand predicts tomorrow's |
| Rolling | 6 | Smooth noise, capture trends |
| Interaction | 4 | Combined effects (e.g. weekend × holiday) |

**Design principles:** No data leakage · Handles unseen items · Business-aware encoders · Robust to missing data

**Outputs:** `processed_data_with_features_v3.csv`, `category_label_encoder.pkl`, `business_label_encoder.pkl`

---

### Phase 4: Model Training (Days 5-7)

```bash
python model_training_and_ensemble.py
```

**Split strategy:** Time-based (not random); first 150 days for training, last 30 days for testing.

| Model | Test MAPE | R² | Train–Test Gap | Status |
|-------|-----------|-----|----------------|--------|
| Ridge (baseline) | 10.99% | 0.859 | 0.67% | Baseline |
| Random Forest | 9.18% | 0.886 | 5.12% | Overfitting |
| Gradient Boosting | 8.68% | 0.918 | 5.18% | Strong |
| **XGBoost** | **8.32%** | **0.916** | **5.98%** | **Selected** |
| Ensemble | 8.51% | 0.913 | - | Good, but complex |

XGBoost was selected for lowest test MAPE, highest R², acceptable train–test gap, and simpler deployment than the ensemble.

**Top features by importance:**

```
rolling_3day_demand    43.5%   ← Recent trend is the strongest signal
rolling_7day_demand    11.6%
holiday_flag            6.1%
prev_week_demand        5.8%
weekend_x_holiday       4.2%
is_saturday             4.0%
business_encoded        3.8%
is_weekend              3.2%
day_of_week             2.5%
is_sunday               2.1%
```

**Outputs:** `final_model_v3.pkl`, `feature_importance_v3.csv/.png`, `prediction_vs_actual_v3.png`, `residual_plot_v3.png`

---

### Phase 5: 7-Day Forecasting (Day 8)

```bash
python forecasting.py
```

Confidence degrades naturally as predictions extend further from observed data:

| Horizon | Confidence | Typical MAPE |
|---------|-----------|--------------|
| Day 1-2 | High (80-85%) | 7.1% |
| Day 3-5 | Medium (65-75%) | 9.3% |
| Day 6-7 | Low (55-60%) | 12.8% |

New items with no sales history are handled gracefully, the model falls back to business-type averages and emits a warning rather than failing.

---

### Phase 6: API Development (Days 9-11)

```bash
python api.py
```

Seven REST endpoints were built and documented. See [API Documentation](#api-documentation) below.

**Performance vs PRD targets:**

| Metric | Achieved | Target |
|--------|----------|--------|
| Response time | < 1 second | < 10 seconds |
| Uptime fallback | Implemented | Required |
| Input validation | Pydantic | Required |
| Interactive docs | Swagger at `/docs` | Nice-to-have |

---

### Phase 7: Testing (Day 12)

```bash
python tests.py -v
```

22/22 tests passing across all modules:

```
TestPredictions         8/8   
TestRiskDetection       5/5   
TestRecommendations     4/4   
TestValidation          3/3   
TestDataValidation      2/2   
─────────────────────────────
Total                  22/22    (3.45s)
```

---

### Phase 8: Deployment (Days 13-15)

The API was exposed to the team via ngrok for integration testing, and a Streamlit demo was deployed to Streamlit Cloud. Production deployment to Railway or Render is planned as the next step.

---

## Model Performance

### Summary

| Metric | Value | PRD Target | Status |
|--------|-------|------------|--------|
| Test MAPE | 8.32% | < 20% | 58% better |
| R² Score | 0.916 | > 0.70 | 31% better |
| MAE | ~4.3 units | < 10 units | Met |
| Train–Test Gap | 5.98% | < 6% | Met |
| Prediction Time | < 1 second | < 10 seconds | 10× faster |

### By Business Type

| Business | Test MAPE | Avg Error |
|----------|-----------|-----------|
| Restaurant | 7.8% | ±3.9 units |
| Café | 8.2% | ±4.3 units |
| Bakery | 8.4% | ±4.5 units |

---

## API Documentation

All endpoints are available interactively at `http://localhost:8000/docs`.

### `GET /api/health`

Returns API and model status.

```json
{ "status": "healthy", "model_loaded": true, "timestamp": "2026-02-19T10:30:00" }
```

---

### `POST /api/predict` - Single-Day Prediction

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
  "predicted_demand": 42,
  "recommended_quantity": 44,
  "confidence": "High",
  "confidence_score": 0.85,
  "explanation": "Based on: weekday pattern, rolling average, weather"
}
```

---

### `POST /api/predict-week` - 7-Day Forecast

Accepts the same item fields plus `starting_date`, `weather_forecast` (array of 7), and `holiday_flags` (array of 7).

Returns a 7-element forecast array with predicted demand, recommended quantity, and confidence per day.

---

### `POST /api/risk-alert` - Waste Risk Assessment

**Request:** `predicted_demand`, `planned_quantity`

**Response:**
```json
{
  "risk_level": "HIGH",
  "waste_percentage": 30.0,
  "expected_waste": 18,
  "message": "High waste risk - strongly recommend reducing quantity",
  "color": "red"
}
```

---

### `POST /api/recommend` - Smart Quantity Recommendation

Returns an adjusted production quantity with a 5% safety buffer and a plain-English action description.

---

### `POST /api/accuracy` - Model Performance Metrics

Returns MAPE, MAE, and R² for a given item over the last N days.

---

### `POST /api/retrain` - Trigger Retraining

Starts a background retraining job using a provided data path. The model auto-retrains when MAPE exceeds 12%.

---

## Deployment Guide

### Option 1: Local + ngrok (Current Setup)

The API runs locally and is exposed to the team via a public ngrok tunnel, no cloud infrastructure required.

```bash
# Terminal 1: start the API
export PREPPAL_DATA_DIR=$(pwd)   # Mac/Linux
set PREPPAL_DATA_DIR=%cd%        # Windows
uvicorn api:app --host 127.0.0.1 --port 8000

# Run this first:$env:Path += ";C:\Program Files"

# Terminal 2: open a public tunnel
ngrok http 8000
```

ngrok prints a public HTTPS URL (e.g. `https://.ngrok.io`):
```
http://192.168.1.181:8501
```

> **Note:** The ngrok URL changes each session unless with a paid ngrok account with a reserved domain.

### Option 2: Railway.app (Planned)

```bash
npm i -g @railway/cli
railway login
railway init
railway variables set PREPPAL_DATA_DIR=/app
railway up
railway domain
```

### Option 3: Render.com (Planned)

Create a `render.yaml` at the project root:

```yaml
services:
  - type: web
    name: preppal-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PREPPAL_DATA_DIR
        value: /opt/render/project/src
```

Push to GitHub, connect to Render, and auto-deploy activates on every push to `main`.

---

## Testing & Validation

### Automated Tests

```bash
python tests.py        # Run full suite
python tests.py -v     # Verbose output
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/api/health

# Single prediction (from file)
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d @test_predict.json
```

### Interactive Testing

Navigate to `http://localhost:8000/docs` - click **Try it out** on any endpoint, enter parameters, and execute directly in the browser.

---

## Business Impact

### Waste Reduction Example

**Scenario:** Restaurant prepares Jollof Rice daily.

| | Without AI | With PrepPal (8.12% MAPE) |
|--|-----------|--------------------------|
| Daily prep | 50 units (estimate) | 44 units (recommended) |
| Actual demand | 42 units | 42 units |
| Daily waste | 8 units | 2 units |
| Weekly waste | 56 units | 14 units |
| Weekly loss | GHS2,800 | GHS700 |

**Result: 75% waste reduction · GHS2,100 saved per week per item**

### ROI Projection (5-item restaurant)

| | Value |
|--|-------|
| Annual savings | ₦546,000 |
| Estimated subscription | ₦50,000/year |
| **Net annual benefit** | **₦496,000** |
| **First-year ROI** | **992%** |

---

## Troubleshooting

**`PREPPAL_DATA_DIR not set`**
```bash
export PREPPAL_DATA_DIR=$(pwd)   # Mac/Linux
set PREPPAL_DATA_DIR=%cd%        # Windows
```

**`ModuleNotFoundError: No module named 'xgboost'`**
```bash
pip install -r requirements.txt
```

**`FileNotFoundError: final_model_v3.pkl not found`**
```bash
# Generate model files first
python 03_feature_engineering_FINAL.py
python model_training_and_ensemble.py
```

**API returns 500 errors**
```bash
# Enable debug logging
uvicorn api:app --reload --log-level debug

# Test model loading directly
python -c "import joblib; m = joblib.load('final_model_v3.pkl'); print('Model loaded ✅')"
```

**Predictions are all zero**

Verify all three required files exist:
```bash
ls -l final_model_v3.pkl category_label_encoder.pkl business_label_encoder.pkl
```

If missing, regenerate with the feature engineering and training scripts above.

---

## Project Structure

```
PrepPal/
├── README.md
├── requirements.txt
├── .env.example
│
├── data/
│   ├── restaurant_sales_dataset.csv
│   ├── cafe_bakery_sales_dataset.csv
│   └── processed_data_with_features_v3.csv
│
├── models/
│   ├── final_model_v3.pkl               ← Production model
│   ├── xgboost_model_v3.pkl             ← Backup
│   ├── ensemble_model_v3.pkl            ← Optional
│   ├── category_label_encoder.pkl
│   └── business_label_encoder.pkl
│
├── scripts/
│   ├── eda_analysis.py
│   ├── data_validation.py
│   ├── 03_feature_engineering_FINAL.py
│   ├── model_training_and_ensemble.py
│   ├── forecasting.py
│   ├── api.py
│   ├── monitoring.py
│   ├── validation.py
│   ├── retrain.py
│   └── 11_unit_tests.py
│
├── outputs/
│   ├── eda_distributions.png
│   ├── demand_timeseries.png
│   ├── correlation_matrix.png
│   ├── feature_importance_v3.png
│   ├── prediction_vs_actual_v3.png
│   └── residual_plot_v3.png
│
├── docs/
│   ├── Model_Training_Report.pdf
│   ├── PrepPal_Progress_Report.pdf
│   └── API_Documentation.md
│
└── logs/
    └── model_metrics.json
```

---

## Contributing

### For Team Members

**Backend integration (Queen):**
```python
import requests

response = requests.post("https://api.preppal.com/api/predict", json={
    "item_name": user_item,
    "business_type": user_business,
    "date": tomorrow,
    "price": item.price,
    "shelf_life_hours": item.shelf_life,
    "weather": weather_api.get_forecast(),
    "is_holiday": calendar.is_holiday(tomorrow)
})

recommended_qty = response.json()["recommended_quantity"]
```

**Mobile integration (Christiana):**
```swift
let url = URL(string: "https://api.preppal.com/api/predict")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("application/json", forHTTPHeaderField: "Content-Type")
request.httpBody = try? JSONSerialization.data(withJSONObject: [
    "item_name": "Jollof Rice",
    "business_type": "Restaurant"
    // ... remaining fields
])
URLSession.shared.dataTask(with: request) { data, _, _ in
    // Handle response
}.resume()
```

### For External Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push and open a Pull Request

**Code standards:** PEP 8 · Docstrings on all functions · Unit tests for new features · Update README where applicable

---

## Contact & Support

| Role | Name | Email |
|------|------|-------|
| Data Science Lead | Euodia Sam | euodiasam@gmail.com |

  
**Live API:** https://api.preppal.com  (edited)

**Demo:** https://preppal-demo.streamlit.app(edited)

---

Libraries: [XGBoost](https://xgboost.readthedocs.io) · [FastAPI](https://fastapi.tiangolo.com) · [scikit-learn](https://scikit-learn.org) · [pandas](https://pandas.pydata.org)

---

*Built by the Euodia Sam · February 2026*
