"""
教师相关 API
分身管理、班级管理
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import User, TeacherProfile, Class
from app.models.schemas import (
    TeacherProfileCreate,
    TeacherProfileUpdate,
    TeacherProfileResponse,
    ClassCreate,
    ClassResponse
)
from app.core.tracing import tracing_logger, get_current_tenant_id
from app.api.auth import get_current_user
import secrets
import string

router = APIRouter()


def generate_invite_code(length=8):
    """生成班级邀请码"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/profile", response_model=TeacherProfileResponse)
async def create_teacher_profile(
    profile_data: TeacherProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建教师数字分身配置

    - **avatar_prompt**: 数字分身提示词
    - **name**: 分身名称
    - **personality**: 性格特征
    - **catchphrase**: 口头禅
    """
    # 检查用户是否为教师
    if current_user.role != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能创建分身"
        )

    tracing_logger.info(f"Creating teacher profile for user: {current_user.id}")

    # 检查是否已有分身配置
    existing = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已存在分身配置,请使用更新接口"
        )

    # 创建分身配置
    new_profile = TeacherProfile(
        user_id=current_user.id,
        **profile_data.dict()
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    tracing_logger.info(f"Teacher profile created: {new_profile.id}")
    return new_profile


@router.get("/profile", response_model=TeacherProfileResponse)
async def get_teacher_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取教师分身配置"""
    if current_user.role != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能查看分身配置"
        )

    profile = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到分身配置"
        )

    return profile


@router.put("/profile", response_model=TeacherProfileResponse)
async def update_teacher_profile(
    profile_data: TeacherProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新教师分身配置"""
    if current_user.role != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能更新分身配置"
        )

    profile = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到分身配置"
        )

    # 更新字段
    update_data = profile_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    tracing_logger.info(f"Teacher profile updated: {profile.id}")
    return profile


@router.post("/classes", response_model=ClassResponse)
async def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建班级

    - **class_name**: 班级名称

    返回班级信息和邀请码
    """
    if current_user.role != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能创建班级"
        )

    tracing_logger.info(f"Creating class for teacher: {current_user.id}")

    # 生成唯一邀请码
    while True:
        invite_code = generate_invite_code()
        existing = db.query(Class).filter(Class.invite_code == invite_code).first()
        if not existing:
            break

    new_class = Class(
        teacher_id=current_user.id,
        class_name=class_data.class_name,
        invite_code=invite_code
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    tracing_logger.info(f"Class created: {new_class.id} with invite code: {invite_code}")
    return new_class


@router.get("/classes", response_model=list[ClassResponse])
async def get_teacher_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取教师的所有班级"""
    if current_user.role != "TEACHER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能查看班级"
        )

    classes = db.query(Class).filter(
        Class.teacher_id == current_user.id
    ).all()

    return classes
