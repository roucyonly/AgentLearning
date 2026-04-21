from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageBase(BaseModel):
    role: Role
    content: str


class MessageCreate(MessageBase):
    task_ids: List[str] = []


class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    task_ids: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    user_id: str


class ConversationCreate(ConversationBase):
    context: Dict[str, Any] = {}


class ConversationUpdate(BaseModel):
    context: Optional[Dict[str, Any]] = None


class ConversationResponse(ConversationBase):
    id: str
    context: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    user_id: str


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    task_id: Optional[str] = None
