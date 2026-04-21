# 阶段 11: 种子数据和初始化

**预估时间**: 1天

**目标**: 创建数据库初始化脚本和种子数据

---

## 11.1 数据库初始化脚本

**文件**: `scripts/init_db.py`

**任务**:
- [ ] 创建所有表
- [ ] 创建初始管理员
- [ ] 创建默认模型配置

**代码框架**:
```python
import asyncio
from app.db.session import engine
from app.models.base import Base
from app.models.model_provider import ModelProvider

async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库表创建成功")

async def seed_dalle_model():
    """添加 DALL-E 3 默认配置"""
    # 实现种子数据逻辑
    pass

if __name__ == "__main__":
    asyncio.run(init_db())
    asyncio.run(seed_dalle_model())
```

---

## 11.2 种子数据

**文件**: `scripts/seed_data.py`

**任务**:
- [ ] 添加 DALL-E 3 配置
- [ ] 添加错误处理配置
- [ ] 添加错误消息模板

**代码框架**:
```python
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.model_provider import ModelProvider
from app.models.error_handling import ErrorHandlingConfig, ErrorPattern, ErrorMessageTemplate
from app.models.api_key import APIKey
from app.utils.crypto import encrypt_api_key

DALLE_CONFIG = {
    "name": "dalle",
    "display_name": "DALL-E 3",
    "description": "OpenAI's DALL-E 3 image generation model",
    "provider_type": "image",
    "category": "openai",
    "api_endpoint": "https://api.openai.com/v1/images/generations",
    "api_version": "v1",
    "http_method": "POST",
    "auth_config": {
        "type": "bearer",
        "key_field": "api_key"
    },
    "request_config": {
        "timeout": 60,
        "retry_enabled": True
    },
    "parameter_mapping": {
        "prompt": "prompt",
        "size": "size",
        "quality": "quality",
        "style": "style",
        "n": "n"
    },
    "parameter_schema": {
        "prompt": {"type": "string", "required": True},
        "size": {
            "type": "string",
            "required": False,
            "enum": ["1024x1024", "1792x1024", "1024x1792"]
        },
        "quality": {
            "type": "string",
            "required": False,
            "enum": ["standard", "hd"]
        }
    },
    "response_mapping": {
        "url": "data[0].url",
        "revised_prompt": "data[0].revised_prompt"
    },
    "is_enabled": True,
    "is_available": True,
    "priority": 10,
    "capabilities": ["text_to_image", "style_control", "size_control"],
    "rate_limit": 50,
    "max_concurrent": 10
}

async def seed_dalle():
    """添加 DALL-E 3 配置"""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在
        from sqlalchemy import select
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "dalle")
        )
        existing = result.scalar_one_or_none()

        if not existing:
            provider = ModelProvider(**DALLE_CONFIG)
            session.add(provider)
            await session.commit()
            print("✅ DALL-E 3 配置已添加")
        else:
            print("ℹ️ DALL-E 3 配置已存在")

async def seed_error_configs(provider_id: str):
    """添加错误处理配置"""
    async with AsyncSessionLocal() as session:
        error_configs = [
            {
                "provider_id": provider_id,
                "error_type": "INVALID_PARAMETER",
                "retry_enabled": False,
                "auto_fix_enabled": True,
                "fix_rules": {"size": {"1792x1024": "1024x1024", "1024x1792": "1024x1024"}}
            },
            {
                "provider_id": provider_id,
                "error_type": "RATE_LIMIT_EXCEEDED",
                "retry_enabled": True,
                "max_attempts": 5,
                "base_wait_time": 2.0,
                "exponential_base": 2.0
            },
            {
                "provider_id": provider_id,
                "error_type": "TIMEOUT",
                "retry_enabled": True,
                "max_attempts": 3
            }
        ]
        # 添加配置
        pass

async def seed_error_messages(provider_id: str):
    """添加错误消息模板"""
    async with AsyncSessionLocal() as session:
        messages = [
            {
                "provider_id": provider_id,
                "error_type": "INVALID_PARAMETER",
                "language": "zh",
                "user_message_template": "参数错误：{parameter}。已为您自动修正为：{fixed_value}",
                "suggestions": ["检查输入参数", "尝试简化描述"]
            },
            {
                "provider_id": provider_id,
                "error_type": "RATE_LIMIT_EXCEEDED",
                "language": "zh",
                "user_message_template": "服务请求过于频繁，请稍后再试。预计等待时间：{wait_time}秒",
                "suggestions": ["等待后重试", "降低请求频率"]
            },
            {
                "provider_id": provider_id,
                "error_type": "TIMEOUT",
                "language": "zh",
                "user_message_template": "请求超时，服务响应时间过长",
                "suggestions": ["稍后重试", "尝试减少图片尺寸"]
            }
        ]
        # 添加消息
        pass

async def main():
    await seed_dalle()
    # seed_error_configs(...)
    # seed_error_messages(...)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 11.3 Alembic 迁移脚本

**任务**:
- [ ] 初始化 Alembic
- [ ] 创建初始迁移
- [ ] 测试迁移

```bash
# 初始化 Alembic
alembic init alembic

# 配置 alembic.ini 中的 sqlalchemy.url
# sqlalchemy.url = sqlite+aiosqlite:///./multimodel.db

# 创建迁移
alembic revision --autogenerate -m "Initial migration"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

---

## 11.4 快速开始脚本

**文件**: `scripts/quickstart.py`

```python
#!/usr/bin/env python
"""快速初始化数据库和种子数据"""

import asyncio
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.init_db import init_db
from scripts.seed_data import main as seed_main

if __name__ == "__main__":
    print("🚀 开始初始化数据库...")
    asyncio.run(init_db())

    print("🌱 开始添加种子数据...")
    asyncio.run(seed_main())

    print("✅ 初始化完成！")
```

---

## 验收标准

- [ ] 数据库初始化脚本可执行
- [ ] 种子数据正确添加
- [ ] Alembic 迁移正常工作
- [ ] 快速开始脚本可运行
