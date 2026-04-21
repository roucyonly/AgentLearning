# 阶段 6: API 层

**预估时间**: 3-4天

**目标**: 实现 FastAPI 路由

---

## 6.1 依赖注入

**文件**: `app/api/dependencies.py`

**任务**:
- [ ] 创建 `get_db()` 依赖
- [ ] 创建 `get_model_registry()` 依赖
- [ ] 创建 `get_current_user()` 依赖（可选）

**代码框架**:
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.model_registry import ModelRegistry

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_model_registry(db: AsyncSession = Depends(get_db)) -> ModelRegistry:
    # 获取或创建 ModelRegistry 单例
    pass
```

---

## 6.2 Chat API

**文件**: `app/api/v1/chat.py`

**任务**:
- [ ] 创建 `POST /api/v1/chat` 路由
- [ ] 实现 `ChatRequest` Schema
- [ ] 实现 `ChatResponse` Schema
- [ ] 集成 Agent 工作流

**代码框架**:
```python
from fastapi import APIRouter, Depends
from app.api.dependencies import get_db, get_model_registry
from app.schemas.conversation import ChatRequest, ChatResponse
from app.agent.graph import create_agent_graph

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db = Depends(get_db),
    registry = Depends(get_model_registry)
):
    # 处理对话请求
    # 执行 Agent 工作流
    # 返回响应
    pass
```

**测试**: `tests/integration/api/test_chat.py`

---

## 6.3 Tasks API

**文件**: `app/api/v1/tasks.py`

**任务**:
- [ ] 创建 `POST /api/v1/tasks` 路由
- [ ] 创建 `GET /api/v1/tasks/{task_id}` 路由
- [ ] 实现 `TaskRequest` Schema
- [ ] 实现 `TaskStatusResponse` Schema

**代码框架**:
```python
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_db
from app.schemas.task import TaskRequest, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse)
async def create_task(
    request: TaskRequest,
    db = Depends(get_db)
):
    # 创建任务
    pass

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db = Depends(get_db)
):
    # 获取任务状态
    pass
```

**测试**: `tests/integration/api/test_tasks.py`

---

## 6.4 Admin Models API

**文件**: `app/api/v1/admin/models.py`

**任务**:
- [ ] 创建 `GET /api/v1/admin/models` (列表)
- [ ] 创建 `POST /api/v1/admin/models` (创建)
- [ ] 创建 `GET /api/v1/admin/models/{model_id}` (详情)
- [ ] 创建 `PUT /api/v1/admin/models/{model_id}` (更新)
- [ ] 创建 `DELETE /api/v1/admin/models/{model_id}` (删除)
- [ ] 创建 `PATCH /api/v1/admin/models/{model_id}/toggle` (启用/禁用)
- [ ] 创建 `POST /api/v1/admin/models/{model_id}/test` (测试连接)

**代码框架**:
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.api.dependencies import get_db
from app.schemas.model_provider import (
    ModelProviderCreate,
    ModelProviderUpdate,
    ModelProviderResponse
)

router = APIRouter(prefix="/models", tags=["admin:models"])

@router.get("/", response_model=List[ModelProviderResponse])
async def list_models(db = Depends(get_db)):
    pass

@router.post("/", response_model=ModelProviderResponse)
async def create_model(
    request: ModelProviderCreate,
    db = Depends(get_db)
):
    pass

@router.get("/{model_id}", response_model=ModelProviderResponse)
async def get_model(model_id: str, db = Depends(get_db)):
    pass

@router.put("/{model_id}", response_model=ModelProviderResponse)
async def update_model(
    model_id: str,
    request: ModelProviderUpdate,
    db = Depends(get_db)
):
    pass

@router.delete("/{model_id}")
async def delete_model(model_id: str, db = Depends(get_db)):
    pass

@router.patch("/{model_id}/toggle")
async def toggle_model(model_id: str, db = Depends(get_db)):
    pass

@router.post("/{model_id}/test")
async def test_model_connection(model_id: str, db = Depends(get_db)):
    pass
```

**测试**: `tests/integration/api/test_admin_models.py`

---

## 6.5 Admin Error Config API

**文件**: `app/api/v1/admin/error_config.py`

**任务**:
- [ ] 创建 `GET /api/v1/admin/models/{model_id}/error-config`
- [ ] 创建 `PUT /api/v1/admin/models/{model_id}/error-config/retry`
- [ ] 创建 `PUT /api/v1/admin/models/{model_id}/error-config/fix-rules`
- [ ] 创建 `POST /api/v1/admin/models/{model_id}/error-patterns`
- [ ] 创建 `PUT /api/v1/admin/models/{model_id}/error-messages/{error_type}`

**代码框架**:
```python
from fastapi import APIRouter, Depends
from app.api.dependencies import get_db

router = APIRouter(prefix="/models/{model_id}/error-config", tags=["admin:error"])

@router.get("/")
async def get_error_config(model_id: str, db = Depends(get_db)):
    pass

@router.put("/retry")
async def update_retry_config(model_id: str, db = Depends(get_db)):
    pass

@router.put("/fix-rules")
async def update_fix_rules(model_id: str, db = Depends(get_db)):
    pass

@router.post("/patterns")
async def create_error_pattern(model_id: str, db = Depends(get_db)):
    pass

@router.put("/messages/{error_type}")
async def update_error_message(model_id: str, error_type: str, db = Depends(get_db)):
    pass
```

**测试**: `tests/integration/api/test_admin_error_config.py`

---

## 6.6 WebSocket (可选)

**文件**: `app/api/websocket/task_progress.py`

**任务**:
- [ ] 创建 WebSocket 端点
- [ ] 实现实时进度推送
- [ ] 实现任务完成通知

**测试**: `tests/integration/websocket/test_task_progress.py`

---

## 验收标准

- [ ] 所有 API 路由正确实现
- [ ] 请求/响应验证正确
- [ ] 错误处理正确
- [ ] 集成测试覆盖所有端点
