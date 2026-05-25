import unittest

from app.services.finance.calculator import PreOpeningFinanceInput, calculate_pre_opening_finance


class PreOpeningFinanceCalculatorTest(unittest.TestCase):
    def test_live_table_formula(self) -> None:
        result = calculate_pre_opening_finance(
            PreOpeningFinanceInput(
                area_sqm=25,
                monthly_rent=6666,
                rent_payment_months=6,
                deposit=6666,
                decoration_and_ads=30000,
                first_batch_material=5000,
                monthly_labor=8000,
                monthly_utilities=2000,
                gross_margin_rate=55,
                estimated_average_ticket=20,
                target_payback_months=12,
                cash_available=150000,
            )
        )

        self.assertEqual(result.build_cost, 81662)
        self.assertEqual(result.daily_fixed_cost, 555.53)
        self.assertEqual(result.daily_breakeven, 1010.06)
        self.assertEqual(result.mode, "pre_opening")
        self.assertNotIn("breakeven_achievement_rate", result.to_dict())

    def test_target_order_count_and_cash_gap(self) -> None:
        result = calculate_pre_opening_finance(
            PreOpeningFinanceInput(
                monthly_rent=15000,
                rent_payment_months=1,
                deposit=30000,
                transfer_fee=225000,
                first_batch_material=10000,
                monthly_labor=26000,
                monthly_utilities=5000,
                gross_margin_rate=60,
                estimated_average_ticket=68,
                target_payback_months=12,
                cash_available=280000,
            )
        )

        self.assertEqual(result.build_cost, 280000)
        self.assertEqual(result.daily_breakeven, 2555.56)
        self.assertEqual(result.target_daily_revenue, 3851.85)
        self.assertEqual(result.finance_status, "finance_do_not_open")
        self.assertIn("cash_below_3m_reserve", result.risk_flags)


if __name__ == "__main__":
    unittest.main()

