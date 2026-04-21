from sqlalchemy import Column, String, Boolean, Integer, Text, JSON, Numeric
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin
import uuid


class ModelProvider(Base, TimestampMixin):
    __tablename__ = "model_providers"

    # 基本信息
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)

    # 分类
    provider_type = Column(String(20), nullable=False)  # image | video | audio | text
    category = Column(String(50))

    # API 配置
    api_endpoint = Column(String(500), nullable=False)
    api_version = Column(String(20))
    http_method = Column(String(10), default="POST")

    # JSON 字段
    auth_config = Column(JSON, nullable=False)
    request_config = Column(JSON, nullable=False)
    parameter_mapping = Column(JSON, nullable=False)
    parameter_schema = Column(JSON, nullable=False)
    response_mapping = Column(JSON, nullable=False)

    # 状态
    is_enabled = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)

    # 其他
    capabilities = Column(JSON, default={})
    priority = Column(Integer, default=0)
    cost_per_request = Column(Numeric(10, 4))
    cost_per_image = Column(Numeric(10, 4))
    rate_limit = Column(Integer)
    max_concurrent = Column(Integer, default=10)
    extra_metadata = Column(JSON, default={})
    version = Column(Integer, default=1)

    # 关系
    api_keys = relationship("APIKey", back_populates="provider", cascade="all, delete-orphan")
    error_configs = relationship("ErrorHandlingConfig", back_populates="provider", cascade="all, delete-orphan")
    error_patterns = relationship("ErrorPattern", back_populates="provider", cascade="all, delete-orphan")
    error_messages = relationship("ErrorMessageTemplate", back_populates="provider", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="provider")
