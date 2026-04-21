#!/usr/bin/env python
"""种子数据 - 添加默认模型配置"""
import asyncio
import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
        "key_field": "Authorization"
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
        "url": "data.0.url",
        "revised_prompt": "data.0.revised_prompt"
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
    from app.db.session import AsyncSessionLocal
    from app.models.model_provider import ModelProvider
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # 检查是否已存在
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
    from app.db.session import AsyncSessionLocal
    from app.models.error_handling import ErrorHandlingConfig

    error_configs = [
        {
            "provider_id": provider_id,
            "error_type": "INVALID_PARAMETER",
            "retry_enabled": False,
            "auto_fix_enabled": True,
            "fix_rules": {
                "size": {"1792x1024": "1024x1024", "1024x1792": "1024x1024"}
            }
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
        },
        {
            "provider_id": provider_id,
            "error_type": "SERVER_ERROR",
            "retry_enabled": True,
            "max_attempts": 3,
            "base_wait_time": 1.0
        }
    ]

    async with AsyncSessionLocal() as session:
        for config_data in error_configs:
            config = ErrorHandlingConfig(**config_data)
            session.add(config)
        await session.commit()
        print(f"✅ {len(error_configs)} 条错误处理配置已添加")


async def seed_error_messages(provider_id: str):
    """添加错误消息模板"""
    from app.db.session import AsyncSessionLocal
    from app.models.error_message import ErrorMessageTemplate

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
        },
        {
            "provider_id": provider_id,
            "error_type": "SERVER_ERROR",
            "language": "zh",
            "user_message_template": "服务暂时不可用，请稍后再试",
            "suggestions": ["稍后重试", "联系技术支持"]
        }
    ]

    async with AsyncSessionLocal() as session:
        for msg_data in messages:
            message = ErrorMessageTemplate(**msg_data)
            session.add(message)
        await session.commit()
        print(f"✅ {len(messages)} 条错误消息模板已添加")


async def main():
    print("🌱 开始添加种子数据...")

    await seed_dalle()

    # 获取 provider_id 并添加错误配置
    from app.db.session import AsyncSessionLocal
    from app.models.model_provider import ModelProvider
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "dalle")
        )
        provider = result.scalar_one_or_none()

        if provider:
            await seed_error_configs(provider.id)
            await seed_error_messages(provider.id)

    print("✅ 种子数据添加完成！")


if __name__ == "__main__":
    asyncio.run(main())
