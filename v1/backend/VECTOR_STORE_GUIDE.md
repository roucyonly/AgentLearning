# 向量数据库切换指南

项目支持两种向量数据库,可根据需求灵活切换:

## 🗄️ Chroma (默认,推荐用于开发)

**优势:**
- ✅ 无需额外安装,Python 包直接使用
- ✅ 数据持久化到本地文件
- ✅ 零配置,开箱即用
- ✅ 适合开发和测试环境
- ✅ 内存友好,资源占用低

**配置:**
```bash
# .env 文件
VECTOR_STORE_TYPE=chroma
```

**数据存储:**
- 数据保存在 `./chroma_db` 目录
- 每个租户的数据自动隔离在不同集合中

---

## 🔥 Milvus (推荐用于生产)

**优势:**
- ✅ 高性能,支持海量数据
- ✅ 支持分布式部署
- ✅ 适合生产环境
- ✅ 支持多种索引类型

**要求:**
- 需要安装 Docker
- 需要运行 Milvus 容器

**配置:**
```bash
# 1. 启动 Milvus
docker run -d -p 19530:19530 milvusdb/milvus:latest

# 2. 修改 .env
VECTOR_STORE_TYPE=milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

---

## 🔄 如何切换

1. **修改 `.env` 文件**
   ```bash
   # 切换到 Chroma
   VECTOR_STORE_TYPE=chroma

   # 或切换到 Milvus
   VECTOR_STORE_TYPE=milvus
   ```

2. **重启服务**
   ```bash
   uvicorn main:app --reload
   ```

3. **初始化向量存储**
   - Chroma: 自动创建,无需手动操作
   - Milvus: 首次使用时自动创建集合

---

## 📊 性能对比

| 特性 | Chroma | Milvus |
|------|--------|--------|
| 安装难度 | ⭐ 简单 | ⭐⭐⭐ 需要 Docker |
| 性能 | ⭐⭐ 适合小规模 | ⭐⭐⭐⭐⭐ 海量数据 |
| 内存占用 | ⭐ 低 | ⭐⭐⭐ 较高 |
| 生产就绪 | ⭐⭐ 适合中小规模 | ⭐⭐⭐⭐⭐ 企业级 |
| 租户隔离 | ⭐⭐⭐⭐⭐ 自动隔离 | ⭐⭐⭐ 需要手动过滤 |

---

## 💡 推荐使用场景

**使用 Chroma:**
- 本地开发
- 功能测试
- 小规模部署 (< 10万文档)
- 快速验证想法

**使用 Milvus:**
- 生产环境
- 大规模部署 (> 10万文档)
- 需要高性能检索
- 需要分布式架构

---

## 🔧 代码兼容性

两种方案的 API 完全兼容,无需修改业务代码:

```python
from app.db.vector import search_documents

# 这段代码在 Chroma 和 Milvus 中都能正常工作
results = search_documents(
    query_vector=embedding,
    top_k=5,
    tenant_id="tenant_123"
)
```

切换数据库只需修改配置,代码无需改动!
