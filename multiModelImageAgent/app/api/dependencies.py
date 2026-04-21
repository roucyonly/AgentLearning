from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.model_registry import ModelRegistry
from app.services.task_service import TaskService
from app.services.conversation import ConversationService
from app.agent.graph import set_services


# 全局 service 实例缓存
_task_service: Optional[TaskService] = None
_conversation_service: Optional[ConversationService] = None
_model_registry: Optional[ModelRegistry] = None


async def get_db() -> AsyncSession:
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


async def get_task_service(
    db: AsyncSession = Depends(get_db)
) -> TaskService:
    """获取 TaskService 实例"""
    global _task_service
    if _task_service is None:
        _task_service = TaskService(db)
    else:
        # 更新 session
        _task_service.session = db
    return _task_service


async def get_conversation_service(
    db: AsyncSession = Depends(get_db)
) -> ConversationService:
    """获取 ConversationService 实例"""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService(db)
    else:
        _conversation_service.session = db
    return _conversation_service


async def get_model_registry(
    db: AsyncSession = Depends(get_db)
) -> ModelRegistry:
    """获取 ModelRegistry 实例"""
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry(db)
    else:
        _model_registry.session = db
    return _model_registry


def init_agent_services():
    """初始化 Agent 服务 - 在应用启动时调用"""
    global _task_service, _conversation_service
    if _task_service and _conversation_service:
        from app.agent.graph import set_services
        set_services(
            task_service=_task_service,
            conversation_service=_conversation_service
        )
