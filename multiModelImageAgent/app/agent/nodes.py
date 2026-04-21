from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.agent.state import AgentState
from app.services.model_registry import ModelRegistry
from app.services.task_service import TaskService
from app.services.conversation import ConversationService
from app.models.task import TaskType


async def intent_node(state: AgentState) -> AgentState:
    """意图识别节点 - 分析用户意图，确定任务类型"""
    last_message = state["messages"][-1]
    user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # 简单的意图识别逻辑
    # 实际应该用 LLM 来分析
    intent = _analyze_intent(user_input)

    state["user_intent"] = intent

    return state


def _analyze_intent(user_input: str) -> str:
    """分析用户意图"""
    user_input_lower = user_input.lower()

    # 图像相关关键词
    image_keywords = ["图片", "图像", "生成图片", "生成图像", "image", "picture", "photo", "画"]
    video_keywords = ["视频", "生成视频", "video", "movie"]

    for keyword in video_keywords:
        if keyword in user_input_lower:
            return "video_generation"

    for keyword in image_keywords:
        if keyword in user_input_lower:
            return "image_generation"

    return "unknown"


async def planner_node(state: AgentState) -> AgentState:
    """任务规划节点 - 选择最佳模型，构建参数"""
    intent = state.get("user_intent", "unknown")
    last_message = state["messages"][-1]
    user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # 根据意图确定任务类型和 provider
    if intent == "image_generation":
        task_type = TaskType.IMAGE
        default_provider = "dalle"
    elif intent == "video_generation":
        task_type = TaskType.VIDEO
        default_provider = "runway"
    else:
        task_type = TaskType.IMAGE
        default_provider = "dalle"

    # 构建任务参数
    task_params = {
        "prompt": user_input,
        "type": task_type.value,
    }

    state["selected_provider"] = default_provider
    state["task_params"] = task_params

    return state


async def executor_node(state: AgentState) -> AgentState:
    """执行节点 - 调用 API"""
    provider_name = state.get("selected_provider")
    task_params = state.get("task_params", {})
    async_mode = state.get("async_mode", False)

    if not provider_name or not task_params:
        state["error"] = {"message": "Missing provider or task params"}
        return state

    try:
        from app.agent.graph import get_task_service

        task_service = get_task_service()
        if not task_service:
            state["error"] = {"message": "Task service not initialized"}
            return state

        task_type_str = task_params.get("type", "image")
        task_type = TaskType(task_type_str)

        # 创建任务
        task = await task_service.create_task(
            task_type=task_type,
            input_params=task_params,
            provider_name=provider_name
        )

        state["task_id"] = task.id

        # 异步模式：只创建任务，不等待执行
        if async_mode:
            state["api_response"] = {"status": "pending", "task_id": task.id}
            return state

        # 同步模式：等待任务完成
        result_task = await task_service.execute_task(task.id)

        if result_task.status.value == "completed":
            state["api_response"] = result_task.output
        else:
            state["error"] = {
                "message": result_task.error_message or "Task failed",
                "status": result_task.status.value
            }

    except Exception as e:
        state["error"] = {"message": str(e)}

    return state


async def response_node(state: AgentState) -> AgentState:
    """响应生成节点 - 格式化输出"""
    error = state.get("error")
    api_response = state.get("api_response")

    if error:
        response = f"抱歉，发生了错误：{error.get('message', '未知错误')}"
        if error.get("suggestions"):
            response += "\n\n建议：" + "，".join(error["suggestions"])
    elif api_response:
        # 格式化成功响应
        if "url" in api_response:
            response = f"已完成！图片链接：{api_response['url']}"
        elif "video_url" in api_response:
            response = f"已完成！视频链接：{api_response['video_url']}"
        else:
            response = f"已完成！结果：{api_response}"
    else:
        response = "正在处理中，请稍候..."

    state["final_response"] = response

    return state


def should_retry(state: AgentState) -> Literal["executor", "response"]:
    """判断是否需要重试"""
    error = state.get("error")
    if error and error.get("should_retry"):
        return "executor"
    return "response"
