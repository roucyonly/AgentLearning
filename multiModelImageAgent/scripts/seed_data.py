#!/usr/bin/env python
"""Seed data - Add default model configuration"""
import asyncio
import sys
import os

# Add project root to path
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

DOUBAO_CONFIG = {
    "name": "doubao",
    "display_name": "Doubao LLM",
    "description": "Volcengine Doubao LLM for intent recognition",
    "provider_type": "llm",
    "category": "volcengine",
    "api_endpoint": "https://ark.cn-beijing.volces.com/api/v3/responses",
    "api_version": "v3",
    "http_method": "POST",
    "auth_config": {
        "type": "bearer",
        "key_field": "Authorization"
    },
    "request_config": {
        "timeout": 30,
        "retry_enabled": True
    },
    "parameter_mapping": {
        "prompt": "input.0.content.0.text"
    },
    "parameter_schema": {
        "prompt": {"type": "string", "required": True}
    },
    "response_mapping": {
        "output_text": "output.0.content.0.text"
    },
    "is_enabled": True,
    "is_available": True,
    "priority": 20,
    "capabilities": ["text_generation", "intent_recognition"],
    "rate_limit": 100,
    "max_concurrent": 5
}


async def seed_dalle():
    """Add DALL-E 3 configuration"""
    from app.db.session import AsyncSessionLocal
    from app.models.model_provider import ModelProvider
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # Check if exists
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "dalle")
        )
        existing = result.scalar_one_or_none()

        if not existing:
            provider = ModelProvider(**DALLE_CONFIG)
            session.add(provider)
            await session.commit()
            print("[OK] DALL-E 3 configuration added")
        else:
            print("[INFO] DALL-E 3 configuration already exists")


async def seed_doubao():
    """Add Doubao configuration"""
    from app.db.session import AsyncSessionLocal
    from app.models.model_provider import ModelProvider
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "doubao")
        )
        existing = result.scalar_one_or_none()

        if not existing:
            provider = ModelProvider(**DOUBAO_CONFIG)
            session.add(provider)
            await session.commit()
            print("[OK] Doubao configuration added")
        else:
            print("[INFO] Doubao configuration already exists")


async def seed_error_configs(provider_id: str):
    """Add error handling configuration"""
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
        print(f"[OK] {len(error_configs)} error handling configs added")


async def seed_error_messages(provider_id: str):
    """Add error message templates"""
    from app.db.session import AsyncSessionLocal
    from app.models.error_message import ErrorMessageTemplate

    messages = [
        {
            "provider_id": provider_id,
            "error_type": "INVALID_PARAMETER",
            "language": "zh",
            "user_message_template": "Parameter error: {parameter}. Auto-corrected to: {fixed_value}",
            "suggestions": ["Check input parameters", "Try simplifying description"]
        },
        {
            "provider_id": provider_id,
            "error_type": "RATE_LIMIT_EXCEEDED",
            "language": "zh",
            "user_message_template": "Too many requests. Please wait {wait_time} seconds",
            "suggestions": ["Wait and retry", "Reduce request frequency"]
        },
        {
            "provider_id": provider_id,
            "error_type": "TIMEOUT",
            "language": "zh",
            "user_message_template": "Request timeout. Service response time too long",
            "suggestions": ["Retry later", "Try reducing image size"]
        },
        {
            "provider_id": provider_id,
            "error_type": "SERVER_ERROR",
            "language": "zh",
            "user_message_template": "Service temporarily unavailable. Please try again later",
            "suggestions": ["Retry later", "Contact support"]
        }
    ]

    async with AsyncSessionLocal() as session:
        for msg_data in messages:
            message = ErrorMessageTemplate(**msg_data)
            session.add(message)
        await session.commit()
        print(f"[OK] {len(messages)} error message templates added")


async def main():
    print("Starting seed data...")

    await seed_dalle()
    await seed_doubao()

    # Get provider_id and add error configs
    from app.db.session import AsyncSessionLocal
    from app.models.model_provider import ModelProvider
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # Seed error configs for DALL-E
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "dalle")
        )
        provider = result.scalar_one_or_none()
        if provider:
            await seed_error_configs(provider.id)
            await seed_error_messages(provider.id)

        # Seed error configs for Doubao
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "doubao")
        )
        provider = result.scalar_one_or_none()
        if provider:
            await seed_error_configs(provider.id)
            await seed_error_messages(provider.id)

    print("[DONE] Seed data complete!")


if __name__ == "__main__":
    asyncio.run(main())
