from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_db, get_task_service, get_conversation_service, init_agent_services
from app.schemas.conversation import ChatRequest, ChatResponse
from app.agent.graph import run_agent
from app.services.task_service import TaskService
from app.services.conversation import ConversationService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    task_service: TaskService = Depends(get_task_service),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    处理对话请求

    - 分析用户意图
    - 选择合适的模型
    - 执行生成任务
    - 返回结果
    """
    try:
        # 初始化 Agent 服务
        init_agent_services()

        # 运行 Agent
        result = await run_agent(
            user_input=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            wait_for_result=True
        )

        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            task_id=result.get("task_id")
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}"
        )


@router.post("/async", response_model=ChatResponse)
async def chat_async(
    request: ChatRequest,
    task_service: TaskService = Depends(get_task_service),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    异步处理对话请求 - 立即返回，任务后台执行

    - 分析用户意图
    - 选择合适的模型
    - 创建任务
    - 立即返回 task_id
    """
    try:
        init_agent_services()

        result = await run_agent(
            user_input=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            wait_for_result=False
        )

        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            task_id=result.get("task_id")
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}"
        )
