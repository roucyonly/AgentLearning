from sqlalchemy import Column, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid


class Conversation(BaseModel):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False)  # 外部用户 ID
    context = Column(JSON, default={})

    # 关系
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(BaseModel):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    task_ids = Column(JSON, default=list)  # 关联的任务 ID 列表

    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    task_id = Column(String(36), ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="conversation_messages")
