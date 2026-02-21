# feature_engineering.py
# Run this SECOND (after data_validation.py)
# Creates: processed_data_with_features_v3.csv, category_label_encoder.pkl, business_label_encoder.pkl

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ── LOAD ─────────────────────────────────────────────────────────────────────
print("Loading datasets...")
restaurant_df  = pd.read_csv(os.path.join(DATA_DIR, 'restaurant_sales_dataset.csv'))
cafe_bakery_df = pd.read_csv(os.path.join(DATA_DIR, 'cafe_bakery_sales_dataset.csv'))

df = pd.concat([restaurant_df, cafe_bakery_df], ignore_index=True)
df['date'] = pd.to_datetime(df['date'])
print(f"Combined: {df.shape} | Business types: {sorted(df['business_type'].unique())}")

# ── ENCODERS ─────────────────────────────────────────────────────────────────
category_encoder = LabelEncoder()
category_encoder.fit(['main_meal', 'side_dish', 'beverage', 'pastry', 'dessert', 'bakery', 'light_meal'])

biz_encoder = LabelEncoder()
biz_encoder.fit(sorted(df['business_type'].unique()))

# ── ITEM MAP ─────────────────────────────────────────────────────────────────
ITEM_FEATURE_MAP = {
    'Jollof Rice':    {'category': 'main_meal',  'preparation_complexity': 3},
    'Fried Chicken':  {'category': 'main_meal',  'preparation_complexity': 2},
    'Beef Stew':      {'category': 'main_meal',  'preparation_complexity': 3},
    'Plantain':       {'category': 'side_dish',  'preparation_complexity': 1},
    'Vegetable Soup': {'category': 'main_meal',  'preparation_complexity': 3},
    'Espresso':       {'category': 'beverage',   'preparation_complexity': 1},
    'Cappuccino':     {'category': 'beverage',   'preparation_complexity': 1},
    'Latte':          {'category': 'beverage',   'preparation_complexity': 1},
    'Croissant':      {'category': 'pastry',     'preparation_complexity': 2},
    'Sandwich':       {'category': 'light_meal', 'preparation_complexity': 2},
    'White Bread':    {'category': 'bakery',     'preparation_complexity': 4},
    'Croissants':     {'category': 'pastry',     'preparation_complexity': 4},
    'Donuts':         {'category': 'dessert',    'preparation_complexity': 3},
    'Cake Slice':     {'category': 'dessert',    'preparation_complexity': 5},
    'Cookies':        {'category': 'dessert',    'preparation_complexity': 2},
}


def guess_item_features(item_name, price, shelf_life_hours):
    f = {'category': 'main_meal', 'preparation_complexity': 2}
    if shelf_life_hours < 2:
        f.update({'category': 'beverage',   'preparation_complexity': 1})
    elif shelf_life_hours > 24:
        f.update({'category': 'bakery',     'preparation_complexity': 3})
    elif shelf_life_hours > 12:
        f.update({'category': 'dessert',    'preparation_complexity': 3})
    elif price < 25:
        f.update({'category': 'side_dish',  'preparation_complexity': 1})
    n = item_name.lower()
    if any(w in n for w in ['coffee', 'tea', 'juice', 'smoothie', 'latte', 'espresso', 'drink']):
        f.update({'category': 'beverage',   'preparation_complexity': 1})
    elif any(w in n for w in ['bread', 'loaf']):
        f.update({'category': 'bakery',     'preparation_complexity': 4})
    elif any(w in n for w in ['cake', 'donut', 'cookie', 'muffin', 'pastry', 'pie']):
        f.update({'category': 'dessert',    'preparation_complexity': 3})
    elif any(w in n for w in ['sandwich', 'wrap', 'roll']):
        f.update({'category': 'light_meal', 'preparation_complexity': 2})
    return f


# ── FEATURE ENGINEERING ──────────────────────────────────────────────────────
print("Engineering features...")

# Time
df['day_of_week']  = df['date'].dt.dayofweek
df['day_name']     = df['date'].dt.day_name()
df['month']        = df['date'].dt.month
df['week_of_year'] = df['date'].dt.isocalendar().week
df['day_of_month'] = df['date'].dt.day
df['is_weekend']   = (df['day_of_week'] >= 5).astype(int)
df['is_monday']    = (df['day_of_week'] == 0).astype(int)
df['is_friday']    = (df['day_of_week'] == 4).astype(int)
df['is_saturday']  = (df['day_of_week'] == 5).astype(int)
df['is_sunday']    = (df['day_of_week'] == 6).astype(int)

# Weather
df['is_rainy'] = (df['weather_condition'] == 'Rainy').astype(int)

# Item characteristics
def get_item_features(row):
    if row['item_name'] in ITEM_FEATURE_MAP:
        return ITEM_FEATURE_MAP[row['item_name']]
    return guess_item_features(row['item_name'], row['price'], row['shelf_life_hours'])

item_feats = df.apply(get_item_features, axis=1, result_type='expand')
df['category']               = item_feats['category']
df['preparation_complexity'] = item_feats['preparation_complexity']
df['category_encoded']       = category_encoder.transform(df['category'])
df['business_encoded']       = biz_encoder.transform(df['business_type'])

# Lag features
df = df.sort_values(['business_type', 'item_name', 'date']).reset_index(drop=True)
for biz in df['business_type'].unique():
    for item in df[df['business_type'] == biz]['item_name'].unique():
        mask = (df['business_type'] == biz) & (df['item_name'] == item)
        df.loc[mask, 'prev_day_demand']  = df.loc[mask, 'customer_demand'].shift(1)
        df.loc[mask, 'prev_day_sold']    = df.loc[mask, 'quantity_sold'].shift(1)
        df.loc[mask, 'prev_day_waste']   = df.loc[mask, 'waste_quantity'].shift(1)
        df.loc[mask, 'prev_week_demand'] = df.loc[mask, 'customer_demand'].shift(7)

# Rolling features
for biz in df['business_type'].unique():
    for item in df[df['business_type'] == biz]['item_name'].unique():
        mask = (df['business_type'] == biz) & (df['item_name'] == item)
        df.loc[mask, 'rolling_3day_demand']  = df.loc[mask, 'customer_demand'].rolling(3,  min_periods=1).mean()
        df.loc[mask, 'rolling_7day_demand']  = df.loc[mask, 'customer_demand'].rolling(7,  min_periods=1).mean()
        df.loc[mask, 'rolling_14day_demand'] = df.loc[mask, 'customer_demand'].rolling(14, min_periods=1).mean()
        df.loc[mask, 'rolling_30day_demand'] = df.loc[mask, 'customer_demand'].rolling(30, min_periods=1).mean()
        df.loc[mask, 'rolling_7day_std']     = df.loc[mask, 'customer_demand'].rolling(7,  min_periods=1).std()
        df.loc[mask, 'rolling_14day_std']    = df.loc[mask, 'customer_demand'].rolling(14, min_periods=1).std()

# Interactions
df['weekend_x_holiday'] = df['is_weekend'] * df['holiday_flag']
df['rainy_x_weekend']   = df['is_rainy']   * df['is_weekend']
df['rainy_x_holiday']   = df['is_rainy']   * df['holiday_flag']
df['friday_x_weekend']  = df['is_friday']  * df['is_weekend']

# Cyclical
df['day_sin']   = np.sin(2 * np.pi * df['day_of_week'] / 7)
df['day_cos']   = np.cos(2 * np.pi * df['day_of_week'] / 7)
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

df = df.fillna(0)

# ── SAVE ─────────────────────────────────────────────────────────────────────
df.to_csv(os.path.join(DATA_DIR, 'processed_data_with_features_v3.csv'), index=False)
joblib.dump(category_encoder, os.path.join(DATA_DIR, 'category_label_encoder.pkl'))
joblib.dump(biz_encoder,      os.path.join(DATA_DIR, 'business_label_encoder.pkl'))

print("=" * 50)
print("FEATURE ENGINEERING COMPLETE")
print(f"Saved to: {DATA_DIR}")
print(f"  processed_data_with_features_v3.csv  {df.shape}")
print(f"  category_label_encoder.pkl")
print(f"  business_label_encoder.pkl")
print("=" * 50)
print("Next step: run model_training_and_ensemble.py")