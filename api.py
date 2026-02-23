# api.py
# Run: uvicorn api:app --host 0.0.0.0 --port 8000
# Docs: http://localhost:8000/docs
#
# Make sure forecasting.py is in the same folder before starting.

from __future__ import annotations

import os
import json
import traceback
from datetime import datetime
from typing import List, Literal, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ------- LOAD MODEL -------------------------------------------
MODEL_HEALTHY = True
MODEL_ERROR   = None
LAST_VALID_FORECASTS: dict = {}

try:
    from forecasting import predict_7_days
    print("Model loaded successfully")
except Exception as e:
    MODEL_HEALTHY = False
    MODEL_ERROR = str(e)
    print(f"Model failed to load: {e}")

# ----- SCHEMAS ------------------------------------
BusinessType = Literal['Restaurant', 'Cafe', 'Bakery']
WeatherType  = Literal['Clear', 'Rainy']


class WeekForecastRequest(BaseModel):
    item_name: str
    business_type: BusinessType
    price: float
    shelf_life_hours: float
    starting_date: str
    weather_forecast: List[WeatherType]
    holiday_flags: List[int]

    @field_validator('item_name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('item_name cannot be empty')
        return v.strip()

    @field_validator('price', 'shelf_life_hours')
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Must be greater than 0')
        return v

    @field_validator('starting_date')
    @classmethod
    def valid_date(cls, v: str) -> str:
        try:
            pd.to_datetime(v)
        except (ValueError, TypeError):
            raise ValueError('Must be a valid YYYY-MM-DD date')
        return v

    @field_validator('weather_forecast')
    @classmethod
    def weather_length(cls, v: List[str]) -> List[str]:
        if len(v) != 7:
            raise ValueError('weather_forecast must have exactly 7 values')
        return v

    @field_validator('holiday_flags')
    @classmethod
    def holiday_valid(cls, v: List[int]) -> List[int]:
        if len(v) != 7:
            raise ValueError('holiday_flags must have exactly 7 values')
        if any(f not in (0, 1) for f in v):
            raise ValueError('Values must be 0 or 1')
        return v


class SinglePredictRequest(BaseModel):
    item_name: str
    business_type: BusinessType
    date: str
    price: float
    shelf_life_hours: float
    weather: WeatherType = 'Clear'
    is_holiday: int = 0

    @field_validator('item_name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('item_name cannot be empty')
        return v.strip()

    @field_validator('price', 'shelf_life_hours')
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Must be greater than 0')
        return v

    @field_validator('date')
    @classmethod
    def valid_date(cls, v: str) -> str:
        try:
            pd.to_datetime(v)
        except (ValueError, TypeError):
            raise ValueError('Must be a valid YYYY-MM-DD date')
        return v

    @field_validator('is_holiday')
    @classmethod
    def holiday_binary(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError('is_holiday must be 0 or 1')
        return v


class RiskAlertRequest(BaseModel):
    predicted_demand: int
    planned_quantity: int

    @field_validator('predicted_demand', 'planned_quantity')
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Must be non-negative')
        return v


class RecommendRequest(BaseModel):
    predicted_demand: int
    current_plan: int = 0

    @field_validator('predicted_demand', 'current_plan')
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError('Must be non-negative')
        return v


class AccuracyRequest(BaseModel):
    item_name: Optional[str] = None
    business_type: Optional[BusinessType] = None
    n_recent: int = 7


class RetrainRequest(BaseModel):
    new_data_path: str


# ---- APP --------------------------------------------
app = FastAPI(
    title='PrepPal ML API',
    description='AI-powered food waste management for SMEs.',
    version='3.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


def _fallback_response(item_name: str, business_type: str) -> dict:
    cache_key = f"{item_name}::{business_type}"
    if cache_key in LAST_VALID_FORECASTS:
        return {
            'success': True,
            'fallback': True,
            'fallback_reason': 'Model temporarily unavailable - showing last valid forecast',
            **LAST_VALID_FORECASTS[cache_key],
        }
    return {
        'success': True,
        'fallback': True,
        'fallback_reason': 'Model unavailable. Please use recent sales history as a guide.',
        'predicted_demand': None,
    }


# ---- ENDPOINTS -----------------------------------------

@app.get('/api/health')
def health_check():
    return {
        'status': 'healthy' if MODEL_HEALTHY else 'degraded',
        'model_loaded': MODEL_HEALTHY,
        'model_error': MODEL_ERROR,
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0',
    }


@app.post('/api/predict-week')
def predict_week(req: WeekForecastRequest):
    if not MODEL_HEALTHY:
        return _fallback_response(req.item_name, req.business_type)
    try:
        forecast = predict_7_days(
            item_name = req.item_name,
            business_type = req.business_type,
            price = req.price,
            shelf_life_hours = req.shelf_life_hours,
            starting_date = req.starting_date,
            weather_forecast = list(req.weather_forecast),
            holiday_flags = list(req.holiday_flags),
        )
        LAST_VALID_FORECASTS[f"{req.item_name}::{req.business_type}"] = {'forecast': forecast}
        return {'success': True, 'fallback': False, 'forecast': forecast}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            'success': False, 'error': str(e), 'traceback': traceback.format_exc()
        })


@app.post('/api/predict')
def predict_single(req: SinglePredictRequest):
    if not MODEL_HEALTHY:
        return _fallback_response(req.item_name, req.business_type)
    try:
        forecast = predict_7_days(
            item_name = req.item_name,
            business_type = req.business_type,
            price = req.price,
            shelf_life_hours = req.shelf_life_hours,
            starting_date = req.date,
            weather_forecast = [req.weather] * 7,
            holiday_flags = [req.is_holiday] + [0] * 6,
        )
        day1 = forecast[0]
        result = {
            'success': True,
            'fallback': False,
            'date': day1['date'],
            'predicted_demand': day1['predicted_demand'],
            'recommended_quantity': day1['recommended_quantity'],
            'confidence': day1['confidence'],
            'confidence_score': day1['confidence_score'],
            'explanation': day1['explanation'],
            'is_new_item': day1['is_new_item'],
        }
        LAST_VALID_FORECASTS[f"{req.item_name}::{req.business_type}"] = result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            'success': False, 'error': str(e), 'traceback': traceback.format_exc()
        })


@app.post('/api/risk-alert')
def waste_risk_alert(req: RiskAlertRequest):
    try:
        if req.planned_quantity == 0:
            return {
                'success': True,
                'risk_level': 'LOW',
                'waste_percentage': 0.0,
                'expected_waste': 0,
                'message': 'No production planned.',
                'color': 'green',
            }
        waste_pct = ((req.planned_quantity - req.predicted_demand) / req.planned_quantity) * 100
        expected_waste = max(0, req.planned_quantity - req.predicted_demand)
        if waste_pct > 15:
            risk_level, message, color = 'HIGH', 'High waste risk - reduce quantity.', 'red'
        elif waste_pct > 5:
            risk_level, message, color = 'MEDIUM', 'Moderate waste risk - consider reducing.', 'yellow'
        else:
            risk_level, message, color = 'LOW', 'Good planning - minimal waste expected.', 'green'
        return {
            'success': True,
            'risk_level': risk_level,
            'waste_percentage': round(waste_pct, 2),
            'expected_waste': int(expected_waste),
            'message': message,
            'color': color,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={'success': False, 'error': str(e)})


@app.post('/api/recommend')
def smart_recommendation(req: RecommendRequest):
    try:
        recommended_qty = round(req.predicted_demand * 1.05)
        difference = recommended_qty - req.current_plan
        if difference < -5:
            action = f'REDUCE by {abs(difference)} units'
            reason = 'Current plan exceeds predicted demand - reducing avoids waste.'
        elif difference > 5:
            action = f'INCREASE by {difference} units'
            reason = 'Current plan is below predicted demand - increasing avoids stockouts.'
        else:
            action = 'MAINTAIN current plan'
            reason = 'Current plan is within the optimal range.'
        return {
            'success': True,
            'recommended_quantity': int(recommended_qty),
            'action': action,
            'reason': reason,
            'explanation': (
                f'Predicted demand: {req.predicted_demand} units. '
                f'With 5% safety buffer → recommend {recommended_qty} units.'
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={'success': False, 'error': str(e)})


@app.post('/api/accuracy')
def get_accuracy(req: AccuracyRequest):
    try:
        metrics_path = os.path.join(DATA_DIR, 'model_metrics.json')
        if not os.path.exists(metrics_path):
            return {
                'success': True,
                'message': 'No accuracy logs yet. They are written by monitoring.py after daily sales.',
                'metrics': None,
            }
        with open(metrics_path, 'r') as f:
            history = json.load(f)
        if req.item_name:
            history = [m for m in history if m.get('item_name') == req.item_name]
        if req.business_type:
            history = [m for m in history if m.get('business_type') == req.business_type]
        recent = history[-req.n_recent:] if history else []
        if not recent:
            return {'success': True, 'message': 'No matching records found.', 'metrics': None}
        avg_mape = round(float(np.mean([m['mape'] for m in recent])), 2)
        avg_mae = round(float(np.mean([m['mae'] for m in recent])), 2)
        avg_r2 = round(float(np.mean([m['r2'] for m in recent])), 3)
        alert = avg_mape > 25
        return {
            'success': True,
            'period': f'Last {len(recent)} evaluations',
            'avg_mape': avg_mape,
            'avg_mae': avg_mae,
            'avg_r2': avg_r2,
            'degraded': alert,
            'alert_message': ' Model accuracy degraded - consider retraining.' if alert else None,
            'target_mape': 20.0,
            'meets_target': avg_mape < 20.0,
            'history': recent,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={'success': False, 'error': str(e)})


@app.post('/api/retrain')
def trigger_retrain(req: RetrainRequest, background_tasks: BackgroundTasks):
    if not os.path.exists(req.new_data_path):
        raise HTTPException(status_code=400, detail={
            'success': False,
            'error': f'File not found: {req.new_data_path}',
        })

    def _run_retrain():
        try:
            from retrain import retrain_model
            result = retrain_model(new_data_path=req.new_data_path)
            global MODEL_HEALTHY, MODEL_ERROR
            if result.get('deployed'):
                MODEL_HEALTHY = True
                MODEL_ERROR = None
                print(f" New model deployed. MAPE: {result['new_mape']}%")
            else:
                print(f" Existing model kept. Reason: {result.get('reason')}")
        except Exception as e:
            print(f" Retraining failed: {e}")

    background_tasks.add_task(_run_retrain)
    return {
        'success': True,
        'message': 'Retraining started. Check /api/health and /api/accuracy for updates.',
        'data_path': req.new_data_path,
    }


# ----- RUN -------------------------------------------
if __name__ == '__main__':
    import uvicorn
    print("\nPrepPal ML API - v3.0.0")
    print("Endpoints: /api/health, /api/predict, /api/predict-week,")
    print("   /api/risk-alert, /api/recommend, /api/accuracy, /api/retrain")
    print("Docs: http://localhost:8000/docs\n")
    uvicorn.run('api:app', host='0.0.0.0', port=8000, reload=True)
