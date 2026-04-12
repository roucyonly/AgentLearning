"""
对话相关 API
RAG 问答接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.database import User, TeacherProfile
from app.models.schemas import ChatRequest, ChatResponse
from app.core.tracing import tracing_logger, get_trace_id, get_current_tenant_id
from app.api.auth import get_current_user
from app.ai.agents.graph import create_rag_chain

router = APIRouter()

# 初始化 Embeddings
embeddings = OpenAIEmbeddings(openai_api_key="your-api-key")


@router.post("/", response_model=ChatResponse)
async def chat(
    chat_data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RAG 问答接口

    - **message**: 学生问题
    - **stream**: 是否流式返回 (暂未实现)

    返回基于教师文档的答案
    """
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生才能使用对话功能"
        )

    trace_id = get_trace_id()
    tenant_id = get_current_tenant_id()

    tracing_logger.info(f"Chat request from user {current_user.id}: {chat_data.message[:50]}...")

    # 获取教师分身配置
    teacher_profile = db.query(TeacherProfile).filter(
        TeacherProfile.user_id == int(tenant_id)
    ).first()

    if not teacher_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到教师分身配置"
        )

    try:
        # 生成查询向量
        query_embedding = embeddings.embed_query(chat_data.message)

        # 检索相关文档 (从 Milvus)
        from app.db.vector import search_documents
        docs = search_documents(
            query_vector=query_embedding,
            top_k=3,
            tenant_id=tenant_id
        )

        # 构建上下文
        context = "\n\n".join([doc["text"] for doc in docs])

        # 生成答案
        from app.core.config import get_llm
        llm = get_llm()

        prompt = f"""
你是教师数字分身 {teacher_profile.name}。

**性格特征:** {teacher_profile.personality}
**口头禅:** {teacher_profile.catchphrase}

**参考文档:**
{context}

**学生问题:** {chat_data.message}

请基于参考文档,以教师的身份回答问题。如果文档中没有相关信息,请礼貌地说明。
"""

        response = llm.invoke(prompt)
        answer = response.content

        # 构建响应
        sources = [
            {
                "text": doc["text"][:200] + "...",
                "score": doc["score"]
            }
            for doc in docs
        ]

        tracing_logger.info(f"Chat response generated for trace_id: {trace_id}")

        return ChatResponse(
            answer=answer,
            sources=sources,
            trace_id=trace_id
        )

    except Exception as e:
        tracing_logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话生成失败: {str(e)}"
        )


@router.get("/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取对话历史"""
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生才能查看对话历史"
        )

    from app.models.database import ChatHistory

    history = db.query(ChatHistory).filter(
        ChatHistory.student_id == current_user.id
    ).order_by(ChatHistory.created_at.desc()).limit(50).all()

    return [
        {
            "id": h.id,
            "message": h.message,
            "answer": h.answer,
            "trace_id": h.trace_id,
            "created_at": h.created_at
        }
        for h in history
    ]
