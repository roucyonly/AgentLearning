from typing import Optional, List, Dict, Any
import asyncio
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from app.agent.state import AgentState
from app.agent.nodes import intent_node, planner_node, executor_node, response_node
from app.services.task_service import TaskService
from app.services.conversation import ConversationService


# 全局 service 实例
_task_service: Optional[TaskService] = None
_conversation_service: Optional[ConversationService] = None


def set_services(
    task_service: TaskService = None,
    conversation_service: ConversationService = None
):
    """设置 service 实例"""
    global _task_service, _conversation_service
    if task_service:
        _task_service = task_service
    if conversation_service:
        _conversation_service = conversation_service


def get_task_service() -> Optional[TaskService]:
    """获取 task_service 实例"""
    return _task_service


def get_conversation_service() -> Optional[ConversationService]:
    """获取 conversation_service 实例"""
    return _conversation_service


def create_agent_graph():
    """创建 Agent 工作流"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent", intent_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("response", response_node)

    # 定义边
    workflow.set_entry_point("intent")
    workflow.add_edge("intent", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "response")
    workflow.add_edge("response", END)

    # 编译
    return workflow.compile()


# 创建默认图
default_graph = create_agent_graph()


def _build_messages_from_history(
    messages: List[Dict[str, Any]]
) -> List[HumanMessage]:
    """从数据库消息历史构建 LangGraph 消息列表"""
    result = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            result.append(HumanMessage(content=content))
        elif role == "assistant":
            result.append(AIMessage(content=content))
    return result


async def _execute_task_background(task_id: str):
    """后台执行任务"""
    global _task_service, _conversation_service

    if not _task_service:
        return

    try:
        # 执行任务（更新数据库中的状态）
        await _task_service.execute_task(task_id)
    except Exception:
        # 任务执行失败，已在 task_service 中处理
        pass


async def run_agent(
    user_input: str,
    conversation_id: str = None,
    user_id: str = "default_user",
    history: List[Dict[str, Any]] = None,
    wait_for_result: bool = True
) -> dict:
    """
    运行 Agent

    Args:
        user_input: 用户输入
        conversation_id: 对话ID（可选，用于持久化消息）
        user_id: 用户ID
        history: 历史消息列表，格式 [{"role": "user"|"assistant", "content": "..."}]
        wait_for_result: 是否等待任务完成 True=同步 False=异步（只创建任务立即返回）

    Returns:
        {"response": "...", "task_id": "...", "conversation_id": "...", "status": "..."}
    """
    global _task_service, _conversation_service

    if not _task_service or not _conversation_service:
        raise RuntimeError("Services not initialized. Call set_services() first.")

    # 1. 创建或获取对话
    if conversation_id:
        conversation = await _conversation_service.get_or_create_conversation(
            user_id=user_id,
            conversation_id=conversation_id
        )
        conversation_id = conversation.id
    else:
        conversation = await _conversation_service.create_conversation(user_id=user_id)
        conversation_id = conversation.id

    # 保存用户消息
    await _conversation_service.add_message(
        conversation_id=conversation_id,
        role="user",
        content=user_input
    )

    # 2. 构建消息历史
    if history:
        messages = _build_messages_from_history(history)
        messages.append(HumanMessage(content=user_input))
    else:
        messages = [HumanMessage(content=user_input)]

    # 3. 初始化状态
    initial_state = {
        "messages": messages,
        "user_intent": None,
        "selected_provider": None,
        "task_params": {},
        "api_response": None,
        "final_response": None,
        "error": None,
        "task_id": None,
        "conversation_id": conversation_id,
    }

    # 4. 如果不等待结果，先更新executor_node返回"处理中"
    if not wait_for_result:
        initial_state["async_mode"] = True

    # 5. 运行图
    result = await default_graph.ainvoke(initial_state)

    # 6. 如果是异步模式，启动后台任务
    task_id = result.get("task_id")
    if not wait_for_result and task_id:
        asyncio.create_task(_execute_task_background(task_id))
        result["final_response"] = "任务已创建，正在后台处理中..."

    final_response = result.get("final_response", "处理完成")

    # 7. 保存助手回复到数据库
    await _conversation_service.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=final_response,
        task_ids=[task_id] if task_id else []
    )

    return {
        "response": final_response,
        "task_id": task_id,
        "conversation_id": conversation_id,
        "api_response": result.get("api_response"),
        "error": result.get("error"),
    }


async def run_agent_async(
    user_input: str,
    conversation_id: str = None,
    user_id: str = "default_user",
    history: List[Dict[str, Any]] = None
) -> dict:
    """
    异步运行 Agent - 立即返回，不等待任务完成
    任务会在后台执行，通过 WebSocket 或轮询获取结果
    """
    return await run_agent(
        user_input=user_input,
        conversation_id=conversation_id,
        user_id=user_id,
        history=history,
        wait_for_result=False
    )
