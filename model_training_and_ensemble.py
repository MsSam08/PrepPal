# model_training_and_ensemble.py
# Run this THIRD (after feature_engineering.py)
# Creates: final_model_v3.pkl, ensemble_model_v3.pkl

import os
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score, mean_squared_error
from xgboost import XGBRegressor

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ── LOAD ─────────────────────────────────────────────────────────────────────
print("Loading processed data...")
df = pd.read_csv(os.path.join(DATA_DIR, 'processed_data_with_features_v3.csv'))
df['date'] = pd.to_datetime(df['date'])
print(f"Shape: {df.shape}")

# ── FEATURES (34) ─────────────────────────────────────────────────────────────
FEATURE_COLS = [
    'day_of_week', 'month', 'week_of_year', 'day_of_month',
    'is_weekend', 'is_monday', 'is_friday', 'is_saturday', 'is_sunday',
    'day_sin', 'day_cos', 'month_sin', 'month_cos',
    'holiday_flag', 'is_rainy',
    'category_encoded', 'preparation_complexity',
    'business_encoded', 'price', 'shelf_life_hours',
    'prev_day_demand', 'prev_day_sold', 'prev_day_waste', 'prev_week_demand',
    'rolling_3day_demand', 'rolling_7day_demand',
    'rolling_14day_demand', 'rolling_30day_demand',
    'rolling_7day_std', 'rolling_14day_std',
    'weekend_x_holiday', 'rainy_x_weekend', 'rainy_x_holiday', 'friday_x_weekend',
]

X = df[FEATURE_COLS]
y = df['customer_demand']

# ── TRAIN / TEST SPLIT (last 30 days = test) ─────────────────────────────────
cutoff     = df['date'].max() - pd.Timedelta(days=30)
train_mask = df['date'] <= cutoff
test_mask  = df['date'] >  cutoff

X_train, y_train = X[train_mask], y[train_mask]
X_test,  y_test  = X[test_mask],  y[test_mask]
print(f"Train: {len(X_train)} rows | Test: {len(X_test)} rows")

# ── MODELS ───────────────────────────────────────────────────────────────────
models = {
    'Ridge': Ridge(alpha=1.0),
    'RandomForest': RandomForestRegressor(
        n_estimators=200, max_depth=15, min_samples_split=5,
        min_samples_leaf=2, random_state=42, n_jobs=-1
    ),
    'GradientBoosting': GradientBoostingRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.1,
        subsample=0.8, random_state=42
    ),
    'XGBoost': XGBRegressor(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, n_jobs=-1, verbosity=0
    ),
}

print("\nTraining models...")
results        = {}
trained_models = {}

for name, model in models.items():
    print(f"  Training {name}...")
    model.fit(X_train, y_train)
    trained_models[name] = model
    ytr = model.predict(X_train)
    yte = model.predict(X_test)
    results[name] = {
        'train_mape': mean_absolute_percentage_error(y_train, ytr) * 100,
        'test_mape':  mean_absolute_percentage_error(y_test,  yte) * 100,
        'test_mae':   mean_absolute_error(y_test, yte),
        'test_r2':    r2_score(y_test, yte),
    }
    print(f"    Train MAPE: {results[name]['train_mape']:.2f}%  "
          f"Test MAPE: {results[name]['test_mape']:.2f}%  "
          f"R²: {results[name]['test_r2']:.3f}")

# ── ENSEMBLE ─────────────────────────────────────────────────────────────────
class EnsembleModel:
    def __init__(self, models, weights):
        self.models  = models
        self.weights = weights

    def predict(self, X):
        out = np.zeros(len(X))
        for name, model in self.models.items():
            out += model.predict(X) * self.weights[name]
        return out


mape_scores = {n: results[n]['test_mape'] for n in models}
inv_total   = sum(1 / s for s in mape_scores.values())
weights     = {n: (1 / s) / inv_total for n, s in mape_scores.items()}

ensemble = EnsembleModel(trained_models, weights)
yte_ens  = ensemble.predict(X_test)
ens_mape = mean_absolute_percentage_error(y_test, yte_ens) * 100
ens_r2   = r2_score(y_test, yte_ens)

print(f"\nEnsemble → Test MAPE: {ens_mape:.2f}% | R²: {ens_r2:.3f}")

# ── SELECT BEST ───────────────────────────────────────────────────────────────
best      = min(results, key=lambda x: results[x]['test_mape'])
best_mape = results[best]['test_mape']

if ens_mape < best_mape:
    final_model, final_name, final_mape = ensemble, 'Ensemble', ens_mape
else:
    final_model, final_name, final_mape = trained_models[best], best, best_mape

print(f"\nBest model: {final_name} (MAPE: {final_mape:.2f}%)")

# ── SAVE ─────────────────────────────────────────────────────────────────────
joblib.dump(ensemble,    os.path.join(DATA_DIR, 'ensemble_model_v3.pkl'))
joblib.dump(final_model, os.path.join(DATA_DIR, 'final_model_v3.pkl'))

# Feature importance chart
if 'XGBoost' in trained_models:
    fi = pd.DataFrame({
        'feature':    FEATURE_COLS,
        'importance': trained_models['XGBoost'].feature_importances_
    }).sort_values('importance', ascending=False)
    plt.figure(figsize=(12, 8))
    top = fi.head(20)
    plt.barh(range(len(top)), top['importance'])
    plt.yticks(range(len(top)), top['feature'])
    plt.xlabel('Importance')
    plt.title('Top 20 Feature Importance')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, 'feature_importance_v3.png'), dpi=300)

print("=" * 50)
print("TRAINING COMPLETE")
print(f"Saved to: {DATA_DIR}")
print(f"  final_model_v3.pkl  ({final_name})")
print(f"  ensemble_model_v3.pkl")
print(f"  MAPE: {final_mape:.2f}%  "
      f"{'✅ MEETS' if final_mape < 20 else '❌ DOES NOT MEET'} PRD target of <20%")
print("=" * 50)
print("Next step: run api.py")