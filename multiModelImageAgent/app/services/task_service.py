from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task, TaskStatus, TaskType
from app.models.model_provider import ModelProvider
from app.repositories.task import TaskRepository
from app.repositories.model_provider import ModelProviderRepository
from app.repositories.api_key import APIKeyRepository
from app.services.model_registry import ModelRegistry
from app.services.adapters.generic import GenericAPIAdapter
from app.services.error_handling.handler import ErrorHandler
from app.repositories.error_handling import (
    ErrorHandlingConfigRepository,
    ErrorPatternRepository,
    ErrorMessageRepository,
)


class TaskService:
    """任务服务"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.provider_repo = ModelProviderRepository(session)
        self.api_key_repo = APIKeyRepository(session)
        self.registry = ModelRegistry(session)

        # 创建错误处理器
        config_repo = ErrorHandlingConfigRepository(session)
        pattern_repo = ErrorPatternRepository(session)
        message_repo = ErrorMessageRepository(session)
        self.error_handler = ErrorHandler(config_repo, pattern_repo, message_repo)

    async def create_task(
        self,
        task_type: TaskType,
        input_params: Dict[str, Any],
        provider_name: Optional[str] = None
    ) -> Task:
        """创建任务"""
        # 如果没有指定 provider，选择默认的
        if not provider_name:
            providers = await self.registry.get_available_providers(
                task_type.value
            )
            if not providers:
                raise ValueError(f"No available providers for type: {task_type}")
            provider = providers[0]
        else:
            provider = await self.registry.get_provider_or_raise(provider_name)

        task = await self.task_repo.create({
            "type": task_type,
            "provider_id": provider.id,
            "input_params": input_params,
            "status": TaskStatus.PENDING
        })

        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return await self.task_repo.get(task_id)

    async def get_task_with_provider(self, task_id: str) -> Optional[Task]:
        """获取任务及其提供商"""
        return await self.task_repo.get_with_provider(task_id)

    async def execute_task(self, task_id: str) -> Task:
        """执行任务"""
        task = await self.task_repo.get_with_provider(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if task.status != TaskStatus.PENDING:
            raise ValueError(f"Task is not pending: {task_id}")

        # 标记为处理中
        await self.task_repo.mark_as_processing(task_id)

        try:
            # 获取 API Key
            api_key_record = await self.api_key_repo.get_active_key(task.provider_id)
            if not api_key_record:
                raise ValueError(f"No active API key for provider: {task.provider_id}")

            # 获取解密的 API Key（这里需要 crypto 模块）
            from app.utils.crypto import decrypt_api_key, generate_kling_token
            from app.config import get_settings
            settings = get_settings()
            api_key = decrypt_api_key(api_key_record.api_key_encrypted, settings.ENCRYPTION_KEY)

            # Kling 使用 accesskey/secretkey 生成 JWT token
            if task.provider.category == "kling":
                api_key = generate_kling_token(
                    settings.KLING_ACCESS_KEY,
                    settings.KLING_SECRET_KEY
                )

            # 创建适配器
            adapter = GenericAPIAdapter(task.provider, self.error_handler)

            # 执行生成
            result = await adapter.generate(
                task.input_params,
                api_key,
                operation_id=task_id
            )

            # 标记为完成
            await self.task_repo.mark_as_completed(task_id, result)

            return await self.task_repo.get(task_id)

        except Exception as e:
            # 标记为失败
            await self.task_repo.mark_as_failed(task_id, str(e))
            raise

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list:
        """列出任务"""
        if status:
            return await self.task_repo.get_by_status(status, skip, limit)
        else:
            return await self.task_repo.get_all(skip, limit)

    async def cancel_task(self, task_id: str) -> Optional[Task]:
        """取消任务"""
        task = await self.task_repo.get(task_id)
        if not task:
            return None

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            raise ValueError(f"Cannot cancel task with status: {task.status}")

        return await self.task_repo.update_status(task_id, TaskStatus.FAILED, error_message="Cancelled by user")
