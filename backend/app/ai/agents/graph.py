"""
LangGraph 状态机
实现 RAG 问答的核心流程
"""
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import get_llm
from app.core.tracing import tracing_logger, get_current_tenant_id
import operator


class GraphState(TypedDict):
    """图状态定义"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    question: str
    context: str
    answer: str
    sources: list


def create_rag_chain():
    """
    创建 RAG 链

    流程:
    1. 接收学生问题
    2. 生成问题向量
    3. 从 Milvus 检索相关文档 (租户隔离)
    4. 构建提示词
    5. 生成答案
    6. 返回结果
    """
    # 初始化模型
    llm = get_llm()
    embeddings = OpenAIEmbeddings()

    # 创建图
    workflow = StateGraph(GraphState)

    # 添加节点
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)

    # 设置入口
    workflow.set_entry_point("retrieve")

    # 添加边
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)

    # 编译图
    app = workflow.compile()

    tracing_logger.info("RAG chain created successfully")
    return app


async def retrieve_node(state: GraphState) -> GraphState:
    """
    检索节点

    功能:
    1. 获取问题向量
    2. 从 Milvus 检索相关文档
    3. 返回上下文
    """
    question = state["question"]

    tracing_logger.info(f"Retrieving documents for question: {question[:50]}...")

    try:
        # 生成查询向量
        embeddings = OpenAIEmbeddings()
        query_vector = embeddings.embed_query(question)

        # 检索文档 (带租户隔离)
        from app.db.vector import search_documents
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
        tracing_logger.error(f"Retrieve node error: {str(e)}")
        return {
            **state,
            "context": "",
            "sources": []
        }


async def generate_node(state: GraphState) -> GraphState:
    """
    生成节点

    功能:
    1. 获取教师分身配置
    2. 构建提示词
    3. 调用 LLM 生成答案
    """
    question = state["question"]
    context = state["context"]

    tracing_logger.info(f"Generating answer for question: {question[:50]}...")

    try:
        # 获取教师分身配置
        from app.db.session import SessionLocal
        from app.models.database import TeacherProfile

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
        tracing_logger.error(f"Generate node error: {str(e)}")
        return {
            **state,
            "answer": f"抱歉,生成答案时出错: {str(e)}"
        }


async def run_rag_pipeline(question: str) -> dict:
    """
    运行 RAG 流水线

    Args:
        question: 学生问题

    Returns:
        dict: 包含 answer 和 sources 的结果
    """
    app = create_rag_chain()

    # 初始化状态
    initial_state = {
        "messages": [],
        "question": question,
        "context": "",
        "answer": "",
        "sources": []
    }

    # 运行图
    result = await app.ainvoke(initial_state)

    return {
        "answer": result["answer"],
        "sources": result["sources"]
    }
