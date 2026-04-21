"""
多厂商 LLM 配置
支持 OpenAI / Anthropic / 智谱 / DeepSeek / SiliconFlow
"""
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models.tongyi import ChatTongyi
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """系统配置"""
    # LLM 厂商配置
    active_llm: Literal["openai", "anthropic", "zhipu", "deepseek", "siliconflow"] = "openai"

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    # Anthropic
    anthropic_api_key: str = ""

    # 智谱
    zhipu_api_key: str = ""

    # DeepSeek
    deepseek_api_key: str = ""

    # SiliconFlow
    siliconflow_api_key: str = ""

    # 数据库
    database_url: str = "sqlite:///./teacher_avatar.db"  # 默认使用SQLite
    # PostgreSQL配置 (如需使用PostgreSQL,请修改上面的database_url为:)
    # database_url: str = "postgresql://user:password@localhost:5432/teacher_avatar"

    # 向量数据库选择
    vector_store_type: Literal["milvus", "chroma"] = "chroma"  # 默认使用Chroma

    # Milvus配置 (仅当vector_store_type="milvus"时需要)
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    # Chroma配置 (仅当vector_store_type="chroma"时需要,已内置默认值)
    chroma_persist_dir: str = "./chroma_db"

    redis_url: str = "redis://localhost:6379/0"

    # 安全
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "teacher-avatar"

    # 文件上传
    max_upload_size: int = 10485760  # 10MB
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


def get_llm():
    """
    根据配置获取 LLM 实例
    支持多厂商动态切换
    """
    settings = get_settings()
    provider = settings.active_llm

    if provider == "openai":
        return ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            api_key=settings.anthropic_api_key,
            temperature=0.7,
        )
    elif provider == "zhipu":
        return ChatTongyi(
            model="qwen-plus",
            dashscope_api_key=settings.zhipu_api_key,
            temperature=0.7,
        )
    elif provider == "deepseek":
        return ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
            temperature=0.7,
        )
    elif provider == "siliconflow":
        return ChatOpenAI(
            model="Qwen/Qwen2.5-7B-Instruct",
            openai_api_key=settings.siliconflow_api_key,
            base_url="https://api.siliconflow.cn/v1",
            temperature=0.7,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


# 初始化 LangSmith
def init_langsmith():
    """初始化 LangSmith 追踪"""
    settings = get_settings()
    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
