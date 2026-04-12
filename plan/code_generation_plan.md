# 代码生成计划：高校教师数字分身系统 (Academic Persona)

本文档基于业务核心设计（`project.md`）和基础 Agent 框架规范（`readme.md`），为生成“高校教师数字分身系统”制定详细的分步代码生成计划。

## 阶段一：项目架构与环境初始化 (Project Setup)

**目标**：构建标准的项目目录结构，搭建 Conda 和 Node.js 环境。

1. **项目目录生成**：
   - 创建 `backend/` 及对应的子目录 (`app/api`, `app/core`, `app/ai/agents`, `app/ai/tools`, `app/ai/prompts`, `app/models`)。
   - 创建 `frontend/` 目录。
2. **后端环境配置 (`backend/environment.yml`)**：
   - 基于 `project.md` 约束（Python 3.13, FastAPI, LangChain 1.2.0, LangGraph, Milvus, PostgreSQL）。
   - 包含必要的环境变量加载工具（如 `python-dotenv`）以及 `readme.md` 提及的多模型、多工具依赖。
3. **前端脚手架初始化**：
   - 初始化 Next.js 14+ (App Router) 搭配 Tailwind CSS。

## 阶段二：全局配置与密钥管理 (Configuration Layer)

**目标**：结合 `readme.md` 的环境管理规范，实现多模型支持和密钥隔离。

1. **环境变量 (.env)**：
   - 编写完整的 `.env.example`，集成 OpenAI、Antropic 乃至追踪服务所需的 `LANGCHAIN_TRACING_V2` 和 `LANGCHAIN_API_KEY`。
2. **后端配置中心 (`backend/app/core/config.py`)**：
   - 参考 `readme.md` 的四段式配置逻辑，实现支持多厂商 API 切换的 `get_llm()` 工厂模式。
   - 配置环境常量、数据库连接字串。

## 阶段三：后端核心骨架 (Backend Core Architecture)

**目标**：实现请求拦截与多租户/角色追踪的数据隔离体系。

1. **上下文追溯中间件 (`backend/app/core/tracing.py`)**：
   - 实现提取 Header 中的 `X-Trace-Id`、`X-Tenant-Id`、`X-Role` 并写入协程安全的 `ContextVar`。
2. **数据交互层设计 (`backend/app/models`)**：
   - 建立请求 Pydantic 模型和初步的 SQLAlchemy 模型。
3. **主入口文件 (`backend/main.py`)**：
   - 初始化 FastAPI 实例，挂载 tracing 中间件，并暴露健康的检查接口。

## 阶段四：AI Agent 编排 (AI & Graph)

**目标**：白盒化状态机建立与场景隔离。

1. **LangGraph 状态机框架 (`backend/app/ai/agents/graph.py`)**：
   - 根据 `project.md` 建立 `AgentState` 数据结构。
   - 实现路由节点 `node_router`：按角色（TEACHER / STUDENT）分发业务节点。
   - 配置并将 `Trace-Id` 和 `Role` 填入 `RunnableConfig` 传入大模型链路。
2. **安全隔离的检索工具 (`backend/app/ai/tools/retriever.py`)**：
   - 基于 ContextVar 提取 `Tenant-Id` 并注入 Milvus 过滤条件的大框架代理，确保内容不出圈。

## 阶段五：前端核心系统 (Frontend Implementation)

**目标**：搭建前端基础设施，适配后端追溯系统。

1. **API 请求封装 (`frontend/src/lib/api.ts`)**：
   - 编写基于 Axios 的拦截器，按照 `project.md` 要求自动注入 `X-Trace-Id`、`X-Tenant-Id`、`X-Role`。
2. **基础界面骨架 (`frontend/src/app`)**：
   - 提供模拟界面的结构以支撑 Chat/问答面板交互。
3. **角色与租户切换机制**：
   - 实现供测试使用的 LocalStorage 设置界面（快速切换角色与 TenantId 身份）。

## 阶段六：集成联调与测试 (Integration & Testing)

**目标**：全链路校验与问题溯源闭环。

1. **API 全链路连通测试**：
   - 编写基本连通性测试：由前端发起会话 -> Axios 注入 Header -> FastApi 中间件捕获 -> LangGraph 解析处理角色。
2. **控制台校验**：
   - 发送模拟请求检测 LangSmith 追踪面板是否成功串联了一次调用的 `Trace-Id`。
3. **编写执行验证文档**：
   - 更新工程级别的 `README.md` 执行步骤，指导开发者一键启动测试。
