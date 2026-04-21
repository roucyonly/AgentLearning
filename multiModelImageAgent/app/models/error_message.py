from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid


class ErrorMessageTemplate(Base, TimestampMixin):
    __tablename__ = "error_message_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)

    error_type = Column(String(50), nullable=False)
    language = Column(String(10), default="zh")

    # 消息
    user_message_template = Column(Text, nullable=False)
    technical_message_template = Column(Text)

    # 建议
    suggestions = Column(JSON, default=[])
    available_variables = Column(JSON, default={})

    # 关系
    provider = relationship("ModelProvider", back_populates="error_messages")
