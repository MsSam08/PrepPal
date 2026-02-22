# forecasting.py
# Core forecasting engine — imported by api.py
# Run standalone to test: python forecasting.py

import os
import numpy as np
import pandas as pd
import joblib
from datetime import timedelta

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ----- LOAD MODEL & DATA -----------------------------------------
try:
    final_model = joblib.load(os.path.join(DATA_DIR, 'final_model_v3.pkl'))
    category_encoder = joblib.load(os.path.join(DATA_DIR, 'category_label_encoder.pkl'))
    biz_encoder = joblib.load(os.path.join(DATA_DIR, 'business_label_encoder.pkl'))
    print(f"Models loaded")
except FileNotFoundError as e:
    raise FileNotFoundError(
        f"\nModel file not found: {e}\n"
        "Run feature_engineering.py then model_training_and_ensemble.py first.\n"
    )

try:
    df_history = pd.read_csv(os.path.join(DATA_DIR, 'processed_data_with_features_v3.csv'))
    df_history['date'] = pd.to_datetime(df_history['date'])
    print(f" Historical data loaded: {len(df_history)} rows")
except FileNotFoundError:
    raise FileNotFoundError(
        "\nprocessed_data_with_features_v3.csv not found.\n"
        "Run feature_engineering.py first.\n"
    )

# ── ITEM MAP ─────────────────────────────────────────────────────────────────
ITEM_FEATURE_MAP = {
    'Jollof Rice': {'category': 'main_meal', 'preparation_complexity': 3},
    'Fried Chicken':  {'category': 'main_meal', 'preparation_complexity': 2},
    'Beef Stew': {'category': 'main_meal', 'preparation_complexity': 3},
    'Plantain': {'category': 'side_dish', 'preparation_complexity': 1},
    'Vegetable Soup': {'category': 'main_meal', 'preparation_complexity': 3},
    'Espresso': {'category': 'beverage', 'preparation_complexity': 1},
    'Cappuccino': {'category': 'beverage', 'preparation_complexity': 1},
    'Latte': {'category': 'beverage', 'preparation_complexity': 1},
    'Croissant': {'category': 'pastry', 'preparation_complexity': 2},
    'Sandwich': {'category': 'light_meal', 'preparation_complexity': 2},
    'White Bread': {'category': 'bakery', 'preparation_complexity': 4},
    'Croissants': {'category': 'pastry', 'preparation_complexity': 4},
    'Donuts': {'category': 'dessert', 'preparation_complexity': 3},
    'Cake Slice': {'category': 'dessert', 'preparation_complexity': 5},
    'Cookies': {'category': 'dessert', 'preparation_complexity': 2},
}


def _guess_item_features(item_name, price, shelf_life_hours):
    f = {'category': 'main_meal', 'preparation_complexity': 2}
    if shelf_life_hours < 2:
        f.update({'category': 'beverage', 'preparation_complexity': 1})
    elif shelf_life_hours > 24:
        f.update({'category': 'bakery', 'preparation_complexity': 3})
    elif shelf_life_hours > 12:
        f.update({'category': 'dessert', 'preparation_complexity': 3})
    elif price < 25:
        f.update({'category': 'side_dish', 'preparation_complexity': 1})
    n = item_name.lower()
    if any(w in n for w in ['coffee', 'tea', 'juice', 'smoothie', 'latte', 'espresso', 'drink']):
        f.update({'category': 'beverage', 'preparation_complexity': 1})
    elif any(w in n for w in ['bread', 'loaf']):
        f.update({'category': 'bakery', 'preparation_complexity': 4})
    elif any(w in n for w in ['cake', 'donut', 'cookie', 'muffin', 'pastry', 'pie']):
        f.update({'category': 'dessert', 'preparation_complexity': 3})
    elif any(w in n for w in ['sandwich', 'wrap', 'roll']):
        f.update({'category': 'light_meal', 'preparation_complexity': 2})
    return f


def _get_recent_data(item_name, business_type, n_days=30):
    mask = (df_history['item_name'] == item_name) & (df_history['business_type'] == business_type)
    recent = df_history[mask].sort_values('date').tail(n_days)
    if len(recent) == 0:
        recent = df_history[df_history['business_type'] == business_type].sort_values('date').tail(30)
    return recent


def predict_7_days(item_name, business_type, price, shelf_life_hours,
                   starting_date, weather_forecast, holiday_flags):
    """
    Generate a 7-day demand forecast.
    Returns a list of 7 dicts, one per day.
    """
    start = pd.to_datetime(starting_date)

    if item_name in ITEM_FEATURE_MAP:
        item_features, is_known = ITEM_FEATURE_MAP[item_name], True
    else:
        item_features, is_known = _guess_item_features(item_name, price, shelf_life_hours), False

    category_enc = category_encoder.transform([item_features['category']])[0]
    business_enc = biz_encoder.transform([business_type])[0]
    recent = _get_recent_data(item_name, business_type)
    predictions  = []

    for day in range(7):
        pred_date = start + timedelta(days=day)
        dow = pred_date.dayofweek
        month = pred_date.month
        week_of_yr = pred_date.isocalendar()[1]
        day_of_mth = pred_date.day

        is_weekend = int(dow >= 5)
        is_monday = int(dow == 0)
        is_friday = int(dow == 4)
        is_saturday = int(dow == 5)
        is_sunday = int(dow == 6)

        day_sin = np.sin(2 * np.pi * dow   / 7)
        day_cos = np.cos(2 * np.pi * dow   / 7)
        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)

        is_rainy = int(weather_forecast[day] == 'Rainy')
        holiday_flag = holiday_flags[day]

        if day == 0:
            prev_day_demand = recent['customer_demand'].iloc[-1]
            prev_day_sold = recent['quantity_sold'].iloc[-1]
            prev_day_waste = recent['waste_quantity'].iloc[-1]
            prev_week_demand = recent['customer_demand'].iloc[-7] if len(recent) >= 7 else prev_day_demand
        else:
            prev_day_demand = predictions[day - 1]['predicted_demand']
            prev_day_sold = prev_day_demand * 0.95
            prev_day_waste = 0
            prev_week_demand = predictions[day - 7]['predicted_demand'] if day >= 7 else prev_day_demand

        if day == 0:
            rolling_3d = recent['customer_demand'].tail(3).mean()
            rolling_7d = recent['customer_demand'].tail(7).mean()
            rolling_14d = recent['customer_demand'].tail(14).mean() if len(recent) >= 14 else rolling_7d
            rolling_30d = recent['customer_demand'].tail(30).mean() if len(recent) >= 30 else rolling_7d
            std_7d = recent['customer_demand'].tail(7).std() or 0
            std_14d = recent['customer_demand'].tail(14).std() if len(recent) >= 14 else std_7d
        else:
            rp = [p['predicted_demand'] for p in predictions[-min(day, 7):]]
            rolling_3d = np.mean(rp[-3:])
            rolling_7d = np.mean(rp)
            rolling_14d = rolling_7d
            rolling_30d = rolling_7d
            std_7d = np.std(rp) if len(rp) > 1 else 0
            std_14d = std_7d

        feat = pd.DataFrame([{
            'day_of_week': dow,
            'month': month,
            'week_of_year': week_of_yr,
            'day_of_month': day_of_mth,
            'is_weekend': is_weekend,
            'is_monday': is_monday,
            'is_friday': is_friday,
            'is_saturday': is_saturday,
            'is_sunday': is_sunday,
            'day_sin': day_sin,
            'day_cos': day_cos,
            'month_sin': month_sin,
            'month_cos': month_cos,
            'holiday_flag': holiday_flag,
            'is_rainy': is_rainy,
            'category_encoded': category_enc,
            'preparation_complexity': item_features['preparation_complexity'],
            'business_encoded': business_enc,
            'price': price,
            'shelf_life_hours': shelf_life_hours,
            'prev_day_demand': prev_day_demand,
            'prev_day_sold': prev_day_sold,
            'prev_day_waste': prev_day_waste,
            'prev_week_demand': prev_week_demand,
            'rolling_3day_demand': rolling_3d,
            'rolling_7day_demand': rolling_7d,
            'rolling_14day_demand': rolling_14d,
            'rolling_30day_demand': rolling_30d,
            'rolling_7day_std': std_7d,
            'rolling_14day_std': std_14d,
            'weekend_x_holiday': is_weekend * holiday_flag,
            'rainy_x_weekend': is_rainy * is_weekend,
            'rainy_x_holiday': is_rainy * holiday_flag,
            'friday_x_weekend': is_friday * is_weekend,
        }])

        predicted_demand = max(0, round(final_model.predict(feat)[0]))
        confidence_score = round(max(0.55, 0.85 - (day * 0.05)), 2)
        confidence = 'High' if confidence_score >= 0.75 else 'Medium' if confidence_score >= 0.60 else 'Low'

        factors = []
        if pred_date.strftime('%A') in ('Saturday', 'Sunday') and business_type != 'Cafe':
            factors.append('weekend uplift')
        if pred_date.strftime('%A') in ('Saturday', 'Sunday') and business_type == 'Cafe':
            factors.append('weekend drop')
        if holiday_flag == 1:
            factors.append('holiday effect')
        if is_rainy:
            factors.append('rainy weather')
        factors.append(f'7-day avg ({rolling_7d:.0f})')

        predictions.append({
            'date': pred_date.strftime('%Y-%m-%d'),
            'day_name': pred_date.strftime('%A'),
            'day_number': day + 1,
            'predicted_demand': int(predicted_demand),
            'recommended_quantity': int(round(predicted_demand * 1.05)),
            'confidence': confidence,
            'confidence_score': confidence_score,
            'weather': weather_forecast[day],
            'is_holiday': 'Yes' if holiday_flag == 1 else 'No',
            'is_new_item': not is_known,
            'explanation': 'Based on: ' + ', '.join(factors[:3]),
        })

    return predictions


# ---- STANDALONE TEST ----------------------------
if __name__ == '__main__':
    print("\nTesting 7-day forecast...")
    fc = predict_7_days(
        item_name='Jollof Rice', business_type='Restaurant',
        price=50, shelf_life_hours=4,
        starting_date='2025-12-01',
        weather_forecast=['Clear', 'Clear', 'Rainy', 'Clear', 'Clear', 'Clear', 'Rainy'],
        holiday_flags=[0, 0, 0, 0, 0, 0, 0],
    )
    for d in fc:
        print(f"  {d['day_name']:10} | demand: {d['predicted_demand']:3} "
              f"| rec: {d['recommended_quantity']:3} | {d['confidence']:6} | {d['explanation']}")
    print("\n forecasting.py working correctly")