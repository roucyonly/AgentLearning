"""
PostgreSQL 数据库连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import get_settings
from app.core.tracing import tracing_logger

settings = get_settings()

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,  # 生产环境设为 False
    pool_size=5,
    max_overflow=10
)

# 创建 SessionLocal 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话

    使用方式:
    ```python
    db: Session = next(get_db())
    ```
    或在 FastAPI 路由中:
    ```python
    @app.get("/users")
    def get_users(db: Session = Depends(get_db)):
        ...
    ```
    """
    db = SessionLocal()
    try:
        tracing_logger.info("Database session created")
        yield db
    finally:
        db.close()
        tracing_logger.info("Database session closed")


def init_db():
    """
    初始化数据库,创建所有表
    """
    from app.models.database import Base
    Base.metadata.create_all(bind=engine)
    tracing_logger.info("Database tables created")
