from sqlalchemy import Column, Date, Integer, String, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid


class ModelUsageStats(BaseModel):
    __tablename__ = "model_usage_stats"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), ForeignKey("model_providers.id", ondelete="CASCADE"), nullable=False)

    # 统计维度
    date = Column(Date, nullable=False)
    hour = Column(Integer)  # 0-23

    # 调用统计
    total_calls = Column(Integer, default=0)
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)

    # 错误分布
    error_distribution = Column(JSON, default={})

    # 性能 (毫秒)
    avg_response_time = Column(Numeric(10, 2))
    p50_response_time = Column(Numeric(10, 2))
    p95_response_time = Column(Numeric(10, 2))
    p99_response_time = Column(Numeric(10, 2))

    # 成本
    total_cost = Column(Numeric(10, 4))
