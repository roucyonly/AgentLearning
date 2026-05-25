from dataclasses import dataclass, field
from typing import Any, Protocol

from app.services.decision.pre_opening import PreOpeningEvaluationInput
from app.services.llm.provider_factory import load_llm_client


ALLOWED_SLOT_IDS = [
    "area_sqm",
    "monthly_rent",
    "rent_payment_months",
    "deposit",
    "transfer_fee",
    "franchise_or_training_fee",
    "decoration_and_ads",
    "equipment",
    "first_batch_material",
    "monthly_labor",
    "monthly_utilities",
    "monthly_fixed_operation_cost",
    "monthly_campaign_cost",
    "gross_margin_rate",
    "average_ticket",
    "cash_available",
    "debt_monthly_payment",
    "city",
    "district",
    "address_text",
    "longitude",
    "latitude",
    "floor",
    "storefront_flow_30min",
    "comparable_orders",
    "category_name",
]


class JsonLLMClient(Protocol):
    @property
    def is_configured(self) -> bool:
        ...

    @property
    def provider_name(self) -> str:
        ...

    def create_json_response(self, *, input_messages: list[dict[str, str]], json_schema: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class LLMGuidedTurn:
    slot_updates: dict[str, Any] = field(default_factory=dict)
    assistant_reply: str = ""
    next_question: str = ""
    intent: str = "pre_opening"
    debug: dict[str, Any] = field(default_factory=dict)


class GuidedAgentLLM:
    def __init__(self, client: JsonLLMClient | None = None) -> None:
        self.client = client or load_llm_client()

    @property
    def is_configured(self) -> bool:
        return self.client.is_configured

    def run(self, *, record_input: PreOpeningEvaluationInput, messages: list[dict[str, Any]], user_message: str) -> LLMGuidedTurn | None:
        if not self.is_configured:
            return None

        response = self.client.create_json_response(
            input_messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_context(record_input, messages, user_message)},
            ],
            json_schema=TURN_SCHEMA,
        )
        return parse_guided_turn(response, provider_name=getattr(self.client, "provider_name", "unknown"))


def parse_guided_turn(response: dict[str, Any], provider_name: str = "unknown") -> LLMGuidedTurn:
    raw_slots = response.get("slot_updates", [])
    updates: dict[str, Any] = {}
    if isinstance(raw_slots, list):
        for item in raw_slots:
            if not isinstance(item, dict):
                continue
            slot_id = item.get("id")
            if slot_id not in ALLOWED_SLOT_IDS:
                continue
            updates[slot_id] = item.get("value")

    return LLMGuidedTurn(
        slot_updates=updates,
        assistant_reply=str(response.get("assistant_reply") or "").strip(),
        next_question=str(response.get("next_question") or "").strip(),
        intent=str(response.get("intent") or "pre_opening"),
        debug={
            "llm_provider": provider_name,
            "llm_slot_count": len(updates),
            "needs_more_data": bool(response.get("needs_more_data")),
        },
    )


def build_user_context(record_input: PreOpeningEvaluationInput, messages: list[dict[str, Any]], user_message: str) -> str:
    recent_messages = [
        {"role": item.get("role"), "content": item.get("content")}
        for item in messages[-8:]
        if item.get("visibility") != "private_debug"
    ]
    context = {
        "current_structured_input": {
            "finance": record_input.finance.__dict__,
            "location": record_input.location,
            "category": record_input.category,
        },
        "recent_messages": recent_messages,
        "latest_user_message": user_message,
        "allowed_slot_ids": ALLOWED_SLOT_IDS,
    }
    return str(context)


SYSTEM_PROMPT = """
You are the language layer for a Chinese restaurant entrepreneurship agent.
You do not make the final business verdict. Finance, location, category, and
decision engines make the verdict after structured slots are updated.

Your job:
1. Extract only explicitly stated facts from the latest user message.
2. Map them to allowed slot IDs.
3. Ask the next useful question in Chinese.
4. Write a short Chinese assistant reply with a direct, practical tone inspired
   by public restaurant-coaching livestreams, without claiming to be any real
   creator.

Hard rules:
- Do not invent numbers, addresses, category, or user capability.
- Do not flatter or discourage by default. Stay neutral and loyal to data.
- Do not reveal hidden scoring or internal debug fields to the user.
- If a value is uncertain, do not extract it.
- If the user says only feelings such as "人流很好", ask for measurable field
  research: 30-minute target-customer count or comparable-store orders.
"""


TURN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["intent", "slot_updates", "assistant_reply", "next_question", "needs_more_data"],
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["pre_opening", "loss_rescue", "growth", "unknown"],
        },
        "slot_updates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "value", "confidence"],
                "properties": {
                    "id": {"type": "string", "enum": ALLOWED_SLOT_IDS},
                    "value": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "number"},
                            {"type": "integer"},
                            {"type": "null"},
                        ]
                    },
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
            },
        },
        "assistant_reply": {"type": "string"},
        "next_question": {"type": "string"},
        "needs_more_data": {"type": "boolean"},
    },
}
