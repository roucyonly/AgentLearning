from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ErrorType(str, Enum):
    INVALID_PARAMETER = "INVALID_PARAMETER"
    INVALID_SIZE = "INVALID_SIZE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SERVER_ERROR = "SERVER_ERROR"
    TIMEOUT = "TIMEOUT"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN = "UNKNOWN"


class RetryStrategy(BaseModel):
    enabled: bool = True
    max_attempts: int = Field(default=3, ge=1, le=10)
    base_wait_time: float = Field(default=1.0, ge=0)
    max_wait_time: float = Field(default=60.0, ge=0)
    exponential_base: float = Field(default=2.0, ge=1)


class FixRule(BaseModel):
    parameter: str
    old_value: Any
    new_value: Any
    description: Optional[str] = None


class ErrorPatternBase(BaseModel):
    pattern_type: str = Field(..., pattern="^(status_code|error_code|message_pattern|regex)$")
    pattern_value: str
    error_type: ErrorType
    priority: int = 0


class ErrorPatternCreate(ErrorPatternBase):
    extract_fields: Dict[str, str] = {}


class ErrorPatternResponse(ErrorPatternBase):
    id: str
    provider_id: str
    extract_fields: Dict[str, str] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ErrorMessageTemplateBase(BaseModel):
    error_type: ErrorType
    language: str = "zh"
    user_message_template: str
    technical_message_template: Optional[str] = None
    suggestions: List[str] = []


class ErrorMessageTemplateCreate(ErrorMessageTemplateBase):
    available_variables: Dict[str, str] = {}


class ErrorMessageTemplateResponse(ErrorMessageTemplateBase):
    id: str
    provider_id: str
    available_variables: Dict[str, str] = {}
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ErrorHandlingConfigBase(BaseModel):
    error_type: ErrorType
    retry_enabled: bool = True
    max_attempts: int = Field(default=3, ge=1, le=10)
    base_wait_time: float = Field(default=1.0, ge=0)
    max_wait_time: float = Field(default=60.0, ge=0)
    exponential_base: float = Field(default=2.0, ge=1)
    auto_fix_enabled: bool = False
    fix_rules: Dict[str, Any] = {}


class ErrorHandlingConfigCreate(ErrorHandlingConfigBase):
    pass


class ErrorHandlingConfigResponse(ErrorHandlingConfigBase):
    id: str
    provider_id: str
    fallback_providers: Optional[List[str]] = None
    custom_handler: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    error_type: ErrorType
    message: str
    technical_message: Optional[str] = None
    suggestions: List[str] = []
    retry_strategy: Optional[RetryStrategy] = None
    fix_rules: List[FixRule] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
