import pandas as pd
import numpy as np
from datetime import datetime, timedelta

"""
CAFÉ AND BAKERY SALES DATASET
Combined dataset with only required columns
"""

# ---------- CONFIGURATION ----------
start_date = "2025-06-01"
days = 180  # 6 months
np.random.seed(42)

# CAFÉ ITEMS
cafe_items = {
    "Espresso": {"price": 25, "shelf_life_hours": 0.5},
    "Cappuccino": {"price": 35, "shelf_life_hours": 0.5},
    "Latte": {"price": 40, "shelf_life_hours": 0.5},
    "Croissant": {"price": 30, "shelf_life_hours": 12},
    "Sandwich": {"price": 45, "shelf_life_hours": 8},
}

cafe_base_demands = {
    "Espresso": 45,
    "Cappuccino": 60,
    "Latte": 55,
    "Croissant": 35,
    "Sandwich": 40,
}

# BAKERY ITEMS
bakery_items = {
    "White Bread": {"price": 20, "shelf_life_hours": 24},
    "Croissants": {"price": 30, "shelf_life_hours": 12},
    "Donuts": {"price": 15, "shelf_life_hours": 12},
    "Cake Slice": {"price": 40, "shelf_life_hours": 48},
    "Cookies": {"price": 10, "shelf_life_hours": 72},
}

bakery_base_demands = {
    "White Bread": 50,
    "Croissants": 40,
    "Donuts": 60,
    "Cake Slice": 25,
    "Cookies": 45,
}

# Business patterns
cafe_weekend_multiplier = 0.85  # Cafés quieter on weekends
bakery_weekend_multiplier = 1.5  # Bakeries busier on weekends

holiday_probability = 0.05
cafe_holiday_multiplier = 0.7  # Cafés quieter on holidays (offices closed)
bakery_holiday_multiplier = 1.8  # Bakeries boom on holidays

rainy_probability = 0.2
cafe_rainy_multiplier = 1.15  # Rainy days good for cafés
bakery_rainy_multiplier = 0.9  # Rainy days slightly reduce bakery traffic

# Monthly seasonality
cafe_monthly_multipliers = {
    6: 1.15, 7: 1.1, 8: 1.0, 9: 1.15, 10: 1.1, 11: 1.05
}

bakery_monthly_multipliers = {
    6: 1.0, 7: 1.05, 8: 0.95, 9: 1.0, 10: 1.1, 11: 1.15
}

# ----------------------------------

date_range = pd.date_range(start=start_date, periods=days)
data = []

for idx, date in enumerate(date_range):
    day_of_week = date.weekday()
    month = date.month
    
    # Weekend check
    is_weekend = day_of_week >= 5
    
    # Trend
    trend_effect = 1 + (0.0008 * idx)
    
    # Random external factors
    is_holiday = np.random.rand() < holiday_probability
    is_rainy = np.random.rand() < rainy_probability
    
    holiday_flag = 1 if is_holiday else 0
    weather_condition = "Rainy" if is_rainy else "Clear"
    
    # ==================== CAFÉ DATA ====================
    cafe_weekend_effect = cafe_weekend_multiplier if is_weekend else 1.0
    cafe_monthly_effect = cafe_monthly_multipliers.get(month, 1.0)
    cafe_weather_effect = cafe_rainy_multiplier if is_rainy else 1.0
    cafe_holiday_effect = cafe_holiday_multiplier if is_holiday else 1.0
    
    for item_name, item_info in cafe_items.items():
        base_demand = cafe_base_demands[item_name]
        price = item_info["price"]
        shelf_life_hours = item_info["shelf_life_hours"]
        
        expected_demand = (base_demand * 
                          cafe_weekend_effect * 
                          cafe_monthly_effect * 
                          trend_effect * 
                          cafe_weather_effect * 
                          cafe_holiday_effect)
        
        planned_quantity = expected_demand * 1.03
        quantity_available = planned_quantity * (1 + np.random.uniform(-0.08, 0.08))
        quantity_available = max(0, round(quantity_available))
        
        customer_demand = expected_demand * (1 + np.random.uniform(-0.18, 0.18))
        customer_demand = max(0, round(customer_demand))
        
        quantity_sold = min(customer_demand, quantity_available)
        waste_quantity = max(0, quantity_available - quantity_sold)
        
        data.append({
            "business_type": "Cafe",
            "item_name": item_name,
            "date": date.strftime("%Y-%m-%d"),
            "price": price,
            "shelf_life_hours": shelf_life_hours,
            "quantity_available": quantity_available,
            "quantity_sold": quantity_sold,
            "customer_demand": customer_demand,
            "waste_quantity": waste_quantity,
            "weather_condition": weather_condition,
            "holiday_flag": holiday_flag
        })
    
    # ==================== BAKERY DATA ====================
    bakery_weekend_effect = bakery_weekend_multiplier if is_weekend else 1.0
    bakery_monthly_effect = bakery_monthly_multipliers.get(month, 1.0)
    bakery_weather_effect = bakery_rainy_multiplier if is_rainy else 1.0
    bakery_holiday_effect = bakery_holiday_multiplier if is_holiday else 1.0
    
    for item_name, item_info in bakery_items.items():
        base_demand = bakery_base_demands[item_name]
        price = item_info["price"]
        shelf_life_hours = item_info["shelf_life_hours"]
        
        expected_demand = (base_demand * 
                          bakery_weekend_effect * 
                          bakery_monthly_effect * 
                          trend_effect * 
                          bakery_weather_effect * 
                          bakery_holiday_effect)
        
        planned_quantity = expected_demand * 1.15
        quantity_available = planned_quantity * (1 + np.random.uniform(-0.1, 0.1))
        quantity_available = max(0, round(quantity_available))
        
        customer_demand = expected_demand * (1 + np.random.uniform(-0.2, 0.2))
        customer_demand = max(0, round(customer_demand))
        
        quantity_sold = min(customer_demand, quantity_available)
        waste_quantity = max(0, quantity_available - quantity_sold)
        
        data.append({
            "business_type": "Bakery",
            "item_name": item_name,
            "date": date.strftime("%Y-%m-%d"),
            "price": price,
            "shelf_life_hours": shelf_life_hours,
            "quantity_available": quantity_available,
            "quantity_sold": quantity_sold,
            "customer_demand": customer_demand,
            "waste_quantity": waste_quantity,
            "weather_condition": weather_condition,
            "holiday_flag": holiday_flag
        })

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
output_file = "cafe_bakery_sales_dataset.csv"
df.to_csv(output_file, index=False)

print("="*80)
print("CAFÉ AND BAKERY SALES DATASET GENERATED")
print("="*80)
print(f"✓ File: {output_file}")
print(f"✓ Shape: {df.shape}")
print(f"✓ Date range: {df['date'].min()} to {df['date'].max()}")
print(f"✓ Business types: Cafe, Bakery")
print(f"✓ Café items: {len(cafe_items)}")
print(f"✓ Bakery items: {len(bakery_items)}")

print("\n" + "="*80)
print("SAMPLE DATA")
print("="*80)
print("\nFirst 5 Café rows:")
print(df[df['business_type'] == 'Cafe'].head())
print("\nFirst 5 Bakery rows:")
print(df[df['business_type'] == 'Bakery'].head())

print("\n" + "="*80)
print("COLUMN CHECK")
print("="*80)
print("Required columns:")
required_cols = [
    "business_type", "item_name", "date", "price", "shelf_life_hours",
    "quantity_available", "quantity_sold", "customer_demand", 
    "waste_quantity", "weather_condition", "holiday_flag"
]
for col in required_cols:
    if col in df.columns:
        print(f"  ✓ {col}")
    else:
        print(f"  ✗ {col} MISSING!")

print("\n" + "="*80)
print("BUSINESS TYPE BREAKDOWN")
print("="*80)
print(df['business_type'].value_counts())

print("\n" + "="*80)
print("BUSINESS INSIGHTS BY TYPE")
print("="*80)

for biz_type in ['Cafe', 'Bakery']:
    biz_df = df[df['business_type'] == biz_type]
    total_revenue = (biz_df['quantity_sold'] * biz_df['price']).sum()
    total_waste = biz_df['waste_quantity'].sum()
    waste_value = sum(biz_df['waste_quantity'] * biz_df['price'])
    
    print(f"\n{biz_type.upper()}:")
    print(f"  Total items sold: {biz_df['quantity_sold'].sum():,}")
    print(f"  Total revenue: ${total_revenue:,.2f}")
    print(f"  Total waste quantity: {total_waste:,} items")
    print(f"  Total waste value: ${waste_value:,.2f}")

print("\n✓ CAFÉ AND BAKERY DATASET COMPLETE!")