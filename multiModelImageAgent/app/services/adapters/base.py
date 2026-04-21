from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from app.models.model_provider import ModelProvider


class BaseAPIAdapter(ABC):
    """API 适配器基类"""

    def __init__(self, provider: ModelProvider):
        self.provider = provider
        self.endpoint = provider.api_endpoint
        self.auth_config = provider.auth_config
        self.request_config = provider.request_config

    @abstractmethod
    async def generate(self, params: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """执行生成任务"""
        pass

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        json_data: Dict[str, Any] = None,
        timeout: int = 60
    ) -> httpx.Response:
        """发送 HTTP 请求"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                return await client.get(url, headers=headers)
            elif method.upper() == "POST":
                return await client.post(url, headers=headers, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

    def _build_headers(self, api_key: str) -> Dict[str, str]:
        """构建请求头"""
        auth_type = self.auth_config.get("type", "bearer")

        if auth_type == "bearer":
            return {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        elif auth_type == "api_key":
            key_field = self.auth_config.get("key_field", "api_key")
            return {
                key_field: api_key,
                "Content-Type": "application/json"
            }
        else:
            return {"Content-Type": "application/json"}

    def _get_timeout(self) -> int:
        """获取超时时间"""
        return self.request_config.get("timeout", 60)
