from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from .models import GAResultSnapshot, UserPlan
from .optimizers import EqualWeightOptimizer, MeanVarianceOptimizer
from .services import build_dca_projection, build_saved_ga_summary, normalize_selected_stocks
from .tasks import optimize_portfolio_task


class PortfolioServiceTests(TestCase):
    def test_normalize_selected_stocks(self):
        cleaned = normalize_selected_stocks("ADVANC, AOT , CPALL ,")
        self.assertEqual(cleaned, ["ADVANC", "AOT", "CPALL"])

    def test_build_dca_projection(self):
        projection = build_dca_projection(
            monthly_investment=Decimal("1000"),
            duration_years=2,
            target_amount=Decimal("30000"),
            expected_return=0.12,
        )

        self.assertEqual(projection["duration_months"], 24)
        self.assertGreater(projection["final_portfolio_value"], 0)
        self.assertIn("chart_labels", projection)
        self.assertIn("chart_data", projection)

    def test_build_saved_ga_summary_requires_matching_stocks(self):
        user = User.objects.create_user(username="tester", password="secret")
        snapshot = GAResultSnapshot.objects.create(
            user=user,
            expected_return=0.14,
            sharpe_ratio=1.6,
            weights={"ADVANC": 0.6, "AOT": 0.4},
        )

        summary = build_saved_ga_summary(snapshot, ["ADVANC", "AOT"], current_return=12.5, current_sharpe=1.8)

        self.assertIsNotNone(summary)
        self.assertEqual(summary["expected_return"], 0.14)
        self.assertEqual(summary["allocations"][0]["name"], "ADVANC")
        self.assertEqual(summary["return_diff"], -1.5)

    def test_build_saved_ga_summary_returns_none_for_mismatched_stocks(self):
        user = User.objects.create_user(username="tester2", password="secret")
        snapshot = GAResultSnapshot.objects.create(
            user=user,
            expected_return=0.14,
            sharpe_ratio=1.6,
            weights={"ADVANC": 0.6, "AOT": 0.4},
        )

        summary = build_saved_ga_summary(snapshot, ["ADVANC", "CPALL"], current_return=12.5, current_sharpe=1.8)

        self.assertIsNone(summary)

    def test_optimize_portfolio_task_fallback_supports_delay(self):
        user = User.objects.create_user(username="taskuser", password="secret")
        plan = UserPlan.objects.create(user=user, selected_stocks="ADVANC")

        with patch('dashboard.ga_optimizer.run_genetic_algorithm', return_value={
            'expected_return': 0.1,
            'sharpe_ratio': 1.0,
            'weights': {'ADVANC': 1.0},
        }):
            result = optimize_portfolio_task.delay(plan.id)

        self.assertEqual(result, plan.id)

    def test_mean_variance_optimizer_falls_back_when_yfinance_fails(self):
        optimizer = MeanVarianceOptimizer()

        with patch('dashboard.optimizers.mean_variance.yf.download', side_effect=Exception('boom')):
            result = optimizer.optimize([type('StockRef', (), {'symbol': 'ADVANC'})()], target_amount=1000)

        self.assertEqual(result['weights'], {'ADVANC': 1.0})
        self.assertEqual(result['expected_return'], 0.0)
        self.assertEqual(result['sharpe_ratio'], 0.0)

    def test_equal_weight_optimizer_falls_back_when_yfinance_fails(self):
        optimizer = EqualWeightOptimizer()

        with patch('dashboard.optimizers.equal_weight.yf.download', side_effect=Exception('boom')):
            result = optimizer.optimize([type('StockRef', (), {'symbol': 'ADVANC'})()], target_amount=1000)

        self.assertEqual(result['weights'], {'ADVANC': 1.0})
        self.assertEqual(result['expected_return'], 0.0)
        self.assertEqual(result['sharpe_ratio'], 0.0)

    def test_optimizers_return_empty_weights_for_empty_stock_list(self):
        mean_variance = MeanVarianceOptimizer()
        equal_weight = EqualWeightOptimizer()

        self.assertEqual(mean_variance.optimize([], target_amount=1000)['weights'], {})
        self.assertEqual(equal_weight.optimize([], target_amount=1000)['weights'], {})
        self.assertEqual(mean_variance.optimize([], target_amount=1000)['expected_return'], 0.0)
        self.assertEqual(equal_weight.optimize([], target_amount=1000)['sharpe_ratio'], 0.0)
