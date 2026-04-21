from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.model_provider import ModelProvider


class ModelProviderRepository(BaseRepository[ModelProvider]):
    def __init__(self, session: AsyncSession):
        super().__init__(ModelProvider, session)

    async def get_by_name(self, name: str) -> Optional[ModelProvider]:
        """根据名称获取模型"""
        result = await self.session.execute(
            select(ModelProvider).where(ModelProvider.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_type(
        self,
        provider_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelProvider]:
        """根据类型获取模型"""
        result = await self.session.execute(
            select(ModelProvider)
            .where(ModelProvider.provider_type == provider_type)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_enabled_providers(
        self,
        provider_type: Optional[str] = None
    ) -> List[ModelProvider]:
        """获取启用的模型列表"""
        query = select(ModelProvider).where(ModelProvider.is_enabled == True)

        if provider_type:
            query = query.where(ModelProvider.provider_type == provider_type)

        query = query.order_by(ModelProvider.priority.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_available_providers(
        self,
        provider_type: Optional[str] = None
    ) -> List[ModelProvider]:
        """获取可用的模型列表（启用且可用）"""
        query = select(ModelProvider).where(
            ModelProvider.is_enabled == True,
            ModelProvider.is_available == True
        )

        if provider_type:
            query = query.where(ModelProvider.provider_type == provider_type)

        query = query.order_by(ModelProvider.priority.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_with_relations(self, provider_id: str) -> Optional[ModelProvider]:
        """获取模型及其所有关联数据"""
        result = await self.session.execute(
            select(ModelProvider)
            .options(
                selectinload(ModelProvider.api_keys),
                selectinload(ModelProvider.error_configs),
                selectinload(ModelProvider.error_patterns),
                selectinload(ModelProvider.error_messages)
            )
            .where(ModelProvider.id == provider_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name_or_raise(self, name: str) -> ModelProvider:
        """根据名称获取模型，不存在则抛出异常"""
        provider = await self.get_by_name(name)
        if not provider:
            raise ValueError(f"Model provider '{name}' not found")
        return provider
