# 阶段 0: 项目初始化

**预估时间**: 1-2天

**目标**: 建立完整的项目骨架

---

## 0.1 创建项目目录结构

**执行步骤**:

```bash
# 创建主目录结构
multiModelImageAgent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 全局配置
│   ├── dependencies.py         # 依赖注入
│   │
│   ├── models/                 # 数据模型 (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── base.py             # Base 模型
│   │   ├── model_provider.py   # 模型配置
│   │   ├── api_key.py          # API Key
│   │   ├── error_handling.py   # 错误处理配置
│   │   ├── error_pattern.py    # 错误模式
│   │   ├── error_message.py    # 错误消息模板
│   │   ├── task.py             # 任务模型
│   │   ├── conversation.py     # 对话模型
│   │   └── usage_stats.py      # 统计模型
│   │
│   ├── schemas/                # Pydantic Schema (请求/响应)
│   │   ├── __init__.py
│   │   ├── model_provider.py
│   │   ├── task.py
│   │   ├── conversation.py
│   │   └── error.py
│   │
│   ├── repositories/           # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py             # Base Repository
│   │   ├── model_provider.py
│   │   ├── api_key.py
│   │   ├── error_handling.py
│   │   ├── error_pattern.py
│   │   ├── error_message.py
│   │   ├── task.py
│   │   └── conversation.py
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── model_registry.py   # 模型注册表
│   │   ├── model_provider.py   # 模型管理服务
│   │   ├── task_service.py     # 任务服务
│   │   ├── conversation.py     # 对话服务
│   │   ├── error_handling/     # 错误处理服务
│   │   │   ├── __init__.py
│   │   │   ├── classifier.py
│   │   │   ├── fixer.py
│   │   │   ├── retry_manager.py
│   │   │   ├── translator.py
│   │   │   └── handler.py
│   │   └── adapters/           # API 适配器
│   │       ├── __init__.py
│   │       ├── base.py
│   │       └── generic.py      # 通用适配器
│   │
│   ├── agent/                  # LangGraph Agent
│   │   ├── __init__.py
│   │   ├── state.py            # 状态定义
│   │   ├── graph.py            # 工作流定义
│   │   └── nodes.py            # 节点实现
│   │
│   ├── api/                    # FastAPI 路由
│   │   ├── __init__.py
│   │   ├── dependencies.py     # 路由依赖
│   │   ├── v1/                 # API v1
│   │   │   ├── __init__.py
│   │   │   ├── chat.py         # 对话接口
│   │   │   ├── tasks.py        # 任务接口
│   │   │   └── admin/          # Admin API
│   │   │       ├── __init__.py
│   │   │       ├── models.py   # 模型管理
│   │   │       ├── error_config.py
│   │   │       └── stats.py
│   │   │
│   │   └── websocket/          # WebSocket
│   │       └── task_progress.py
│   │
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── crypto.py           # 加密工具
│   │   └── helpers.py
│   │
│   └── db/                     # 数据库
│       ├── __init__.py
│       ├── session.py          # 数据库会话
│       └── migrations/         # Alembic 迁移
│           └── versions/
│
├── tests/                      # 测试
│   ├── __init__.py
│   ├── conftest.py             # pytest 配置
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── e2e/                    # 端到端测试
│
├── docs/                       # 文档
├── scripts/                    # 脚本
│   ├── init_db.py              # 初始化数据库
│   └── seed_data.py            # 种子数据
│
├── .env.example
├── requirements.txt
├── pytest.ini
├── alembic.ini
└── README.md
```

**任务**:
- [ ] 创建所有目录和 `__init__.py` 文件
- [ ] 创建 `.gitignore` 文件
- [ ] 创建 `.env.example` 文件

---

## 0.2 配置项目依赖

**文件**: `requirements.txt`

```txt
# Web 框架
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# LangChain & LangGraph
langchain==0.1.0
langchain-openai==0.0.2
langchain-anthropic==0.1.0
langgraph==0.0.20

# HTTP 客户端
httpx==0.25.2
aiohttp==3.9.1

# 数据库 (SQLite)
sqlalchemy==2.0.23
aiosqlite==0.19.0  # SQLite 异步驱动
alembic==1.13.0

# 缓存 (可选)
redis==5.0.1

# 工具
python-dotenv==1.0.0
loguru==0.7.2
cryptography==41.0.7

# 测试
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2  # 用于测试 API
```

**任务**:
- [ ] 创建 `requirements.txt`
- [ ] 创建 `pytest.ini`
- [ ] 创建 `alembic.ini`

---

## 0.3 配置全局配置

**文件**: `app/config.py`

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置"""

    # 应用
    APP_NAME: str = "MultiModel Image Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库 (SQLite)
    DATABASE_URL: str = "sqlite+aiosqlite:///./multimodel.db"

    # Redis (可选)
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM API (用于 Agent)
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # 加密
    SECRET_KEY: str
    ENCRYPTION_KEY: str

    # 日志
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**任务**:
- [ ] 创建 `app/config.py`
- [ ] 创建 `.env.example` 文件

---

## 0.4 创建 .gitignore

**文件**: `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Docker
.docker/

# Misc
.DS_Store
Thumbs.db
```

---

## 验收标准

- [ ] 所有目录结构已创建
- [ ] `requirements.txt` 包含所有依赖
- [ ] `.env.example` 包含所有环境变量
- [ ] `pytest.ini` 配置完成
- [ ] `alembic.ini` 配置完成
