from langchain.messages import HumanMessage
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import intent_node, planner_node, executor_node, response_node
from app.services.task_service import TaskService
from sqlalchemy.ext.asyncio import AsyncSession


# 全局 task_service 实例
_task_service: TaskService = None


def set_task_service(task_service: TaskService):
    """设置 task_service 实例"""
    global _task_service
    _task_service = task_service


def get_task_service() -> TaskService:
    """获取 task_service 实例"""
    return _task_service


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


async def run_agent(user_input: str, task_service: TaskService = None) -> dict:
    """运行 Agent"""
    global _task_service

    # 更新 task_service
    if task_service:
        _task_service = task_service

    # 初始化状态
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "user_intent": None,
        "selected_provider": None,
        "task_params": {},
        "api_response": None,
        "final_response": None,
        "error": None,
        "task_id": None,
    }

    # 运行图
    result = await default_graph.ainvoke(initial_state)

    return {
        "response": result.get("final_response", "处理完成"),
        "task_id": result.get("task_id"),
        "api_response": result.get("api_response"),
        "error": result.get("error"),
    }
