import re
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.services.decision.pre_opening import PreOpeningEvaluationInput, evaluate_pre_opening
from app.services.finance.calculator import PreOpeningFinanceInput


FINANCE_SLOT_FIELDS = {
    "area_sqm": "area_sqm",
    "monthly_rent": "monthly_rent",
    "rent_payment_months": "rent_payment_months",
    "deposit": "deposit",
    "transfer_fee": "transfer_fee",
    "franchise_or_training_fee": "franchise_or_training_fee",
    "decoration_and_ads": "decoration_and_ads",
    "equipment": "equipment",
    "first_batch_material": "first_batch_material",
    "monthly_labor": "monthly_labor",
    "monthly_utilities": "monthly_utilities",
    "monthly_fixed_operation_cost": "monthly_fixed_operation_cost",
    "monthly_campaign_cost": "monthly_campaign_cost",
    "gross_margin_rate": "gross_margin_rate",
    "average_ticket": "estimated_average_ticket",
    "target_payback_months": "target_payback_months",
    "cash_available": "cash_available",
    "debt_monthly_payment": "debt_monthly_payment",
}

INTEGER_FINANCE_FIELDS = {"rent_payment_months", "target_payback_months"}
OPTIONAL_FINANCE_FIELDS = {"area_sqm", "cash_available", "effective_gross_margin_rate"}

LOCATION_SLOT_FIELDS = {
    "city": "city",
    "district": "district",
    "address_text": "address_text",
    "longitude": "longitude",
    "latitude": "latitude",
    "floor": "floor",
    "storefront_flow_30min": "target_customer_flow_30min",
    "comparable_orders": "comparable_store_orders_per_day",
    "evidence_level": "evidence_level",
}

INTEGER_LOCATION_FIELDS = {"target_customer_flow_30min", "comparable_store_orders_per_day"}
NUMERIC_LOCATION_FIELDS = {"longitude", "latitude", "target_customer_flow_30min", "comparable_store_orders_per_day"}

CATEGORY_SLOT_FIELDS = {"category_name": "category_name", "category_demand_type": "demand_type"}

CATEGORY_KEYWORDS = [
    "米饭快餐",
    "快餐",
    "咖啡",
    "奶茶",
    "饮品",
    "小吃",
    "早餐",
    "面馆",
    "粉面",
    "融合菜",
    "火锅",
    "烧烤",
    "烘焙",
]

CITY_KEYWORDS = [
    "北京",
    "上海",
    "广州",
    "深圳",
    "重庆",
    "成都",
    "杭州",
    "南京",
    "武汉",
    "长沙",
    "西安",
    "南昌",
    "黔江",
    "苏州",
    "无锡",
    "合肥",
]


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
    messages: list[dict[str, Any]] = field(default_factory=list)


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
            messages=initial_messages(now),
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

    def patch_pre_opening_slots(self, session_id: str, updates: dict[str, Any]) -> SessionRecord:
        record = self.get(session_id)
        if record is None:
            raise KeyError(session_id)

        finance_changes: dict[str, Any] = {}
        location_changes = dict(record.input_payload.location)
        category_changes = dict(record.input_payload.category)

        for slot_id, value in updates.items():
            if slot_id in FINANCE_SLOT_FIELDS:
                field_name = FINANCE_SLOT_FIELDS[slot_id]
                finance_changes[field_name] = coerce_finance_value(field_name, value)
            elif slot_id in LOCATION_SLOT_FIELDS:
                field_name = LOCATION_SLOT_FIELDS[slot_id]
                location_changes[field_name] = coerce_location_value(field_name, value)
            elif slot_id in CATEGORY_SLOT_FIELDS:
                field_name = CATEGORY_SLOT_FIELDS[slot_id]
                category_changes[field_name] = coerce_text(value, slot_id)
            else:
                raise ValueError(f"unsupported slot id: {slot_id}")

        patched_payload = PreOpeningEvaluationInput(
            session_id=session_id,
            finance=replace(record.input_payload.finance, **finance_changes),
            location=location_changes,
            category=category_changes,
        )
        return self.update_pre_opening(session_id, patched_payload)

    def handle_chat_message(self, session_id: str, message: str) -> SessionRecord:
        record = self.get(session_id)
        if record is None:
            raise KeyError(session_id)
        text = message.strip()
        if not text:
            raise ValueError("message must not be empty")

        now = utc_now()
        record.messages.append(
            {
                "role": "user",
                "content": text,
                "created_at": now,
                "visibility": "public",
                "slot_updates": [],
            }
        )

        updates = extract_slot_updates(text)
        if updates:
            record = self.patch_pre_opening_slots(session_id, updates)
            reply = build_chat_reply(record, updates)
        else:
            reply = "我先没抓到能直接算账的数字。你按这句回我就行：城市、位置、品类、房租、人工、毛利率、客单价。"

        record.messages.append(
            {
                "role": "assistant",
                "content": reply,
                "created_at": utc_now(),
                "visibility": "public",
                "slot_updates": list(updates.keys()),
            }
        )
        return record


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def initial_messages(created_at: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "assistant",
            "content": "你要开店，先别急着看感觉。你直接告诉我：在哪个城市/位置，想做什么品类，房租、人工、毛利率、客单价大概多少。我边听边把账算出来。",
            "created_at": created_at,
            "visibility": "public",
            "slot_updates": [],
        }
    ]


def extract_slot_updates(text: str) -> dict[str, Any]:
    updates: dict[str, Any] = {}

    numeric_patterns = [
        ("monthly_rent", r"(?:房租|租金)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("monthly_labor", r"(?:人工|人力|员工工资)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("monthly_utilities", r"(?:水电|杂费|水电杂费)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("gross_margin_rate", r"(?:毛利率|毛利)[^\d]*(\d+(?:\.\d+)?)(%|％)?"),
        ("average_ticket", r"(?:客单价|客单)[^\d]*(\d+(?:\.\d+)?)(元|块)?"),
        ("cash_available", r"(?:现金|资金|预算|准备投|手里)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("area_sqm", r"(?:面积|平方)[^\d]*(\d+(?:\.\d+)?)(平|平方|㎡)?"),
        ("deposit", r"(?:押金)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("transfer_fee", r"(?:转让费|中介费)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("franchise_or_training_fee", r"(?:加盟费|学习费|技术费)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("decoration_and_ads", r"(?:装修|广告)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("equipment", r"(?:设备)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("first_batch_material", r"(?:首批物料|物料|食材)[^\d]*(\d+(?:\.\d+)?)(万|w|W|元|块)?"),
        ("storefront_flow_30min", r"(?:门前|人流|目标客群)[^\d]*(\d+(?:\.\d+)?)(人)?"),
        ("comparable_orders", r"(?:同类店|附近店|竞品|日单|订单)[^\d]*(\d+(?:\.\d+)?)(单)?"),
    ]
    for slot_id, pattern in numeric_patterns:
        match = re.search(pattern, text)
        if match:
            updates[slot_id] = amount_from_match(match)

    flow_match = re.search(r"(?:门前|人流|目标客群)[^\d]*30\s*分钟[^\d]*(\d+(?:\.\d+)?)", text)
    if flow_match:
        updates["storefront_flow_30min"] = float(flow_match.group(1))

    for city in CITY_KEYWORDS:
        if city in text:
            updates["city"] = city
            break

    address_match = re.search(r"(?:位置|地址|铺位|店址)(?:是|在|：|:)?([^，。,\n]{2,24})", text)
    if address_match:
        updates["address_text"] = address_match.group(1).strip()

    for keyword in CATEGORY_KEYWORDS:
        if keyword in text:
            updates["category_name"] = normalize_category(keyword)
            break

    return updates


def amount_from_match(match: re.Match[str]) -> float:
    value = float(match.group(1))
    unit = match.group(2) if match.lastindex and match.lastindex >= 2 else None
    if unit in {"万", "w", "W"}:
        value *= 10000
    return value


def normalize_category(keyword: str) -> str:
    if keyword == "快餐":
        return "米饭快餐"
    return keyword


def build_chat_reply(record: SessionRecord, updates: dict[str, Any]) -> str:
    result = record.evaluation
    captured = "、".join(slot_label(slot_id) for slot_id in updates)
    question = next_question(record)
    return (
        f"我抓到了：{captured}。现在日盈亏平衡点是 {result['finance']['daily_breakeven']} 元，"
        f"目标回本日销是 {result['finance']['target_daily_revenue']} 元，地址分 {result['location']['score']}。"
        f"{question}"
    )


def next_question(record: SessionRecord) -> str:
    payload = record.input_payload
    location = payload.location
    finance = payload.finance
    category_name = payload.category.get("category_name")

    if not location.get("city") or location.get("city") in {"unknown", "待确认"}:
        return "先告诉我城市和具体铺位位置，别只说人流不错。"
    if not category_name or category_name in {"unknown", "待确认品类"}:
        return "你准备做什么品类？喝的、小吃、米面主食，还是正餐？"
    if finance.monthly_rent <= 1:
        return "房租一个月多少？押几付几？这个不说，账没法判断。"
    if finance.monthly_labor <= 0:
        return "人工怎么配？自己干、夫妻店，还是要请人？每月人工大概多少？"
    if finance.gross_margin_rate <= 0:
        return "毛利率按多少算？不会算就先说进货成本和售价，我帮你换。"
    if finance.estimated_average_ticket <= 0:
        return "客单价预计多少？目标订单数要靠这个算出来。"
    if location.get("target_customer_flow_30min") is None:
        return "现在做现场验证：你在门口数 30 分钟，目标客群过了多少人？"
    if location.get("comparable_store_orders_per_day") is None:
        return "再蹲一下附近同类店，估一个日订单水位，别只看热闹。"
    return "关键账先跑出来了。你可以继续补押金、装修、设备、现金预算，或者直接看报告里的下一步。"


def slot_label(slot_id: str) -> str:
    labels = {
        "monthly_rent": "房租",
        "monthly_labor": "人工",
        "monthly_utilities": "水电杂费",
        "gross_margin_rate": "毛利率",
        "average_ticket": "客单价",
        "cash_available": "现金预算",
        "area_sqm": "面积",
        "deposit": "押金",
        "transfer_fee": "转让费",
        "franchise_or_training_fee": "加盟/学习费",
        "decoration_and_ads": "装修/广告",
        "equipment": "设备",
        "first_batch_material": "首批物料",
        "storefront_flow_30min": "门前人流",
        "comparable_orders": "同类店订单",
        "city": "城市",
        "address_text": "铺位位置",
        "category_name": "品类",
    }
    return labels.get(slot_id, slot_id)


def coerce_finance_value(field_name: str, value: Any) -> float | int | None:
    if value is None and field_name in OPTIONAL_FINANCE_FIELDS:
        return None
    number = coerce_non_negative_number(value, field_name)
    if field_name in INTEGER_FINANCE_FIELDS:
        integer = int(number)
        if integer < 1:
            raise ValueError(f"{field_name} must be at least 1")
        return integer
    if field_name in {"gross_margin_rate", "effective_gross_margin_rate"} and number <= 0:
        raise ValueError(f"{field_name} must be positive")
    if field_name in {"monthly_rent", "estimated_average_ticket"} and number <= 0:
        raise ValueError(f"{field_name} must be positive")
    return number


def coerce_location_value(field_name: str, value: Any) -> str | int | float | None:
    if value is None:
        return None
    if field_name in NUMERIC_LOCATION_FIELDS:
        number = coerce_non_negative_number(value, field_name) if field_name in INTEGER_LOCATION_FIELDS else coerce_number(value, field_name)
        return int(number) if field_name in INTEGER_LOCATION_FIELDS else number
    return coerce_text(value, field_name)


def coerce_non_negative_number(value: Any, field_name: str) -> float:
    number = coerce_number(value, field_name)
    if number < 0:
        raise ValueError(f"{field_name} must not be negative")
    return number


def coerce_number(value: Any, field_name: str) -> float:
    if value is None or value == "":
        raise ValueError(f"{field_name} is required")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc


def coerce_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    return text


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
        "messages": record.messages,
        "current_question": next_question(record),
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
