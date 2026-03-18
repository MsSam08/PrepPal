# PrepPal - AI Food Waste Management

> Helping SME food businesses reduce waste by up to 85% through AI-powered demand forecasting.

A streamlined machine learning system for accurate food demand forecasting. Built specifically for restaurants, cafés, and bakeries, this system supports single-day predictions, 7-day forecasts, waste risk alerts, smart recommendations, and automatic retraining—all within an efficient, production-ready API.

---

## What It Does

Small food businesses like restaurants, cafés, bakeries lose thousands every month to overproduction. They prep based on guesswork, and what doesn't sell gets thrown away.

PrepPal fixes this with a demand forecasting model that predicts how much of each menu item a business will sell on any given day. It tells you what to make, how much to make, and flags when your plan puts you at risk of waste before you start cooking.

**[Live Demo](#) | [API Docs](http://localhost:8000/docs)**

---

## 🌟 Key Features

**🎯 Accurate Demand Prediction**  
Predicts tomorrow's demand per menu item with 8.32% MAPE (58% better than target). Works for items you've never sold before.

**📅 7-Day Forecasting**  
Week-ahead predictions with confidence scores that degrade naturally (High → Medium → Low) as forecasts extend further.

**🚨 Waste Risk Alerts**  
Real-time red/yellow/green alerts warn you before overproduction happens. Tells you exactly how much waste to expect.

**💡 Smart Recommendations**  
AI recommends optimal production quantities with a 5% safety buffer. Provides plain-English explanations: "REDUCE by 13 units" or "MAINTAIN current plan."

**🔄 Continuous Learning**  
Model automatically retrains when accuracy drops below 12% MAPE. Gets smarter over time as it sees more data.

**⚡ Fast API Response**  
All predictions return in under 1 second. 10x faster than PRD requirement.

---

## Tech Stack

| Backend | ML | Data Processing | Deployment |
|---------|-----|-----------------|------------|
| FastAPI | XGBoost | scikit-learn | Streamlit Cloud |
| Python 3.12 | 34 features | pandas, numpy | Railway (planned) |
| Pydantic | 0.916 R² | pytest | |

---

## Performance

| Prediction Results | 7-Day Forecast | Business Impact |
|-------------------|----------------|-----------------|
| MAPE: 8.32% | Confidence degrades naturally | 85% waste reduction |
| ±4.3 units accuracy | Day 1: 85%, Day 7: 55% | ₦546K annual savings |

---

## 🧩 Core Components

**XGBoost Model**: Trained on 180 days of sales data (2,700 records) with 34 engineered features.

**Business Encoder**: Differentiates Restaurant, Café, and Bakery demand patterns.

**FastAPI Backend**: 7 REST endpoints for predictions, risk alerts, recommendations, and monitoring.

**Monitoring System**: Tracks daily MAPE and triggers auto-retraining when accuracy degrades.

---

## 🚀 Quick Setup

Clone and install dependencies:
```bash
git clone https://github.com/MsSam08/PrepPal.git
cd PrepPal
python -m venv .venv
source .venv/bin/activate  # Mac/Linux | .\.venv\Scripts\Activate.ps1 (Windows)
pip install -r requirements.txt
```

Launch app:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

Admin panel at `http://localhost:8000/docs`

---

## Quick Test

Make your first prediction:
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

Response:
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

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Check system status |
| `POST /api/predict` | Single-day demand forecast |
| `POST /api/predict-week` | 7-day forecast with confidence scores |
| `POST /api/risk-alert` | Waste risk assessment (red/yellow/green) |
| `POST /api/recommend` | Smart quantity recommendation |
| `POST /api/accuracy` | Model performance metrics |
| `POST /api/retrain` | Trigger model retraining |

Interactive documentation at `/docs`

---

## 📊 Model Performance

| Metric | Result | Target | Performance |
|--------|--------|--------|-------------|
| **Test MAPE** | 8.32% | < 20% | 58% better ✓ |
| **R² Score** | 0.916 | > 0.70 | 31% better ✓ |
| **MAE** | 4.3 units | < 10 units | Met ✓ |
| **Response Time** | < 1 second | < 10 seconds | 10x faster ✓ |

**By Business Type:**

| Business | MAPE | Avg Error |
|----------|------|-----------|
| Restaurant | 7.8% | ±3.9 units |
| Café | 8.2% | ±4.3 units |
| Bakery | 8.4% | ±4.5 units |

**Top Features by Importance:**
```
rolling_3day_demand    43.5%
rolling_7day_demand    11.6%
holiday_flag            6.1%
prev_week_demand        5.8%
weekend_x_holiday       4.2%
```

---

## 💼 Business Impact

**Example: 5-item Restaurant**

| | Without AI | With PrepPal |
|--|------------|--------------|
| Daily prep | 50 units (guess) | 44 units (predicted) |
| Actual demand | 42 units | 42 units |
| Daily waste | 8 units | 2 units |
| Weekly loss | ₦2,800 | ₦700 |

**Result:** 75% waste reduction per item

**Annual ROI:**

| Metric | Value |
|--------|-------|
| Waste reduction | 85% |
| Annual savings | ₦546,000 |
| Estimated cost | ₦50,000/year |
| **Net benefit** | **₦496,000** |
| **ROI** | **992%** |

---

## 🛡️ System Highlights

- **Secure API** with Pydantic validation
- **Single-use predictions** with confidence scoring
- **Auto-retraining** when MAPE exceeds 12%
- **Fallback mechanism** returns last valid forecast if model fails
- **New item handling** via feature estimation (no retraining needed)

---

## Testing

Run test suite:
```bash
python tests.py -v
```

22/22 tests passing (3.45s):
- ✓ Prediction logic
- ✓ Risk detection (HIGH/MEDIUM/LOW)
- ✓ Recommendations (REDUCE/INCREASE/MAINTAIN)
- ✓ Data validation
- ✓ New item handling

---

## 📁 Project Structure
```
PrepPal/
├── data/
│   ├── restaurant_sales_dataset.csv
│   ├── cafe_bakery_sales_dataset.csv
│   └── processed_data_with_features_v3.csv
├── models/
│   ├── final_model_v3.pkl
│   ├── category_label_encoder.pkl
│   └── business_label_encoder.pkl
├── scripts/
│   ├── eda_analysis.py
│   ├── data_validation.py
│   ├── 03_feature_engineering_FINAL.py
│   ├── model_training_and_ensemble.py
│   ├── forecasting.py
│   ├── api.py
│   ├── monitoring.py
│   └── tests.py
└── outputs/
    ├── eda_distributions.png
    ├── feature_importance_v3.png
    └── prediction_vs_actual_v3.png
```

---

## 👤 Contact

**Euodia Sam** - Data Science Lead

- Email: euodiasam@gmail.com
- GitHub: [@MsSam08](https://github.com/MsSam08)
