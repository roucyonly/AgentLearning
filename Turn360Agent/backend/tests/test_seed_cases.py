import unittest

from app.services.cases.repository import CaseRepository


class SeedCasesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = CaseRepository()

    def test_seed_cases_parse(self) -> None:
        cases = self.repo.list_cases()
        self.assertEqual(len(cases), 3)

    def test_takeover_case_finance_indicators(self) -> None:
        case = self.repo.get_case("yg_seed_003_takeover_unverified_claims")
        self.assertIsNotNone(case)
        finance = case["finance_indicators"]

        self.assertEqual(finance["build_cost_table"]["value"], 280000)
        self.assertEqual(finance["daily_breakeven"]["value"], 2555.56)
        self.assertEqual(finance["target_daily_revenue_12m_payback"]["value"], 3851.85)
        self.assertEqual(case["location_indicators"]["business_district_status"], "过期商圈")

    def test_case_summaries(self) -> None:
        summaries = self.repo.list_case_summaries()
        self.assertEqual(summaries[0]["case_usage"], "reverse_pre_opening_risk_case")
        self.assertIn("risk_flags", summaries[1])


if __name__ == "__main__":
    unittest.main()

