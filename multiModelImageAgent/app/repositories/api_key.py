from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.api_key import APIKey


class APIKeyRepository(BaseRepository[APIKey]):
    def __init__(self, session: AsyncSession):
        super().__init__(APIKey, session)

    async def get_active_key(self, provider_id: str) -> Optional[APIKey]:
        """获取提供商的活跃 API Key"""
        result = await self.session.execute(
            select(APIKey)
            .where(
                APIKey.provider_id == provider_id,
                APIKey.is_active == True
            )
            .order_by(APIKey.priority.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, provider_id: str) -> List[APIKey]:
        """获取提供商的所有 Key"""
        result = await self.session.execute(
            select(APIKey)
            .where(APIKey.provider_id == provider_id)
            .order_by(APIKey.priority.desc())
        )
        return result.scalars().all()

    async def get_by_name(self, provider_id: str, name: str) -> Optional[APIKey]:
        """根据名称获取 Key"""
        result = await self.session.execute(
            select(APIKey).where(
                APIKey.provider_id == provider_id,
                APIKey.name == name
            )
        )
        return result.scalar_one_or_none()

    async def update_quota(self, key_id: str, used_delta: int = 1) -> bool:
        """更新配额使用量"""
        result = await self.session.execute(
            update(APIKey)
            .where(APIKey.id == key_id)
            .values(quota_used=APIKey.quota_used + used_delta)
        )
        return result.rowcount > 0

    async def increment_quota(self, key_id: str) -> bool:
        """增加配额使用量"""
        return await self.update_quota(key_id, 1)

    async def decrement_quota(self, key_id: str) -> bool:
        """减少配额使用量"""
        return await self.update_quota(key_id, -1)

    async def get_available_quota(self, key_id: str) -> Optional[int]:
        """获取剩余配额"""
        result = await self.session.execute(
            select(APIKey.quota_limit, APIKey.quota_used).where(APIKey.id == key_id)
        )
        row = result.first()
        if row and row[0]:
            return row[0] - row[1]
        return None
