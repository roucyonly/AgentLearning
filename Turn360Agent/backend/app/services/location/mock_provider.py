from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class MockLocationEvidence:
    city: str
    address_text: str
    target_customer_flow_30min: int | None
    comparable_store_orders_per_day: int | None
    evidence_level: str
    score: int
    flags: list[str]
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_mock_location(location: dict, target_order_count: float) -> MockLocationEvidence:
    flow = location.get("target_customer_flow_30min")
    comparable_orders = location.get("comparable_store_orders_per_day")
    flags: list[str] = []
    notes: list[str] = []
    score = 60

    if flow is None:
        flags.append("missing_storefront_flow")
        notes.append("缺少目标铺位门前 30 分钟目标客群人数，地址最高只能待验证。")
        score -= 20
    elif flow < max(10, target_order_count * 0.15):
        flags.append("storefront_flow_low_for_target_orders")
        notes.append("门前目标客群与目标订单数不匹配。")
        score -= 25
    else:
        notes.append("门前客群数据对目标订单数有一定支撑。")
        score += 10

    if comparable_orders is None:
        flags.append("missing_comparable_store_orders")
        notes.append("缺少附近相似店订单水位，不能确认目标订单数是否现实。")
        score -= 15
    elif comparable_orders < target_order_count:
        flags.append("target_orders_above_comparable_store_level")
        notes.append("目标订单数高于已观察同类店水位。")
        score -= 20
    else:
        notes.append("同类店订单水位可支撑目标订单数。")
        score += 15

    score = max(0, min(100, score))
    return MockLocationEvidence(
        city=location.get("city", "unknown"),
        address_text=location.get("address_text", "unknown"),
        target_customer_flow_30min=flow,
        comparable_store_orders_per_day=comparable_orders,
        evidence_level=location.get("evidence_level", "mock"),
        score=score,
        flags=flags,
        notes=notes,
    )

