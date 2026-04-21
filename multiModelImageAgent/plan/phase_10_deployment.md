# 阶段 10: 部署和文档

**预估时间**: 1-2天

**目标**: Docker 容器化和部署文档

---

## 10.1 Docker 配置

### 10.1.1 Dockerfile

**文件**: `Dockerfile`

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000

# 环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 10.1.2 docker-compose.yml

**文件**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./multimodel.db
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### 10.1.3 .dockerignore

**文件**: `.dockerignore`

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
logs
.env
.env.local
*.log
.pytest_cache
.coverage
htmlcov
.git
.gitignore
README.md
docs
tests
.vscode
.idea
*.md
```

---

## 10.2 API 文档

**任务**:
- [ ] 生成 OpenAPI 文档
- [ ] 编写 API 使用示例
- [ ] 创建 Postman Collection

### 10.2.1 OpenAPI 文档

FastAPI 自带 OpenAPI 文档，访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 10.2.2 API 使用示例

**文件**: `docs/api_usage.md`

```python
import httpx

async def example():
    # 发起对话
    async with httpx.AsyncClient() as client:
        # Chat
        response = await client.post(
            "http://localhost:8000/api/v1/chat",
            json={
                "message": "生成一张猫的图片",
                "user_id": "user_123"
            }
        )
        print(response.json())

        # Create Task
        response = await client.post(
            "http://localhost:8000/api/v1/tasks",
            json={
                "type": "image",
                "provider_name": "dalle",
                "input_params": {
                    "prompt": "a cute cat",
                    "size": "1024x1024"
                }
            }
        )
        print(response.json())

        # Get Task
        task_id = "task_xxx"
        response = await client.get(f"http://localhost:8000/api/v1/tasks/{task_id}")
        print(response.json())
```

---

## 10.3 部署文档

**文件**: `docs/deployment.md`

### 10.3.1 环境要求

- Python 3.10+
- SQLite 3
- Redis (可选)
- Docker (可选)

### 10.3.2 部署步骤

#### Docker 部署

```bash
# 构建镜像
docker build -t multimodel-agent .

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

#### 直接部署

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env

# 初始化数据库
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 10.3.3 故障排查

| 问题 | 解决方案 |
|------|----------|
| 数据库连接失败 | 检查 DATABASE_URL 配置 |
| API Key 无效 | 检查 .env 中的 API Keys |
| 端口被占用 | 修改 PORT 配置或杀掉占用进程 |

---

## 验收标准

- [ ] Dockerfile 可构建
- [ ] docker-compose 可启动
- [ ] API 文档可访问
- [ ] 部署文档完整
