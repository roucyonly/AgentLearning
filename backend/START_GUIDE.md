# 🚀 项目启动指南

## 方案选择

### 🌟 方案 1: 无数据库快速体验（推荐新手）

**适合**: 想快速体验 API 和多租户隔离，不配置数据库

#### 1. 安装核心依赖
```bash
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-jose passlib python-multipart python-dotenv
pip install langchain langchain-openai langchain-core langchain-community
pip install bcrypt email-validator
```

#### 2. 启动 FastAPI 服务
```bash
cd D:\AgentLecdarning\backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 访问 API 文档
打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### 4. 测试基础功能

在 Swagger UI 中测试：

**① 健康检查**
```bash
GET http://localhost:8000/health
```

**② 用户注册**
```json
POST /api/auth/register
{
  "username": "test_teacher",
  "password": "pass123",
  "role": "TEACHER"
}
```

**③ 用户登录**
```json
POST /api/auth/login
{
  "username": "test_teacher",
  "password": "pass123"
}
```
返回 JWT Token

**④ 获取用户信息**
```bash
GET /api/auth/me
Headers:
  Authorization: Bearer <你的token>
```

#### 5. 观察多租户隔离

所有请求都会返回 `X-Trace-Id`，可以在响应头中看到：
```
X-Trace-Id: 550e8400-e29b-41d4-a716-446655440000
```

---

### 🎯 方案 2: 完整功能体验（需要数据库）

**适合**: 想体验完整功能，包括 RAG 对话

#### 前置条件

1. **安装 PostgreSQL**
   - 下载: https://www.postgresql.org/download/
   - 创建数据库: `createdb teacher_avatar`

2. **安装 Docker (用于 Milvus)**
   - 下载: https://www.docker.com/products/docker-desktop/
   - 运行 Milvus:
     ```bash
     docker run -d -p 19530:19530 milvusdb/milvus:latest
     ```

3. **配置环境变量**
   编辑 `.env` 文件：
   ```bash
   DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/teacher_avatar
   OPENAI_API_KEY=sk-你的真实key
   ```

#### 启动完整服务

```bash
# 1. 安装所有依赖
pip install -r requirements.txt

# 2. 初始化数据库
python init_db.py

# 3. 启动服务
uvicorn main:app --reload
```

#### 测试完整流程

使用 `test_api.py`:
```bash
python test_api.py
```

---

## 📝 常见问题

### Q1: 启动时报错 "No module named 'xxx'"
```bash
pip install xxx
```

### Q2: 数据库连接失败
检查 PostgreSQL 是否启动：
```bash
# Windows
services.msc 查看 PostgreSQL 服务

# 测试连接
psql -U postgres -d teacher_avatar
```

### Q3: API 返回 500 错误
查看控制台日志，通常是配置问题

### Q4: 没有 OpenAI API Key？
可以使用其他 LLM：
编辑 `.env`:
```bash
ACTIVE_LLM=deepseek  # 或 siliconflow
DEEPSEEK_API_KEY=你的key
```

---

## 🎓 推荐学习路径

1. **先运行方案 1** (无数据库)
   - 理解 API 结构
   - 查看请求/响应格式
   - 观察 Trace-Id

2. **阅读代码**
   - `app/core/tracing.py` - 多租户隔离核心
   - `app/api/auth.py` - 认证逻辑
   - `app/models/schemas.py` - 数据模型

3. **再尝试方案 2** (完整功能)
   - 体验 RAG 对话
   - 测试文件上传
   - 查看 LangSmith 追踪

---

## 📞 需要帮助？

如果遇到问题：
1. 检查错误信息
2. 查看 `backend/README.md`
3. 确认依赖是否安装完整
