from typing import Dict, Any, Optional
from app.models.error_message import ErrorMessageTemplate
from app.repositories.error_handling import ErrorMessageRepository
import re


class ErrorTranslator:
    """错误消息翻译器"""

    def __init__(self, message_repo: ErrorMessageRepository):
        self.message_repo = message_repo

    async def translate(
        self,
        error_type: str,
        provider_id: str,
        language: str = "zh",
        variables: Optional[Dict[str, Any]] = None
    ) -> Optional[ErrorMessageTemplate]:
        """翻译错误消息"""
        message = await self.message_repo.get_by_provider_and_type(
            provider_id, error_type, language
        )

        # 如果指定语言没有，尝试获取英语
        if not message and language != "en":
            message = await self.message_repo.get_by_provider_and_type(
                provider_id, error_type, "en"
            )

        # 如果还是没有，获取任意语言的第一个
        if not message:
            message = await self.message_repo.get_fallback_message(provider_id, error_type)

        return message

    async def translate_to_user(
        self,
        error_type: str,
        provider_id: str,
        language: str = "zh",
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """翻译为用户友好的消息"""
        message = await self.translate(error_type, provider_id, language, variables)
        if not message:
            return self._get_default_message(error_type)

        template = message.user_message_template
        return self._replace_variables(template, variables or {})

    async def translate_to_technical(
        self,
        error_type: str,
        provider_id: str,
        language: str = "zh",
        variables: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """翻译为技术消息"""
        message = await self.translate(error_type, provider_id, language, variables)
        if not message or not message.technical_message_template:
            return None

        return self._replace_variables(message.technical_message_template, variables or {})

    async def get_suggestions(
        self,
        error_type: str,
        provider_id: str,
        language: str = "zh"
    ) -> list:
        """获取错误建议"""
        message = await self.translate(error_type, provider_id, language)
        if not message:
            return self._get_default_suggestions(error_type)
        return message.suggestions or []

    def _replace_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """替换模板变量"""
        if not template:
            return template

        result = template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))

        # 清理未替换的变量
        result = re.sub(r'\{[^}]+\}', '', result)
        return result.strip()

    def _get_default_message(self, error_type: str) -> str:
        """获取默认错误消息"""
        defaults = {
            "INVALID_PARAMETER": "参数错误，请检查输入",
            "INVALID_SIZE": "尺寸参数不支持，已自动调整",
            "RATE_LIMIT_EXCEEDED": "请求过于频繁，请稍后再试",
            "SERVER_ERROR": "服务暂时不可用，请稍后再试",
            "TIMEOUT": "请求超时，请稍后再试",
            "AUTHENTICATION_FAILED": "认证失败，请检查 API Key",
            "PERMISSION_DENIED": "权限不足",
            "NOT_FOUND": "请求的资源不存在",
            "UNKNOWN": "发生未知错误，请稍后再试",
        }
        return defaults.get(error_type, "发生错误，请稍后再试")

    def _get_default_suggestions(self, error_type: str) -> list:
        """获取默认建议"""
        defaults = {
            "INVALID_PARAMETER": ["检查输入参数", "简化描述"],
            "RATE_LIMIT_EXCEEDED": ["等待后重试", "降低请求频率"],
            "TIMEOUT": ["稍后重试", "尝试减少图片尺寸"],
            "SERVER_ERROR": ["稍后重试", "联系技术支持"],
        }
        return defaults.get(error_type, ["稍后重试"])
