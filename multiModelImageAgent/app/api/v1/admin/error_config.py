from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.schemas.error import (
    ErrorHandlingConfigCreate,
    ErrorHandlingConfigResponse,
    ErrorPatternCreate,
    ErrorPatternResponse,
    ErrorMessageTemplateCreate,
    ErrorMessageTemplateResponse,
)
from app.repositories.error_handling import (
    ErrorHandlingConfigRepository,
    ErrorPatternRepository,
    ErrorMessageRepository,
)

router = APIRouter(prefix="/models/{model_id}/error-config", tags=["admin:error"])


@router.get("/", response_model=List[ErrorHandlingConfigResponse])
async def get_error_configs(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取错误处理配置列表"""
    repo = ErrorHandlingConfigRepository(db)
    configs = await repo.get_by_provider(model_id)

    return [
        ErrorHandlingConfigResponse(
            id=c.id,
            provider_id=c.provider_id,
            error_type=c.error_type,
            retry_enabled=c.retry_enabled,
            max_attempts=c.max_attempts,
            base_wait_time=float(c.base_wait_time),
            max_wait_time=float(c.max_wait_time),
            exponential_base=float(c.exponential_base),
            auto_fix_enabled=c.auto_fix_enabled,
            fix_rules=c.fix_rules or {},
            fallback_providers=c.fallback_providers,
            custom_handler=c.custom_handler,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in configs
    ]


@router.post("/", response_model=ErrorHandlingConfigResponse)
async def create_error_config(
    model_id: str,
    request: ErrorHandlingConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建错误处理配置"""
    repo = ErrorHandlingConfigRepository(db)

    data = request.model_dump()
    data["provider_id"] = model_id

    config = await repo.create(data)

    return ErrorHandlingConfigResponse(
        id=config.id,
        provider_id=config.provider_id,
        error_type=config.error_type,
        retry_enabled=config.retry_enabled,
        max_attempts=config.max_attempts,
        base_wait_time=float(config.base_wait_time),
        max_wait_time=float(config.max_wait_time),
        exponential_base=float(config.exponential_base),
        auto_fix_enabled=config.auto_fix_enabled,
        fix_rules=config.fix_rules or {},
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("/{config_id}", response_model=ErrorHandlingConfigResponse)
async def update_error_config(
    model_id: str,
    config_id: str,
    request: ErrorHandlingConfigCreate,
    db: AsyncSession = Depends(get_db)
):
    """更新错误处理配置"""
    repo = ErrorHandlingConfigRepository(db)

    existing = await repo.get(config_id)
    if not existing or existing.provider_id != model_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置不存在: {config_id}"
        )

    update_data = request.model_dump()
    config = await repo.update(config_id, update_data)

    return ErrorHandlingConfigResponse(
        id=config.id,
        provider_id=config.provider_id,
        error_type=config.error_type,
        retry_enabled=config.retry_enabled,
        max_attempts=config.max_attempts,
        base_wait_time=float(config.base_wait_time),
        max_wait_time=float(config.max_wait_time),
        exponential_base=float(config.exponential_base),
        auto_fix_enabled=config.auto_fix_enabled,
        fix_rules=config.fix_rules or {},
        created_at=config.created_at,
        updated_at=config.updated_at
    )


# Error Patterns
@router.get("/patterns", response_model=List[ErrorPatternResponse])
async def get_error_patterns(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取错误模式列表"""
    repo = ErrorPatternRepository(db)
    patterns = await repo.get_by_provider(model_id)

    return [
        ErrorPatternResponse(
            id=p.id,
            provider_id=p.provider_id,
            pattern_type=p.pattern_type,
            pattern_value=p.pattern_value,
            error_type=p.error_type,
            priority=p.priority,
            extract_fields=p.extract_fields or {},
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in patterns
    ]


@router.post("/patterns", response_model=ErrorPatternResponse)
async def create_error_pattern(
    model_id: str,
    request: ErrorPatternCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建错误模式"""
    repo = ErrorPatternRepository(db)

    data = request.model_dump()
    data["provider_id"] = model_id

    pattern = await repo.create(data)

    return ErrorPatternResponse(
        id=pattern.id,
        provider_id=pattern.provider_id,
        pattern_type=pattern.pattern_type,
        pattern_value=pattern.pattern_value,
        error_type=pattern.error_type,
        priority=pattern.priority,
        extract_fields=pattern.extract_fields or {},
        is_active=pattern.is_active,
        created_at=pattern.created_at,
        updated_at=pattern.updated_at
    )


# Error Messages
@router.get("/messages", response_model=List[ErrorMessageTemplateResponse])
async def get_error_messages(
    model_id: str,
    language: str = "zh",
    db: AsyncSession = Depends(get_db)
):
    """获取错误消息模板列表"""
    repo = ErrorMessageRepository(db)
    messages = await repo.get_by_provider(model_id, language)

    return [
        ErrorMessageTemplateResponse(
            id=m.id,
            provider_id=m.provider_id,
            error_type=m.error_type,
            language=m.language,
            user_message_template=m.user_message_template,
            technical_message_template=m.technical_message_template,
            suggestions=m.suggestions or [],
            available_variables=m.available_variables or {},
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in messages
    ]


@router.post("/messages", response_model=ErrorMessageTemplateResponse)
async def create_error_message(
    model_id: str,
    request: ErrorMessageTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建错误消息模板"""
    repo = ErrorMessageRepository(db)

    data = request.model_dump()
    data["provider_id"] = model_id

    message = await repo.create(data)

    return ErrorMessageTemplateResponse(
        id=message.id,
        provider_id=message.provider_id,
        error_type=message.error_type,
        language=message.language,
        user_message_template=message.user_message_template,
        technical_message_template=message.technical_message_template,
        suggestions=message.suggestions or [],
        available_variables=message.available_variables or {},
        created_at=message.created_at,
        updated_at=message.updated_at
    )
