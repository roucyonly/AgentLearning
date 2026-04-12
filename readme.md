# AgentLearning 项目启动流程

## 一、环境准备

### 1.1 基础环境
- Python >= 3.10
- Node.js >= 18（前端）
- API Keys:
  - LLM API
  - TTS API
  - Search API
        c8f6b4e611e0f4766dd0a2f43b5c07bf36058811825098eae147ea2aad3589e5

### 1.2 项目初始化
```bash
# 创建项目目录
cd D:\AgentLearning
mkdir -p src/agents src/tools src/chains src/memory src/ui
```

## 二、依赖安装

### 2.1 Python 依赖
```bash
pip install langchain langchain-community langchain-core
pip install langchain-openai / langchain-anthropic / 其他LLM provider
pip install langchain-tools  # 工具能力
pip install duckduckgo-search  # 搜索工具
pip install elevenlabs / edge-tts  # TTS
pip install flask / fastapi  # Web服务
```

### 2.2 前端依赖（如需要）
```bash
npm install react langchain.js
```

## 三、项目结构

```
AgentLearning/
├── src/
│   ├── agents/        # Agent定义
│   ├── tools/         # 工具集（搜索/TTS/搜索等）
│   ├── chains/        # Chain编排
│   ├── memory/        # 记忆管理
│   └── ui/            # 前端界面
├── config/            # 配置文件
├── .env               # API密钥管理
└── main.py            # 入口文件
```

## 四、核心配置（config.py / .env）

支持多厂商 API Key 切换，通过配置文件的 `ACTIVE_PROVIDER` 字段指定当前使用的厂商。

```python
# config.py - 多厂商配置示例
import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# ==================== LLM 配置 ====================
# 当前激活的厂商（切换时只需修改此行）
ACTIVE_LLM = "openai"  # 可选: openai / anthropic / zhipu / deepseek / siliconflow ...

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# 智谱 GLM
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# SiliconFlow（聚合多个模型）
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")

# ==================== TTS 配置 ====================
ACTIVE_TTS = "edge"  # 可选: edge / elevenlabs / minimax ...
EDGE_TTS_KEY = os.getenv("EDGE_TTS_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")

# ==================== 搜索配置 ====================
ACTIVE_SEARCH = "duckduckgo"  # 可选: duckduckgo / serpapi / serper / tavily ...
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


# ==================== LLM 实例获取 ====================
def get_llm():
    """根据当前 ACTIVE_LLM 返回对应实例"""
    if ACTIVE_LLM == "openai":
        return ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    elif ACTIVE_LLM == "anthropic":
        return ChatAnthropic(model="claude-sonnet-4", api_key=ANTHROPIC_API_KEY)
    elif ACTIVE_LLM == "zhipu":
        return ChatOpenAI(model="glm-4", api_key=ZHIPU_API_KEY, base_url="https://open.bigmodel.cn/api/paas/v4")
    elif ACTIVE_LLM == "deepseek":
        return ChatOpenAI(model="deepseek-chat", api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    elif ACTIVE_LLM == "siliconflow":
        return ChatOpenAI(model="Qwen/Qwen2.5-7B-Instruct", api_key=SILICONFLOW_API_KEY, base_url="https://api.siliconflow.cn/v1")
    else:
        raise ValueError(f"未支持的 LLM 厂商: {ACTIVE_LLM}")
```

```bash
# .env 文件
# LLM Keys
OPENAI_API_KEY=sk-xxxx
ANTHROPIC_API_KEY=sk-ant-xxxx
ZHIPU_API_KEY=xxxx
DEEPSEEK_API_KEY=sk-xxxx
SILICONFLOW_API_KEY=sk-xxxx

# TTS Keys
EDGE_TTS_KEY=xxxx
ELEVENLABS_API_KEY=xxxx
MINIMAX_API_KEY=xxxx

# Search Keys
SERPAPI_API_KEY=xxxx
SERPER_API_KEY=xxxx
TAVILY_API_KEY=xxxx
```

### 4.1 切换厂商步骤

1. 修改 `config.py` 中的 `ACTIVE_LLM`（或 `ACTIVE_TTS`、`ACTIVE_SEARCH`）
2. 确保 `.env` 中对应厂商的 API Key 已配置
3. 无需改动 Agent 代码，重启即可生效

## 五、核心模块设计

### 5.1 工具层（Tools）
| 工具 | 功能 | 集成方式 |
|------|------|----------|
| SearchTool | 网页搜索 | DuckDuckGo API |
| TTS tool | 语音合成 | Edge-TTS / ElevenLabs |
| Calculator | 数学计算 | Python REPL |

### 5.2 Chain层
```
User Input → Parser → Router Chain → Action Chain → Response
```

### 5.3 Agent层
- ReAct Agent（推理+行动）
- Conversational Agent（对话记忆）

## 六、启动流程

### 6.1 开发环境
```bash
# 1. 激活虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 2. 配置环境变量
# 编辑 .env 文件填入 API Keys

# 3. 验证依赖
python -c "import langchain; print(langchain.__version__)"

# 4. 启动服务
python src/main.py
```

### 6.2 前端（如需要）
```bash
cd src/ui
npm run dev
```

## 七、验证步骤

- [ ] LLM API 连通性测试
- [ ] 搜索工具测试
- [ ] TTS 工具测试
- [ ] Agent 对话测试
- [ ] Web 界面加载测试

## 八、常见问题

1. **API Key 无效** → 检查 .env 配置
2. **LangChain 版本冲突** → 使用 `pip list | grep langchain` 检查
3. **网络问题** → 配置代理或使用国内镜像源
