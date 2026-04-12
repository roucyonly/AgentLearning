"""
Milvus 向量数据库连接管理
用于 RAG 检索的向量存储
"""
from typing import Optional, List, Dict, Any
from pymilvus import (
    connections,
    Collection,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
)
from app.core.config import get_settings
from app.core.tracing import tracing_logger, get_current_tenant_id

settings = get_settings()

# 集合名称
COLLECTION_NAME = "teacher_documents"


def get_milvus_connection():
    """
    获取 Milvus 连接

    Returns:
        connections: Milvus 连接对象
    """
    try:
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port
        )
        tracing_logger.info("Milvus connected successfully")
        return connections
    except Exception as e:
        tracing_logger.error(f"Failed to connect to Milvus: {e}")
        raise


def init_collection():
    """
    初始化 Milvus 集合

    集合结构:
    - id: int64 (主键)
    - tenant_id: varchar (租户隔离)
    - vector: float_vector (文档向量)
    - text: varchar (原文)
    - metadata: varchar (JSON 元数据)
    """
    if utility.has_collection(COLLECTION_NAME):
        tracing_logger.info(f"Collection {COLLECTION_NAME} already exists")
        collection = Collection(COLLECTION_NAME)
        return collection

    # 定义字段
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536),  # OpenAI embedding dimension
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
    ]

    # 创建 Schema
    schema = CollectionSchema(
        fields=fields,
        description="Teacher documents for RAG",
        enable_dynamic_field=True
    )

    # 创建集合
    collection = Collection(
        name=COLLECTION_NAME,
        schema=schema
    )

    # 创建索引 (IVF_FLAT)
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    collection.create_index(
        field_name="vector",
        index_params=index_params
    )

    tracing_logger.info(f"Collection {COLLECTION_NAME} created successfully")
    return collection


def insert_documents(
    tenant_id: str,
    vectors: List[List[float]],
    texts: List[str],
    metadata: List[Dict[str, Any]]
) -> None:
    """
    插入文档向量

    Args:
        tenant_id: 租户 ID
        vectors: 向量列表
        texts: 原文列表
        metadata: 元数据列表
    """
    collection = Collection(COLLECTION_NAME)

    # 构建数据
    data = [
        [tenant_id] * len(vectors),  # tenant_id
        vectors,  # vector
        texts,  # text
        [str(m) for m in metadata]  # metadata
    ]

    # 插入数据
    collection.insert(data)
    collection.flush()

    tracing_logger.info(f"Inserted {len(vectors)} documents for tenant {tenant_id}")


def search_documents(
    query_vector: List[float],
    top_k: int = 5,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    搜索文档向量 (带租户隔离)

    Args:
        query_vector: 查询向量
        top_k: 返回结果数量
        tenant_id: 租户 ID (如果不提供,使用当前上下文)

    Returns:
        List[Dict[str, Any]]: 搜索结果
    """
    # 获取当前租户 ID
    if tenant_id is None:
        tenant_id = get_current_tenant_id()

    collection = Collection(COLLECTION_NAME)
    collection.load()

    # 构建查询表达式 (租户隔离核心)
    expr = f"tenant_id == '{tenant_id}'"

    # 执行搜索
    results = collection.search(
        data=[query_vector],
        anns_field="vector",
        param={"metric_type": "L2", "params": {"nprobe": 10}},
        limit=top_k,
        expr=expr,
        output_fields=["text", "metadata", "tenant_id"]
    )

    # 格式化结果
    formatted_results = []
    for hit in results[0]:
        formatted_results.append({
            "text": hit.entity.get("text"),
            "metadata": hit.entity.get("metadata"),
            "tenant_id": hit.entity.get("tenant_id"),
            "score": hit.score
        })

    tracing_logger.info(f"Found {len(formatted_results)} documents for tenant {tenant_id}")
    return formatted_results
