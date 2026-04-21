#!/usr/bin/env python
"""Seed data - Add default model configuration"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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

DOUBAO_SEEDREAM_CONFIG = {
    "name": "doubao_seedream",
    "display_name": "Doubao Seedream",
    "description": "Volcengine Doubao Seedream image generation model",
    "provider_type": "image",
    "category": "volcengine",
    "api_endpoint": "https://ark.cn-beijing.volces.com/api/v3/images/generations",
    "api_version": "v3",
    "http_method": "POST",
    "auth_config": {
        "type": "bearer",
        "key_field": "Authorization"
    },
    "request_config": {
        "timeout": 120,
        "retry_enabled": True
    },
    "parameter_mapping": {
        "prompt": "prompt",
        "model": "model",
        "size": "size",
        "image": "image",
        "sequential_image_generation": "sequential_image_generation",
        "sequential_image_generation_options": "sequential_image_generation_options",
        "output_format": "output_format",
        "watermark": "watermark"
    },
    "parameter_schema": {
        "prompt": {"type": "string", "required": True},
        "model": {"type": "string", "required": True, "default": "doubao-seedream-5-0-260128"},
        "size": {"type": "string", "required": False, "enum": ["1K", "2K", "4K"]},
        "image": {"type": "array", "required": False},
        "sequential_image_generation": {"type": "string", "required": False},
        "output_format": {"type": "string", "required": False, "enum": ["png", "jpg"]},
        "watermark": {"type": "boolean", "required": False, "default": False}
    },
    "response_mapping": {
        "images": "data",
        "image_url": "data.0.url",
        "revised_prompt": "data.0.revised_prompt"
    },
    "is_enabled": True,
    "is_available": True,
    "priority": 5,
    "capabilities": ["text_to_image", "image_to_image", "sequential_generation", "style_control"],
    "rate_limit": 20,
    "max_concurrent": 3
}

KLING_CONFIG = {
    "name": "kling",
    "display_name": "Kling AI",
    "description": "Kling AI image generation model",
    "provider_type": "image",
    "category": "kling",
    "api_endpoint": "https://api-beijing.klingai.com/v1/images/generations",
    "api_version": "v1",
    "http_method": "POST",
    "auth_config": {
        "type": "bearer",
        "key_field": "Authorization"
    },
    "request_config": {
        "timeout": 120,
        "retry_enabled": True
    },
    "parameter_mapping": {
        "prompt": "prompt",
        "model_name": "model_name",
        "negative_prompt": "negative_prompt",
        "image": "image",
        "n": "n",
        "external_task_id": "external_task_id",
        "callback_url": "callback_url"
    },
    "parameter_schema": {
        "prompt": {"type": "string", "required": True},
        "model_name": {"type": "string", "required": True, "default": "kling-v2-1"},
        "negative_prompt": {"type": "string", "required": False},
        "image": {"type": "string", "required": False},
        "n": {"type": "integer", "required": False, "default": 1},
        "external_task_id": {"type": "string", "required": False},
        "callback_url": {"type": "string", "required": False}
    },
    "response_mapping": {
        "task_id": "task_id",
        "task_status": "task_status",
        "images": "data.images",
        "image_url": "data.images.0.url"
    },
    "is_enabled": True,
    "is_available": True,
    "priority": 10,
    "capabilities": ["text_to_image", "image_to_image", "negative_prompt"],
    "rate_limit": 20,
    "max_concurrent": 3
}


async def seed_doubao():
    """Add Doubao LLM configuration for intent recognition"""
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
            print("[OK] Doubao LLM configuration added")
        else:
            print("[INFO] Doubao LLM configuration already exists")


async def seed_doubao_seedream():
    """Add Doubao Seedream configuration for image generation"""
    from app.db.session import AsyncSessionLocal
    from app.models.model_provider import ModelProvider
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "doubao_seedream")
        )
        existing = result.scalar_one_or_none()

        if not existing:
            provider = ModelProvider(**DOUBAO_SEEDREAM_CONFIG)
            session.add(provider)
            await session.commit()
            print("[OK] Doubao Seedream configuration added")
        else:
            print("[INFO] Doubao Seedream configuration already exists")


async def seed_kling():
    """Add Kling configuration for image generation"""
    from app.db.session import AsyncSessionLocal
    from app.models.model_provider import ModelProvider
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "kling")
        )
        existing = result.scalar_one_or_none()

        if not existing:
            provider = ModelProvider(**KLING_CONFIG)
            session.add(provider)
            await session.commit()
            print("[OK] Kling configuration added")
        else:
            print("[INFO] Kling configuration already exists")


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

    await seed_doubao()
    await seed_doubao_seedream()
    await seed_kling()

    # Get provider_id and add error configs
    from app.db.session import AsyncSessionLocal
    from app.models.model_provider import ModelProvider
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # Seed error configs for Doubao LLM
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "doubao")
        )
        provider = result.scalar_one_or_none()
        if provider:
            await seed_error_configs(provider.id)
            await seed_error_messages(provider.id)

        # Seed error configs for Doubao Seedream
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "doubao_seedream")
        )
        provider = result.scalar_one_or_none()
        if provider:
            await seed_error_configs(provider.id)
            await seed_error_messages(provider.id)

        # Seed error configs for Kling
        result = await session.execute(
            select(ModelProvider).where(ModelProvider.name == "kling")
        )
        provider = result.scalar_one_or_none()
        if provider:
            await seed_error_configs(provider.id)
            await seed_error_messages(provider.id)

    print("[DONE] Seed data complete!")


if __name__ == "__main__":
    asyncio.run(main())
