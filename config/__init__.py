# config/__init__.py
"""
配置模块 - 支持多厂商 API Key 切换
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== LLM 配置 ====================
ACTIVE_LLM = os.getenv("ACTIVE_LLM", "openai")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")

# ==================== TTS 配置 ====================
ACTIVE_TTS = os.getenv("ACTIVE_TTS", "edge")

EDGE_TTS_KEY = os.getenv("EDGE_TTS_KEY", "")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")

# ==================== 搜索配置 ====================
ACTIVE_SEARCH = os.getenv("ACTIVE_SEARCH", "duckduckgo")

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


# ==================== LLM 实例获取 ====================
def get_llm():
    """根据当前 ACTIVE_LLM 返回对应实例"""
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic

    if ACTIVE_LLM == "openai":
        return ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    elif ACTIVE_LLM == "anthropic":
        return ChatAnthropic(model="claude-sonnet-4-20250514", api_key=ANTHROPIC_API_KEY)
    elif ACTIVE_LLM == "zhipu":
        return ChatOpenAI(model="glm-4", api_key=ZHIPU_API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4")
    elif ACTIVE_LLM == "deepseek":
        return ChatOpenAI(model="deepseek-chat", api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    elif ACTIVE_LLM == "siliconflow":
        return ChatOpenAI(model="Qwen/Qwen2.5-7B-Instruct", api_key=SILICONFLOW_API_KEY, base_url="https://api.siliconflow.cn/v1")
    else:
        raise ValueError(f"未支持的 LLM 厂商: {ACTIVE_LLM}")
