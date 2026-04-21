from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.repositories.base import BaseRepository
from app.models.error_handling import ErrorHandlingConfig
from app.models.error_pattern import ErrorPattern
from app.models.error_message import ErrorMessageTemplate


class ErrorHandlingConfigRepository(BaseRepository[ErrorHandlingConfig]):
    def __init__(self, session: AsyncSession):
        super().__init__(ErrorHandlingConfig, session)

    async def get_by_provider_and_type(
        self,
        provider_id: str,
        error_type: str
    ) -> Optional[ErrorHandlingConfig]:
        result = await self.session.execute(
            select(ErrorHandlingConfig).where(
                ErrorHandlingConfig.provider_id == provider_id,
                ErrorHandlingConfig.error_type == error_type
            )
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, provider_id: str) -> List[ErrorHandlingConfig]:
        result = await self.session.execute(
            select(ErrorHandlingConfig).where(
                ErrorHandlingConfig.provider_id == provider_id
            )
        )
        return result.scalars().all()

    async def get_retry_enabled_configs(
        self,
        provider_id: str
    ) -> List[ErrorHandlingConfig]:
        result = await self.session.execute(
            select(ErrorHandlingConfig).where(
                ErrorHandlingConfig.provider_id == provider_id,
                ErrorHandlingConfig.retry_enabled == True
            )
        )
        return result.scalars().all()

    async def get_auto_fix_configs(
        self,
        provider_id: str
    ) -> List[ErrorHandlingConfig]:
        result = await self.session.execute(
            select(ErrorHandlingConfig).where(
                ErrorHandlingConfig.provider_id == provider_id,
                ErrorHandlingConfig.auto_fix_enabled == True
            )
        )
        return result.scalars().all()


class ErrorPatternRepository(BaseRepository[ErrorPattern]):
    def __init__(self, session: AsyncSession):
        super().__init__(ErrorPattern, session)

    async def get_by_provider(self, provider_id: str) -> List[ErrorPattern]:
        result = await self.session.execute(
            select(ErrorPattern).where(
                ErrorPattern.provider_id == provider_id,
                ErrorPattern.is_active == True
            )
        )
        return result.scalars().all()

    async def get_by_type_and_priority(
        self,
        provider_id: str,
        error_type: str
    ) -> List[ErrorPattern]:
        result = await self.session.execute(
            select(ErrorPattern).where(
                ErrorPattern.provider_id == provider_id,
                ErrorPattern.error_type == error_type,
                ErrorPattern.is_active == True
            ).order_by(ErrorPattern.priority.desc())
        )
        return result.scalars().all()

    async def get_matching_patterns(
        self,
        provider_id: str,
        pattern_type: str,
        pattern_value: str
    ) -> List[ErrorPattern]:
        result = await self.session.execute(
            select(ErrorPattern).where(
                ErrorPattern.provider_id == provider_id,
                ErrorPattern.pattern_type == pattern_type,
                ErrorPattern.pattern_value == pattern_value,
                ErrorPattern.is_active == True
            )
        )
        return result.scalars().all()


class ErrorMessageRepository(BaseRepository[ErrorMessageTemplate]):
    def __init__(self, session: AsyncSession):
        super().__init__(ErrorMessageTemplate, session)

    async def get_by_provider_and_type(
        self,
        provider_id: str,
        error_type: str,
        language: str = "zh"
    ) -> Optional[ErrorMessageTemplate]:
        result = await self.session.execute(
            select(ErrorMessageTemplate).where(
                ErrorMessageTemplate.provider_id == provider_id,
                ErrorMessageTemplate.error_type == error_type,
                ErrorMessageTemplate.language == language
            )
        )
        return result.scalar_one_or_none()

    async def get_by_provider(
        self,
        provider_id: str,
        language: str = "zh"
    ) -> List[ErrorMessageTemplate]:
        result = await self.session.execute(
            select(ErrorMessageTemplate).where(
                ErrorMessageTemplate.provider_id == provider_id,
                ErrorMessageTemplate.language == language
            )
        )
        return result.scalars().all()

    async def get_fallback_message(
        self,
        provider_id: str,
        error_type: str
    ) -> Optional[ErrorMessageTemplate]:
        """获取备选消息（不限定语言）"""
        result = await self.session.execute(
            select(ErrorMessageTemplate).where(
                ErrorMessageTemplate.provider_id == provider_id,
                ErrorMessageTemplate.error_type == error_type
            ).limit(1)
        )
        return result.scalar_one_or_none()
