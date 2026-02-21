# tests.py
# Run: python -m pytest tests.py -v
# Or:  python tests.py

import os
import sys
import unittest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forecasting import predict_7_days
from validation import validate_csv_upload


def predict_day1(date, item, biz, weather, holiday, price, shelf):
    fc = predict_7_days(
        item_name=item, business_type=biz, price=price, shelf_life_hours=shelf,
        starting_date=date, weather_forecast=[weather] * 7,
        holiday_flags=[holiday] + [0] * 6,
    )
    return fc[0]


def detect_waste_risk(predicted_demand, planned_quantity):
    if planned_quantity == 0:
        return {'risk_level': 'LOW', 'waste_percentage': 0.0, 'expected_waste': 0}
    waste_pct      = ((planned_quantity - predicted_demand) / planned_quantity) * 100
    expected_waste = max(0, planned_quantity - predicted_demand)
    risk_level     = 'HIGH' if waste_pct > 15 else 'MEDIUM' if waste_pct > 5 else 'LOW'
    return {'risk_level': risk_level, 'waste_percentage': round(waste_pct, 2), 'expected_waste': int(expected_waste)}


def generate_recommendation(predicted_demand, current_plan):
    recommended = round(predicted_demand * 1.05)
    diff        = recommended - current_plan
    if diff < -5:
        action = f'REDUCE by {abs(diff)} units'
    elif diff > 5:
        action = f'INCREASE by {diff} units'
    else:
        action = 'MAINTAIN current plan'
    return {'recommended_quantity': recommended, 'action': action}


class TestPredictions(unittest.TestCase):

    def test_prediction_non_negative(self):
        r = predict_day1('2025-12-01', 'Jollof Rice', 'Restaurant', 'Clear', 0, 50, 4)
        self.assertGreaterEqual(r['predicted_demand'], 0)

    def test_restaurant_weekend_higher(self):
        weekday = predict_day1('2025-12-01', 'Jollof Rice', 'Restaurant', 'Clear', 0, 50, 4)
        weekend = predict_day1('2025-12-06', 'Jollof Rice', 'Restaurant', 'Clear', 0, 50, 4)
        self.assertGreater(weekend['predicted_demand'], weekday['predicted_demand'])

    def test_cafe_weekday_higher(self):
        weekday = predict_day1('2025-12-01', 'Espresso', 'Cafe', 'Clear', 0, 25, 0.5)
        weekend = predict_day1('2025-12-06', 'Espresso', 'Cafe', 'Clear', 0, 25, 0.5)
        self.assertLess(weekend['predicted_demand'], weekday['predicted_demand'])

    def test_holiday_changes_demand(self):
        regular = predict_day1('2025-12-01', 'Jollof Rice', 'Restaurant', 'Clear', 0, 50, 4)
        holiday = predict_day1('2025-12-01', 'Jollof Rice', 'Restaurant', 'Clear', 1, 50, 4)
        self.assertNotEqual(regular['predicted_demand'], holiday['predicted_demand'])

    def test_confidence_valid(self):
        r = predict_day1('2025-12-01', 'Jollof Rice', 'Restaurant', 'Clear', 0, 50, 4)
        self.assertIn(r['confidence'], ['High', 'Medium', 'Low'])

    def test_recommended_has_buffer(self):
        r = predict_day1('2025-12-01', 'Jollof Rice', 'Restaurant', 'Clear', 0, 50, 4)
        self.assertGreaterEqual(r['recommended_quantity'], r['predicted_demand'])

    def test_new_item_works(self):
        r = predict_day1('2025-12-01', 'Fufu', 'Restaurant', 'Clear', 0, 45, 3)
        self.assertGreaterEqual(r['predicted_demand'], 0)
        self.assertTrue(r['is_new_item'])

    def test_all_business_types(self):
        cases = [
            ('Jollof Rice', 'Restaurant', 50, 4),
            ('Espresso',    'Cafe',       25, 0.5),
            ('Donuts',      'Bakery',     15, 12),
        ]
        for item, biz, price, shelf in cases:
            with self.subTest(business=biz):
                r = predict_day1('2025-12-01', item, biz, 'Clear', 0, price, shelf)
                self.assertGreaterEqual(r['predicted_demand'], 0)

    def test_7_days_returned(self):
        fc = predict_7_days('Jollof Rice', 'Restaurant', 50, 4, '2025-12-01', ['Clear'] * 7, [0] * 7)
        self.assertEqual(len(fc), 7)

    def test_confidence_degrades(self):
        fc     = predict_7_days('Jollof Rice', 'Restaurant', 50, 4, '2025-12-01', ['Clear'] * 7, [0] * 7)
        scores = [d['confidence_score'] for d in fc]
        self.assertGreater(scores[0], scores[-1])


class TestRiskDetection(unittest.TestCase):

    def test_high_risk(self):
        self.assertEqual(detect_waste_risk(40, 60)['risk_level'], 'HIGH')

    def test_medium_risk(self):
        self.assertEqual(detect_waste_risk(40, 45)['risk_level'], 'MEDIUM')

    def test_low_risk(self):
        self.assertEqual(detect_waste_risk(40, 42)['risk_level'], 'LOW')

    def test_waste_calculation(self):
        self.assertEqual(detect_waste_risk(40, 50)['expected_waste'], 10)

    def test_zero_planned(self):
        r = detect_waste_risk(40, 0)
        self.assertEqual(r['risk_level'], 'LOW')
        self.assertEqual(r['expected_waste'], 0)


class TestRecommendations(unittest.TestCase):

    def test_reduce(self):
        self.assertIn('REDUCE', generate_recommendation(40, 55)['action'])

    def test_increase(self):
        self.assertIn('INCREASE', generate_recommendation(50, 35)['action'])

    def test_maintain(self):
        self.assertIn('MAINTAIN', generate_recommendation(40, 42)['action'])

    def test_buffer_applied(self):
        self.assertEqual(generate_recommendation(40, 0)['recommended_quantity'], round(40 * 1.05))


class TestValidation(unittest.TestCase):

    def test_valid_passes(self):
        df = pd.DataFrame({
            'date': ['2025-06-01', '2025-06-02'],
            'item_name': ['Jollof Rice', 'Jollof Rice'],
            'quantity_sold': [40, 42],
            'quantity_available': [45, 45],
        })
        self.assertTrue(validate_csv_upload(df)['valid'])

    def test_missing_column_fails(self):
        df = pd.DataFrame({'date': ['2025-06-01'], 'item_name': ['Jollof Rice']})
        self.assertFalse(validate_csv_upload(df)['valid'])

    def test_negative_quantity_fails(self):
        df = pd.DataFrame({
            'date': ['2025-06-01'], 'item_name': ['Jollof Rice'], 'quantity_sold': [-5]
        })
        self.assertFalse(validate_csv_upload(df)['valid'])


if __name__ == '__main__':
    unittest.main(verbosity=2)