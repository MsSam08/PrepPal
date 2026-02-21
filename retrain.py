# retrain.py
# Retrains the model with new sales data.
# Called by POST /api/retrain or from command line:
#   python retrain.py path/to/new_data.csv

import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_percentage_error
from xgboost import XGBRegressor

from validation import validate_csv_upload

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

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


def _guess_item_features(item_name, price, shelf_life_hours):
    f = {'category': 'main_meal', 'preparation_complexity': 2}
    if shelf_life_hours < 2:
        f.update({'category': 'beverage',   'preparation_complexity': 1})
    elif shelf_life_hours > 24:
        f.update({'category': 'bakery',     'preparation_complexity': 3})
    elif shelf_life_hours > 12:
        f.update({'category': 'dessert',    'preparation_complexity': 3})
    elif price < 25:
        f.update({'category': 'side_dish',  'preparation_complexity': 1})
    return f


def create_features(df):
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    category_encoder = joblib.load(os.path.join(DATA_DIR, 'category_label_encoder.pkl'))
    biz_encoder      = joblib.load(os.path.join(DATA_DIR, 'business_label_encoder.pkl'))

    df['day_of_week']  = df['date'].dt.dayofweek
    df['month']        = df['date'].dt.month
    df['week_of_year'] = df['date'].dt.isocalendar().week.astype(int)
    df['day_of_month'] = df['date'].dt.day
    df['is_weekend']   = (df['day_of_week'] >= 5).astype(int)
    df['is_monday']    = (df['day_of_week'] == 0).astype(int)
    df['is_friday']    = (df['day_of_week'] == 4).astype(int)
    df['is_saturday']  = (df['day_of_week'] == 5).astype(int)
    df['is_sunday']    = (df['day_of_week'] == 6).astype(int)
    df['is_rainy']     = (df['weather_condition'] == 'Rainy').astype(int)

    def get_feats(row):
        return ITEM_FEATURE_MAP.get(
            row['item_name'],
            _guess_item_features(row['item_name'], row['price'], row['shelf_life_hours'])
        )

    item_feats = df.apply(get_feats, axis=1, result_type='expand')
    df['category']               = item_feats['category']
    df['preparation_complexity'] = item_feats['preparation_complexity']
    df['category_encoded']       = category_encoder.transform(df['category'])
    df['business_encoded']       = biz_encoder.transform(df['business_type'])

    df = df.sort_values(['business_type', 'item_name', 'date']).reset_index(drop=True)
    for biz in df['business_type'].unique():
        for item in df[df['business_type'] == biz]['item_name'].unique():
            mask = (df['business_type'] == biz) & (df['item_name'] == item)
            df.loc[mask, 'prev_day_demand']      = df.loc[mask, 'customer_demand'].shift(1)
            df.loc[mask, 'prev_day_sold']        = df.loc[mask, 'quantity_sold'].shift(1)
            df.loc[mask, 'prev_day_waste']       = df.loc[mask, 'waste_quantity'].shift(1)
            df.loc[mask, 'prev_week_demand']     = df.loc[mask, 'customer_demand'].shift(7)
            df.loc[mask, 'rolling_3day_demand']  = df.loc[mask, 'customer_demand'].rolling(3,  min_periods=1).mean()
            df.loc[mask, 'rolling_7day_demand']  = df.loc[mask, 'customer_demand'].rolling(7,  min_periods=1).mean()
            df.loc[mask, 'rolling_14day_demand'] = df.loc[mask, 'customer_demand'].rolling(14, min_periods=1).mean()
            df.loc[mask, 'rolling_30day_demand'] = df.loc[mask, 'customer_demand'].rolling(30, min_periods=1).mean()
            df.loc[mask, 'rolling_7day_std']     = df.loc[mask, 'customer_demand'].rolling(7,  min_periods=1).std()
            df.loc[mask, 'rolling_14day_std']    = df.loc[mask, 'customer_demand'].rolling(14, min_periods=1).std()

    df['weekend_x_holiday'] = df['is_weekend'] * df['holiday_flag']
    df['rainy_x_weekend']   = df['is_rainy']   * df['is_weekend']
    df['rainy_x_holiday']   = df['is_rainy']   * df['holiday_flag']
    df['friday_x_weekend']  = df['is_friday']  * df['is_weekend']
    df['day_sin']   = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_cos']   = np.cos(2 * np.pi * df['day_of_week'] / 7)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

    return df.fillna(0)


def retrain_model(new_data_path):
    print("=" * 50)
    print("RETRAINING PIPELINE")
    print("=" * 50)

    new_df = pd.read_csv(new_data_path)
    print(f"Loaded {len(new_df)} rows")

    result = validate_csv_upload(new_df)
    if not result['valid']:
        for e in result['errors']:
            print(f"  ❌ {e}")
        return {'success': False, 'errors': result['errors']}

    new_df_feat = create_features(new_df)

    hist_path = os.path.join(DATA_DIR, 'processed_data_with_features_v3.csv')
    hist_df   = pd.read_csv(hist_path)
    hist_df['date'] = pd.to_datetime(hist_df['date'])
    combined  = pd.concat([hist_df, new_df_feat], ignore_index=True)
    combined['date'] = pd.to_datetime(combined['date'])

    cutoff     = combined['date'].max() - pd.Timedelta(days=30)
    train_mask = combined['date'] <= cutoff
    test_mask  = combined['date'] >  cutoff
    X_train = combined[train_mask][FEATURE_COLS]
    y_train = combined[train_mask]['customer_demand']
    X_test  = combined[test_mask][FEATURE_COLS]
    y_test  = combined[test_mask]['customer_demand']

    if len(X_test) == 0:
        return {'success': False, 'errors': ['Not enough data for test split']}

    new_model = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.1,
                             random_state=42, n_jobs=-1, verbosity=0)
    new_model.fit(X_train, y_train)
    new_mape = mean_absolute_percentage_error(y_test, new_model.predict(X_test)) * 100

    old_model = joblib.load(os.path.join(DATA_DIR, 'final_model_v3.pkl'))
    old_mape  = mean_absolute_percentage_error(y_test, old_model.predict(X_test)) * 100
    improvement = old_mape - new_mape

    print(f"Old MAPE: {old_mape:.2f}%  New MAPE: {new_mape:.2f}%  Improvement: {improvement:.2f}%")

    if new_mape < old_mape:
        joblib.dump(new_model, os.path.join(DATA_DIR, 'final_model_v3.pkl'))
        combined.to_csv(hist_path, index=False)
        print("✅ New model deployed!")
        deployed = True
        reason   = 'New model improved performance'
    else:
        print("ℹ️  Existing model kept")
        deployed = False
        reason   = 'New model did not improve performance'

    return {
        'success':     True,
        'deployed':    deployed,
        'new_mape':    round(new_mape, 2),
        'old_mape':    round(old_mape, 2),
        'improvement': round(improvement, 2),
        'reason':      reason,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python retrain.py path/to/new_data.csv")
        sys.exit(1)
    result = retrain_model(sys.argv[1])
    for k, v in result.items():
        print(f"  {k}: {v}")