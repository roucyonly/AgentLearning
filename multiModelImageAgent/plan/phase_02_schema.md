# 阶段 2: Schema 层

**预估时间**: 1-2天

**目标**: 实现所有 Pydantic Schema 用于请求/响应验证

---

## 2.1 ModelProvider Schema

**文件**: `app/schemas/model_provider.py`

**任务**:
- [ ] 创建 `ModelProviderCreate` Schema
- [ ] 创建 `ModelProviderUpdate` Schema
- [ ] 创建 `ModelProviderResponse` Schema
- [ ] 添加验证逻辑

**代码框架**:
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class ModelProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    provider_type: str = Field(..., pattern="^(image|video|audio|text)$")
    category: Optional[str] = None

class ModelProviderCreate(ModelProviderBase):
    api_endpoint: str = Field(..., min_length=1)
    auth_config: Dict[str, Any]
    parameter_schema: Dict[str, Any]
    parameter_mapping: Dict[str, str]
    response_mapping: Dict[str, str]

class ModelProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = None

class ModelProviderResponse(ModelProviderBase):
    id: str  # UUID 字符串
    is_enabled: bool
    is_available: bool
    priority: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**测试**: `tests/unit/schemas/test_model_provider.py`

---

## 2.2 Task Schema

**文件**: `app/schemas/task.py`

**任务**:
- [ ] 创建 `TaskCreate` Schema
- [ ] 创建 `TaskResponse` Schema
- [ ] 创建 `TaskStatusUpdate` Schema

**代码框架**:
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TaskType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskBase(BaseModel):
    type: TaskType
    provider_name: Optional[str] = None

class TaskCreate(TaskBase):
    input_params: Dict[str, Any]

class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class TaskResponse(TaskBase):
    id: str
    provider_id: Optional[str] = None
    status: TaskStatus
    input_params: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
```

**测试**: `tests/unit/schemas/test_task.py`

---

## 2.3 Conversation Schema

**文件**: `app/schemas/conversation.py`

**任务**:
- [ ] 创建 `ConversationCreate` Schema
- [ ] 创建 `MessageCreate` Schema
- [ ] 创建 `ConversationResponse` Schema

**代码框架**:
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageBase(BaseModel):
    role: Role
    content: str

class MessageCreate(MessageBase):
    task_ids: List[str] = []

class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    task_ids: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationBase(BaseModel):
    user_id: str

class ConversationCreate(ConversationBase):
    context: Dict[str, Any] = {}

class ConversationUpdate(BaseModel):
    context: Optional[Dict[str, Any]] = None

class ConversationResponse(ConversationBase):
    id: str
    context: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    user_id: str

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    task_id: Optional[str] = None
```

**测试**: `tests/unit/schemas/test_conversation.py`

---

## 2.4 Error Schema

**文件**: `app/schemas/error.py`

**任务**:
- [ ] 创建 `ErrorResponse` Schema
- [ ] 创建 `RetryStrategy` Schema
- [ ] 创建 `FixRule` Schema

**代码框架**:
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ErrorType(str, Enum):
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_SIZE = "INVALID_SIZE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"

class RetryStrategy(BaseModel):
    enabled: bool = True
    max_attempts: int = Field(default=3, ge=1, le=10)
    base_wait_time: float = Field(default=1.0, ge=0)
    max_wait_time: float = Field(default=60.0, ge=0)
    exponential_base: float = Field(default=2.0, ge=1)

class FixRule(BaseModel):
    parameter: str
    old_value: Any
    new_value: Any
    description: Optional[str] = None

class ErrorPatternBase(BaseModel):
    pattern_type: str = Field(..., pattern="^(status_code|error_code|message_pattern|regex)$")
    pattern_value: str
    error_type: ErrorType
    priority: int = 0

class ErrorPatternCreate(ErrorPatternBase):
    extract_fields: Dict[str, str] = {}

class ErrorPatternResponse(ErrorPatternBase):
    id: str
    provider_id: str
    extract_fields: Dict[str, str]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class ErrorMessageTemplateBase(BaseModel):
    error_type: ErrorType
    language: str = "zh"
    user_message_template: str
    technical_message_template: Optional[str] = None
    suggestions: List[str] = []

class ErrorMessageTemplateCreate(ErrorMessageTemplateBase):
    available_variables: Dict[str, str] = {}

class ErrorMessageTemplateResponse(ErrorMessageTemplateBase):
    id: str
    provider_id: str
    available_variables: Dict[str, str]

    model_config = ConfigDict(from_attributes=True)

class ErrorResponse(BaseModel):
    error_type: ErrorType
    message: str
    technical_message: Optional[str] = None
    suggestions: List[str] = []
    retry_strategy: Optional[RetryStrategy] = None
    fix_rules: List[FixRule] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**测试**: `tests/unit/schemas/test_error.py`

---

## 验收标准

- [ ] 所有 Schema 类已创建
- [ ] 验证逻辑正确
- [ ] 单元测试覆盖所有 Schema
