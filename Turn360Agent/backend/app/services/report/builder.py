from app.services.finance.calculator import PreOpeningFinanceResult
from app.services.location.mock_provider import MockLocationEvidence


def build_pre_opening_report(
    finance: PreOpeningFinanceResult,
    location: MockLocationEvidence,
    category: dict,
    final_verdict: str,
) -> dict:
    return {
        "verdict": final_verdict,
        "executive_summary": make_summary(finance, location, category, final_verdict),
        "sections": [
            {
                "id": "finance",
                "title": "财务测算",
                "items": [
                    f"建店成本：{finance.build_cost}",
                    f"日盈亏平衡点：{finance.daily_breakeven}",
                    f"目标回本日销：{finance.target_daily_revenue}",
                    f"目标订单数：{finance.target_order_count}",
                    f"3个月现金预留：{finance.minimum_cash_reserve_3m}",
                ],
            },
            {
                "id": "location",
                "title": "地址证据",
                "items": location.notes,
            },
            {
                "id": "category",
                "title": "品类判断",
                "items": category.get("notes", []),
            },
        ],
        "next_actions": make_next_actions(final_verdict),
    }


def make_summary(
    finance: PreOpeningFinanceResult,
    location: MockLocationEvidence,
    category: dict,
    final_verdict: str,
) -> str:
    if final_verdict == "can_open":
        return "财务目标线、地址证据和品类条件当前互相支撑，可以进入下一步低成本验证和谈租约。"
    if final_verdict == "do_not_open":
        return "当前财务目标线或地址证据不支持开店，不建议签约或追加投入。"
    if final_verdict == "validate_first":
        return "账面可能成立，但地址或订单水位证据不足，先验证再决定。"
    return "关键数据不足，暂不下结论。"


def make_next_actions(final_verdict: str) -> list[str]:
    if final_verdict == "can_open":
        return ["继续压租金和支付方式。", "做 3 天现场蹲点。", "用目标订单数设计试卖。"]
    if final_verdict == "do_not_open":
        return ["不要签长租或交大额费用。", "重新找有真实客流的位置。", "降低建店投入再重算。"]
    return ["补齐门前人流。", "观察 3 家相似店订单水位。", "补充租金、人工、毛利率和现金数据。"]

