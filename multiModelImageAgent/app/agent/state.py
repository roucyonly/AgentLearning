from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Agent 状态定义"""
    messages: Annotated[List[BaseMessage], "消息历史"]
    user_intent: Annotated[Optional[str], "用户意图"]
    selected_provider: Annotated[Optional[str], "选择的模型"]
    task_params: Annotated[dict, "任务参数"]
    api_response: Annotated[Optional[dict], "API 响应"]
    final_response: Annotated[Optional[str], "最终回复"]
    error: Annotated[Optional[dict], "错误信息"]
    task_id: Annotated[Optional[str], "任务ID"]
