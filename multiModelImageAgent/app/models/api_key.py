from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid


class APIKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    api_key_encrypted = Column(String, nullable=False)
    key_type = Column(String(20), default="production")  # production | test

    # 配额
    quota_limit = Column(Integer)
    quota_used = Column(Integer, default=0)
    quota_reset_at = Column(DateTime)

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    priority = Column(Integer, default=0)

    # 关系
    provider = relationship("ModelProvider", back_populates="api_keys")
