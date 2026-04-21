from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_db
from app.schemas.model_provider import (
    ModelProviderCreate,
    ModelProviderUpdate,
    ModelProviderResponse
)
from app.repositories.model_provider import ModelProviderRepository

router = APIRouter(prefix="/models", tags=["admin:models"])


@router.get("/", response_model=List[ModelProviderResponse])
async def list_models(
    provider_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取所有模型配置"""
    repo = ModelProviderRepository(db)

    if provider_type:
        models = await repo.get_by_type(provider_type)
    else:
        models = await repo.get_all()

    return [
        ModelProviderResponse(
            id=m.id,
            name=m.name,
            display_name=m.display_name,
            description=m.description,
            provider_type=m.provider_type,
            category=m.category,
            api_endpoint=m.api_endpoint,
            api_version=m.api_version,
            http_method=m.http_method,
            is_enabled=m.is_enabled,
            is_available=m.is_available,
            priority=m.priority,
            capabilities=m.capabilities or {},
            cost_per_request=float(m.cost_per_request) if m.cost_per_request else None,
            cost_per_image=float(m.cost_per_image) if m.cost_per_image else None,
            rate_limit=m.rate_limit,
            max_concurrent=m.max_concurrent,
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in models
    ]


@router.post("/", response_model=ModelProviderResponse)
async def create_model(
    request: ModelProviderCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新模型配置"""
    repo = ModelProviderRepository(db)

    # 检查名称是否已存在
    existing = await repo.get_by_name(request.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"模型名称已存在: {request.name}"
        )

    model = await repo.create(request.model_dump())

    return ModelProviderResponse(
        id=model.id,
        name=model.name,
        display_name=model.display_name,
        description=model.description,
        provider_type=model.provider_type,
        category=model.category,
        api_endpoint=model.api_endpoint,
        api_version=model.api_version,
        http_method=model.http_method,
        is_enabled=model.is_enabled,
        is_available=model.is_available,
        priority=model.priority,
        capabilities=model.capabilities or {},
        created_at=model.created_at,
        updated_at=model.updated_at
    )


@router.get("/{model_id}", response_model=ModelProviderResponse)
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取模型详情"""
    repo = ModelProviderRepository(db)
    model = await repo.get(model_id)

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型不存在: {model_id}"
        )

    return ModelProviderResponse(
        id=model.id,
        name=model.name,
        display_name=model.display_name,
        description=model.description,
        provider_type=model.provider_type,
        category=model.category,
        api_endpoint=model.api_endpoint,
        api_version=model.api_version,
        http_method=model.http_method,
        is_enabled=model.is_enabled,
        is_available=model.is_available,
        priority=model.priority,
        capabilities=model.capabilities or {},
        cost_per_request=float(model.cost_per_request) if model.cost_per_request else None,
        cost_per_image=float(model.cost_per_image) if model.cost_per_image else None,
        rate_limit=model.rate_limit,
        max_concurrent=model.max_concurrent,
        created_at=model.created_at,
        updated_at=model.updated_at
    )


@router.put("/{model_id}", response_model=ModelProviderResponse)
async def update_model(
    model_id: str,
    request: ModelProviderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新模型配置"""
    repo = ModelProviderRepository(db)

    existing = await repo.get(model_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型不存在: {model_id}"
        )

    update_data = request.model_dump(exclude_unset=True)
    model = await repo.update(model_id, update_data)

    return ModelProviderResponse(
        id=model.id,
        name=model.name,
        display_name=model.display_name,
        description=model.description,
        provider_type=model.provider_type,
        category=model.category,
        api_endpoint=model.api_endpoint,
        api_version=model.api_version,
        http_method=model.http_method,
        is_enabled=model.is_enabled,
        is_available=model.is_available,
        priority=model.priority,
        capabilities=model.capabilities or {},
        created_at=model.created_at,
        updated_at=model.updated_at
    )


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除模型配置"""
    repo = ModelProviderRepository(db)

    existing = await repo.get(model_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型不存在: {model_id}"
        )

    await repo.delete(model_id)

    return {"message": "删除成功", "model_id": model_id}


@router.patch("/{model_id}/toggle")
async def toggle_model(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """启用/禁用模型"""
    repo = ModelProviderRepository(db)

    model = await repo.get(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型不存在: {model_id}"
        )

    updated = await repo.update(model_id, {"is_enabled": not model.is_enabled})

    return {
        "model_id": model_id,
        "is_enabled": updated.is_enabled,
        "message": f"模型已{'启用' if updated.is_enabled else '禁用'}"
    }


@router.post("/{model_id}/test")
async def test_model_connection(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """测试模型连接"""
    repo = ModelProviderRepository(db)

    model = await repo.get(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"模型不存在: {model_id}"
        )

    # TODO: 实现实际的连接测试
    # 目前返回模拟结果
    return {
        "model_id": model_id,
        "status": "success",
        "message": "连接测试成功"
    }
