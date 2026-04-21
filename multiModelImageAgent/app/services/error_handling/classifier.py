from typing import Optional, Dict, Any, List
from app.models.error_pattern import ErrorPattern
from app.models.error_handling import ErrorHandlingConfig
from app.repositories.error_handling import ErrorPatternRepository, ErrorHandlingConfigRepository
import re


class ErrorClassifier:
    """错误分类器"""

    # HTTP 状态码到错误类型的映射
    STATUS_CODE_MAPPING = {
        400: "INVALID_PARAMETER",
        401: "AUTHENTICATION_FAILED",
        403: "PERMISSION_DENIED",
        404: "NOT_FOUND",
        429: "RATE_LIMIT_EXCEEDED",
        500: "SERVER_ERROR",
        502: "SERVER_ERROR",
        503: "SERVER_ERROR",
        504: "TIMEOUT",
    }

    def __init__(
        self,
        pattern_repo: ErrorPatternRepository,
        config_repo: ErrorHandlingConfigRepository
    ):
        self.pattern_repo = pattern_repo
        self.config_repo = config_repo

    async def classify(
        self,
        error_response: Dict[str, Any],
        provider_id: str
    ) -> str:
        """根据错误响应分类错误类型"""
        # 1. 尝试从错误模式匹配
        patterns = await self.pattern_repo.get_by_provider(provider_id)
        for pattern in patterns:
            if self._match_pattern(pattern, error_response):
                return pattern.error_type

        # 2. 根据 HTTP 状态码分类
        status_code = error_response.get("status_code")
        if status_code:
            mapped_type = self._classify_by_status_code(status_code)
            if mapped_type:
                return mapped_type

        # 3. 默认未知错误
        return "UNKNOWN"

    def _match_pattern(self, pattern: ErrorPattern, error_data: Dict[str, Any]) -> bool:
        """匹配单个模式"""
        pattern_type = pattern.pattern_type
        pattern_value = pattern.pattern_value

        if pattern_type == "status_code":
            return str(error_data.get("status_code")) == pattern_value

        elif pattern_type == "error_code":
            return error_data.get("error_code") == pattern_value

        elif pattern_type == "message_pattern":
            message = error_data.get("message", "")
            return pattern_value.lower() in message.lower()

        elif pattern_type == "regex":
            return bool(re.search(pattern_value, str(error_data)))

        return False

    def _classify_by_status_code(self, status_code: int) -> Optional[str]:
        """根据 HTTP 状态码分类"""
        return self.STATUS_CODE_MAPPING.get(status_code)

    async def get_error_config(
        self,
        provider_id: str,
        error_type: str
    ) -> Optional[ErrorHandlingConfig]:
        """获取错误处理配置"""
        return await self.config_repo.get_by_provider_and_type(provider_id, error_type)
