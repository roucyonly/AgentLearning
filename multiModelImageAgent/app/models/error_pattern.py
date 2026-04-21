from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid


class ErrorPattern(BaseModel):
    __tablename__ = "error_patterns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)

    # 匹配规则
    pattern_type = Column(String(20), nullable=False)  # status_code | error_code | message_pattern | regex
    pattern_value = Column(String(500), nullable=False)

    # 映射
    error_type = Column(String(50), nullable=False)
    priority = Column(Integer, default=0)

    # 提取
    extract_fields = Column(JSON, default={})
    is_active = Column(Boolean, default=True)

    # 关系
    provider = relationship("ModelProvider", back_populates="error_patterns")
