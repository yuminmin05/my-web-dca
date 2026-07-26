from decimal import Decimal
from django.test import TestCase

from .services import build_dca_projection, normalize_selected_stocks


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
