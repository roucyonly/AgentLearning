from typing import Dict, Any, Optional, Callable
from app.services.error_handling.classifier import ErrorClassifier
from app.services.error_handling.fixer import ParameterFixer
from app.services.error_handling.retry_manager import RetryManager
from app.services.error_handling.translator import ErrorTranslator
from app.repositories.error_handling import (
    ErrorHandlingConfigRepository,
    ErrorPatternRepository,
    ErrorMessageRepository,
)


class ErrorHandler:
    """错误处理器 - 整合所有错误处理模块"""

    def __init__(
        self,
        config_repo: ErrorHandlingConfigRepository,
        pattern_repo: ErrorPatternRepository,
        message_repo: ErrorMessageRepository
    ):
        self.config_repo = config_repo
        self.pattern_repo = pattern_repo
        self.message_repo = message_repo

        self.classifier = ErrorClassifier(pattern_repo, config_repo)
        self.fixer = ParameterFixer()
        self.retry_manager = RetryManager()
        self.translator = ErrorTranslator(message_repo)

    async def handle_api_call(
        self,
        func: Callable,
        provider_id: str,
        params: Dict[str, Any],
        operation_id: str = None,
        *args,
        **kwargs
    ) -> Any:
        """处理 API 调用，集成错误分类、修正、重试和翻译"""
        current_params = params.copy()
        last_error = None

        # 1. 尝试调用
        try:
            return await func(current_params, *args, **kwargs)
        except Exception as e:
            last_error = e

        # 2. 错误分类
        error_type = await self.classifier.classify(
            self._extract_error_info(last_error),
            provider_id
        )

        # 3. 获取错误配置
        config = await self.classifier.get_error_config(provider_id, error_type)

        # 4. 如果配置了自动修正，尝试修正参数
        if config and config.auto_fix_enabled:
            current_params = await self.fixer.fix_parameters(
                current_params, error_type, config
            )

            # 用修正后的参数重试
            try:
                return await func(current_params, *args, **kwargs)
            except Exception as e:
                last_error = e

        # 5. 如果配置了重试，执行重试逻辑
        if config and config.retry_enabled:
            try:
                return await self.retry_manager.execute_with_retry(
                    func,
                    config,
                    current_params,
                    *args,
                    operation_id=operation_id,
                    **kwargs
                )
            except Exception as e:
                last_error = e

        # 6. 所有重试都失败，翻译错误消息
        user_message = await self.translator.translate_to_user(
            error_type, provider_id, "zh", {"error": str(last_error)}
        )

        technical_message = await self.translator.translate_to_technical(
            error_type, provider_id, "zh", {"error": str(last_error)}
        )

        suggestions = await self.translator.get_suggestions(error_type, provider_id)

        # 抛出用户友好的错误
        raise APIError(
            error_type=error_type,
            message=user_message,
            technical_message=technical_message,
            suggestions=suggestions,
            original_error=last_error
        )

    def _extract_error_info(self, error: Exception) -> Dict[str, Any]:
        """从异常中提取错误信息"""
        return {
            "message": str(error),
            "type": type(error).__name__,
        }


class APIError(Exception):
    """API 错误异常"""

    def __init__(
        self,
        error_type: str,
        message: str,
        technical_message: Optional[str] = None,
        suggestions: list = None,
        original_error: Exception = None
    ):
        self.error_type = error_type
        self.message = message
        self.technical_message = technical_message
        self.suggestions = suggestions or []
        self.original_error = original_error
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "technical_message": self.technical_message,
            "suggestions": self.suggestions,
        }
