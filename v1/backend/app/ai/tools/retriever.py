"""
RAG 检索器
向量检索核心逻辑
"""
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from app.core.tracing import tracing_logger, get_current_tenant_id
from app.db.vector import search_documents


class TenantAwareRetriever:
    """
    租户感知的检索器

    自动从上下文获取 tenant_id,确保租户隔离
    """

    def __init__(self, embeddings: Optional[OpenAIEmbeddings] = None):
        """
        初始化检索器

        Args:
            embeddings: OpenAI Embeddings 实例
        """
        self.embeddings = embeddings or OpenAIEmbeddings()
        tracing_logger.info("TenantAwareRetriever initialized")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回结果数量
            tenant_id: 租户 ID (如果不提供,使用当前上下文)

        Returns:
            检索结果列表
        """
        tracing_logger.info(f"Retrieving for query: {query[:50]}...")

        # 生成查询向量
        try:
            query_vector = self.embeddings.embed_query(query)
        except Exception as e:
            tracing_logger.error(f"Embedding error: {str(e)}")
            return []

        # 检索文档
        try:
            docs = search_documents(
                query_vector=query_vector,
                top_k=top_k,
                tenant_id=tenant_id
            )
            tracing_logger.info(f"Retrieved {len(docs)} documents")
            return docs
        except Exception as e:
            tracing_logger.error(f"Search error: {str(e)}")
            return []

    def retrieve_with_scores(
        self,
        query: str,
        top_k: int = 5,
        tenant_id: Optional[str] = None
    ) -> List[tuple[Dict[str, Any], float]]:
        """
        检索相关文档并返回分数

        Args:
            query: 查询文本
            top_k: 返回结果数量
            tenant_id: 租户 ID

        Returns:
            (文档, 分数) 元组列表
        """
        docs = self.retrieve(query, top_k, tenant_id)
        return [(doc, doc.get("score", 0.0)) for doc in docs]


def create_retriever() -> TenantAwareRetriever:
    """
    创建检索器实例

    Returns:
        TenantAwareRetriever 实例
    """
    return TenantAwareRetriever()


# 便捷函数
def retrieve_documents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    便捷函数: 检索文档

    Args:
        query: 查询文本
        top_k: 返回结果数量

    Returns:
        检索结果列表
    """
    retriever = create_retriever()
    return retriever.retrieve(query, top_k)
