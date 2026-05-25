from dataclasses import dataclass
from typing import Any

from app.services.category.catalog import get_category_profile
from app.services.finance.calculator import (
    PreOpeningFinanceInput,
    calculate_pre_opening_finance,
)
from app.services.location.mock_provider import evaluate_mock_location
from app.services.report.builder import build_pre_opening_report


@dataclass(frozen=True)
class PreOpeningEvaluationInput:
    session_id: str
    finance: PreOpeningFinanceInput
    location: dict[str, Any]
    category: dict[str, Any]


def evaluate_pre_opening(payload: PreOpeningEvaluationInput) -> dict[str, Any]:
    finance = calculate_pre_opening_finance(payload.finance)
    category_profile = get_category_profile(payload.category.get("category_name", "unknown"))
    location = evaluate_mock_location(payload.location, finance.target_order_count)

    final_verdict = merge_verdicts(finance.pre_opening_verdict, location.score, location.flags)
    category_dict = {
        "name": category_profile.name,
        "major_type": category_profile.major_type,
        "demand_type": category_profile.demand_type,
        "operation_complexity": category_profile.operation_complexity,
        "default_gross_margin_rate": category_profile.default_gross_margin_rate,
        "notes": category_profile.notes,
    }

    return {
        "session_id": payload.session_id,
        "verdict": final_verdict,
        "finance": finance.to_dict(),
        "location": location.to_dict(),
        "category": category_dict,
        "report": build_pre_opening_report(finance, location, category_dict, final_verdict),
        "agent_path": [
            {"engine": "finance", "status": "completed"},
            {"engine": "location", "status": "completed"},
            {"engine": "category", "status": "completed"},
            {"engine": "report", "status": "completed"},
        ],
    }


def merge_verdicts(finance_verdict: str, location_score: int, location_flags: list[str]) -> str:
    if finance_verdict == "do_not_open":
        return "do_not_open"
    if any(flag.startswith("missing_") for flag in location_flags):
        return "validate_first"
    if location_score < 40:
        return "do_not_open"
    if finance_verdict == "validate_first" or location_score < 70:
        return "validate_first"
    return "can_open"
