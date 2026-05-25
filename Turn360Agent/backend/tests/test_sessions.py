import os
import unittest

os.environ.pop("OPENAI_API_KEY", None)

from app.services.decision.pre_opening import PreOpeningEvaluationInput
from app.services.finance.calculator import PreOpeningFinanceInput
from app.services.llm.guided_agent import LLMGuidedTurn
from app.services.session.store import SessionStore, build_session_view, stream_events_for_view


class SessionStoreTest(unittest.TestCase):
    def test_user_view_hides_private_debug_slots_and_events(self) -> None:
        store = SessionStore()
        record = store.create_pre_opening()

        view = build_session_view(record, "user")

        self.assertEqual(view["scenario"], "pre_opening")
        self.assertEqual(view["evaluation"]["session_id"], record.session_id)
        self.assertTrue(view["visible_slots"])
        self.assertNotIn("hidden_slots", view)
        self.assertTrue(all(slot["visibility"] != "private_debug" for slot in view["visible_slots"]))
        self.assertTrue(all(event["sessionId"] == record.session_id for event in view["events"]))
        self.assertTrue(all(event["visibility"] != "private_debug" for event in view["events"]))

    def test_debug_view_contains_hidden_assessment_slots(self) -> None:
        store = SessionStore()
        record = store.create_pre_opening()

        view = build_session_view(record, "debug")

        hidden_ids = {slot["id"] for slot in view["hidden_slots"]}
        self.assertIn("founder_expression_score", hidden_ids)
        self.assertIn("founder_location_bias_score", hidden_ids)
        self.assertGreater(view["debug_summary"]["private_event_count"], 0)
        self.assertTrue(any(event["type"] == "hidden.patch" for event in view["events"]))

    def test_update_session_recalculates_same_session_id(self) -> None:
        store = SessionStore()
        record = store.create_pre_opening()
        updated = store.update_pre_opening(
            record.session_id,
            PreOpeningEvaluationInput(
                session_id="ignored-by-store",
                finance=PreOpeningFinanceInput(
                    monthly_rent=8000,
                    monthly_labor=6000,
                    monthly_utilities=1500,
                    gross_margin_rate=60,
                    estimated_average_ticket=25,
                    rent_payment_months=3,
                    deposit=8000,
                    decoration_and_ads=15000,
                    first_batch_material=4000,
                    cash_available=120000,
                ),
                location={
                    "city": "南京",
                    "address_text": "社区底商",
                    "target_customer_flow_30min": 120,
                    "comparable_store_orders_per_day": 120,
                    "evidence_level": "field_research",
                },
                category={"category_name": "米饭快餐"},
            ),
        )

        self.assertEqual(updated.session_id, record.session_id)
        self.assertEqual(updated.evaluation["session_id"], record.session_id)
        self.assertEqual(updated.evaluation["finance"]["daily_breakeven"], 861.11)

    def test_stream_events_filter_private_debug_for_user(self) -> None:
        store = SessionStore()
        record = store.create_pre_opening()

        user_events = stream_events_for_view(record, "user")
        debug_events = stream_events_for_view(record, "debug")

        self.assertLess(len(user_events), len(debug_events))
        self.assertFalse(any(event["visibility"] == "private_debug" for event in user_events))

    def test_patch_slots_recalculates_session(self) -> None:
        store = SessionStore()
        record = store.create_pre_opening()

        patched = store.patch_pre_opening_slots(
            record.session_id,
            {
                "monthly_rent": 12000,
                "monthly_labor": 7000,
                "gross_margin_rate": 60,
                "storefront_flow_30min": 24,
                "category_name": "咖啡",
            },
        )
        user_view = build_session_view(patched, "user")
        slot_values = {slot["id"]: slot["value"] for slot in user_view["visible_slots"]}

        self.assertEqual(patched.session_id, record.session_id)
        self.assertEqual(patched.evaluation["finance"]["monthly_fixed_cost"], 21000)
        self.assertEqual(patched.evaluation["finance"]["daily_breakeven"], 1166.67)
        self.assertEqual(patched.evaluation["location"]["target_customer_flow_30min"], 24)
        self.assertEqual(patched.evaluation["category"]["name"], "咖啡")
        self.assertEqual(slot_values["monthly_rent"], 12000)

    def test_patch_slots_rejects_unknown_slot(self) -> None:
        store = SessionStore()
        record = store.create_pre_opening()

        with self.assertRaises(ValueError):
            store.patch_pre_opening_slots(record.session_id, {"made_up_slot": 1})

    def test_chat_message_extracts_slots_and_keeps_flow(self) -> None:
        store = SessionStore()
        record = store.create_pre_opening()

        updated = store.handle_chat_message(
            record.session_id,
            "我想在南京开咖啡店，房租12000，人工7000，毛利率60，客单价25，门前30分钟20人，同类店订单80单",
        )
        view = build_session_view(updated, "user")

        self.assertEqual(updated.evaluation["location"]["city"], "南京")
        self.assertEqual(updated.evaluation["category"]["name"], "咖啡")
        self.assertEqual(updated.evaluation["finance"]["monthly_fixed_cost"], 21000)
        self.assertEqual(updated.evaluation["finance"]["daily_breakeven"], 1166.67)
        self.assertEqual(updated.evaluation["location"]["target_customer_flow_30min"], 20)
        self.assertEqual(updated.messages[-2]["role"], "user")
        self.assertEqual(updated.messages[-1]["role"], "assistant")
        self.assertIn("日盈亏平衡点", updated.messages[-1]["content"])
        self.assertIn("current_question", view)
        debug_view = build_session_view(updated, "debug")
        self.assertTrue(any(event["type"] == "llm.disabled" for event in debug_view["events"]))

    def test_chat_message_uses_llm_slots_when_available(self) -> None:
        store = SessionStore(guided_agent=FakeGuidedAgent())
        record = store.create_pre_opening()

        updated = store.handle_chat_message(record.session_id, "我想做社区早餐，人流挺好")
        debug_view = build_session_view(updated, "debug")

        self.assertEqual(updated.evaluation["location"]["city"], "杭州")
        self.assertEqual(updated.evaluation["category"]["name"], "早餐")
        self.assertEqual(updated.evaluation["finance"]["monthly_fixed_cost"], 18000)
        self.assertIn("先别只说人流好", updated.messages[-1]["content"])
        self.assertTrue(any(event["type"] == "llm.completed" for event in debug_view["events"]))


if __name__ == "__main__":
    unittest.main()


class FakeGuidedAgent:
    is_configured = True

    def run(self, **_: object) -> LLMGuidedTurn:
        return LLMGuidedTurn(
            slot_updates={
                "city": "杭州",
                "category_name": "早餐",
                "monthly_rent": 9000,
                "monthly_labor": 7000,
                "monthly_utilities": 2000,
            },
            assistant_reply="先别只说人流好，我先把你说出来的硬数字放进表里。",
            next_question="你在门口数 30 分钟，目标客群到底有多少人？",
            debug={"llm_provider": "fake"},
        )
