import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.api import (
    PreOpeningEvaluationRequest,
    PreOpeningFinanceRequest,
)
from app.services.cases.repository import CaseRepository
from app.services.decision.pre_opening import evaluate_pre_opening
from app.services.finance.calculator import calculate_pre_opening_finance


router = APIRouter()
cases = CaseRepository()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/cases")
def list_cases() -> list[dict]:
    return cases.list_cases()


@router.get("/cases/{case_id}")
def get_case(case_id: str) -> dict:
    case = cases.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    return case


@router.post("/finance/pre-opening")
def pre_opening_finance(payload: PreOpeningFinanceRequest) -> dict:
    result = calculate_pre_opening_finance(payload.to_domain())
    return result.to_dict()


@router.post("/sessions/pre-opening/evaluate")
def pre_opening_evaluate(payload: PreOpeningEvaluationRequest) -> dict:
    result = evaluate_pre_opening(payload.to_domain())
    return result


@router.get("/chat/stream")
def chat_stream(session_id: str = "demo") -> StreamingResponse:
    def events() -> Iterator[str]:
        steps = [
            {"type": "engine.started", "step": "intent_router", "message": "识别为开店前评估"},
            {"type": "engine.started", "step": "finance", "message": "正在计算日盈亏平衡点"},
            {"type": "engine.completed", "step": "finance", "message": "财务目标线已生成"},
            {"type": "engine.started", "step": "location", "message": "正在读取 Mock 地址证据"},
            {"type": "engine.completed", "step": "report", "message": "报告草稿已生成"},
        ]
        for step in steps:
            yield f"data: {json.dumps({'sessionId': session_id, **step}, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")

