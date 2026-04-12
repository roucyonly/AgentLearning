"""
LangGraph 节点实现
具体的节点逻辑
"""
from typing import Dict, Any
from app.core.tracing import tracing_logger
from app.ai.agents.graph import GraphState


async def retrieve_node(state: GraphState) -> GraphState:
    """
    检索节点 - 从向量数据库检索相关文档

    Args:
        state: 图状态

    Returns:
        更新后的状态
    """
    question = state["question"]

    tracing_logger.info(f"Retrieving documents for: {question[:50]}...")

    try:
        # 生成查询向量
        from langchain_openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings()
        query_vector = embeddings.embed_query(question)

        # 检索文档
        from app.db.vector import search_documents
        from app.core.tracing import get_current_tenant_id

        tenant_id = get_current_tenant_id()
        docs = search_documents(
            query_vector=query_vector,
            top_k=3,
            tenant_id=tenant_id
        )

        # 构建上下文
        context = "\n\n".join([doc["text"] for doc in docs])

        # 提取来源
        sources = [
            {
                "text": doc["text"][:200] + "...",
                "score": doc["score"]
            }
            for doc in docs
        ]

        tracing_logger.info(f"Retrieved {len(docs)} documents")

        return {
            **state,
            "context": context,
            "sources": sources
        }

    except Exception as e:
        tracing_logger.error(f"Retrieve error: {str(e)}")
        return {
            **state,
            "context": "",
            "sources": []
        }


async def generate_node(state: GraphState) -> GraphState:
    """
    生成节点 - 基于检索结果生成答案

    Args:
        state: 图状态

    Returns:
        更新后的状态
    """
    question = state["question"]
    context = state["context"]

    tracing_logger.info(f"Generating answer for: {question[:50]}...")

    try:
        # 获取教师分身配置
        from app.db.session import SessionLocal
        from app.models.database import TeacherProfile
        from app.core.tracing import get_current_tenant_id

        db = SessionLocal()
        tenant_id = get_current_tenant_id()

        teacher_profile = db.query(TeacherProfile).filter(
            TeacherProfile.user_id == int(tenant_id)
        ).first()

        if not teacher_profile:
            raise ValueError("未找到教师分身配置")

        # 构建提示词
        from app.ai.prompts.templates import get_rag_prompt
        prompt = get_rag_prompt(
            teacher_name=teacher_profile.name,
            personality=teacher_profile.personality,
            catchphrase=teacher_profile.catchphrase,
            context=context,
            question=question
        )

        # 生成答案
        from app.core.config import get_llm
        llm = get_llm()
        response = llm.invoke(prompt)
        answer = response.content

        db.close()

        tracing_logger.info(f"Answer generated: {answer[:50]}...")

        return {
            **state,
            "answer": answer
        }

    except Exception as e:
        tracing_logger.error(f"Generate error: {str(e)}")
        return {
            **state,
            "answer": f"抱歉,生成答案时出错: {str(e)}"
        }
