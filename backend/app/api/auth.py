"""
认证相关 API
用户注册、登录
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import User
from app.models.schemas import UserRegister, UserLogin, Token, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.tracing import tracing_logger, get_trace_id

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    用户注册

    - **username**: 用户名 (唯一)
    - **password**: 密码 (至少 6 位)
    - **email**: 邮箱 (可选)
    - **role**: 角色 (TEACHER / STUDENT)
    """
    tracing_logger.info(f"User registration attempt: {user_data.username}")

    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        tracing_logger.warning(f"Username already exists: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 创建新用户
    new_user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        email=user_data.email,
        role=user_data.role.value
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    tracing_logger.info(f"User registered successfully: {new_user.id}")
    return new_user


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录

    - **username**: 用户名
    - **password**: 密码

    返回 JWT Token
    """
    tracing_logger.info(f"Login attempt: {user_data.username}")

    # 查找用户
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user:
        tracing_logger.warning(f"User not found: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(user_data.password, user.password_hash):
        tracing_logger.warning(f"Invalid password for user: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 生成 Token
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "role": user.role
        }
    )

    tracing_logger.info(f"User logged in successfully: {user.id}")
    return Token(
        access_token=access_token,
        user_id=user.id,
        role=user.role
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户

    从 JWT Token 中解析用户信息
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token"
        )

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息

    需要在请求头中携带 Authorization: Bearer <token>
    """
    tracing_logger.info(f"Fetching user info: {current_user.id}")
    return current_user
