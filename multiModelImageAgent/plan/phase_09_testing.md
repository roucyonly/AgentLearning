# 阶段 9: 测试

**预估时间**: 2-3天

**目标**: 实现完整的测试覆盖

---

## 9.1 测试配置

**文件**: `tests/conftest.py`

**任务**:
- [ ] 配置 pytest fixtures
- [ ] 创建测试数据库 (SQLite 内存数据库)
- [ ] 创建 Mock 服务

**代码框架**:
```python
import pytest
import tempfile
import os
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.base import Base
from app.config import Settings

# 创建临时数据库文件
@pytest.fixture
def temp_db_file():
    """创建临时数据库文件"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.fixture
async def test_db(temp_db_file):
    """创建测试数据库"""
    # 使用临时文件数据库
    TEST_DATABASE_URL = f"sqlite+aiosqlite:///{temp_db_file}"

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture
async def client(test_db):
    """创建测试客户端"""
    # 注入测试数据库
    def override_get_db():
        async with AsyncSession(test_db) as session:
            try:
                yield session
            finally:
                await session.close()

    from app.api.dependencies import get_db
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

---

## 9.2 单元测试

**任务**:
- [ ] 完成 Models 测试
- [ ] 完成 Schemas 测试
- [ ] 完成 Repositories 测试
- [ ] 完成 Services 测试
- [ ] 完成 Agent 节点测试

**目标覆盖率**: >80%

### 9.2.1 Models 测试

```
tests/unit/models/
├── test_base.py
├── test_model_provider.py
├── test_api_key.py
├── test_error_handling.py
├── test_task.py
├── test_conversation.py
└── test_usage_stats.py
```

### 9.2.2 Schemas 测试

```
tests/unit/schemas/
├── test_model_provider.py
├── test_task.py
├── test_conversation.py
└── test_error.py
```

### 9.2.3 Repositories 测试

```
tests/unit/repositories/
├── test_base.py
├── test_model_provider.py
├── test_api_key.py
├── test_error_handling.py
├── test_task.py
└── test_conversation.py
```

### 9.2.4 Services 测试

```
tests/unit/services/
├── test_model_registry.py
├── test_classifier.py
├── test_fixer.py
├── test_retry_manager.py
├── test_translator.py
├── test_handler.py
├── test_generic_adapter.py
├── test_task_service.py
└── test_conversation.py
```

### 9.2.5 Agent 测试

```
tests/unit/agent/
├── test_nodes.py
└── test_graph.py
```

---

## 9.3 集成测试

**任务**:
- [ ] 测试 API 端点
- [ ] 测试数据库操作
- [ ] 测试错误处理流程

### 9.3.1 API 测试

```
tests/integration/api/
├── test_chat.py
├── test_tasks.py
├── test_admin_models.py
└── test_admin_error_config.py
```

### 9.3.2 WebSocket 测试

```
tests/integration/websocket/
└── test_task_progress.py
```

---

## 9.4 端到端测试

**任务**:
- [ ] 测试完整对话流程
- [ ] 测试任务创建和执行
- [ ] 测试错误恢复

```
tests/e2e/
├── test_conversation_flow.py
├── test_task_execution.py
└── test_error_recovery.py
```

---

## 9.5 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行端到端测试
pytest tests/e2e/

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 查看覆盖率
open htmlcov/index.html
```

---

## 验收标准

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码覆盖率 >80%
- [ ] 测试文档完整
