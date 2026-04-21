from sqlalchemy import Column, String, Boolean, Integer, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid


class ErrorHandlingConfig(BaseModel):
    __tablename__ = "error_handling_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)
    error_type = Column(String(50), nullable=False)

    # 重试策略
    retry_enabled = Column(Boolean, default=True)
    max_attempts = Column(Integer, default=3)
    base_wait_time = Column(Numeric(5, 2), default=1.0)
    max_wait_time = Column(Numeric(5, 2), default=60.0)
    exponential_base = Column(Numeric(3, 1), default=2.0)

    # 参数修正
    auto_fix_enabled = Column(Boolean, default=False)
    fix_rules = Column(JSON, default={})

    # 降级
    fallback_providers = Column(JSON)  # 字符串列表
    custom_handler = Column(String(100))

    # 关系
    provider = relationship("ModelProvider", back_populates="error_configs")
