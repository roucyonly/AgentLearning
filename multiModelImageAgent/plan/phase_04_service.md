# 阶段 4: 服务层

**预估时间**: 4-5天

**目标**: 实现核心业务逻辑和错误处理服务

---

## 4.1 ModelRegistry 服务

**文件**: `app/services/model_registry.py`

**任务**:
- [ ] 创建 `ModelRegistry` 类
- [ ] 实现缓存机制
- [ ] 实现 `get_provider()` 方法
- [ ] 实现 `list_providers()` 方法
- [ ] 实现 `refresh_provider()` 方法

**代码框架**:
```python
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio
from app.repositories.model_provider import ModelProviderRepository
from app.models.model_provider import ModelProvider
from app.db.session import AsyncSessionLocal

class ModelRegistry:
    def __init__(self):
        self.db = None  # 依赖注入
        self._cache: dict = {}
        self._cache_expiry: dict = {}
        self._cache_ttl = timedelta(minutes=5)
        self._reload_lock = asyncio.Lock()

    async def get_provider(self, name: str) -> Optional[ModelProvider]:
        """获取模型配置（带缓存）"""
        # 检查缓存
        # 加载配置
        # 更新缓存
        pass

    async def list_providers(
        self,
        provider_type: Optional[str] = None,
        only_enabled: bool = True
    ) -> List[ModelProvider]:
        """列出所有模型"""
        pass

    async def refresh_provider(self, name: str):
        """刷新指定模型的配置"""
        pass
```

**测试**: `tests/unit/services/test_model_registry.py`

---

## 4.2 错误处理服务

### 4.2.1 ErrorClassifier

**文件**: `app/services/error_handling/classifier.py`

**任务**:
- [ ] 创建 `ErrorClassifier` 类
- [ ] 实现 `classify()` 方法
- [ ] 实现模式匹配逻辑
- [ ] 实现 HTTP 状态码映射

**代码框架**:
```python
from typing import Optional, Dict, Any
from app.models.error_pattern import ErrorPattern
from app.models.error_handling import ErrorHandlingConfig
import re

class ErrorClassifier:
    def __init__(self):
        pass

    async def classify(
        self,
        error_response: Dict[str, Any],
        provider_id: str
    ) -> str:
        """根据错误响应分类错误类型"""
        pass

    def _match_pattern(self, pattern: ErrorPattern, error_data: Dict[str, Any]) -> bool:
        """匹配单个模式"""
        pass

    def _classify_by_status_code(self, status_code: int) -> str:
        """根据 HTTP 状态码分类"""
        pass
```

**测试**: `tests/unit/services/test_classifier.py`

### 4.2.2 ParameterFixer

**文件**: `app/services/error_handling/fixer.py`

**任务**:
- [ ] 创建 `ParameterFixer` 类
- [ ] 实现 `fix_parameter()` 方法
- [ ] 实现尺寸修正逻辑
- [ ] 实现格式修正逻辑

**代码框架**:
```python
from typing import Dict, Any, List
from app.models.error_handling import ErrorHandlingConfig

class ParameterFixer:
    def __init__(self):
        self._fix_strategies = {}

    async def fix_parameters(
        self,
        params: Dict[str, Any],
        error_type: str,
        config: ErrorHandlingConfig
    ) -> Dict[str, Any]:
        """修正参数"""
        pass

    def _fix_size(self, size: str) -> str:
        """修正尺寸参数"""
        size_mapping = {
            "1024x1024": "1024x1024",
            "1792x1024": "1024x1024",  # DALL-E 不支持
            # ...
        }
        return size_mapping.get(size, size)

    def _fix_format(self, format: str) -> str:
        """修正格式参数"""
        pass
```

**测试**: `tests/unit/services/test_fixer.py`

### 4.2.3 RetryManager

**文件**: `app/services/error_handling/retry_manager.py`

**任务**:
- [ ] 创建 `RetryManager` 类
- [ ] 实现 `execute_with_retry()` 方法
- [ ] 实现指数退避算法
- [ ] 实现重试历史记录

**代码框架**:
```python
from typing import Callable, Any, Optional, List
import asyncio
from datetime import datetime
from app.models.error_handling import ErrorHandlingConfig

class RetryHistory:
    """重试历史记录"""
    def __init__(self):
        self.attempts: List[datetime] = []
        self.errors: List[str] = []

class RetryManager:
    def __init__(self):
        self._history: Dict[str, RetryHistory] = {}

    async def execute_with_retry(
        self,
        func: Callable,
        config: ErrorHandlingConfig,
        *args,
        **kwargs
    ) -> Any:
        """执行函数并在失败时重试"""
        pass

    def _calculate_wait_time(
        self,
        attempt: int,
        config: ErrorHandlingConfig
    ) -> float:
        """计算等待时间（指数退避）"""
        wait_time = config.base_wait_time * (config.exponential_base ** attempt)
        return min(wait_time, float(config.max_wait_time))

    def _should_retry(self, attempt: int, config: ErrorHandlingConfig) -> bool:
        """判断是否应该重试"""
        pass
```

**测试**: `tests/unit/services/test_retry_manager.py`

### 4.2.4 ErrorTranslator

**文件**: `app/services/error_handling/translator.py`

**任务**:
- [ ] 创建 `ErrorTranslator` 类
- [ ] 实现 `translate()` 方法
- [ ] 实现模板变量替换
- [ ] 实现多语言支持

**代码框架**:
```python
from typing import Dict, Any, Optional
from app.models.error_message import ErrorMessageTemplate
import re

class ErrorTranslator:
    def __init__(self):
        pass

    async def translate(
        self,
        error_type: str,
        provider_id: str,
        language: str = "zh",
        variables: Optional[Dict[str, Any]] = None
    ) -> ErrorMessageTemplate:
        """翻译错误消息"""
        pass

    def _replace_variables(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """替换模板变量"""
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template
```

**测试**: `tests/unit/services/test_translator.py`

### 4.2.5 ErrorHandler

**文件**: `app/services/error_handling/handler.py`

**任务**:
- [ ] 创建 `ErrorHandler` 类
- [ ] 整合所有错误处理模块
- [ ] 实现 `handle_api_call()` 方法

**代码框架**:
```python
from typing import Dict, Any, Optional, Callable
from app.services.error_handling.classifier import ErrorClassifier
from app.services.error_handling.fixer import ParameterFixer
from app.services.error_handling.retry_manager import RetryManager
from app.services.error_handling.translator import ErrorTranslator
from app.services.error_handling.repository import ErrorHandlingConfigRepository

class ErrorHandler:
    def __init__(
        self,
        classifier: ErrorClassifier,
        fixer: ParameterFixer,
        retry_manager: RetryManager,
        translator: ErrorTranslator
    ):
        self.classifier = classifier
        self.fixer = fixer
        self.retry_manager = retry_manager
        self.translator = translator

    async def handle_api_call(
        self,
        func: Callable,
        provider_id: str,
        params: Dict[str, Any],
        *args,
        **kwargs
    ) -> Any:
        """处理 API 调用，集成错误分类、修正、重试和翻译"""
        pass
```

**测试**: `tests/unit/services/test_handler.py`

---

## 4.3 GenericAPIAdapter 服务

**文件**: `app/services/adapters/generic.py`

**任务**:
- [ ] 创建 `GenericAPIAdapter` 类
- [ ] 实现 `call()` 方法
- [ ] 实现参数映射
- [ ] 实现响应提取
- [ ] 集成错误处理

**代码框架**:
```python
from typing import Dict, Any, Optional
import httpx
from app.models.model_provider import ModelProvider
from app.services.error_handling.handler import ErrorHandler
from app.utils.helpers import get_by_path

class GenericAPIAdapter:
    def __init__(self, provider: ModelProvider, error_handler: ErrorHandler):
        self.provider = provider
        self.error_handler = error_handler
        self.auth_config = provider.auth_config
        self.request_config = provider.request_config
        self.parameter_mapping = provider.parameter_mapping
        self.response_mapping = provider.response_mapping

    async def call(
        self,
        params: Dict[str, Any],
        api_key: str
    ) -> Dict[str, Any]:
        """调用 API"""
        # 映射参数
        mapped_params = self._map_parameters(params)

        # 构建请求
        request_data = self._build_request(mapped_params)

        # 执行请求
        response = await self._execute_request(request_data, api_key)

        # 提取响应
        return self._extract_response(response)

    def _map_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """映射参数到 provider 格式"""
        mapped = {}
        for user_key, provider_key in self.parameter_mapping.items():
            if user_key in params:
                mapped[provider_key] = params[user_key]
        return mapped

    def _build_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """构建请求数据"""
        pass

    def _extract_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """从响应中提取数据"""
        result = {}
        for user_path, provider_path in self.response_mapping.items():
            result[user_path] = get_by_path(response, provider_path)
        return result
```

**测试**: `tests/unit/services/test_generic_adapter.py`

---

## 4.4 TaskService

**文件**: `app/services/task_service.py`

**任务**:
- [ ] 创建 `TaskService` 类
- [ ] 实现 `create_task()` 方法
- [ ] 实现 `get_task_status()` 方法
- [ ] 实现 `execute_task()` 方法

**代码框架**:
```python
from typing import Optional, Dict, Any
from app.models.task import Task, TaskStatus, TaskType
from app.repositories.task import TaskRepository
from app.services.model_registry import ModelRegistry
from app.services.adapters.generic import GenericAPIAdapter

class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        model_registry: ModelRegistry
    ):
        self.task_repo = task_repository
        self.model_registry = model_registry

    async def create_task(
        self,
        task_type: TaskType,
        input_params: Dict[str, Any],
        provider_name: Optional[str] = None
    ) -> Task:
        """创建任务"""
        pass

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        pass

    async def execute_task(self, task_id: str) -> Task:
        """执行任务"""
        pass

    async def _select_provider(self, task_type: TaskType) -> str:
        """选择最佳 provider"""
        pass
```

**测试**: `tests/unit/services/test_task_service.py`

---

## 4.5 ConversationService

**文件**: `app/services/conversation.py`

**任务**:
- [ ] 创建 `ConversationService` 类
- [ ] 实现 `create_conversation()` 方法
- [ ] 实现 `add_message()` 方法
- [ ] 实现 `get_history()` 方法

**代码框架**:
```python
from typing import Optional, List, Dict, Any
from app.models.conversation import Conversation, ConversationMessage
from app.repositories.conversation import ConversationRepository

class ConversationService:
    def __init__(self, conversation_repo: ConversationRepository):
        self.conversation_repo = conversation_repo

    async def create_conversation(
        self,
        user_id: str,
        context: Dict[str, Any] = None
    ) -> Conversation:
        """创建对话"""
        pass

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        task_ids: List[str] = None
    ) -> ConversationMessage:
        """添加消息"""
        pass

    async def get_history(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConversationMessage]:
        """获取对话历史"""
        pass

    async def get_or_create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Conversation:
        """获取或创建对话"""
        pass
```

**测试**: `tests/unit/services/test_conversation.py`

---

## 验收标准

- [ ] ModelRegistry 服务正确实现缓存
- [ ] ErrorClassifier 正确分类错误
- [ ] ParameterFixer 正确修正参数
- [ ] RetryManager 正确实现指数退避
- [ ] ErrorTranslator 正确翻译错误消息
- [ ] GenericAPIAdapter 正确调用 API
- [ ] TaskService 正确管理任务
- [ ] ConversationService 正确管理对话
- [ ] 单元测试覆盖所有服务
