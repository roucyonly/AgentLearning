from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.api.dependencies import get_db, get_task_service
from app.schemas.task import TaskCreate, TaskResponse, TaskStatus
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    task_service: TaskService = Depends(get_task_service)
):
    """获取任务列表（支持分页）"""
    status = TaskStatus(status_filter) if status_filter else None
    tasks = await task_service.list_tasks(status=status, skip=skip, limit=limit)

    return [
        TaskResponse(
            id=task.id,
            type=task.type.value,
            provider_id=task.provider_id,
            status=task.status.value,
            input_params=task.input_params,
            output=task.output,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.output.get("completed_at") if task.output else None
        )
        for task in tasks
    ]


@router.post("/", response_model=TaskResponse)
async def create_task(
    request: TaskCreate,
    task_service: TaskService = Depends(get_task_service)
):
    """直接创建任务，跳过对话"""
    try:
        task = await task_service.create_task(
            task_type=request.type,
            input_params=request.input_params,
            provider_name=request.provider_name
        )

        return TaskResponse(
            id=task.id,
            type=task.type.value,
            provider_name=request.provider_name,
            provider_id=task.provider_id,
            status=task.status.value,
            input_params=task.input_params,
            created_at=task.created_at,
            updated_at=task.updated_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """获取任务状态和结果"""
    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在: {task_id}"
        )

    return TaskResponse(
        id=task.id,
        type=task.type.value,
        provider_id=task.provider_id,
        status=task.status.value,
        input_params=task.input_params,
        output=task.output,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.output.get("completed_at") if task.output else None
    )


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """执行任务"""
    try:
        task = await task_service.execute_task(task_id)

        return {
            "task_id": task.id,
            "status": task.status.value,
            "output": task.output,
            "error_message": task.error_message
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行任务失败: {str(e)}"
        )


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
):
    """取消任务"""
    try:
        task = await task_service.cancel_task(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {task_id}"
            )

        return {
            "task_id": task.id,
            "status": task.status.value,
            "message": "任务已取消"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
