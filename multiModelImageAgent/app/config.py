from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""

    # 应用
    APP_NAME: str = "MultiModel Image Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库 (SQLite)
    DATABASE_URL: str = "sqlite+aiosqlite:///./multimodel.db"

    # Redis (可选)
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM API (用于 Agent)
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Volcengine Doubao API (用于图像生成)
    ARK_API_KEY: str = ""

    # Kling AI API (用于图像生成)
    KLING_ACCESS_KEY: str = ""
    KLING_SECRET_KEY: str = ""

    # 加密
    SECRET_KEY: str = "change-me-in-production"
    ENCRYPTION_KEY: str = "change-me-in-production"

    # 日志
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
