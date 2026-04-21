from typing import Callable, Any, Optional, List, Dict
import asyncio
from datetime import datetime
from app.models.error_handling import ErrorHandlingConfig


class RetryHistory:
    """重试历史记录"""

    def __init__(self):
        self.attempts: List[datetime] = []
        self.errors: List[str] = []

    def add_attempt(self, error: str = None):
        self.attempts.append(datetime.utcnow())
        if error:
            self.errors.append(error)


class RetryManager:
    """重试管理器"""

    def __init__(self):
        self._history: Dict[str, RetryHistory] = {}

    def get_history(self, operation_id: str) -> RetryHistory:
        """获取操作的历史记录"""
        if operation_id not in self._history:
            self._history[operation_id] = RetryHistory()
        return self._history[operation_id]

    def clear_history(self, operation_id: str):
        """清除历史记录"""
        if operation_id in self._history:
            del self._history[operation_id]

    async def execute_with_retry(
        self,
        func: Callable,
        config: Optional[ErrorHandlingConfig],
        *args,
        operation_id: str = None,
        **kwargs
    ) -> Any:
        """执行函数并在失败时重试"""
        if not config or not config.retry_enabled:
            return await func(*args, **kwargs)

        max_attempts = config.max_attempts
        history = self.get_history(operation_id or "default")

        last_error = None
        for attempt in range(max_attempts):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    history.add_attempt()  # 成功记录
                return result
            except Exception as e:
                last_error = e
                history.add_attempt(str(e))

                if attempt < max_attempts - 1:
                    wait_time = self._calculate_wait_time(attempt, config)
                    await asyncio.sleep(wait_time)

        raise last_error

    def _calculate_wait_time(
        self,
        attempt: int,
        config: ErrorHandlingConfig
    ) -> float:
        """计算等待时间（指数退避）"""
        base = float(config.base_wait_time)
        exponential_base = float(config.exponential_base)
        max_wait = float(config.max_wait_time)

        wait_time = base * (exponential_base ** attempt)
        return min(wait_time, max_wait)

    def _should_retry(
        self,
        attempt: int,
        config: ErrorHandlingConfig,
        error: Exception
    ) -> bool:
        """判断是否应该重试"""
        if attempt >= config.max_attempts:
            return False

        # 可以添加更多逻辑来判断错误是否可重试
        # 例如：网络错误可重试，认证错误不重试
        error_msg = str(error).lower()
        non_retryable = ["auth", "credential", "permission"]
        return not any(keyword in error_msg for keyword in non_retryable)
