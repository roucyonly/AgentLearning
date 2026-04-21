# MultiModel Image Agent - 实施计划

## 概述

本文档是 MultiModel Image Agent 项目的详细实施计划，基于以下设计文档：
- [project.md](../docs/project.md) - 项目概述和技术架构
- [error_handling.md](../docs/error_handling.md) - 错误处理机制
- [model_configuration.md](../docs/model_configuration.md) - 模型可配置化设计

## 开发原则

1. **分层架构**: 严格按照 model → config → repository → service → controller → testCase 的顺序
2. **先建架构**: 先创建完整的目录结构和基础配置
3. **数据库优先**: 先实现数据库层（model + repository），再实现业务逻辑
4. **配置驱动**: 所有模型和错误处理配置来自数据库
5. **测试覆盖**: 每个模块完成后立即编写测试

## 阶段总览

| 阶段 | 名称 | 预估时间 | 关键任务 |
|------|------|----------|----------|
| 0 | [项目初始化](phase_00_initialization.md) | 1-2天 | 目录结构、依赖、配置 |
| 1 | [数据库层](phase_01_database.md) | 3-4天 | Models、DB Session、Alembic |
| 2 | [Schema层](phase_02_schema.md) | 1-2天 | Pydantic Schemas |
| 3 | [Repository层](phase_03_repository.md) | 2-3天 | 数据访问层 |
| 4 | [服务层](phase_04_service.md) | 4-5天 | 业务逻辑、错误处理 |
| 5 | [Agent层](phase_05_agent.md) | 2-3天 | LangGraph工作流 |
| 6 | [API层](phase_06_api.md) | 3-4天 | FastAPI路由 |
| 7 | [工具层](phase_07_utils.md) | 1-2天 | 加密、日志、辅助函数 |
| 8 | [应用入口](phase_08_main.md) | 1天 | FastAPI应用、依赖注入 |
| 9 | [测试](phase_09_testing.md) | 2-3天 | 单元测试、集成测试 |
| 10 | [部署](phase_10_deployment.md) | 1-2天 | Docker、文档 |
| 11 | [种子数据](phase_11_seed.md) | 1天 | 初始化脚本、种子数据 |

**总计**: 约 22-28 天

## 开发顺序

```
阶段 0 → 阶段 1 → 阶段 2 → 阶段 3 → 阶段 4 → 阶段 5 → 阶段 6 → 阶段 7 → 阶段 8 → 阶段 9 → 阶段 10 → 阶段 11
  ↓         ↓         ↓         ↓         ↓         ↓         ↓         ↓         ↓         ↓         ↓
初始化   数据库层   Schema层  Repository  服务层     Agent    API层     工具层    应用入口   测试      部署
```

## 关键里程碑

- **里程碑 1**: 数据库层完成 (阶段 1-2)
- **里程碑 2**: 服务层完成 (阶段 3-4)
- **里程碑 3**: Agent 和 API 完成 (阶段 5-6)
- **里程碑 4**: 测试完成 (阶段 9)
- **里程碑 5**: 部署就绪 (阶段 10)

## 快速开始

### 1. 创建虚拟环境
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填写必要的配置
```

### 4. 初始化数据库
```bash
python scripts/init_db.py
```

### 5. 启动服务
```bash
python -m app.main
```

### 6. 访问 API 文档
浏览器打开: http://localhost:8000/docs

## 注意事项

1. 每个模块完成后立即编写测试
2. 遵循 TDD 原则: 先写测试，再写实现
3. 每个阶段结束后进行代码审查
4. 定期更新文档
5. 使用 Git 分支管理: 每个阶段一个分支
