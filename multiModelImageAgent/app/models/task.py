from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid
import enum


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class Task(BaseModel):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(Enum(TaskType), nullable=False)
    provider_id = Column(String(36), ForeignKey("model_providers.id"))
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    # 输入输出
    input_params = Column(JSON, nullable=False)
    output = Column(JSON)
    error_message = Column(Text)

    # 关系
    provider = relationship("ModelProvider", back_populates="tasks")
    conversation_messages = relationship("ConversationMessage", back_populates="task")
