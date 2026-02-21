# monitoring.py
# Tracks model accuracy over time.
# Called after real sales data comes in each day.

import os
import json
import numpy as np
from datetime import datetime
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

METRICS_FILE = os.path.join(DATA_DIR, 'model_metrics.json')


class ModelMonitor:

    def __init__(self):
        self.metrics_history = self._load()

    def _load(self):
        try:
            with open(METRICS_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save(self):
        with open(METRICS_FILE, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)

    def log_predictions(self, y_true, y_pred, business_type=None, item_name=None):
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        metrics = {
            'timestamp':     datetime.now().isoformat(),
            'mae':           round(float(mean_absolute_error(y_true, y_pred)), 2),
            'mape':          round(float(mean_absolute_percentage_error(y_true, y_pred)) * 100, 2),
            'rmse':          round(float(np.sqrt(np.mean((y_true - y_pred) ** 2))), 2),
            'r2':            round(float(r2_score(y_true, y_pred)), 3),
            'n_predictions': int(len(y_true)),
            'business_type': business_type,
            'item_name':     item_name,
        }
        if metrics['mape'] > 25:
            print(f"🚨 MAPE {metrics['mape']:.2f}% exceeds 25% — model drift detected. Call /api/retrain.")
        self.metrics_history.append(metrics)
        self._save()
        return metrics

    def get_recent_performance(self, n=7):
        recent = self.metrics_history[-n:] if self.metrics_history else []
        if not recent:
            return None
        return {
            'avg_mape': round(float(np.mean([m['mape'] for m in recent])), 2),
            'avg_mae':  round(float(np.mean([m['mae']  for m in recent])), 2),
            'avg_r2':   round(float(np.mean([m['r2']   for m in recent])), 3),
        }

    def needs_retraining(self, threshold_mape=12.0, window=7):
        if len(self.metrics_history) < window:
            return False
        recent   = self.metrics_history[-window:]
        avg_mape = float(np.mean([m['mape'] for m in recent]))
        if avg_mape > threshold_mape:
            print(f"⚠️  Retraining needed: avg MAPE {avg_mape:.2f}% over last {window} logs")
            return True
        return False


if __name__ == '__main__':
    monitor = ModelMonitor()
    metrics = monitor.log_predictions(
        y_true=[40, 45, 38, 50, 42],
        y_pred=[42, 43, 40, 48, 41],
        business_type='Restaurant',
        item_name='Jollof Rice',
    )
    print(f"Logged: MAPE {metrics['mape']}% | MAE {metrics['mae']}")
    perf = monitor.get_recent_performance()
    if perf:
        print(f"Recent avg MAPE: {perf['avg_mape']}%")