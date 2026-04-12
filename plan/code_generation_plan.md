# 高校教师数字分身系统 - 代码生成计划

**版本：** 2.0
**生成时间：** 2026-04-13
**状态：** 待执行

---

## 📋 执行策略总览

**核心理念：后端优先、迭代递进、隔离优先、可验证性**

### 为什么后端优先？

1. **API 契约稳定性** - 前端依赖后端 API，后端先行可避免大量返工
2. **多租户隔离** - 这是架构核心，必须在代码层面从第一行就正确实现
3. **AI 核心逻辑** - LangGraph 状态机和 RAG 链是系统最复杂的部分，需要充分测试
4. **独立验证** - 后端可以通过 curl/Postman 独立验证，不依赖前端界面

---

## 🎯 MVP（最小可用产品）定义

**Phase 1 (MVP Core):**
- 用户注册/登录（基础身份管理）
- 教师创建分身设定
- 学生绑定班级
- 基于租户隔离的 RAG 问答（核心功能）
- Trace-Id 全链路追踪

**Phase 2 (Content Generation):**
- AIGC 文案生成
- 文件上传与向量化
- 广播消息基础功能

**Phase 3 (Advanced Features):**
- WebSocket 实时推送
- 多媒体生成（图片/视频）
- 高级分析面板

---

## 📦 Phase 1: 核心基础设施（Week 1-2）

### 目标
建立多租户隔离的 API 基础，实现可用的用户系统和核心 AI 能力

### 1.1 环境与依赖初始化

**创建文件清单：**

```
D:\AgentLearning\
├── backend\
│   ├── environment.yml           # Conda 环境配置
│   ├── requirements.txt          # Python 依赖
│   ├── .env.example              # 环境变量模板
│   ├── main.py                   # FastAPI 应用入口
│   └── app\
│       ├── __init__.py
│       ├── core\
│       │   ├── __init__.py
│       │   ├── config.py         # 多厂商 LLM 配置
│       │   ├── tracing.py        # 追踪中间件（核心代码）
│       │   └── security.py       # JWT/密码哈希
│       ├── db\
│       │   ├── __init__.py
│       │   ├── session.py        # PostgreSQL 连接
│       │   └── vector.py         # Milvus 连接
│       └── models\
│           ├── __init__.py
│           ├── schemas.py        # Pydantic 模型
│           └── database.py       # SQLAlchemy 表定义
```

### 1.2 核心 API 路由

**创建文件：**

```
backend/app/api/
├── __init__.py
├── auth.py           # 注册/登录
├── teachers.py       # 教师分身管理
├── students.py       # 学生班级绑定
└── chat.py           # RAG 问答接口
```

### 1.3 LangGraph 状态机（核心 AI）

**创建文件：**

```
backend/app/ai/
├── __init__.py
├── agents/
│   ├── __init__.py
│   ├── graph.py          # LangGraph 状态机
│   └── nodes.py          # 具体节点实现
├── tools/
│   ├── __init__.py
│   └── retriever.py      # RAG 检索器
└── prompts/
    ├── __init__.py
    └── templates.py      # 提示词模板
```

### 核心代码示例

**backend/app/core/tracing.py**
```python
import uuid
from contextvars import ContextVar
from fastapi import Request

trace_id_ctx = ContextVar("trace_id", default="")
tenant_id_ctx = ContextVar("tenant_id", default="")
role_ctx = ContextVar("role", default="STUDENT")

async def context_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    tenant_id = request.headers.get("X-Tenant-Id", "default")
    role = request.headers.get("X-Role", "STUDENT")

    trace_id_ctx.set(trace_id)
    tenant_id_ctx.set(tenant_id)
    role_ctx.set(role)

    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response
```

**backend/app/models/database.py**
```python
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # TEACHER / STUDENT
    created_at = Column(DateTime, default=datetime.utcnow)

class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    avatar_prompt = Column(Text)
    name = Column(String(100))
    personality = Column(Text)
    catchphrase = Column(String(200))

class Class(Base):
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    class_name = Column(String(100), nullable=False)
    invite_code = Column(String(20), unique=True, nullable=False)

class StudentClassMapping(Base):
    __tablename__ = "student_class_mappings"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
```

### Phase 1 验证方式

**自动化测试：**
```bash
# 测试多租户隔离
curl -X POST http://localhost:8000/api/chat \
  -H "X-Tenant-Id: teacher_123" \
  -H "X-Role: STUDENT" \
  -d '{"message": "什么是机器学习？"}'

# 验证 Trace-Id 返回
# 验证日志中 LangSmith 追踪
# 验证 Milvus 查询带有 tenant_id 过滤器
```

---

## 📚 Phase 2: RAG 能力与文件管理（Week 3-4）

### 目标
实现文档上传、向量化、多租户检索的完整闭环

### 2.1 文件上传与解析

**创建文件：**

```
backend/app/api/
├── files.py          # 文件上传接口

backend/app/ai/
├── processors/
│   ├── __init__.py
│   ├── pdf_parser.py      # PDF 解析
│   ├── pptx_parser.py     # PPTX 解析
│   └── chunker.py         # 文档切分
```

### 2.2 RAG 检索优化

**创建文件：**

```
backend/app/db/
└── vector.py         # Milvus 连接与集合管理
```

---

## 🎨 Phase 3: AIGC 内容生成（Week 5-6）

### 目标
实现小红书文案、海报提示词、短视频脚本的生成链

### 3.1 AIGC 工作流

**创建文件：**

```
backend/app/ai/
├── chains/
│   ├── __init__.py
│   ├── aigc_chain.py      # AIGC 生成链
│   └── summarization.py   # 论文总结

backend/app/api/
├── aigc.py            # AIGC 接口
```

### AIGC 核心代码

**backend/app/ai/chains/aigc_chain.py**
```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def generate_social_media_assets(paper_text: str):
    # 小红书文案生成
    xiaohongshu_prompt = ChatPromptTemplate.from_template(
        "提炼以下学术论文的亮点，写小红书文案：{paper}"
    )
    copy_chain = xiaohongshu_prompt | llm | StrOutputParser()
    copy_result = copy_chain.invoke({"paper": paper_text})

    # 海报提示词生成
    poster_prompt = ChatPromptTemplate.from_template(
        "基于文案设计 DALL-E 提示词：{copy}"
    )
    poster_chain = poster_prompt | llm | StrOutputParser()
    image_prompt = poster_chain.invoke({"copy": copy_result})

    return {"copy": copy_result, "image_prompt": image_prompt}
```

---

## 🌐 Phase 4: 前端开发（Week 7-9）

### 目标
基于稳定的后端 API，构建 Next.js 用户界面

### 4.1 前端脚手架

**创建文件：**

```
frontend/
├── package.json
├── next.config.js
├── tailwind.config.js
└── src/
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   ├── login/
    │   ├── teacher/
    │   └── student/
    ├── components/
    │   ├── ChatWindow.tsx
    │   ├── FileUploader.tsx
    │   └── AIGCWorkspace.tsx
    └── lib/
        └── api.ts           # API 客户端
```

### 前端核心代码

**frontend/src/lib/api.ts**
```typescript
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
});

client.interceptors.request.use((config) => {
  config.headers['X-Trace-Id'] = uuidv4();
  config.headers['X-Tenant-Id'] = localStorage.getItem('active_teacher_id') || '';
  config.headers['X-Role'] = localStorage.getItem('current_role') || 'STUDENT';
  return config;
});

export default client;
```

---

## 🚀 Phase 5: 高级功能（Week 10-12）

### 目标
实时推送、多媒体生成、数据分析

### 5.1 WebSocket 实时推送

**创建文件：**

```
backend/app/
├── websocket/
│   ├── __init__.py
│   └── manager.py       # WebSocket 连接管理

backend/app/api/
├── ws.py               # WebSocket 路由
```

---

## 🔗 依赖关系图

```
Phase 1 (基础设施)
    ├── tracing.py (中间件) → 所有 API
    ├── database.py (数据模型) → auth.py, teachers.py
    ├── graph.py (LangGraph) → chat.py
    └── config.py (LLM 配置) → 所有 AI 模块

Phase 2 (RAG 能力)
    ├── 依赖 Phase 1 的数据库模型
    ├── retriever.py → 依赖 tracing.py (tenant_id_ctx)
    └── files.py → 依赖 database.py, vector.py

Phase 3 (AIGC)
    ├── 依赖 Phase 1 的 config.py (get_llm)
    └── 独立于 Phase 2

Phase 4 (前端)
    ├── 依赖 Phase 1-3 的 API 稳定性
    └── api.ts → 所有后端路由

Phase 5 (高级功能)
    ├── WebSocket → 依赖 Phase 1 的用户系统
    └── 图片生成 → 依赖 Phase 3 的 AIGC 链
```

---

## ✅ 验收标准总结

### Phase 1 完成标准
- [ ] 用户能注册并获得 JWT
- [ ] 所有 API 返回 X-Trace-Id
- [ ] LangSmith 能追踪完整调用链
- [ ] 租户隔离在数据库层强制执行
- [ ] 学生提问能基于教师文档回答

### Phase 2 完成标准
- [ ] 教师能上传 PDF/PPTX
- [ ] 文档正确切分并向量化
- [ ] 向量数据带有 tenant_id 元数据
- [ ] 检索结果只返回当前租户数据

### Phase 3 完成标准
- [ ] 能生成小红书风格文案
- [ ] 能生成 DALL-E 图片提示词
- [ ] AIGC 链路在 LangSmith 可追踪

### Phase 4 完成标准
- [ ] 前端能登录并保持会话
- [ ] 学生对话界面支持流式显示
- [ ] 教师能上传文件并看到进度
- [ ] 浏览器 Console 显示 Trace-Id

### Phase 5 完成标准
- [ ] 教师广播后学生实时收到
- [ ] 能生成图片并展示
- [ ] 系统能处理 10+ 并发用户

---

## 🔑 Critical Files（实现时优先关注）

1. **`backend/app/core/tracing.py`** - 多租户隔离核心
2. **`backend/app/ai/agents/graph.py`** - LangGraph 状态机
3. **`backend/app/models/database.py`** - 数据模型
4. **`backend/app/ai/tools/retriever.py`** - RAG 检索核心
5. **`frontend/src/lib/api.ts`** - 前端 API 桥梁

**完整代码参考 `D:\AgentLearning\project.md` 第四章**

---

## 📝 执行建议

### Day 1 开始
1. 创建 Conda 环境：`conda env create -f backend/environment.yml`
2. 创建目录结构（使用 `mkdir -p`）
3. 创建第一批 6 个核心文件
4. 编写第一个 API（`/api/auth/register`）并测试

### Week 1 里程碑
- 完成用户注册/登录
- 实现追踪中间件
- 数据库表创建成功
- LangGraph 状态机基础跑通

### Week 2 里程碑
- 学生 RAG 问答可用
- 文件上传和向量化完成
- 租户隔离验证通过
- LangSmith 追踪正常

### 持续验证
- 每个阶段结束后运行完整测试套件
- 每次代码变更后检查 LangSmith 日志
- 每周审查多租户隔离机制

---

## 📚 参考资料

- **技术方案：** `D:\AgentLearning\project.md`
- **项目说明：** `D:\AgentLearning\README.md`
- **执行计划：** 本文档

---

**最后更新：** 2026-04-13
**状态：** 准备开始实施
