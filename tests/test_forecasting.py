import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path
from forecasting import CSVEmploymentSource, EmploymentObservation, ExponentialSmoothingForecaster


class MemorySource:
    def __init__(self, levels):
        self.levels = levels

    def monthly_series(self, breakdown, category):
        return [EmploymentObservation(date(2023, i + 1, 1), v) for i, v in enumerate(self.levels)]


class ForecastTests(unittest.TestCase):
    def test_forecast_is_change_not_level_and_rolls_year(self):
        source = MemorySource([100 + i * 10 for i in range(12)])
        result = ExponentialSmoothingForecaster(source).forecast()
        self.assertEqual(result.predicted_change, 10)
        self.assertEqual(result.predicted_employment, 220)
        self.assertEqual(result.target_month, date(2024, 1, 1))

    def test_as_of_cannot_see_future(self):
        model = ExponentialSmoothingForecaster(MemorySource([100, 110, 130, 999999]), alpha=0.5)
        result = model.forecast(as_of=date(2023, 3, 1))
        self.assertEqual(result.predicted_change, 15)
        self.assertEqual(result.predicted_employment, 145)

    def test_backtest_predicts_before_updating_and_excludes_scores_only(self):
        model = ExponentialSmoothingForecaster(MemorySource([100, 110, 130, 170]), alpha=0.5)
        result = model.backtest(min_training_months=2, excluded_periods=[(date(2023, 3, 1), date(2023, 3, 1))])
        self.assertEqual(result.predictions[0].predicted_change, 15)
        self.assertEqual(result.predictions[0].actual_change, 40)
        self.assertEqual(result.mae, 25)
        self.assertEqual(result.bias, -25)
        self.assertEqual(result.excluded_targets, (date(2023, 3, 1),))

    def test_rejects_bad_alpha_and_invalid_series(self):
        for alpha in [0, -1, 1.1, float('nan')]:
            with self.assertRaises(ValueError):
                ExponentialSmoothingForecaster(alpha=alpha)
        with self.assertRaises(ValueError):
            ExponentialSmoothingForecaster(MemorySource([100])).forecast()
        with self.assertRaises(ValueError):
            ExponentialSmoothingForecaster(MemorySource([100, float('nan')])).forecast()
        class GapSource:
            def monthly_series(self, *args):
                return [EmploymentObservation(date(2023, 1, 1), 100), EmploymentObservation(date(2023, 3, 1), 110)]
        with self.assertRaises(ValueError):
            ExponentialSmoothingForecaster(GapSource()).forecast()

    def test_csv_filters_frequency_category_and_uses_adjusted_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.csv'
            path.write_text('timestep,agg_RIS,category,date,NER,NER_SA\nM,National,U.S.,2023-02-01,900,120\nW,National,U.S.,2023-01-07,900,999\nM,Industry,Information,2023-01-01,900,999\nM,National,U.S.,2023-01-01,900,100\n')
            result = ExponentialSmoothingForecaster(CSVEmploymentSource(path)).forecast()
            self.assertEqual(result.predicted_change, 20)
            self.assertEqual(result.predicted_employment, 140)


if __name__ == '__main__':
    unittest.main()
