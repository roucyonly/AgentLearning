import unittest

from app.services.decision.pre_opening import PreOpeningEvaluationInput, evaluate_pre_opening
from app.services.finance.calculator import PreOpeningFinanceInput


class PreOpeningDecisionTest(unittest.TestCase):
    def test_validate_first_when_location_evidence_missing(self) -> None:
        result = evaluate_pre_opening(
            PreOpeningEvaluationInput(
                session_id="test",
                finance=PreOpeningFinanceInput(
                    monthly_rent=6000,
                    rent_payment_months=3,
                    deposit=6000,
                    monthly_labor=8000,
                    monthly_utilities=2000,
                    gross_margin_rate=60,
                    estimated_average_ticket=28,
                    target_payback_months=12,
                    cash_available=120000,
                ),
                location={
                    "city": "上海",
                    "address_text": "测试铺位",
                    "evidence_level": "mock",
                },
                category={"category_name": "米饭快餐"},
            )
        )

        self.assertEqual(result["verdict"], "validate_first")
        self.assertIn("missing_storefront_flow", result["location"]["flags"])

    def test_can_open_when_finance_and_location_support(self) -> None:
        result = evaluate_pre_opening(
            PreOpeningEvaluationInput(
                session_id="test",
                finance=PreOpeningFinanceInput(
                    monthly_rent=4000,
                    rent_payment_months=3,
                    deposit=4000,
                    monthly_labor=6000,
                    monthly_utilities=1500,
                    gross_margin_rate=60,
                    estimated_average_ticket=35,
                    target_payback_months=12,
                    cash_available=100000,
                ),
                location={
                    "city": "成都",
                    "address_text": "测试铺位",
                    "target_customer_flow_30min": 80,
                    "comparable_store_orders_per_day": 120,
                    "evidence_level": "field_observed",
                },
                category={"category_name": "米饭快餐"},
            )
        )

        self.assertEqual(result["verdict"], "can_open")
        self.assertEqual(result["report"]["verdict"], "can_open")


if __name__ == "__main__":
    unittest.main()

