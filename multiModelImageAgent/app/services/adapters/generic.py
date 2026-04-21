from typing import Dict, Any, Optional, Callable
import httpx
from app.models.model_provider import ModelProvider
from app.services.adapters.base import BaseAPIAdapter
from app.services.error_handling.handler import ErrorHandler
from app.utils.helpers import get_by_path, set_by_path


class GenericAPIAdapter(BaseAPIAdapter):
    """通用 API 适配器 - 支持动态配置"""

    def __init__(
        self,
        provider: ModelProvider,
        error_handler: Optional[ErrorHandler] = None
    ):
        super().__init__(provider)
        self.error_handler = error_handler
        self.parameter_mapping = provider.parameter_mapping or {}
        self.parameter_schema = provider.parameter_schema or {}
        self.response_mapping = provider.response_mapping or {}

    async def generate(
        self,
        params: Dict[str, Any],
        api_key: str,
        operation_id: str = None
    ) -> Dict[str, Any]:
        """调用 API"""
        if self.error_handler:
            return await self.error_handler.handle_api_call(
                self._do_generate,
                self.provider.id,
                params,
                operation_id=operation_id,
                api_key=api_key
            )
        else:
            return await self._do_generate(params, api_key)

    async def _do_generate(
        self,
        params: Dict[str, Any],
        api_key: str
    ) -> Dict[str, Any]:
        """执行实际的 API 调用"""
        # 1. 映射参数
        mapped_params = self._map_parameters(params)

        # 2. 构建请求
        request_data = self._build_request_data(mapped_params)

        # 3. 执行请求
        response = await self._execute_request(request_data, api_key)

        # 4. 提取响应
        return self._extract_response(response)

    def _map_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """映射参数到 provider 格式"""
        mapped = {}
        for user_key, provider_key in self.parameter_mapping.items():
            if user_key in params:
                value = params[user_key]
                # 处理嵌套映射，如 "data.url"
                if "." in provider_key:
                    set_by_path(mapped, provider_key, value)
                else:
                    mapped[provider_key] = value

        # 添加不在映射中但存在的参数
        mapped_keys = set(self.parameter_mapping.values())
        for key, value in params.items():
            if key not in self.parameter_mapping:
                if "." in key:
                    # 如果是嵌套格式，直接添加
                    mapped[key] = value
                elif key not in mapped_keys:
                    mapped[key] = value

        return mapped

    def _build_request_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """构建请求数据"""
        http_method = self.provider.http_method or "POST"

        if http_method.upper() == "GET":
            return {
                "method": "GET",
                "url": self.endpoint,
                "params": params
            }
        else:
            return {
                "method": "POST",
                "url": self.endpoint,
                "json_data": params
            }

    async def _execute_request(
        self,
        request_data: Dict[str, Any],
        api_key: str
    ) -> Dict[str, Any]:
        """执行 HTTP 请求"""
        headers = self._build_headers(api_key)
        timeout = self._get_timeout()

        async with httpx.AsyncClient(timeout=timeout) as client:
            method = request_data["method"]
            url = request_data["url"]

            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=request_data.get("params"))
            else:
                response = await client.post(
                    url,
                    headers=headers,
                    json=request_data.get("json_data")
                )

            # 检查 HTTP 状态码
            response.raise_for_status()

            # 解析响应
            return response.json()

    def _extract_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """从响应中提取数据"""
        result = {}
        for user_path, provider_path in self.response_mapping.items():
            value = get_by_path(response, provider_path)
            if value is not None:
                # 处理嵌套路径，如 "data.url"
                if "." in user_path:
                    set_by_path(result, user_path, value)
                else:
                    result[user_path] = value

        return result

    async def test_connection(self, api_key: str) -> bool:
        """测试连接"""
        try:
            # 尝试发送一个最小请求
            test_params = {}
            for param_name, schema in self.parameter_schema.items():
                if schema.get("required") and "default" in schema:
                    test_params[param_name] = schema["default"]

            await self.generate(test_params, api_key, operation_id="test_connection")
            return True
        except Exception:
            return False
