from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.services.decision.pre_opening import PreOpeningEvaluationInput, evaluate_pre_opening
from app.services.finance.calculator import PreOpeningFinanceInput


DEFAULT_PRE_OPENING_INPUT = PreOpeningEvaluationInput(
    session_id="demo-pre-opening",
    finance=PreOpeningFinanceInput(
        area_sqm=25,
        monthly_rent=6666,
        rent_payment_months=6,
        deposit=6666,
        transfer_fee=0,
        franchise_or_training_fee=0,
        decoration_and_ads=30000,
        equipment=0,
        first_batch_material=5000,
        monthly_labor=8000,
        monthly_utilities=2000,
        monthly_fixed_operation_cost=0,
        monthly_campaign_cost=0,
        gross_margin_rate=55,
        estimated_average_ticket=22,
        target_payback_months=12,
        cash_available=130000,
        debt_monthly_payment=0,
    ),
    location={
        "city": "上海",
        "district": "徐汇区",
        "address_text": "目标铺位门口",
        "target_customer_flow_30min": 90,
        "comparable_store_orders_per_day": 95,
        "evidence_level": "mock",
    },
    category={"category_name": "米饭快餐"},
)


@dataclass
class SessionRecord:
    session_id: str
    scenario: str
    created_at: str
    updated_at: str
    status: str
    input_payload: PreOpeningEvaluationInput
    evaluation: dict[str, Any]
    events: list[dict[str, Any]] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._records: dict[str, SessionRecord] = {}

    def create_pre_opening(self, payload: PreOpeningEvaluationInput | None = None) -> SessionRecord:
        input_payload = payload or DEFAULT_PRE_OPENING_INPUT
        session_id = input_payload.session_id if input_payload.session_id != "demo" else str(uuid4())
        input_payload = PreOpeningEvaluationInput(
            session_id=session_id,
            finance=input_payload.finance,
            location=input_payload.location,
            category=input_payload.category,
        )
        evaluation = evaluate_pre_opening(input_payload)
        now = utc_now()
        record = SessionRecord(
            session_id=session_id,
            scenario="pre_opening",
            created_at=now,
            updated_at=now,
            status="active",
            input_payload=input_payload,
            evaluation=evaluation,
            events=build_stream_events(evaluation),
        )
        self._records[session_id] = record
        return record

    def get(self, session_id: str) -> SessionRecord | None:
        return self._records.get(session_id)

    def update_pre_opening(self, session_id: str, payload: PreOpeningEvaluationInput) -> SessionRecord:
        if session_id not in self._records:
            raise KeyError(session_id)
        payload = PreOpeningEvaluationInput(
            session_id=session_id,
            finance=payload.finance,
            location=payload.location,
            category=payload.category,
        )
        evaluation = evaluate_pre_opening(payload)
        record = self._records[session_id]
        record.input_payload = payload
        record.evaluation = evaluation
        record.updated_at = utc_now()
        record.events = build_stream_events(evaluation)
        return record


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_session_view(record: SessionRecord, view: str) -> dict[str, Any]:
    if view not in {"user", "report", "debug", "admin"}:
        raise ValueError("view must be one of user, report, debug, admin")

    slots = build_slots(record)
    visible_slots = [
        slot
        for slot in slots
        if slot["visibility"] in {"public", "editable"}
        or (view == "report" and slot["visibility"] == "report_only")
    ]
    hidden_slots = [slot for slot in slots if slot["visibility"] == "private_debug"]
    public_events = [event for event in record.events if event["visibility"] != "private_debug"]

    response: dict[str, Any] = {
        "session_id": record.session_id,
        "scenario": record.scenario,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "view": view,
        "evaluation": record.evaluation,
        "visible_slots": visible_slots,
        "events": attach_session_id(public_events if view in {"user", "report"} else record.events, record.session_id),
    }

    if view in {"debug", "admin"}:
        response["hidden_slots"] = hidden_slots
        response["raw_input"] = serialize_input(record.input_payload)
        response["debug_summary"] = {
            "event_count": len(record.events),
            "visible_slot_count": len(visible_slots),
            "hidden_slot_count": len(hidden_slots),
            "private_event_count": len(record.events) - len(public_events),
        }

    if view == "admin":
        response["admin_summary"] = {
            "requires_human_review": record.evaluation["verdict"] != "can_open",
            "risk_flags": record.evaluation["finance"]["risk_flags"] + record.evaluation["location"]["flags"],
            "report_ready": True,
        }

    return response


def stream_events_for_view(record: SessionRecord, view: str) -> list[dict[str, Any]]:
    if view == "debug":
        return record.events
    return [event for event in record.events if event["visibility"] != "private_debug"]


def attach_session_id(events: list[dict[str, Any]], session_id: str) -> list[dict[str, Any]]:
    return [{"sessionId": session_id, **event} for event in events]


def build_slots(record: SessionRecord) -> list[dict[str, Any]]:
    finance_input = record.input_payload.finance
    location_input = record.input_payload.location
    category_input = record.input_payload.category
    evaluation = record.evaluation
    finance = evaluation["finance"]
    location = evaluation["location"]
    category = evaluation["category"]
    updated_at = record.updated_at

    editable = "editable"
    public = "public"
    private = "private_debug"

    slots = [
        slot("monthly_rent", "房租/月", finance_input.monthly_rent, "元", "finance", editable, "user_input", "low", True, updated_at),
        slot("monthly_labor", "人工/月", finance_input.monthly_labor, "元", "finance", editable, "user_input", "low", True, updated_at),
        slot("monthly_utilities", "水电杂费/月", finance_input.monthly_utilities, "元", "finance", editable, "user_input", "low", True, updated_at),
        slot("gross_margin_rate", "毛利率", finance_input.gross_margin_rate, "%", "finance", editable, "user_input", "low", True, updated_at),
        slot("average_ticket", "预估客单价", finance_input.estimated_average_ticket, "元", "finance", editable, "user_input", "low", True, updated_at),
        slot("build_cost", "建店成本", finance["build_cost"], "元", "finance", public, "system_calculated", "high", False, updated_at),
        slot("daily_breakeven", "日盈亏平衡点", finance["daily_breakeven"], "元/日", "finance", public, "system_calculated", "high", False, updated_at),
        slot("target_daily_revenue", "目标回本日销", finance["target_daily_revenue"], "元/日", "finance", public, "system_calculated", "high", False, updated_at),
        slot("target_order_count", "目标订单数", finance["target_order_count"], "单/日", "finance", public, "system_calculated", "high", False, updated_at),
        slot("cash_gap_3m", "3个月现金缺口", finance["cash_gap_3m"], "元", "finance", public, "system_calculated", "high", False, updated_at),
        slot("city", "城市", location["city"], None, "location", editable, "user_input", "low", True, updated_at),
        slot("address_text", "铺位地址", location["address_text"], None, "location", editable, "user_input", "low", True, updated_at),
        slot("longitude", "经度", location_input.get("longitude"), None, "location", editable, "device_location", "medium", True, updated_at),
        slot("latitude", "纬度", location_input.get("latitude"), None, "location", editable, "device_location", "medium", True, updated_at),
        slot("storefront_flow_30min", "门前30分钟目标客群", location["target_customer_flow_30min"], "人", "location", editable, "field_research", "medium", True, updated_at),
        slot("comparable_orders", "附近同类店日单量", location["comparable_store_orders_per_day"], "单/日", "location", editable, "field_research", "medium", True, updated_at),
        slot("location_score", "地址评分", location["score"], "分", "location", public, "system_calculated", "medium", False, updated_at),
        slot("category_name", "品类", category["name"], None, "category", editable, "user_input", "low", True, updated_at),
        slot("category_demand_type", "需求类型", category["demand_type"], None, "category", public, "category_catalog", "medium", False, updated_at),
        slot("founder_expression_score", "表达清晰度", None, "分", "founder", private, "conversation_analysis", "pending", False, updated_at),
        slot("founder_data_command_score", "数据掌握度", None, "分", "founder", private, "conversation_analysis", "pending", False, updated_at),
        slot("founder_execution_stability", "执行稳定性", None, "分", "founder", private, "conversation_analysis", "pending", False, updated_at),
        slot("founder_location_bias_score", "选址判断偏差", None, "分", "founder", private, "map_cross_check", "pending", False, updated_at),
    ]
    return slots


def slot(
    slot_id: str,
    label: str,
    value: Any,
    unit: str | None,
    group: str,
    visibility: str,
    source: str,
    confidence: str,
    editable: bool,
    updated_at: str,
) -> dict[str, Any]:
    return {
        "id": slot_id,
        "label": label,
        "value": value,
        "unit": unit,
        "group": group,
        "visibility": visibility,
        "source": source,
        "confidence": confidence,
        "editable": editable,
        "updated_at": updated_at,
    }


def build_stream_events(evaluation: dict[str, Any]) -> list[dict[str, Any]]:
    finance = evaluation["finance"]
    location = evaluation["location"]
    verdict = evaluation["verdict"]
    return [
        event("tool.started", "intent_router", "识别咨询场景：开店前地址评定 + 选品 + 算账", "public"),
        event("agent.path.patch", "finance", "先算账，建店成本、日平衡点和回本日销同时更新", "public"),
        event(
            "slot.patch",
            "finance",
            f"日盈亏平衡点 {finance['daily_breakeven']} 元，目标回本日销 {finance['target_daily_revenue']} 元",
            "public",
            {"slot_ids": ["daily_breakeven", "target_daily_revenue", "target_order_count"]},
        ),
        event("tool.completed", "finance", "财务目标线已生成", "public"),
        event("agent.path.patch", "location", "读取坐标/街边证据，等待真实地图 API 接入", "public"),
        event(
            "slot.patch",
            "location",
            f"地址评分 {location['score']}，证据级别 {location['evidence_level']}",
            "public",
            {"slot_ids": ["location_score"]},
        ),
        event(
            "hidden.patch",
            "founder_capability",
            "内部经营者能力槽位已建立，沟通过程不向用户展示原始分",
            "private_debug",
            {"slot_ids": ["founder_expression_score", "founder_execution_stability", "founder_location_bias_score"]},
        ),
        event("card.patch", "report", f"生成阶段性结论：{verdict}", "public"),
        event("message.done", "report", evaluation["report"]["executive_summary"], "public"),
    ]


def event(
    event_type: str,
    step: str,
    message: str,
    visibility: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": event_type,
        "step": step,
        "message": message,
        "visibility": visibility,
        "payload": payload or {},
    }


def serialize_input(payload: PreOpeningEvaluationInput) -> dict[str, Any]:
    return {
        "session_id": payload.session_id,
        "finance": payload.finance.__dict__,
        "location": payload.location,
        "category": payload.category,
    }
