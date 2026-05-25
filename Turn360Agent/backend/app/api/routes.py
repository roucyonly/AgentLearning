import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.api import (
    ChatMessageRequest,
    CreateSessionRequest,
    PreOpeningEvaluationRequest,
    PreOpeningFinanceRequest,
    SlotPatchRequest,
)
from app.services.cases.repository import CaseRepository
from app.services.decision.pre_opening import evaluate_pre_opening
from app.services.finance.calculator import calculate_pre_opening_finance
from app.services.session.store import SessionStore, build_session_view, stream_events_for_view


router = APIRouter()
cases = CaseRepository()
sessions = SessionStore()


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


@router.post("/sessions")
def create_session(payload: CreateSessionRequest | None = None) -> dict:
    if payload is not None and payload.scenario != "pre_opening":
        raise HTTPException(status_code=400, detail="only pre_opening sessions are supported in MVP")
    domain_payload = None if payload is None or payload.pre_opening is None else payload.pre_opening.to_domain()
    record = sessions.create_pre_opening(domain_payload)
    return {
        "session_id": record.session_id,
        "scenario": record.scenario,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.get("/sessions/{session_id}")
def get_session(session_id: str, view: str = "user") -> dict:
    record = sessions.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="session not found")
    try:
        return build_session_view(record, view)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/pre-opening/evaluate")
def update_pre_opening_session(session_id: str, payload: PreOpeningEvaluationRequest) -> dict:
    try:
        record = sessions.update_pre_opening(session_id, payload.to_domain())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc
    return build_session_view(record, "debug")


@router.patch("/sessions/{session_id}/slots")
def patch_session_slots(session_id: str, payload: SlotPatchRequest) -> dict:
    try:
        record = sessions.patch_pre_opening_slots(session_id, payload.updates)
        return build_session_view(record, payload.view)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/chat")
def post_session_chat(session_id: str, payload: ChatMessageRequest) -> dict:
    try:
        record = sessions.handle_chat_message(session_id, payload.message)
        return build_session_view(record, payload.view)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="session not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/chat/stream")
def session_chat_stream(session_id: str, view: str = "user") -> StreamingResponse:
    record = sessions.get(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail="session not found")
    if view not in {"user", "debug"}:
        raise HTTPException(status_code=400, detail="stream view must be user or debug")

    def events() -> Iterator[str]:
        for step in stream_events_for_view(record, view):
            yield f"data: {json.dumps({'sessionId': session_id, **step}, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


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
