"""
向量数据库模块
根据配置自动选择 Chroma 或 Milvus
"""
from typing import Optional, List, Dict, Any
from app.core.config import get_settings
from app.core.tracing import tracing_logger

settings = get_settings()

# 根据配置导入对应的向量存储实现
if settings.vector_store_type == "chroma":
    from app.db.vector_chroma import (
        ChromaVectorStore,
        get_vector_store,
        init_collection,
        insert_documents,
        search_documents
    )
    tracing_logger.info("Using Chroma as vector store")
elif settings.vector_store_type == "milvus":
    from app.db.vector_milvus import (
        get_milvus_connection,
        init_collection,
        insert_documents,
        search_documents
    )
    tracing_logger.info("Using Milvus as vector store")
else:
    raise ValueError(f"Unsupported vector store type: {settings.vector_store_type}")

__all__ = [
    "init_collection",
    "insert_documents",
    "search_documents",
]

# 如果是 Chroma,额外导出 ChromaVectorStore
if settings.vector_store_type == "chroma":
    __all__.extend([
        "ChromaVectorStore",
        "get_vector_store",
    ])