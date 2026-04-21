from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class ModelProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    provider_type: str = Field(..., pattern="^(image|video|audio|text)$")
    category: Optional[str] = None


class ModelProviderCreate(ModelProviderBase):
    api_endpoint: str = Field(..., min_length=1)
    auth_config: Dict[str, Any]
    parameter_schema: Dict[str, Any]
    parameter_mapping: Dict[str, str]
    response_mapping: Dict[str, str]


class ModelProviderUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = None


class ModelProviderResponse(ModelProviderBase):
    id: str
    api_endpoint: str
    api_version: Optional[str] = None
    http_method: str
    is_enabled: bool
    is_available: bool
    priority: int
    capabilities: Dict[str, Any] = {}
    cost_per_request: Optional[float] = None
    cost_per_image: Optional[float] = None
    rate_limit: Optional[int] = None
    max_concurrent: int = 10
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
