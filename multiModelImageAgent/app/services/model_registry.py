from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.model_provider import ModelProviderRepository
from app.models.model_provider import ModelProvider


class ModelRegistry:
    """模型注册表，提供缓存机制"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ModelProviderRepository(session)
        self._cache: Dict[str, ModelProvider] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)
        self._reload_lock = asyncio.Lock()

    def _is_cache_valid(self, name: str) -> bool:
        """检查缓存是否有效"""
        if name not in self._cache:
            return False
        if name not in self._cache_expiry:
            return False
        return datetime.utcnow() < self._cache_expiry[name]

    def _invalidate_cache(self, name: str) -> None:
        """使缓存失效"""
        if name in self._cache:
            del self._cache[name]
        if name in self._cache_expiry:
            del self._cache_expiry[name]

    def _set_cache(self, name: str, provider: ModelProvider) -> None:
        """设置缓存"""
        self._cache[name] = provider
        self._cache_expiry[name] = datetime.utcnow() + self._cache_ttl

    async def get_provider(self, name: str) -> Optional[ModelProvider]:
        """获取模型配置（带缓存）"""
        if self._is_cache_valid(name):
            return self._cache[name]

        async with self._reload_lock:
            # 双重检查
            if self._is_cache_valid(name):
                return self._cache[name]

            provider = await self.repo.get_by_name(name)
            if provider:
                self._set_cache(name, provider)
            return provider

    async def list_providers(
        self,
        provider_type: Optional[str] = None,
        only_enabled: bool = True
    ) -> List[ModelProvider]:
        """列出所有模型"""
        if only_enabled:
            return await self.repo.get_enabled_providers(provider_type)
        else:
            if provider_type:
                return await self.repo.get_by_type(provider_type)
            else:
                return await self.repo.get_all()

    async def get_available_providers(
        self,
        provider_type: Optional[str] = None
    ) -> List[ModelProvider]:
        """获取可用的模型列表"""
        return await self.repo.get_available_providers(provider_type)

    async def refresh_provider(self, name: str) -> Optional[ModelProvider]:
        """刷新指定模型的配置"""
        self._invalidate_cache(name)
        provider = await self.repo.get_by_name(name)
        if provider:
            self._set_cache(name, provider)
        return provider

    async def refresh_all(self) -> None:
        """刷新所有缓存"""
        self._cache.clear()
        self._cache_expiry.clear()

    async def get_provider_or_raise(self, name: str) -> ModelProvider:
        """获取模型，不存在则抛出异常"""
        provider = await self.get_provider(name)
        if not provider:
            raise ValueError(f"Model provider '{name}' not found")
        return provider
