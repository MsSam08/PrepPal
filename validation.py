# validation.py
# Validates user-uploaded CSVs before retraining.
# Imported by retrain.py — no need to run this directly.

import pandas as pd


def validate_csv_upload(df: pd.DataFrame) -> dict:
    errors, warnings = [], []

    # Required columns
    required = ['date', 'item_name', 'quantity_sold']
    missing  = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")

    # Date format
    if 'date' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['date'])
        except (ValueError, TypeError):
            errors.append("Date column has invalid format — use YYYY-MM-DD")

    # Negative quantity_sold
    if 'quantity_sold' in df.columns:
        n = (df['quantity_sold'] < 0).sum()
        if n > 0:
            errors.append(f"Found {n} negative quantity_sold value(s)")

    # Business logic
    if all(c in df.columns for c in ['quantity_sold', 'quantity_available']):
        v = (df['quantity_sold'] > df['quantity_available']).sum()
        if v > 0:
            errors.append(f"{v} row(s) have quantity_sold > quantity_available")

    # Missing values (warning only)
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        warnings.append(f"Missing values: {dict(null_counts[null_counts > 0])}")

    return {
        'valid':    len(errors) == 0,
        'errors':   errors,
        'warnings': warnings,
        'rows':     len(df),
        'columns':  list(df.columns),
    }