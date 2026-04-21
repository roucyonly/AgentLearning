# 阶段 1: 数据库层

**预估时间**: 3-4天

**目标**: 实现所有数据模型和数据库会话管理

---

## 1.1 Base 模型

**文件**: `app/models/base.py`

**任务**:
- [ ] 创建 `Base` 模型类
- [ ] 添加 `id`、`created_at`、`updated_at` 字段
- [ ] 实现 `to_dict()` 方法
- [ ] 实现 `__repr__()` 方法

**代码框架**:
```python
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base 模型"""
    pass

class TimestampMixin:
    """时间戳混入类"""
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

**测试**: `tests/unit/models/test_base.py`

---

## 1.2 ModelProvider 模型

**文件**: `app/models/model_provider.py`

**任务**:
- [ ] 创建 `ModelProvider` 模型
- [ ] 定义所有字段（参考 model_configuration.md）
- [ ] 添加索引
- [ ] 添加约束

**代码框架**:
```python
from sqlalchemy import Column, String, Boolean, Integer, Text, JSON, Enum, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid

class ModelProvider(Base, TimestampMixin):
    __tablename__ = "model_providers"

    # 基本信息
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)

    # 分类
    provider_type = Column(String(20), nullable=False)
    category = Column(String(50))

    # API 配置
    api_endpoint = Column(String(500), nullable=False)
    api_version = Column(String(20))
    http_method = Column(String(10), default="POST")

    # JSON 字段
    auth_config = Column(JSON, nullable=False)
    request_config = Column(JSON, nullable=False)
    parameter_mapping = Column(JSON, nullable=False)
    parameter_schema = Column(JSON, nullable=False)
    response_mapping = Column(JSON, nullable=False)

    # 状态
    is_enabled = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)

    # 其他
    capabilities = Column(JSON, default={})
    priority = Column(Integer, default=0)
    cost_per_request = Column(Numeric(10, 4))
    cost_per_image = Column(Numeric(10, 4))
    rate_limit = Column(Integer)
    max_concurrent = Column(Integer, default=10)
    metadata = Column(JSON, default={})
    version = Column(Integer, default=1)

    # 关系
    api_keys = relationship("APIKey", back_populates="provider", cascade="all, delete-orphan")
    error_configs = relationship("ErrorHandlingConfig", back_populates="provider", cascade="all, delete-orphan")
    error_patterns = relationship("ErrorPattern", back_populates="provider", cascade="all, delete-orphan")
    error_messages = relationship("ErrorMessageTemplate", back_populates="provider", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="provider")
```

**测试**: `tests/unit/models/test_model_provider.py`

---

## 1.3 APIKey 模型

**文件**: `app/models/api_key.py`

**任务**:
- [ ] 创建 `APIKey` 模型
- [ ] 实现加密字段
- [ ] 添加配额追踪

**代码框架**:
```python
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid

class APIKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    api_key_encrypted = Column(String, nullable=False)
    key_type = Column(String(20), default="production")

    # 配额
    quota_limit = Column(Integer)
    quota_used = Column(Integer, default=0)
    quota_reset_at = Column(DateTime)

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    priority = Column(Integer, default=0)

    # 关系
    provider = relationship("ModelProvider", back_populates="api_keys")
```

**测试**: `tests/unit/models/test_api_key.py`

---

## 1.4 ErrorHandling 相关模型

### 1.4.1 ErrorHandlingConfig

**文件**: `app/models/error_handling.py`

**任务**:
- [ ] 创建 `ErrorHandlingConfig` 模型
- [ ] 定义重试策略字段
- [ ] 定义修正规则字段

**代码框架**:
```python
from sqlalchemy import Column, String, Boolean, Integer, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid

class ErrorHandlingConfig(Base, TimestampMixin):
    __tablename__ = "error_handling_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)
    error_type = Column(String(50), nullable=False)

    # 重试策略
    retry_enabled = Column(Boolean, default=True)
    max_attempts = Column(Integer, default=3)
    base_wait_time = Column(Numeric(5, 2), default=1.0)
    max_wait_time = Column(Numeric(5, 2), default=60.0)
    exponential_base = Column(Numeric(3, 1), default=2.0)

    # 参数修正
    auto_fix_enabled = Column(Boolean, default=False)
    fix_rules = Column(JSON, default={})

    # 降级
    fallback_providers = Column(JSON)  # 字符串列表
    custom_handler = Column(String(100))

    # 关系
    provider = relationship("ModelProvider", back_populates="error_configs")
```

### 1.4.2 ErrorPattern

**文件**: `app/models/error_pattern.py`

**任务**:
- [ ] 创建 `ErrorPattern` 模型
- [ ] 定义模式匹配字段

**代码框架**:
```python
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid

class ErrorPattern(Base, TimestampMixin):
    __tablename__ = "error_patterns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)

    # 匹配规则
    pattern_type = Column(String(20), nullable=False)  # status_code | error_code | message_pattern | regex
    pattern_value = Column(String(500), nullable=False)

    # 映射
    error_type = Column(String(50), nullable=False)
    priority = Column(Integer, default=0)

    # 提取
    extract_fields = Column(JSON, default={})
    is_active = Column(Boolean, default=True)

    # 关系
    provider = relationship("ModelProvider", back_populates="error_patterns")
```

### 1.4.3 ErrorMessageTemplate

**文件**: `app/models/error_message.py`

**任务**:
- [ ] 创建 `ErrorMessageTemplate` 模型
- [ ] 定义多语言消息字段

**代码框架**:
```python
from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid

class ErrorMessageTemplate(Base, TimestampMixin):
    __tablename__ = "error_message_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)

    error_type = Column(String(50), nullable=False)
    language = Column(String(10), default="zh")

    # 消息
    user_message_template = Column(Text, nullable=False)
    technical_message_template = Column(Text)

    # 建议
    suggestions = Column(JSON, default=[])
    available_variables = Column(JSON, default={})

    # 关系
    provider = relationship("ModelProvider", back_populates="error_messages")
```

**测试**: `tests/unit/models/test_error_handling.py`

---

## 1.5 Task 模型

**文件**: `app/models/task.py`

**任务**:
- [ ] 创建 `Task` 模型
- [ ] 定义任务状态枚举
- [ ] 添加输入输出字段

**代码框架**:
```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"

class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(Enum(TaskType), nullable=False)
    provider_id = Column(String(36), ForeignKey("model_providers.id"))
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    # 输入输出
    input_params = Column(JSON, nullable=False)
    output = Column(JSON)
    error_message = Column(Text)

    # 关系
    provider = relationship("ModelProvider", back_populates="tasks")
    conversation_messages = relationship("ConversationMessage", back_populates="task")
```

**测试**: `tests/unit/models/test_task.py`

---

## 1.6 Conversation 相关模型

**文件**: `app/models/conversation.py`

**任务**:
- [ ] 创建 `Conversation` 模型
- [ ] 创建 `ConversationMessage` 模型
- [ ] 定义关系

**代码框架**:
```python
from sqlalchemy import Column, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False)  # 外部用户 ID
    context = Column(JSON, default={})

    # 关系
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

class ConversationMessage(Base, TimestampMixin):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    task_ids = Column(JSON, default=list)  # 关联的任务 ID 列表

    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    task_id = Column(String(36), ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="conversation_messages")
```

**测试**: `tests/unit/models/test_conversation.py`

---

## 1.7 UsageStats 模型

**文件**: `app/models/usage_stats.py`

**任务**:
- [ ] 创建 `ModelUsageStats` 模型
- [ ] 定义统计字段

**代码框架**:
```python
from sqlalchemy import Column, Date, Integer, String, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid

class ModelUsageStats(Base, TimestampMixin):
    __tablename__ = "model_usage_stats"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)

    # 统计维度
    date = Column(Date, nullable=False)
    hour = Column(Integer)  # 0-23

    # 调用统计
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)

    # 错误分布
    error_distribution = Column(JSON, default={})

    # 性能
    avg_response_time = Column(Numeric(10, 2))
    p50_response_time = Column(Numeric(10, 2))
    p95_response_time = Column(Numeric(10, 2))
    p99_response_time = Column(Numeric(10, 2))

    # 成本
    total_cost = Column(Numeric(10, 4))
```

**测试**: `tests/unit/models/test_usage_stats.py`

---

## 1.8 数据库连接

**文件**: `app/db/session.py`

**任务**:
- [ ] 创建 SQLite 异步引擎
- [ ] 创建会话工厂
- [ ] 实现上下文管理器

**代码框架**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}  # SQLite 特定配置
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**测试**: `tests/unit/db/test_session.py`

---

## 1.9 Alembic 迁移

**任务**:
- [ ] 初始化 Alembic
- [ ] 创建初始迁移脚本
- [ ] 测试迁移

**执行**:
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

---

## 验收标准

- [ ] 所有 Model 类已创建
- [ ] 数据库会话管理正常
- [ ] Alembic 迁移脚本可执行
- [ ] 单元测试覆盖所有 Model
