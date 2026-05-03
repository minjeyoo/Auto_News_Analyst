from datetime import date
import unittest

from eval_harness import evaluate_predictions
from domain_types import (
    Direction,
    InsightPrediction,
    PricePoint,
)


class EvaluatePredictionsTest(unittest.TestCase):
    def test_scores_hit_rate_and_virtual_return_for_long_and_short_calls(self):
        predictions = [
            InsightPrediction("AAPL", date(2026, 4, 26), 0.8, 0.9, "positive guide"),
            InsightPrediction("TSLA", date(2026, 4, 26), -0.7, 0.8, "margin pressure"),
        ]
        prices = {
            "AAPL": [
                PricePoint("AAPL", date(2026, 4, 27), 100.0),
                PricePoint("AAPL", date(2026, 5, 3), 110.0),
            ],
            "TSLA": [
                PricePoint("TSLA", date(2026, 4, 27), 200.0),
                PricePoint("TSLA", date(2026, 5, 3), 180.0),
            ],
        }

        result = evaluate_predictions(
            predictions=predictions,
            prices_by_ticker=prices,
            run_id="test",
            forecast_start=date(2026, 4, 26),
            forecast_end=date(2026, 5, 3),
            transaction_cost=0.001,
            min_evaluated_count=1,
        )

        self.assertEqual(result.evaluated_count, 2)
        self.assertEqual(result.hit_rate, 1.0)
        self.assertAlmostEqual(result.virtual_return, 0.099)
        self.assertAlmostEqual(result.benchmark_return, 0.0)
        self.assertGreater(result.composite_score, result.hit_rate * 0.35)
        self.assertEqual(result.long_count, 1)
        self.assertEqual(result.short_count, 1)

    def test_skips_missing_price_data(self):
        predictions = [
            InsightPrediction("NVDA", date(2026, 4, 26), 0.5, 0.7, "data center demand"),
        ]

        result = evaluate_predictions(
            predictions=predictions,
            prices_by_ticker={},
            run_id="test",
            forecast_start=date(2026, 4, 26),
            forecast_end=date(2026, 5, 3),
            min_evaluated_count=1,
        )

        self.assertEqual(result.evaluated_count, 0)
        self.assertEqual(result.skipped_count, 1)
        self.assertEqual(result.details[0].skipped_reason, "missing price data")

    def test_flags_future_dated_predictions_as_leakage_error(self):
        predictions = [
            InsightPrediction("MSFT", date(2026, 4, 28), 0.5, 0.6, "future leak"),
        ]

        result = evaluate_predictions(
            predictions=predictions,
            prices_by_ticker={},
            run_id="test",
            forecast_start=date(2026, 4, 26),
            forecast_end=date(2026, 5, 3),
            min_evaluated_count=1,
        )

        self.assertEqual(result.evaluated_count, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("future as_of_date", result.errors[0])

    def test_neutral_predictions_are_not_counted_in_hit_rate(self):
        predictions = [
            InsightPrediction("GOOGL", date(2026, 4, 26), 0.05, 0.5, "mixed"),
        ]
        prices = {
            "GOOGL": [
                PricePoint("GOOGL", date(2026, 4, 27), 100.0),
                PricePoint("GOOGL", date(2026, 5, 3), 120.0),
            ],
        }

        result = evaluate_predictions(
            predictions=predictions,
            prices_by_ticker=prices,
            run_id="test",
            forecast_start=date(2026, 4, 26),
            forecast_end=date(2026, 5, 3),
            min_evaluated_count=1,
        )

        self.assertEqual(result.evaluated_count, 0)
        self.assertEqual(result.neutral_count, 1)
        self.assertEqual(result.details[0].predicted_direction, Direction.NEUTRAL)


if __name__ == "__main__":
    unittest.main()
