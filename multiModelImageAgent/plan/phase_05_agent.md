# 阶段 5: Agent 层

**预估时间**: 2-3天

**目标**: 实现 LangGraph Agent 工作流

---

## 5.1 Agent 状态定义

**文件**: `app/agent/state.py`

**任务**:
- [ ] 创建 `AgentState` TypedDict
- [ ] 定义所有状态字段

**代码框架**:
```python
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
```

---

## 5.2 Agent 节点实现

**文件**: `app/agent/nodes.py`

**任务**:
- [ ] 实现 `intent_node()` (意图识别)
- [ ] 实现 `planner_node()` (任务规划)
- [ ] 实现 `executor_node()` (API 调用)
- [ ] 实现 `response_node()` (响应生成)

**代码框架**:
```python
from langchain_core.messages import HumanMessage, AIMessage
from app.agent.state import AgentState
from app.services.model_registry import ModelRegistry
from app.services.adapters.generic import GenericAPIAdapter

async def intent_node(state: AgentState) -> AgentState:
    """意图识别节点"""
    last_message = state["messages"][-1]
    # 使用 LLM 识别意图
    pass

async def planner_node(state: AgentState) -> AgentState:
    """任务规划节点"""
    # 选择最佳模型
    # 构建参数
    pass

async def executor_node(state: AgentState) -> AgentState:
    """执行节点 - 调用 API"""
    # 使用 GenericAPIAdapter 调用
    pass

async def response_node(state: AgentState) -> AgentState:
    """响应生成节点"""
    # 格式化输出
    pass
```

**测试**: `tests/unit/agent/test_nodes.py`

---

## 5.3 LangGraph 工作流

**文件**: `app/agent/graph.py`

**任务**:
- [ ] 创建 LangGraph 工作流
- [ ] 添加所有节点
- [ ] 定义边和条件边
- [ ] 编译工作流

**代码框架**:
```python
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import intent_node, planner_node, executor_node, response_node

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
```

**测试**: `tests/unit/agent/test_graph.py`

---

## 验收标准

- [ ] AgentState 正确定义
- [ ] 所有节点正确实现
- [ ] LangGraph 工作流正确编译
- [ ] 单元测试覆盖 Agent
