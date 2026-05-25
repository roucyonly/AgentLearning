import json
import unittest

from app.services.llm.guided_agent import GuidedAgentLLM
from app.services.llm.openai_responses import extract_response_text


class OpenAIResponsesTest(unittest.TestCase):
    def test_extract_response_text_from_responses_output(self) -> None:
        body = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps({"assistant_reply": "ok"}),
                        }
                    ],
                }
            ]
        }

        self.assertEqual(extract_response_text(body), '{"assistant_reply": "ok"}')

    def test_guided_agent_returns_none_without_api_key(self) -> None:
        agent = GuidedAgentLLM(client=UnconfiguredClient())

        self.assertIsNone(agent.run(record_input=DummyRecordInput(), messages=[], user_message="我要开店"))


class UnconfiguredClient:
    @property
    def is_configured(self) -> bool:
        return False

    def create_json_response(self, **_: object) -> dict:
        raise AssertionError("should not call API without configuration")


class DummyFinance:
    monthly_rent = 0
    monthly_labor = 0
    monthly_utilities = 0
    gross_margin_rate = 0
    estimated_average_ticket = 0

    @property
    def __dict__(self) -> dict:
        return {}


class DummyRecordInput:
    finance = DummyFinance()
    location: dict = {}
    category: dict = {}


if __name__ == "__main__":
    unittest.main()
