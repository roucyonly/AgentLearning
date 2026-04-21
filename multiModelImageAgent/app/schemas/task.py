from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TaskType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskBase(BaseModel):
    type: TaskType
    provider_name: Optional[str] = None


class TaskCreate(TaskBase):
    input_params: Dict[str, Any]


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskResponse(TaskBase):
    id: str
    provider_id: Optional[str] = None
    status: TaskStatus
    input_params: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
