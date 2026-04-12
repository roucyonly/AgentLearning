"""
数据库初始化脚本
创建所有数据库表和 Milvus 集合
"""
from app.db.session import init_db
from app.db.vector import init_collection
from app.core.config import init_langsmith
from app.core.tracing import tracing_logger


def main():
    """初始化数据库"""
    tracing_logger.info("Starting database initialization...")

    # 初始化 LangSmith
    init_langsmith()

    # 初始化 PostgreSQL 表
    init_db()

    # 初始化 Milvus 集合
    init_collection()

    tracing_logger.info("Database initialization completed!")


if __name__ == "__main__":
    main()
