import unittest
from src.features import FEATURE_COLUMNS, TARGET_COLUMN
from src.synthetic_data import generate_dataset

class SyntheticDataTests(unittest.TestCase):
    def test_generation_and_target_integrity(self):
        df = generate_dataset(n_patients=4, days=3, seed=7)
        self.assertEqual(df.patient_id.nunique(), 4)
        self.assertEqual(len(df), 4 * (3 * 24 - 2))
        self.assertTrue(set(df[TARGET_COLUMN].unique()).issubset({0, 1}))
        for _, g in df.groupby('patient_id'):
            g = g.sort_values('timestamp').reset_index(drop=True)
            for i in range(len(g) - 2):
                if g.loc[i, 'eligible_for_early_warning']:
                    expected = int(max(g.loc[i+1, 'current_glucose_mg_dl'], g.loc[i+2, 'current_glucose_mg_dl']) >= 180)
                    self.assertEqual(int(g.loc[i, TARGET_COLUMN]), expected)

    def test_no_future_label_or_future_glucose_in_features(self):
        self.assertNotIn(TARGET_COLUMN, FEATURE_COLUMNS)
        self.assertNotIn('future_2h_max_glucose_mg_dl', FEATURE_COLUMNS)
        self.assertIn('current_glucose_mg_dl', FEATURE_COLUMNS)

if __name__ == '__main__':
    unittest.main()
