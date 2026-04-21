# MultiModel Image Agent

## 项目概述

MultiModel Image Agent 是一个基于 LangGraph 实现的智能代理系统，通过调用第三方 AI 服务的 API，支持执行图像生成、视频生成等任务。用户通过自然语言对话与 Agent 交互，Agent 自动理解意图并调用相应的 API 完成任务。

### 核心特性

- **多服务集成**: 通过 API 集成多个 AI 服务提供商（OpenAI DALL-E、Stability AI、Runway 等）
- **对话式交互**: 自然语言理解，无需学习复杂参数
- **智能任务编排**: 使用 LangGraph 实现任务流程自动化
- **异步处理**: 支持长时生成任务的后台处理
- **统一接口**: 屏蔽不同服务商 API 差异

## 技术栈

- **LangGraph**: 工作流编排和状态管理
- **LangChain**: LLM 集成和工具调用框架
- **Python 3.10+**: 主要开发语言
- **FastAPI**: RESTful API 框架
- **httpx/aiohttp**: 异步 HTTP 客户端

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                      用户接口层                            │
│  ┌──────────────┐           ┌──────────────┐            │
│  │  Chat UI     │           │  REST API    │            │
│  └──────┬───────┘           └──────┬───────┘            │
└─────────┼──────────────────────────┼────────────────────┘
          │                          │
          └──────────────┬───────────┘
                         ▼
              ┌─────────────────────┐
              │   LangGraph Agent   │
              │   ┌───────────────┐ │
              │   │   LLM (Claude │ │
              │   │   / GPT-4)    │ │
              │   └───────────────┘ │
              └─────────┬───────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 图像生成工具  │ │ 视频生成工具  │ │  其他工具     │
│ - DALL-E 3   │ │ - Runway      │ │ - 搜索       │
│ - Stable Diff│ │ - Pika        │ │ - 存储       │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                 │
       └────────────────┼─────────────────┘
                        ▼
              ┌─────────────────────┐
              │   第三方 API 服务    │
              └─────────────────────┘
```

## LangGraph 工作流设计

```
用户输入
    │
    ▼
┌─────────────┐
│ 意图识别节点 │ → 分析用户需求（生成图像/视频/查询）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 任务规划节点 │ → 分解任务，确定所需工具和参数
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 工具选择节点 │ → 根据需求选择最佳服务提供商
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 参数构建节点 │ → 映射并构建 API 请求参数
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ API调用节点  │ → 异步调用第三方服务 API
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 结果处理节点 │ → 解析响应，存储结果，提取 URL
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 响应生成节点 │ → 格式化输出，生成用户友好的回复
└─────────────┘
```

## 集成的 AI 服务 API

### 图像生成服务

| 服务商 | API | 特点 |
|--------|-----|------|
| **OpenAI** | DALL-E 3 API | 高质量，理解能力强 |
| **Stability AI** | SDXL API | 开放性强，参数丰富 |
| **Midjourney** | Discord API (通过代理) | 艺术性高 |
| **Replicate** | 多模型聚合 API | 提供多种模型选择 |

### 视频生成服务

| 服务商 | API | 特点 |
|--------|-----|------|
| **Runway** | Gen-2/Gen-3 API | 专业视频生成 |
| **Pika Labs** | Pika API | 动画风格 |
| **Stability AI** | Stable Video Diffusion | 开源模型 API |
| **Luma AI** | Dream Machine API | 高质量视频 |

### 辅助服务

- **LLM API**: Claude / GPT-4 用于意图理解和规划
- **存储服务**: AWS S3 / Cloudflare R2 用于结果存储
- **CDN**: 加速内容分发

## 核心功能模块

### 1. 对话管理器
```python
class ConversationManager:
    """管理用户对话历史和上下文"""
    
    async def handle_message(self, message: str) -> str
    async def get_conversation_history(self, user_id: str) -> List[Message]
    async def update_context(self, context: dict)
```

### 2. API 适配器
```python
class BaseAPIAdapter(ABC):
    """API 适配器基类，统一不同服务的接口"""
    
    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> ImageResult
    
    @abstractmethod
    async def generate_video(self, prompt: str, **kwargs) -> VideoResult

class DALLEAdapter(BaseAPIAdapter):
    """OpenAI DALL-E API 适配器"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    async def generate_image(self, prompt: str, **kwargs) -> ImageResult:
        response = await self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=kwargs.get("size", "1024x1024"),
            quality=kwargs.get("quality", "standard")
        )
        return ImageResult(url=response.data[0].url, ...)
```

### 3. 任务调度器
```python
class TaskScheduler:
    """异步任务调度和状态跟踪"""
    
    async def submit_task(self, task: Task) -> str
    async def get_task_status(self, task_id: str) -> TaskStatus
    async def cancel_task(self, task_id: str)
```

### 4. 参数映射器
```python
class ParameterMapper:
    """将通用参数映射到特定服务商的 API 参数"""
    
    def map_for_dalle(self, params: dict) -> dict
    def map_for_stability(self, params: dict) -> dict
    def map_for_runway(self, params: dict) -> dict
```

## 数据模型

### 任务模型
```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class Task(BaseModel):
    id: str
    type: Literal["image", "video"]
    provider: str  # "dalle", "stability", "runway", etc.
    status: Literal["pending", "processing", "completed", "failed"]
    input_params: dict
    output: Optional[dict]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
```

### 对话模型
```python
class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    task_ids: list[str] = []

class Conversation(BaseModel):
    id: str
    user_id: str
    messages: list[Message]
    context: dict
    created_at: datetime
    updated_at: datetime
```

## API 接口设计

### 对话接口
```python
POST /api/v1/chat
"""
发起对话，提交自然语言请求

Request:
{
    "message": "生成一张猫的图片，风格要可爱",
    "conversation_id": "optional-existing-id"
}

Response:
{
    "response": "好的，我正在使用 DALL-E 为您生成一张可爱风格的猫咪图片...",
    "conversation_id": "conv_123",
    "task_id": "task_456",
    "estimated_time": 30
}
"""
```

### 任务查询接口
```python
GET /api/v1/tasks/{task_id}
"""
查询任务状态和结果

Response:
{
    "task_id": "task_456",
    "status": "completed",
    "type": "image",
    "provider": "dalle",
    "result": {
        "url": "https://...",
        "revised_prompt": "..."
    },
    "created_at": "2024-01-15T10:00:00Z",
    "completed_at": "2024-01-15T10:00:25Z"
}
"""
```

### 直接任务接口
```python
POST /api/v1/tasks
"""
直接创建任务，跳过对话

Request:
{
    "type": "image",
    "provider": "dalle",
    "prompt": "a sunset over mountains",
    "parameters": {
        "size": "1024x1024",
        "quality": "hd"
    }
}
"""
```

### 服务列表接口
```python
GET /api/v1/providers
"""
获取可用的 AI 服务列表

Response:
{
    "image_generation": [
        {
            "name": "dalle",
            "display_name": "DALL-E 3",
            "features": ["high_quality", "prompt_understanding"],
            "parameters": ["size", "quality", "style"]
        },
        ...
    ],
    "video_generation": [...]
}
"""
```

## LangGraph 实现示例

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """Agent 状态定义"""
    messages: Annotated[list[BaseMessage], "消息历史"]
    user_intent: Annotated[str, "用户意图"]
    selected_provider: Annotated[str, "选择的服务商"]
    task_params: Annotated[dict, "任务参数"]
    api_response: Annotated[dict, "API 响应"]
    final_response: Annotated[str, "最终回复"]

def intent_node(state: AgentState) -> AgentState:
    """意图识别节点"""
    last_message = state["messages"][-1].content
    
    # 使用 LLM 识别意图
    intent = llm.invoke(f"分析用户意图: {last_message}")
    state["user_intent"] = intent.content
    
    return state

def planner_node(state: AgentState) -> AgentState:
    """任务规划节点"""
    intent = state["user_intent"]
    
    # 选择最佳服务商
    if "image" in intent:
        provider = select_best_image_provider(intent)
    elif "video" in intent:
        provider = select_best_video_provider(intent)
    
    state["selected_provider"] = provider
    
    # 构建参数
    state["task_params"] = build_parameters(intent, provider)
    
    return state

def executor_node(state: AgentState) -> AgentState:
    """执行节点 - 调用 API"""
    provider = state["selected_provider"]
    params = state["task_params"]
    
    # 获取对应的 API 适配器
    adapter = adapter_factory.get_adapter(provider)
    
    # 异步调用 API
    if provider == "dalle":
        response = await adapter.generate_image(**params)
    elif provider == "runway":
        response = await adapter.generate_video(**params)
    
    state["api_response"] = response
    
    return state

def response_node(state: AgentState) -> AgentState:
    """响应生成节点"""
    response = format_response(state["api_response"])
    state["final_response"] = response
    
    return state

# 构建工作流
workflow = StateGraph(AgentState)

workflow.add_node("intent", intent_node)
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("response", response_node)

workflow.set_entry_point("intent")
workflow.add_edge("intent", "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "response")
workflow.add_edge("response", END)

app = workflow.compile()
```

## 项目结构

```
multiModelImageAgent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   │
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── chat.py             # 对话接口
│   │   ├── tasks.py            # 任务管理接口
│   │   └── providers.py        # 服务信息接口
│   │
│   ├── agent/                  # Agent 核心逻辑
│   │   ├── __init__.py
│   │   ├── graph.py            # LangGraph 定义
│   │   ├── nodes.py            # 节点实现
│   │   └── state.py            # 状态定义
│   │
│   ├── adapters/               # API 适配器
│   │   ├── __init__.py
│   │   ├── base.py             # 基类
│   │   ├── dalle.py            # DALL-E 适配器
│   │   ├── stability.py        # Stability AI 适配器
│   │   ├── runway.py           # Runway 适配器
│   │   └── factory.py          # 适配器工厂
│   │
│   ├── services/               # 业务服务
│   │   ├── __init__.py
│   │   ├── conversation.py     # 对话管理
│   │   ├── task.py             # 任务管理
│   │   └── storage.py          # 存储服务
│   │
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── task.py
│   │   ├── conversation.py
│   │   └── schemas.py
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
│
├── tests/                      # 测试
│   ├── test_adapters.py
│   ├── test_agent.py
│   └── test_api.py
│
├── requirements.txt            # 依赖
├── .env.example               # 环境变量示例
├── README.md
└── project.md                 # 本文档
```

## 配置示例

### .env.example
```env
# LLM API (用于意图理解和规划)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# 图像生成服务
DALLE_API_KEY=sk-...
STABILITY_API_KEY=...
REPLICATE_API_TOKEN=r8_...

# 视频生成服务
RUNWAY_API_KEY=...
PIKA_API_KEY=...

# 存储 (可选)
AWS_S3_BUCKET=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# 应用配置
APP_PORT=8000
APP_ENV=development
LOG_LEVEL=INFO

# 数据库 (可选)
DATABASE_URL=sqlite:///./app.db
REDIS_URL=redis://localhost:6379
```

### requirements.txt
```
# Web 框架
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# LangChain & LangGraph
langchain==0.1.0
langchain-openai==0.0.2
langchain-anthropic==0.1.0
langgraph==0.0.20

# HTTP 客户端
httpx==0.25.2
aiohttp==3.9.1

# AI SDKs
openai==1.3.7
stability-sdk==0.8.4
replicate==0.22.0

# 工具
python-dotenv==1.0.0
pydantic-settings==2.1.0
loguru==0.7.2

# 数据库
sqlalchemy==2.0.23
redis==5.0.1

# 开发工具
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.0
```

## 开发计划

### Phase 1: 基础框架搭建 ✅
- [x] 项目结构设计
- [x] 依赖配置
- [x] LangGraph 基础工作流
- [ ] 基础对话功能
- [ ] 简单 API 适配器（DALL-E）

### Phase 2: API 集成
- [ ] DALL-E 3 API 适配器
- [ ] Stability AI API 适配器
- [ ] Runway API 适配器
- [ ] 参数映射和转换

### Phase 3: Agent 增强
- [ ] 意图识别优化
- [ ] 多步骤任务编排
- [ ] 错误处理和重试
- [ ] 上下文管理

### Phase 4: API 服务
- [ ] FastAPI 接口开发
- [ ] WebSocket 实时推送
- [ ] 任务状态管理
- [ ] API 文档

### Phase 5: 部署和优化
- [ ] Docker 容器化
- [ ] 测试覆盖
- [ ] 性能优化
- [ ] 监控和日志

## 使用示例

### 启动服务
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 启动服务
python -m app.main
```

### 调用示例
```python
import httpx

# 发起对话
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/chat",
        json={"message": "生成一张日落山脉的图片"}
    )
    result = response.json()
    print(result["response"])
    # 输出: 好的，我正在使用 DALL-E 为您生成日落山脉的图片...
    
    # 查询任务状态
    task_id = result["task_id"]
    status = await client.get(f"http://localhost:8000/api/v1/tasks/{task_id}")
    print(status.json())
```

## 注意事项

### API 调用限制
- 不同服务商有各自的速率限制
- 需要实现请求队列和限流
- 监控 API 配额使用情况

### 成本控制
- 记录每次 API 调用的成本
- 设置用户级别的使用配额
- 优先选择性价比高的服务

### 错误处理
- API 调用失败时的降级策略
- 超时处理和重试机制
- 详细的错误日志记录

### 内容安全
- 输入内容过滤
- 生成结果审核
- 敏感词过滤

## 未来扩展

- [ ] 支持更多 AI 服务商
- [ ] 批量任务处理
- [ ] 任务模板系统
- [ ] 用户偏好学习
- [ ] 成本优化建议
- [ ] 结果缓存机制

## 许可证
MIT License
