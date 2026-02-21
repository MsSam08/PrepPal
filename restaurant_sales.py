import pandas as pd
import numpy as np
from datetime import datetime, timedelta

"""
RESTAURANT SALES DATASET
Simplified dataset with only required columns
"""

# ---------- CONFIGURATION ----------
start_date = "2025-06-01"
days = 180  # 6 months
np.random.seed(42)

# RESTAURANT ITEMS
items = {
    "Jollof Rice": {"price": 50, "shelf_life_hours": 4},
    "Fried Chicken": {"price": 70, "shelf_life_hours": 6},
    "Beef Stew": {"price": 60, "shelf_life_hours": 8},
    "Plantain": {"price": 20, "shelf_life_hours": 3},
    "Vegetable Soup": {"price": 40, "shelf_life_hours": 6},
}

# Base demand per item
base_demands = {
    "Jollof Rice": 40,
    "Fried Chicken": 30,
    "Beef Stew": 25,
    "Plantain": 20,
    "Vegetable Soup": 15,
}

# Business patterns
weekend_multiplier = 1.2
holiday_probability = 0.05
holiday_multiplier = 1.3
rainy_probability = 0.2
rainy_multiplier = 0.85

# Monthly seasonality
monthly_multipliers = {
    6: 1.15, 7: 1.1, 8: 1.05, 9: 1.0, 10: 0.95, 11: 0.9
}

# ----------------------------------

date_range = pd.date_range(start=start_date, periods=days)
data = []

for idx, date in enumerate(date_range):
    day_of_week = date.weekday()
    month = date.month
    
    # Weekend effect
    is_weekend = day_of_week >= 5
    weekend_effect = weekend_multiplier if is_weekend else 1.0
    
    # Monthly effect
    monthly_effect = monthly_multipliers.get(month, 1.0)
    
    # Trend
    trend_effect = 1 + (0.001 * idx)
    
    # Random external factors
    is_holiday = np.random.rand() < holiday_probability
    is_rainy = np.random.rand() < rainy_probability
    
    holiday_flag = 1 if is_holiday else 0
    weather_condition = "Rainy" if is_rainy else "Clear"
    
    weather_effect = rainy_multiplier if is_rainy else 1.0
    holiday_effect = holiday_multiplier if is_holiday else 1.0
    
    # Generate data for each item
    for item_name, item_info in items.items():
        base_demand = base_demands[item_name]
        price = item_info["price"]
        shelf_life_hours = item_info["shelf_life_hours"]
        
        # Calculate expected demand
        expected_demand = (base_demand * 
                          weekend_effect * 
                          monthly_effect * 
                          trend_effect * 
                          weather_effect * 
                          holiday_effect)
        
        # Planned production (with buffer)
        planned_quantity = expected_demand * 1.05
        quantity_available = planned_quantity * (1 + np.random.uniform(-0.1, 0.1))
        quantity_available = max(0, round(quantity_available))
        
        # Customer demand (actual)
        customer_demand = expected_demand * (1 + np.random.uniform(-0.15, 0.15))
        customer_demand = max(0, round(customer_demand))
        
        # Actual sales
        quantity_sold = min(customer_demand, quantity_available)
        
        # Waste
        waste_quantity = max(0, quantity_available - quantity_sold)
        
        data.append({
            "business_type": "Restaurant",
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
output_file = "restaurant_sales_dataset.csv"
df.to_csv(output_file, index=False)

print("="*80)
print("RESTAURANT SALES DATASET GENERATED")
print("="*80)
print(f"✓ File: {output_file}")
print(f"✓ Shape: {df.shape}")
print(f"✓ Date range: {df['date'].min()} to {df['date'].max()}")
print(f"✓ Business type: Restaurant")
print(f"✓ Items: {len(items)}")
print(f"\nFirst 10 rows:")
print(df.head(10))

print("\n" + "="*80)
print("DATASET SUMMARY")
print("="*80)
print(df.describe())

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
print("BUSINESS INSIGHTS")
print("="*80)
total_revenue = (df['quantity_sold'] * df['price']).sum()
total_waste = df['waste_quantity'].sum()
waste_value = sum(df['waste_quantity'] * df['price'])

print(f"Total items sold: {df['quantity_sold'].sum():,}")
print(f"Total revenue: ${total_revenue:,.2f}")
print(f"Total waste quantity: {total_waste:,} items")
print(f"Total waste value: ${waste_value:,.2f}")
print(f"Average waste per day: {waste_value / days:.2f}")

print("\n✓ RESTAURANT DATASET COMPLETE!")