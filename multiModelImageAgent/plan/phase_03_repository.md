# 阶段 3: Repository 层

**预估时间**: 2-3天

**目标**: 实现数据访问层

---

## 3.1 Base Repository

**文件**: `app/repositories/base.py`

**任务**:
- [ ] 创建 `BaseRepository` 类
- [ ] 实现 CRUD 方法
- [ ] 实现通用查询方法

**代码框架**:
```python
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: str) -> Optional[ModelType]:
        """获取单条记录"""
        result = await self.session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """获取所有记录"""
        result = await self.session.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, obj_in: dict) -> ModelType:
        """创建记录"""
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def update(self, id: str, obj_in: dict) -> Optional[ModelType]:
        """更新记录"""
        await self.session.execute(update(self.model).where(self.model.id == id).values(**obj_in))
        return await self.get(id)

    async def delete(self, id: str) -> bool:
        """删除记录"""
        result = await self.session.execute(delete(self.model).where(self.model.id == id))
        return result.rowcount > 0
```

**测试**: `tests/unit/repositories/test_base.py`

---

## 3.2 ModelProvider Repository

**文件**: `app/repositories/model_provider.py`

**任务**:
- [ ] 创建 `ModelProviderRepository` 类
- [ ] 实现 `get_by_name()` 方法
- [ ] 实现 `get_enabled_providers()` 方法
- [ ] 实现 `get_by_type()` 方法

**代码框架**:
```python
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.model_provider import ModelProvider
from typing import Optional, List

class ModelProviderRepository(BaseRepository[ModelProvider]):
    def __init__(self, session: AsyncSession):
        super().__init__(ModelProvider, session)

    async def get_by_name(self, name: str) -> Optional[ModelProvider]:
        """根据名称获取模型"""
        result = await self.session.execute(
            select(ModelProvider).where(ModelProvider.name == name)
        )
        return result.scalar_one_or_none()

    async def get_enabled_providers(
        self,
        provider_type: Optional[str] = None
    ) -> List[ModelProvider]:
        """获取启用的模型列表"""
        query = select(ModelProvider).where(ModelProvider.is_enabled == True)

        if provider_type:
            query = query.where(ModelProvider.provider_type == provider_type)

        query = query.order_by(ModelProvider.priority.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_with_error_config(self, provider_id: str) -> Optional[ModelProvider]:
        """获取模型及其错误处理配置"""
        # SQLite 可以使用 join
        pass
```

**测试**: `tests/unit/repositories/test_model_provider.py`

---

## 3.3 APIKey Repository

**文件**: `app/repositories/api_key.py`

**任务**:
- [ ] 创建 `APIKeyRepository` 类
- [ ] 实现 `get_active_key()` 方法
- [ ] 实现 `update_quota()` 方法

**代码框架**:
```python
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.api_key import APIKey
from typing import Optional, List

class APIKeyRepository(BaseRepository[APIKey]):
    def __init__(self, session: AsyncSession):
        super().__init__(APIKey, session)

    async def get_active_key(self, provider_id: str) -> Optional[APIKey]:
        """获取提供商的活跃 API Key"""
        result = await self.session.execute(
            select(APIKey)
            .where(
                APIKey.provider_id == provider_id,
                APIKey.is_active == True
            )
            .order_by(APIKey.priority.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, provider_id: str) -> List[APIKey]:
        """获取提供商的所有 Key"""
        result = await self.session.execute(
            select(APIKey)
            .where(APIKey.provider_id == provider_id)
            .order_by(APIKey.priority.desc())
        )
        return result.scalars().all()

    async def update_quota(self, key_id: str, used_delta: int = 1) -> bool:
        """更新配额使用量"""
        result = await self.session.execute(
            update(APIKey)
            .where(APIKey.id == key_id)
            .values(quota_used=APIKey.quota_used + used_delta)
        )
        return result.rowcount > 0
```

**测试**: `tests/unit/repositories/test_api_key.py`

---

## 3.4 ErrorHandling Repository

**文件**: `app/repositories/error_handling.py`

**任务**:
- [ ] 创建 `ErrorHandlingConfigRepository`
- [ ] 创建 `ErrorPatternRepository`
- [ ] 创建 `ErrorMessageRepository`

**代码框架**:
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.error_handling import ErrorHandlingConfig
from app.models.error_pattern import ErrorPattern
from app.models.error_message import ErrorMessageTemplate
from typing import Optional, List

class ErrorHandlingConfigRepository(BaseRepository[ErrorHandlingConfig]):
    def __init__(self, session: AsyncSession):
        super().__init__(ErrorHandlingConfig, session)

    async def get_by_provider_and_type(
        self,
        provider_id: str,
        error_type: str
    ) -> Optional[ErrorHandlingConfig]:
        result = await self.session.execute(
            select(ErrorHandlingConfig).where(
                ErrorHandlingConfig.provider_id == provider_id,
                ErrorHandlingConfig.error_type == error_type
            )
        )
        return result.scalar_one_or_none()

    async def get_by_provider(self, provider_id: str) -> List[ErrorHandlingConfig]:
        result = await self.session.execute(
            select(ErrorHandlingConfig).where(
                ErrorHandlingConfig.provider_id == provider_id
            )
        )
        return result.scalars().all()

class ErrorPatternRepository(BaseRepository[ErrorPattern]):
    def __init__(self, session: AsyncSession):
        super().__init__(ErrorPattern, session)

    async def get_by_provider(self, provider_id: str) -> List[ErrorPattern]:
        result = await self.session.execute(
            select(ErrorPattern).where(
                ErrorPattern.provider_id == provider_id,
                ErrorPattern.is_active == True
            )
        )
        return result.scalars().all()

    async def get_by_type_and_priority(
        self,
        provider_id: str,
        error_type: str
    ) -> List[ErrorPattern]:
        result = await self.session.execute(
            select(ErrorPattern).where(
                ErrorPattern.provider_id == provider_id,
                ErrorPattern.error_type == error_type,
                ErrorPattern.is_active == True
            ).order_by(ErrorPattern.priority.desc())
        )
        return result.scalars().all()

class ErrorMessageRepository(BaseRepository[ErrorMessageTemplate]):
    def __init__(self, session: AsyncSession):
        super().__init__(ErrorMessageTemplate, session)

    async def get_by_provider_and_type(
        self,
        provider_id: str,
        error_type: str,
        language: str = "zh"
    ) -> Optional[ErrorMessageTemplate]:
        result = await self.session.execute(
            select(ErrorMessageTemplate).where(
                ErrorMessageTemplate.provider_id == provider_id,
                ErrorMessageTemplate.error_type == error_type,
                ErrorMessageTemplate.language == language
            )
        )
        return result.scalar_one_or_none()
```

**测试**: `tests/unit/repositories/test_error_handling.py`

---

## 3.5 Task Repository

**文件**: `app/repositories/task.py`

**任务**:
- [ ] 创建 `TaskRepository` 类
- [ ] 实现 `get_by_status()` 方法
- [ ] 实现 `get_user_tasks()` 方法

**代码框架**:
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.task import Task, TaskStatus
from typing import Optional, List

class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def get_by_status(
        self,
        status: TaskStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        result = await self.session.execute(
            select(Task)
            .where(Task.status == status)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_provider(
        self,
        provider_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        result = await self.session.execute(
            select(Task)
            .where(Task.provider_id == provider_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        output: dict = None,
        error_message: str = None
    ) -> Optional[Task]:
        update_data = {"status": status}
        if output is not None:
            update_data["output"] = output
        if error_message is not None:
            update_data["error_message"] = error_message

        await self.session.execute(
            self.model.__table__.update()
            .where(self.model.id == task_id)
            .values(**update_data)
        )
        return await self.get(task_id)
```

**测试**: `tests/unit/repositories/test_task.py`

---

## 3.6 Conversation Repository

**文件**: `app/repositories/conversation.py`

**任务**:
- [ ] 创建 `ConversationRepository` 类
- [ ] 实现 `get_user_conversations()` 方法
- [ ] 实现 `get_with_messages()` 方法

**代码框架**:
```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.conversation import Conversation, ConversationMessage
from typing import Optional, List

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def get_user_conversations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Conversation.updated_at.desc())
        )
        return result.scalars().all()

    async def get_with_messages(self, conversation_id: str) -> Optional[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

class ConversationMessageRepository(BaseRepository[ConversationMessage]):
    def __init__(self, session: AsyncSession):
        super().__init__(ConversationMessage, session)

    async def get_by_conversation(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConversationMessage]:
        result = await self.session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .offset(skip)
            .limit(limit)
            .order_by(ConversationMessage.created_at)
        )
        return result.scalars().all()
```

**测试**: `tests/unit/repositories/test_conversation.py`

---

## 验收标准

- [ ] 所有 Repository 类已创建
- [ ] CRUD 方法正确实现
- [ ] 特定查询方法正确实现
- [ ] 单元测试覆盖所有 Repository
