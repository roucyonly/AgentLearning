"""模型执行器 - 抽象不同模型的调用逻辑"""
from typing import Dict, Any, Optional
from app.models.model_provider import ModelProvider
from app.services.adapters.generic import GenericAPIAdapter
from app.utils.helpers import get_by_path


class ModelExecutor:
    """模型执行器 - 统一处理不同模型的调用流程"""

    def __init__(self):
        self._model_cache: Dict[str, ModelProvider] = {}

    async def load_model(self, provider_name: str) -> Optional[ModelProvider]:
        """从数据库加载模型配置"""
        from app.repositories.model_provider import ModelProviderRepository
        from app.db.session import AsyncSessionLocal

        if provider_name in self._model_cache:
            return self._model_cache[provider_name]

        async with AsyncSessionLocal() as session:
            repo = ModelProviderRepository(session)
            model = await repo.get_by_name(provider_name)
            if model:
                self._model_cache[provider_name] = model
            return model

    def prepare_input(
        self,
        model: ModelProvider,
        user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备输入参数 - 合并用户输入和模型默认参数"""
        params = {}

        # 1. 添加模型默认参数（从 parameter_schema 获取）
        schema = model.parameter_schema or {}
        for param_name, param_schema in schema.items():
            if "default" in param_schema:
                params[param_name] = param_schema["default"]

        # 2. 覆盖用户输入的参数
        params.update(user_input)

        # 3. 应用参数映射（user_input key -> API key）
        mapped_params = {}
        mapping = model.parameter_mapping or {}
        for user_key, api_key in mapping.items():
            if user_key in params:
                value = params[user_key]
                # 处理嵌套映射如 "data.url"
                if "." in api_key:
                    self._set_nested(mapped_params, api_key, value)
                else:
                    mapped_params[api_key] = value

        # 添加不在映射中但存在的参数
        mapped_keys = set(mapping.values())
        for key, value in params.items():
            if key not in mapping:
                if "." in key:
                    mapped_params[key] = value
                elif key not in mapped_keys:
                    mapped_params[key] = value

        return mapped_params

    def _set_nested(self, obj: Dict, path: str, value: Any):
        """设置嵌套字典值"""
        keys = path.split(".")
        current = obj
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    async def execute(
        self,
        model: ModelProvider,
        input_params: Dict[str, Any],
        api_key: str
    ) -> Dict[str, Any]:
        """执行模型调用"""
        adapter = GenericAPIAdapter(model)
        return await adapter.generate(input_params, api_key)

    def parse_output(self, model: ModelProvider, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """解析模型输出"""
        output = {}

        mapping = model.response_mapping or {}
        for output_key, response_path in mapping.items():
            value = get_by_path(raw_response, response_path)
            if value is not None:
                if "." in output_key:
                    self._set_nested(output, output_key, value)
                else:
                    output[output_key] = value

        return output

    async def execute_model(
        self,
        provider_name: str,
        user_input: Dict[str, Any],
        api_key: str
    ) -> Dict[str, Any]:
        """完整的模型执行流程"""
        # 1. 加载模型配置
        model = await self.load_model(provider_name)
        if not model:
            raise ValueError(f"Model not found: {provider_name}")

        # 2. 准备输入参数
        input_params = self.prepare_input(model, user_input)

        # 3. 执行调用
        raw_response = await self.execute(model, input_params, api_key)

        # 4. 解析输出
        output = self.parse_output(model, raw_response)

        return output


# 全局单例
_executor: Optional[ModelExecutor] = None


def get_model_executor() -> ModelExecutor:
    global _executor
    if _executor is None:
        _executor = ModelExecutor()
    return _executor
