# eda_analysis.py
# PrepPal — Exploratory Data Analysis
#
# Run from the folder containing your CSV files:
#   python eda_analysis.py
#
# Outputs (saved to same folder):
#   eda_distributions.png
#   demand_timeseries.png
#   correlation_matrix.png

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ── 1. LOAD DATASETS ─────────────────────────────────────────────────────────

restaurant_df  = pd.read_csv('restaurant_sales_dataset.csv')
cafe_bakery_df = pd.read_csv('cafe_bakery_sales_dataset.csv')

all_data = pd.concat([restaurant_df, cafe_bakery_df], ignore_index=True)
all_data['date'] = pd.to_datetime(all_data['date'])

print("=" * 80)
print("DATASET OVERVIEW")
print("=" * 80)
print(all_data.info())
print("\n", all_data.describe())
print("\nBusiness types:\n", all_data['business_type'].value_counts())
print("\nItems per business:\n", all_data.groupby('business_type')['item_name'].nunique())

# ── 2. DATA QUALITY CHECKS ───────────────────────────────────────────────────

print("\n" + "=" * 80)
print("DATA QUALITY CHECKS")
print("=" * 80)
print("\nMissing values:\n", all_data.isnull().sum())
print(f"\nNegative quantity_sold:      {(all_data['quantity_sold'] < 0).sum()}")
print(f"Negative quantity_available: {(all_data['quantity_available'] < 0).sum()}")
print(f"Sales > Available:           {len(all_data[all_data['quantity_sold'] > all_data['quantity_available']])} rows")
print(f"Sales > Demand:              {len(all_data[all_data['quantity_sold'] > all_data['customer_demand']])} rows")

date_range    = pd.date_range(all_data['date'].min(), all_data['date'].max())
missing_dates = set(date_range) - set(all_data['date'].unique())
print(f"Missing dates:               {len(missing_dates)}")

# ── 3. DISTRIBUTION PLOTS ────────────────────────────────────────────────────

fig, axes = plt.subplots(3, 3, figsize=(20, 15))
for idx, biz in enumerate(['Restaurant', 'Cafe', 'Bakery']):
    biz_data = all_data[all_data['business_type'] == biz].copy()

    biz_data['customer_demand'].hist(bins=30, ax=axes[0, idx], alpha=0.7)
    axes[0, idx].set_title(f'{biz} — Demand Distribution')

    biz_data['waste_quantity'].hist(bins=30, ax=axes[1, idx], alpha=0.7, color='red')
    axes[1, idx].set_title(f'{biz} — Waste Distribution')

    biz_data['day_of_week'] = biz_data['date'].dt.dayofweek
    biz_data.groupby('day_of_week')['customer_demand'].mean().plot(kind='bar', ax=axes[2, idx])
    axes[2, idx].set_title(f'{biz} — Avg Demand by Day')
    axes[2, idx].set_xticklabels(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], rotation=45)

plt.tight_layout()
plt.savefig('eda_distributions.png', dpi=300)
print("\n✓ Saved: eda_distributions.png")

# ── 4. PATTERN ANALYSIS ──────────────────────────────────────────────────────

print("\n" + "=" * 80)
print("WEATHER IMPACT")
print("=" * 80)
print(all_data.groupby(['business_type', 'weather_condition']).agg(
    mean_demand=('customer_demand', 'mean'),
    std_demand=('customer_demand', 'std'),
    mean_waste=('waste_quantity', 'mean')
).round(2))

print("\n" + "=" * 80)
print("HOLIDAY IMPACT")
print("=" * 80)
print(all_data.groupby(['business_type', 'holiday_flag']).agg(
    mean_demand=('customer_demand', 'mean'),
    mean_waste=('waste_quantity', 'mean')
).round(2))

all_data['is_weekend'] = (all_data['date'].dt.dayofweek >= 5).astype(int)
print("\n" + "=" * 80)
print("WEEKEND VS WEEKDAY")
print("=" * 80)
print(all_data.groupby(['business_type','is_weekend']).agg(
    mean_demand=('customer_demand','mean')).round(2))

# ── 5. TIME SERIES ───────────────────────────────────────────────────────────

fig, axes = plt.subplots(3, 1, figsize=(15, 12))
for idx, biz in enumerate(['Restaurant', 'Cafe', 'Bakery']):
    daily = all_data[all_data['business_type'] == biz].groupby('date')['customer_demand'].sum()
    axes[idx].plot(daily.index, daily.values, linewidth=1)
    axes[idx].set_title(f'{biz} — Daily Demand Over Time')
    axes[idx].set_ylabel('Total Demand')
    axes[idx].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('demand_timeseries.png', dpi=300)
print("✓ Saved: demand_timeseries.png")

# ── 6. CORRELATION MATRIX ────────────────────────────────────────────────────

numeric_cols = ['price','shelf_life_hours','quantity_available',
                'quantity_sold','customer_demand','waste_quantity']
plt.figure(figsize=(10, 8))
sns.heatmap(all_data[numeric_cols].corr(), annot=True, fmt='.2f',
            cmap='coolwarm', center=0, square=True, linewidths=1)
plt.title('Feature Correlation Matrix', fontsize=16)
plt.tight_layout()
plt.savefig('correlation_matrix.png', dpi=300)
print("✓ Saved: correlation_matrix.png")

# ── 7. ITEM STATS ────────────────────────────────────────────────────────────

print("\n" + "=" * 80)
print("AVERAGE WASTE % BY ITEM")
print("=" * 80)
all_data['waste_pct'] = (
    all_data['waste_quantity'] / all_data['quantity_available'] * 100).fillna(0)
print(all_data.groupby(['business_type','item_name'])['waste_pct']
      .mean().round(2).sort_values(ascending=False))

print("\n" + "=" * 80)
print("EDA COMPLETE")
print("=" * 80)