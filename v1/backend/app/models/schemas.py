"""
Pydantic 模型
用于请求/响应验证
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== 通用模型 ====================

class UserRole(str, Enum):
    """用户角色"""
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class ResponseModel(BaseModel):
    """通用响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


# ==================== 认证相关 ====================

class UserRegister(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    email: Optional[EmailStr] = None
    role: UserRole


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class Token(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str] = None
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 教师相关 ====================

class TeacherProfileCreate(BaseModel):
    """创建教师分身请求"""
    avatar_prompt: str = Field(..., description="数字分身提示词")
    name: str = Field(..., min_length=1, max_length=100, description="分身名称")
    personality: str = Field(..., description="性格特征")
    catchphrase: str = Field(..., max_length=200, description="口头禅")


class TeacherProfileUpdate(BaseModel):
    """更新教师分身请求"""
    avatar_prompt: Optional[str] = None
    name: Optional[str] = None
    personality: Optional[str] = None
    catchphrase: Optional[str] = None


class TeacherProfileResponse(BaseModel):
    """教师分身响应"""
    id: int
    user_id: int
    avatar_prompt: str
    name: str
    personality: str
    catchphrase: str
    created_at: datetime

    class Config:
        from_attributes = True


class ClassCreate(BaseModel):
    """创建班级请求"""
    class_name: str = Field(..., min_length=1, max_length=100)


class ClassResponse(BaseModel):
    """班级响应"""
    id: int
    teacher_id: int
    class_name: str
    invite_code: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 学生相关 ====================

class StudentJoinClass(BaseModel):
    """学生加入班级请求"""
    invite_code: str = Field(..., min_length=1, max_length=20)


class StudentClassResponse(BaseModel):
    """学生班级响应"""
    id: int
    student_id: int
    class_id: int
    class_name: str
    teacher_name: str

    class Config:
        from_attributes = True


# ==================== 对话相关 ====================

class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., min_length=1, max_length=2000)
    stream: bool = False


class ChatResponse(BaseModel):
    """对话响应"""
    answer: str
    sources: Optional[List[dict]] = None
    trace_id: str


# ==================== 文档相关 ====================

class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: int
    filename: str
    chunk_count: int
    status: str
