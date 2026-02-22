# data_validation.py
# PrepPal - Raw Dataset Validation (runs once on your training CSVs)
#
## NB: This is separate from validation.py which validates
# user-uploaded CSVs before retraining. Both are needed.
#
# Run from the folder containing the CSV files:
#   python data_validation.py

import pandas as pd
import numpy as np


def validate_dataset(df: pd.DataFrame, dataset_name: str) -> dict:
    """
    Validate a raw sales CSV.
    Checks schema, types, nulls, negatives, business logic,
    duplicates, date continuity, and value ranges.
    """
    print(f"\n{'=' * 80}")
    print(f"VALIDATING: {dataset_name}")
    print(f"{'=' * 80}")

    issues   = []
    warnings = []

    # 1. Schema
    required = ['business_type','item_name','date','price','shelf_life_hours',
                'quantity_available','quantity_sold','customer_demand',
                'waste_quantity','weather_condition','holiday_flag']
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        issues.append(f"Missing columns: {missing_cols}")
    else:
        print(" All required columns present")

    # 2. Date type
    try:
        df['date'] = pd.to_datetime(df['date'])
        print(" Date column valid")
    except Exception as e:
        issues.append(f"Date conversion failed: {e}")

    # 3. Nulls
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        issues.append(f"Missing values:\n{null_counts[null_counts > 0]}")
    else:
        print(" No missing values")

    # 4. Negatives
    for col in ['quantity_available','quantity_sold','customer_demand','waste_quantity']:
        if col in df.columns:
            n = (df[col] < 0).sum()
            if n > 0:
                issues.append(f"{col}: {n} negative value(s)")
            else:
                print(f" {col}: no negatives")

    # 5. Sales vs availability
    if 'quantity_sold' in df.columns and 'quantity_available' in df.columns:
        v = (df['quantity_sold'] > df['quantity_available']).sum()
        if v > 0:
            issues.append(f"{v} rows: quantity_sold > quantity_available")
        else:
            print(" Sales never exceed availability")

    # 6. Sales vs demand
    if 'quantity_sold' in df.columns and 'customer_demand' in df.columns:
        v = (df['quantity_sold'] > df['customer_demand']).sum()
        if v > 0:
            issues.append(f"{v} rows: quantity_sold > customer_demand")
        else:
            print(" Sales never exceed demand")

    # 7. Waste calculation
    if all(c in df.columns for c in ['waste_quantity','quantity_available','quantity_sold']):
        calc = (df['quantity_available'] - df['quantity_sold']).clip(lower=0)
        errs = (df['waste_quantity'] != calc).sum()
        if errs > 0:
            issues.append(f"{errs} rows: incorrect waste calculation")
        else:
            print(" Waste calculated correctly")

    # 8. Duplicates
    if 'date' in df.columns and 'item_name' in df.columns:
        dupes = df.duplicated(subset=['date','item_name'], keep=False).sum()
        if dupes > 0:
            issues.append(f"{dupes} duplicate date-item combinations")
        else:
            print(" No duplicates")

    # 9. Date continuity
    if 'date' in df.columns:
        full_range = pd.date_range(df['date'].min(), df['date'].max())
        expected_rows = len(full_range) * df['item_name'].nunique()
        if expected_rows != len(df):
            warnings.append(f"Expected {expected_rows} rows, found {len(df)}")
        else:
            print(" Date continuity validated")

    # 10. Price / shelf life
    if 'price' in df.columns and (df['price'] <= 0).any():
        issues.append("Price must be positive")
    else:
        print(" All prices positive")

    if 'shelf_life_hours' in df.columns and (df['shelf_life_hours'] < 0).any():
        issues.append("Shelf life cannot be negative")
    else:
        print(" Shelf life values valid")

    # 11. Categoricals
    if 'weather_condition' in df.columns:
        invalid = df[~df['weather_condition'].isin(['Clear','Rainy'])]
        if len(invalid) > 0:
            issues.append(f"Invalid weather values: {df['weather_condition'].unique()}")
        else:
            print(" Weather values valid")

    if 'holiday_flag' in df.columns:
        invalid = df[~df['holiday_flag'].isin([0,1])]
        if len(invalid) > 0:
            issues.append("holiday_flag must be 0 or 1")
        else:
            print(" Holiday flag valid")

    print(f"\n{'=' * 80}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 80}")
    print(f"Rows: {len(df)}")
    print(f"Range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"Issues: {len(issues)}")
    print(f"Warnings:{len(warnings)}")

    for issue in issues: print(f"\n {issue}")
    for warn in warnings: print(f"\n  {warn}")
    if not issues and not warnings:
        print("\n ALL CHECKS PASSED")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'total_rows': len(df),
        'date_range': f"{df['date'].min().date()} to {df['date'].max().date()}",
    }


# ---- Run validation --------------------------------------------

restaurant_df  = pd.read_csv('restaurant_sales_dataset.csv')
cafe_bakery_df = pd.read_csv('cafe_bakery_sales_dataset.csv')

r_result = validate_dataset(restaurant_df,  "Restaurant Dataset")
c_result = validate_dataset(cafe_bakery_df, "Cafe & Bakery Dataset")

# Save report
with open('validation_report.md', 'w') as f:
    f.write("# DATA VALIDATION REPORT\n\n")
    for label, result in [("Restaurant", r_result), ("Cafe & Bakery", c_result)]:
        f.write(f"## {label} Dataset\n")
        f.write(f"- Valid: {result['valid']}\n")
        f.write(f"- Rows:  {result['total_rows']}\n")
        f.write(f"- Range: {result['date_range']}\n")
        if result['issues']:
            f.write("\n### Issues:\n")
            for i in result['issues']:
                f.write(f"- {i}\n")
        f.write("\n")

print("\n Saved: validation_report.md")