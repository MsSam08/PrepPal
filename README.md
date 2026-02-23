# PrepPal — AI Food Waste Management

> Helping SME food businesses reduce waste by up to 85% through AI-powered demand forecasting.

**Built by the PrepPal Team · February 2026**

---

## What It Does

Small food businesses — restaurants, cafés, bakeries — lose thousands every month to overproduction. They prep based on guesswork, and what doesn't sell gets thrown away.

PrepPal fixes this with a demand forecasting model that predicts how much of each menu item a business will sell on any given day. It tells you what to make, how much to make, and flags when your plan puts you at risk of waste — before you start cooking.

- **Single-day predictions** with confidence scores
- **7-day forecasts** so you can plan the week ahead
- **Waste risk alerts** — red, yellow, or green based on your planned vs predicted quantities
- **Smart recommendations** with a 5% safety buffer built in
- **Works for new menu items** — no prior sales history needed

---

## Model Performance

The core model is XGBoost, trained on 180 days of sales data across restaurants, cafés, and bakeries.

| Metric | Result | Target |
|--------|--------|--------|
| Test MAPE | **8.32%** | < 20% |
| R² Score | **0.916** | > 0.70 |
| Prediction time | **< 1 second** | < 10 seconds |

Predictions are accurate to within ±4 units on average — good enough to cut waste by 85% in pilot testing.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Model | XGBoost |
| API | FastAPI (Python 3.12) |
| Preprocessing | scikit-learn, pandas |
| Validation | Pydantic |
| Demo | Streamlit |
| Public URL | ngrok |

---

## API

Seven REST endpoints, documented interactively at `/docs`.

| Endpoint | What it does |
|----------|-------------|
| `GET /api/health` | Health check |
| `POST /api/predict` | Single-day demand forecast |
| `POST /api/predict-week` | 7-day forecast |
| `POST /api/risk-alert` | Waste risk classification |
| `POST /api/recommend` | Optimal quantity recommendation |
| `POST /api/accuracy` | Model performance metrics |
| `POST /api/retrain` | Trigger background retraining |

---

## Quick Start

```bash
git clone https://github.com/yourusername/preppal-ml.git
cd preppal-ml

python -m venv .venv
source .venv/bin/activate        # Mac/Linux
.\.venv\Scripts\Activate.ps1    # Windows

pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

Then visit `http://localhost:8000/docs` to explore the API.

---

## Business Impact

A restaurant preparing Jollof Rice daily:

| | Without PrepPal | With PrepPal |
|--|----------------|-------------|
| Daily prep | 50 units (estimate) | 44 units (recommended) |
| Actual demand | 42 units | 42 units |
| Weekly waste | 56 units | 14 units |
| Weekly loss | ₦2,800 | ₦700 |

**75% waste reduction · ₦2,100 saved per week, per item.**

For a 5-item restaurant, that's roughly ₦496,000 net saved in the first year.

---

## Team

| Role | Name |
|------|------|
| Data Science Lead | Euodia Sam |
| Backend Lead | Queen Kuje |
| Mobile App Lead | Christiana Kyebambo |
| DevOps Lead | Precious Nwabueze |
| Product Lead | Belinda Mahachi |
| Design Lead | Mutiat Sanusi |
| Cyber Security Lead | Margaret Macharia |
| Mentor | Bolatito Sarumi |

---

## Contact

For questions or integration support, reach out to **euodia@preppal.com**.

**Demo:** https://preppal-demo.streamlit.app  
**API docs:** https://your-ngrok-url.ngrok.io/docs
