from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.agent.state import AgentState
from app.services.model_registry import ModelRegistry
from app.services.task_service import TaskService
from app.services.conversation import ConversationService
from app.models.task import TaskType
from app.config import get_settings


async def intent_node(state: AgentState) -> AgentState:
    """意图识别节点 - 使用豆包LLM分析用户意图，确定任务类型"""
    last_message = state["messages"][-1]
    user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # 使用豆包LLM进行意图识别
    intent = "unknown"
    # await _analyze_intent_with_llm(user_input)

    state["user_intent"] = intent

    return state


async def _analyze_intent_with_llm(user_input: str) -> str:
    """使用豆包LLM分析用户意图"""
    settings = get_settings()
    api_key = settings.ARK_API_KEY

    if not api_key:
        # 如果没有配置API Key，使用简单的关键词匹配作为后备
        return _keyword_fallback_intent(user_input)

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )

        response = await client.responses.create(
            model="doubao-seed-1-8-251228",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"""请分析用户输入的意图。用户输入："{user_input}"

任务类型选项：
1. image_generation - 用户想要生成图片/图像
2. video_generation - 用户想要生成视频
3. unknown - 无法确定意图

请根据用户输入返回一个最合适的任务类型（只需返回类型名称，如：image_generation）。"""
                        }
                    ]
                }
            ] 
        )
        
        intent = response.output[0].content[0].text.strip().lower() if response.output[0].content else "unknown"

        # 验证返回的意图是否有效
        valid_intents = ["image_generation", "video_generation", "unknown"]
        if intent not in valid_intents:
            # 尝试从返回内容中提取有效意图
            for valid_intent in valid_intents:
                if valid_intent in intent:
                    return valid_intent
            return "unknown"

        return intent

    except Exception as e:
        # LLM调用失败时使用后备方案
        print(f"[WARN] Doubao LLM调用失败: {e}，使用后备意图识别")
        return _keyword_fallback_intent(user_input)


def _keyword_fallback_intent(user_input: str) -> str:
    """后备意图识别 - 简单的关键词匹配"""
    user_input_lower = user_input.lower()

    # 图像相关关键词
    image_keywords = ["图片", "图像", "生成图片", "生成图像", "image", "picture", "photo", "画"]
    video_keywords = ["视频", "生成视频", "video", "movie"]

    for keyword in video_keywords:
        if keyword in user_input_lower:
            return "video_generation"

    for keyword in image_keywords:
        if keyword in user_input_lower:
            return "image_generation"

    return "unknown"


async def planner_node(state: AgentState) -> AgentState:
    """任务规划节点 - 选择最佳模型，构建参数"""
    intent = state.get("user_intent", "unknown")
    last_message = state["messages"][-1]
    user_input = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # 根据意图确定任务类型和 provider
    if intent == "image_generation":
        task_type = TaskType.IMAGE
        default_provider = "doubao_seedream"
    elif intent == "video_generation":
        task_type = TaskType.VIDEO
        default_provider = "runway"
    else:
        task_type = TaskType.IMAGE
        default_provider = "doubao_seedream"

    # 构建用户输入参数（只需要用户的原始输入，ModelExecutor会自动处理参数映射和默认值）
    user_params = {
        "prompt": user_input,
    }

    state["selected_provider"] = default_provider
    state["task_type"] = task_type
    state["user_params"] = user_params

    return state


async def executor_node(state: AgentState) -> AgentState:
    """执行节点 - 调用 API"""
    provider_name = state.get("selected_provider")
    user_params = state.get("user_params", {})

    if not provider_name or not user_params:
        state["error"] = {"message": "Missing provider or params"}
        return state

    try:
        from app.services.model_executor import get_model_executor
        from app.utils.crypto import decrypt_api_key, generate_kling_token
        from app.config import get_settings
        from app.repositories.api_key import ApiKeyRepository
        from app.repositories.model_provider import ModelProviderRepository
        from app.db.session import AsyncSessionLocal

        executor = get_model_executor()
        settings = get_settings()

        # 尝试从数据库获取 API Key
        api_key = None
        async with AsyncSessionLocal() as session:
            # 先获取provider_id
            provider_repo = ModelProviderRepository(session)
            provider = await provider_repo.get_by_name(provider_name)
            if provider:
                api_key_repo = ApiKeyRepository(session)
                api_key_record = await api_key_repo.get_active_key(provider.id)
                if api_key_record:
                    api_key = decrypt_api_key(api_key_record.api_key_encrypted, settings.ENCRYPTION_KEY)

        # 如果数据库没有，使用配置中的key
        if not api_key:
            if provider_name == "doubao_seedream":
                api_key = settings.ARK_API_KEY
            elif provider_name == "kling":
                api_key = generate_kling_token(settings.KLING_ACCESS_KEY, settings.KLING_SECRET_KEY)
            else:
                state["error"] = {"message": f"No API key configured for: {provider_name}"}
                return state

        # 使用 ModelExecutor 执行（它会处理参数映射和默认值）
        output = await executor.execute_model(provider_name, user_params, api_key)

        state["api_response"] = output

    except Exception as e:
        state["error"] = {"message": str(e)}

    return state


async def response_node(state: AgentState) -> AgentState:
    """响应生成节点 - 格式化输出"""
    error = state.get("error")
    api_response = state.get("api_response")

    if error:
        response = f"抱歉，发生了错误：{error.get('message', '未知错误')}"
        if error.get("suggestions"):
            response += "\n\n建议：" + "，".join(error["suggestions"])
    elif api_response:
        # 格式化成功响应
        if "url" in api_response:
            response = f"已完成！图片链接：{api_response['url']}"
        elif "video_url" in api_response:
            response = f"已完成！视频链接：{api_response['video_url']}"
        else:
            response = f"已完成！结果：{api_response}"
    else:
        response = "正在处理中，请稍候..."

    state["final_response"] = response

    return state


def should_retry(state: AgentState) -> Literal["executor", "response"]:
    """判断是否需要重试"""
    error = state.get("error")
    if error and error.get("should_retry"):
        return "executor"
    return "response"
