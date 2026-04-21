"""
Chroma 向量数据库连接管理 (轻量级方案)
用于 RAG 检索的向量存储
"""
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import get_settings
from app.core.tracing import tracing_logger, get_current_tenant_id

settings = get_settings()

# 集合名称
COLLECTION_NAME = "teacher_documents"

# 持久化路径
CHROMA_PERSIST_DIR = "./chroma_db"


class ChromaVectorStore:
    """Chroma 向量存储管理类"""

    def __init__(self):
        """初始化 Chroma 客户端"""
        try:
            # 使用持久化存储
            self.client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            tracing_logger.info(f"Chroma client initialized with persist dir: {CHROMA_PERSIST_DIR}")
        except Exception as e:
            tracing_logger.error(f"Failed to initialize Chroma client: {e}")
            raise

    def get_or_create_collection(self, tenant_id: str):
        """
        获取或创建租户专属集合

        Args:
            tenant_id: 租户 ID

        Returns:
            Collection: Chroma 集合对象
        """
        collection_name = f"{COLLECTION_NAME}_{tenant_id}"

        try:
            # 获取或创建集合
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "l2"}  # 使用 L2 距离
            )
            tracing_logger.info(f"Collection {collection_name} ready")
            return collection
        except Exception as e:
            tracing_logger.error(f"Failed to get/create collection {collection_name}: {e}")
            raise

    def insert_documents(
        self,
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
        collection = self.get_or_create_collection(tenant_id)

        # 生成 ID 列表
        ids = [f"{tenant_id}_{i}" for i in range(len(vectors))]

        # 插入数据
        collection.add(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadata
        )

        tracing_logger.info(f"Inserted {len(vectors)} documents for tenant {tenant_id}")

    def search_documents(
        self,
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

        collection = self.get_or_create_collection(tenant_id)

        # 执行搜索
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )

        # 格式化结果
        formatted_results = []
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "tenant_id": tenant_id,
                    "score": 1.0 - results['distances'][0][i] if 'distances' in results else 0.0  # 转换为相似度
                })

        tracing_logger.info(f"Found {len(formatted_results)} documents for tenant {tenant_id}")
        return formatted_results

    def delete_tenant_data(self, tenant_id: str) -> None:
        """
        删除租户的所有数据

        Args:
            tenant_id: 租户 ID
        """
        collection_name = f"{COLLECTION_NAME}_{tenant_id}"

        try:
            self.client.delete_collection(collection_name)
            tracing_logger.info(f"Deleted collection {collection_name} for tenant {tenant_id}")
        except Exception as e:
            tracing_logger.error(f"Failed to delete collection {collection_name}: {e}")
            raise

    def get_collection_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        获取集合统计信息

        Args:
            tenant_id: 租户 ID

        Returns:
            Dict[str, Any]: 统计信息
        """
        collection = self.get_or_create_collection(tenant_id)
        count = collection.count()

        return {
            "tenant_id": tenant_id,
            "document_count": count,
            "collection_name": collection.name
        }


# 全局单例
_vector_store: Optional[ChromaVectorStore] = None


def get_vector_store() -> ChromaVectorStore:
    """获取向量存储单例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore()
    return _vector_store


# 兼容原有 API 的函数
def init_collection():
    """初始化集合 (兼容接口)"""
    return get_vector_store()


def insert_documents(
    tenant_id: str,
    vectors: List[List[float]],
    texts: List[str],
    metadata: List[Dict[str, Any]]
) -> None:
    """插入文档 (兼容接口)"""
    vector_store = get_vector_store()
    vector_store.insert_documents(tenant_id, vectors, texts, metadata)


def search_documents(
    query_vector: List[float],
    top_k: int = 5,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """搜索文档 (兼容接口)"""
    vector_store = get_vector_store()
    return vector_store.search_documents(query_vector, top_k, tenant_id)