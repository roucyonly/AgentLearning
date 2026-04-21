# 阶段 8: 应用入口和配置

**预估时间**: 1天

**目标**: 创建 FastAPI 应用和依赖注入配置

---

## 8.1 FastAPI 应用

**文件**: `app/main.py`

**任务**:
- [ ] 创建 FastAPI 应用
- [ ] 配置中间件 (CORS, 等)
- [ ] 注册所有路由
- [ ] 配置异常处理
- [ ] 添加健康检查端点

**代码框架**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.v1 import chat, tasks, admin
from app.utils.logger import setup_logger

settings = get_settings()
setup_logger(settings.LOG_LEVEL)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 路由
app.include_router(chat.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1/admin")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    # 初始化操作
    pass

@app.on_event("shutdown")
async def shutdown_event():
    # 清理操作
    pass
```

---

## 8.2 依赖注入配置

**文件**: `app/dependencies.py`

**任务**:
- [ ] 创建全局依赖容器
- [ ] 配置单例服务
- [ ] 实现生命周期管理

**代码框架**:
```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.model_registry import ModelRegistry
from app.services.task_service import TaskService
from app.services.conversation import ConversationService

# 单例服务实例
_model_registry: Optional[ModelRegistry] = None
_task_service: Optional[TaskService] = None
_conversation_service: Optional[ConversationService] = None

async def get_model_registry() -> ModelRegistry:
    """获取 ModelRegistry 单例"""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry

async def get_task_service() -> TaskService:
    """获取 TaskService 单例"""
    global _task_service
    if _task_service is None:
        _task_service = TaskService(...)
    return _task_service

async def get_conversation_service() -> ConversationService:
    """获取 ConversationService 单例"""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService(...)
    return _conversation_service

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

## 8.3 应用初始化

**文件**: `app/__init__.py`

```python
"""MultiModel Image Agent Application"""

__version__ = "1.0.0"
```

---

## 验收标准

- [ ] FastAPI 应用正确创建
- [ ] 中间件正确配置
- [ ] 路由正确注册
- [ ] 健康检查端点正常
- [ ] 依赖注入正确实现
