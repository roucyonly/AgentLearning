# Academic Persona - 高校教师数字分身系统

构建具备多租户隔离、身份动态切换、全链路追溯能力的 AI Agent 系统。

## 快速开始

```bash
# 后端
conda env create -f backend/environment.yml
conda activate academic_persona
python backend/main.py

# 前端
cd frontend
npm install
npm run dev
```

## 文档导航

- **[技术方案与实现](./project.md)** - 完整的技术架构、数据库设计、核心代码
- **[代码生成计划](./plan/code_generation_plan.md)** - 开发路线图

## 核心特性

- **多租户隔离** - 数据完全隔离，学生只能访问订阅老师的内容
- **角色动态切换** - 教师/学生不同身份，不同权限和功能
- **全链路追溯** - LangSmith 追踪每个请求的完整生命周期
- **RAG 答疑** - 基于课件和学术成果的智能问答
- **AIGC 宣发** - 一键生成小红书文案、海报、短视频

## 技术栈

- **后端:** FastAPI + LangChain + LangGraph
- **前端:** Next.js 14 + Tailwind CSS
- **数据库:** Milvus (向量) + PostgreSQL (关系)
- **追踪:** LangSmith

## 目录结构

```
.
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # 路由
│   │   ├── core/     # 中间件
│   │   └── ai/       # Agent 逻辑
└── frontend/         # Next.js 前端
    └── src/
        ├── app/      # App Router
        └── lib/      # API 客户端
```

## 环境要求

- Python >= 3.10
- Node.js >= 18
- LLM API Key
- LangSmith API Key (可选，用于追踪)
