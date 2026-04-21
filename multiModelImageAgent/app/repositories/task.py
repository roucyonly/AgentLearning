from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.task import Task, TaskStatus, TaskType


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def get_by_status(
        self,
        status: TaskStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        result = await self.session.execute(
            select(Task)
            .where(Task.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Task.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_provider(
        self,
        provider_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        result = await self.session.execute(
            select(Task)
            .where(Task.provider_id == provider_id)
            .offset(skip)
            .limit(limit)
            .order_by(Task.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_type(
        self,
        task_type: TaskType,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        result = await self.session.execute(
            select(Task)
            .where(Task.type == task_type)
            .offset(skip)
            .limit(limit)
            .order_by(Task.created_at.desc())
        )
        return result.scalars().all()

    async def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """获取待处理任务"""
        return await self.get_by_status(TaskStatus.PENDING, limit=limit)

    async def get_processing_tasks(self, limit: int = 100) -> List[Task]:
        """获取处理中任务"""
        return await self.get_by_status(TaskStatus.PROCESSING, limit=limit)

    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        output: dict = None,
        error_message: str = None
    ) -> Optional[Task]:
        """更新任务状态"""
        update_data = {"status": status}
        if output is not None:
            update_data["output"] = output
        if error_message is not None:
            update_data["error_message"] = error_message

        await self.session.execute(
            update(Task).where(Task.id == task_id).values(**update_data)
        )
        await self.session.flush()
        return await self.get(task_id)

    async def mark_as_processing(self, task_id: str) -> Optional[Task]:
        """标记任务为处理中"""
        return await self.update_status(task_id, TaskStatus.PROCESSING)

    async def mark_as_completed(
        self,
        task_id: str,
        output: dict
    ) -> Optional[Task]:
        """标记任务为已完成"""
        return await self.update_status(task_id, TaskStatus.COMPLETED, output=output)

    async def mark_as_failed(
        self,
        task_id: str,
        error_message: str
    ) -> Optional[Task]:
        """标记任务为失败"""
        return await self.update_status(
            task_id, TaskStatus.FAILED, error_message=error_message
        )

    async def get_with_provider(self, task_id: str) -> Optional[Task]:
        """获取任务及其提供商"""
        result = await self.session.execute(
            select(Task)
            .options(selectinload(Task.provider))
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()
