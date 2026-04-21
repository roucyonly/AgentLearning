# 模型可配置化设计

## 概述

本文档描述如何实现模型的动态可配置化，包括模型注册、API配置、参数映射和错误处理策略的完全外部化。所有配置存储在数据库中，可通过 Admin UI 动态管理，无需修改代码或重启服务。

### 核心特性

- **完全外部化**: 所有模型配置存储在数据库，不硬编码
- **动态加载**: 运行时动态加载模型配置和错误处理策略
- **UI 管理**: 提供 Admin UI 进行可视化配置
- **版本控制**: 支持配置的版本管理和回滚
- **即时生效**: 配置修改后实时生效，无需重启
- **测试验证**: UI 中提供配置测试功能

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Admin UI (管理界面)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 模型管理                                              │  │
│  │ - 模型列表（查看/启用/禁用）                          │  │
│  │ - 添加模型（填写配置表单）                            │  │
│  │ - 编辑模型（修改配置）                                │  │
│  │ - 删除模型                                            │  │
│  │ - 测试连接（验证配置）                                │  │
│  │ - 查看统计（调用次数/成功率/错误分布）                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 错误处理配置                                          │  │
│  │ - 重试策略（每个模型的每个错误类型）                  │  │
│  │ - 参数修正规则                                        │  │
│  │ - 错误消息翻译                                        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
                         ▼
         ┌───────────────────────────────┐
         │   ModelProvider Service       │
         │   - CRUD 操作                 │
         │   - 配置验证                  │
         │   - 版本管理                  │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │   PostgreSQL Database         │
         │  ┌─────────────────────────┐  │
         │  │ model_providers         │  │
         │  │ - 基本信息             │  │
         │  │ - API 配置             │  │
         │  │ - 参数定义             │  │
         │  ├─────────────────────────┤  │
         │  │ error_handling_config   │  │
         │  │ - 重试策略             │  │
         │  │ - 修正规则             │  │
         │  │ - 消息模板             │  │
         │  ├─────────────────────────┤  │
         │  │ error_patterns          │  │
         │  │ - 错误模式映射         │  │
         │  └─────────────────────────┘  │
         └───────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent 运行时                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ModelRegistry (模型注册表)                           │  │
│  │ - 从数据库加载启用的模型                             │  │
│  │ - 缓存配置（带失效机制）                             │  │
│  │ - 监听配置变更事件                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ErrorHandler (动态加载配置)                          │  │
│  │ - 错误分类器（从 DB 加载模式）                       │  │
│  │ - 参数修正器（从 DB 加载规则）                       │  │
│  │ - 重试管理器（从 DB 加载策略）                       │  │
│  │ - 错误翻译器（从 DB 加载模板）                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ GenericAPIAdapter (通用 API 调用器)                  │  │
│  │ - 读取模型配置                                       │  │
│  │ - 执行参数映射                                       │  │
│  │ - 调用第三方 API                                     │  │
│  │ - 处理响应                                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 数据库设计

### 1. 模型配置表 (model_providers)

存储所有 AI 服务的配置信息。

```sql
CREATE TABLE model_providers (
    -- 基本信息
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,              -- 模型唯一标识: "dalle-3"
    display_name VARCHAR(100) NOT NULL,            -- 显示名称: "DALL-E 3"
    description TEXT,                              -- 描述

    -- 分类
    provider_type VARCHAR(20) NOT NULL,            -- "image" | "video"
    category VARCHAR(50),                          -- "openai", "stability", "runway"

    -- API 配置
    api_endpoint VARCHAR(500) NOT NULL,            -- API 端点
    api_version VARCHAR(20),                       -- API 版本
    http_method VARCHAR(10) DEFAULT 'POST',        -- HTTP 方法

    -- 认证配置 (JSON)
    auth_config JSONB NOT NULL,                    -- 认证配置
    -- 示例:
    -- {
    --   "type": "bearer",                         -- bearer | api_key | basic
    --   "header_name": "Authorization",           -- 请求头名称
    --   "token_prefix": "Bearer ",               -- Token 前缀
    --   "key_location": "header"                  -- header | query | body
    -- }

    -- 请求配置 (JSON)
    request_config JSONB NOT NULL,                 -- 请求配置
    -- 示例:
    -- {
    --   "headers": {                              -- 固定请求头
    --     "Content-Type": "application/json"
    --   },
    --   "timeout": 30,                            -- 超时时间（秒）
    --   "max_retries": 3                          -- 最大重试次数（覆盖全局配置）
    -- }

    -- 参数映射 (JSON)
    parameter_mapping JSONB NOT NULL,              -- 参数映射规则
    -- 示例:
    -- {
    --   "prompt": "prompt",                       -- 用户输入 → API 参数
    --   "size": "size",
    --   "quality": "quality",
    --   "style": "options.style"                  -- 嵌套映射
    -- }

    -- 参数定义 (JSON Schema)
    parameter_schema JSONB NOT NULL,               -- 参数定义（JSON Schema）
    -- 示例:
    -- {
    --   "type": "object",
    --   "properties": {
    --     "size": {
    --       "type": "string",
    --       "enum": ["1024x1024", "1792x1024", "1024x1792"],
    --       "default": "1024x1024",
    --       "description": "图片尺寸"
    --     },
    --     "quality": {
    --       "type": "string",
    --       "enum": ["standard", "hd"],
    --       "default": "standard"
    --     }
    --   },
    --   "required": ["prompt"]
    -- }

    -- 响应映射 (JSON)
    response_mapping JSONB NOT NULL,               -- 响应提取规则
    -- 示例:
    -- {
    --   "image_url": "data.0.url",                -- JSONPath 提取
    --   "revised_prompt": "data.0.revised_prompt",
    --   "model": "model"
    -- }

    -- 状态
    is_enabled BOOLEAN DEFAULT true,               -- 是否启用
    is_available BOOLEAN DEFAULT true,             -- 是否可用（通过健康检查更新）

    -- 能力标签
    capabilities JSONB DEFAULT '{}',               -- 能力标签
    -- 示例:
    -- {
    --   "high_quality": true,                     -- 高质量
    --   "fast_generation": true,                  -- 快速生成
    --   "prompt_understanding": true,             -- 理解能力强
    --   "supports_editing": false                 -- 支持编辑
    -- }

    -- 优先级和成本
    priority INTEGER DEFAULT 0,                    -- 优先级（数字越大越优先）
    cost_per_request DECIMAL(10, 4),               -- 每次请求成本（USD）
    cost_per_image DECIMAL(10, 4),                 -- 每张图片成本

    -- 限制
    rate_limit INTEGER,                            -- 速率限制（请求/分钟）
    max_concurrent INTEGER DEFAULT 10,             -- 最大并发数

    -- 元数据
    metadata JSONB DEFAULT '{}',                   -- 其他元数据

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_health_check TIMESTAMP,

    -- 版本控制
    version INTEGER DEFAULT 1,

    -- 索引
    CONSTRAINT provider_type_enabled CHECK (
        provider_type IN ('image', 'video', 'audio', 'text')
    )
);

CREATE INDEX idx_model_providers_type ON model_providers(provider_type);
CREATE INDEX idx_model_providers_enabled ON model_providers(is_enabled);
CREATE INDEX idx_model_providers_category ON model_providers(category);
```

### 2. API Key 存储表 (api_keys)

加密存储 API Key，与模型配置分离。

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES model_providers(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,                    -- Key 名称（用于区分多个 Key）
    api_key_encrypted TEXT NOT NULL,               -- 加密后的 API Key
    key_type VARCHAR(20) DEFAULT 'production',     -- production | test | staging

    -- 限制
    quota_limit INTEGER,                           -- 配额限制
    quota_used INTEGER DEFAULT 0,                  -- 已使用配额
    quota_reset_at TIMESTAMP,                      -- 配额重置时间

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,                          -- 过期时间

    -- 优先级（用于负载均衡）
    priority INTEGER DEFAULT 0
);

CREATE INDEX idx_api_keys_provider ON api_keys(provider_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);
```

### 3. 错误处理配置表 (error_handling_config)

存储每个模型的错误处理策略。

```sql
CREATE TABLE error_handling_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES model_providers(id) ON DELETE CASCADE,

    -- 错误类型
    error_type VARCHAR(50) NOT NULL,               -- INVALID_SIZE, RATE_LIMIT_EXCEEDED 等

    -- 重试策略
    retry_enabled BOOLEAN DEFAULT true,
    max_attempts INTEGER DEFAULT 3,
    base_wait_time DECIMAL(5, 2) DEFAULT 1.0,      -- 基础等待时间（秒）
    max_wait_time DECIMAL(5, 2) DEFAULT 60.0,      -- 最大等待时间（秒）
    exponential_base DECIMAL(3, 1) DEFAULT 2.0,    -- 指数退避基数

    -- 参数修正配置
    auto_fix_enabled BOOLEAN DEFAULT false,
    fix_rules JSONB DEFAULT '{}',
    -- 示例:
    -- {
    --   "size": {
    --     "supported": ["1024x1024", "1792x1024"],
    --     "fallback": "1024x1024",
    --     "strategy": "closest_match"              -- closest_match | fallback | strict
    --   }
    -- }

    -- 降级策略
    fallback_providers UUID[],                     -- 降级到其他模型

    -- 特殊处理
    custom_handler VARCHAR(100),                   -- 自定义处理器名称

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(provider_id, error_type)
);

CREATE INDEX idx_error_handling_provider ON error_handling_config(provider_id);
```

### 4. 错误模式映射表 (error_patterns)

存储服务商特定的错误码映射。

```sql
CREATE TABLE error_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES model_providers(id) ON DELETE CASCADE,

    -- 匹配规则
    pattern_type VARCHAR(20) NOT NULL,             -- status_code | error_code | message_pattern | regex
    pattern_value VARCHAR(500) NOT NULL,           -- 模式值
    -- 示例:
    -- status_code: "429"
    -- error_code: "rate_limit_exceeded"
    -- message_pattern: "rate limit"
    -- regex: "invalid.*size.*(\\d+x\\d+)"

    -- 映射结果
    error_type VARCHAR(50) NOT NULL,               -- 映射到的错误类型
    priority INTEGER DEFAULT 0,                    -- 优先级（数字越大越优先）

    -- 提取信息（用于修正或提示）
    extract_fields JSONB DEFAULT '{}',
    -- 示例:
    -- {
    --   "invalid_size": "{match1}",                -- 从正则提取
    --   "retry_after": "{headers.Retry-After}"     -- 从响应头提取
    -- }

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_error_patterns_provider ON error_patterns(provider_id);
CREATE INDEX idx_error_patterns_active ON error_patterns(is_active);
```

### 5. 错误消息模板表 (error_message_templates)

存储多语言的错误消息模板。

```sql
CREATE TABLE error_message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES model_providers(id) ON DELETE CASCADE,

    error_type VARCHAR(50) NOT NULL,
    language VARCHAR(10) DEFAULT 'zh',             -- zh, en, ja 等

    -- 消息模板
    user_message_template TEXT NOT NULL,           -- 用户看到的消息
    -- 示例: "尺寸 '{size}' 不支持，已调整为 '{adjusted_size}'"

    technical_message_template TEXT,               -- 技术详情（可选）

    -- 解决建议
    suggestions JSONB DEFAULT '[]',
    -- 示例: ["尝试使用 1024x1024", "查看支持的尺寸列表"]

    -- 可用于模板的变量
    available_variables JSONB DEFAULT '{}',
    -- 示例: ["size", "adjusted_size", "supported_sizes"]

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(provider_id, error_type, language)
);

CREATE INDEX idx_error_messages_provider ON error_message_templates(provider_id);
```

### 6. 模型调用统计表 (model_usage_stats)

存储调用统计，用于分析和优化。

```sql
CREATE TABLE model_usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES model_providers(id) ON DELETE CASCADE,

    -- 统计维度
    date DATE NOT NULL,
    hour INTEGER,                                  -- 0-23，可选的更细粒度

    -- 调用统计
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,

    -- 错误分布
    error_distribution JSONB DEFAULT '{}',
    -- 示例: {"rate_limit_exceeded": 10, "timeout": 5}

    -- 性能指标
    avg_response_time DECIMAL(10, 2),             -- 平均响应时间（毫秒）
    p50_response_time DECIMAL(10, 2),
    p95_response_time DECIMAL(10, 2),
    p99_response_time DECIMAL(10, 2),

    -- 成本
    total_cost DECIMAL(10, 4),

    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(provider_id, date, hour)
);

CREATE INDEX idx_stats_provider_date ON model_usage_stats(provider_id, date);
```

## 配置加载机制

### 1. ModelRegistry (模型注册表)

```python
from typing import Optional, Dict
from datetime import datetime, timedelta
import asyncio
from app.database import Database
from app.models.model_provider import ModelProvider

class ModelRegistry:
    """模型注册表 - 管理所有模型配置"""

    def __init__(self, db: Database):
        self.db = db
        self._cache: Dict[str, ModelProvider] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)  # 缓存5分钟
        self._reload_lock = asyncio.Lock()

    async def get_provider(self, name: str) -> Optional[ModelProvider]:
        """
        获取模型配置

        - 优先从缓存读取
        - 缓存过期则重新从数据库加载
        - 支持手动刷新
        """
        # 检查缓存
        if name in self._cache:
            expiry = self._cache_expiry.get(name)
            if expiry and expiry > datetime.now():
                return self._cache[name]

        # 从数据库加载
        async with self._reload_lock:
            # 双重检查
            if name in self._cache:
                expiry = self._cache_expiry.get(name)
                if expiry and expiry > datetime.now():
                    return self._cache[name]

            # 加载配置
            provider = await self._load_from_db(name)
            if provider:
                self._cache[name] = provider
                self._cache_expiry[name] = datetime.now() + self._cache_ttl

            return provider

    async def _load_from_db(self, name: str) -> Optional[ModelProvider]:
        """从数据库加载模型配置"""
        query = """
            SELECT * FROM model_providers
            WHERE name = $1 AND is_enabled = true
        """
        row = await self.db.fetch_one(query, name)

        if not row:
            return None

        # 加载关联的错误处理配置
        error_config = await self._load_error_config(row['id'])

        # 加载错误模式
        error_patterns = await self._load_error_patterns(row['id'])

        return ModelProvider(
            id=row['id'],
            name=row['name'],
            display_name=row['display_name'],
            api_endpoint=row['api_endpoint'],
            auth_config=row['auth_config'],
            request_config=row['request_config'],
            parameter_mapping=row['parameter_mapping'],
            parameter_schema=row['parameter_schema'],
            response_mapping=row['response_mapping'],
            error_config=error_config,
            error_patterns=error_patterns,
            **row
        )

    async def _load_error_config(self, provider_id: str) -> Dict:
        """加载错误处理配置"""
        query = """
            SELECT error_type, *
            FROM error_handling_config
            WHERE provider_id = $1
        """
        rows = await self.db.fetch_all(query, provider_id)

        return {
            row['error_type']: {
                'retry': {
                    'enabled': row['retry_enabled'],
                    'max_attempts': row['max_attempts'],
                    'base_wait': float(row['base_wait_time']),
                    'max_wait': float(row['max_wait_time']),
                    'exponential_base': float(row['exponential_base'])
                },
                'auto_fix': {
                    'enabled': row['auto_fix_enabled'],
                    'rules': row['fix_rules']
                }
            }
            for row in rows
        }

    async def _load_error_patterns(self, provider_id: str) -> List[Dict]:
        """加载错误模式"""
        query = """
            SELECT * FROM error_patterns
            WHERE provider_id = $1 AND is_active = true
            ORDER BY priority DESC
        """
        return await self.db.fetch_all(query, provider_id)

    async def list_providers(
        self,
        provider_type: Optional[str] = None,
        only_enabled: bool = True
    ) -> List[ModelProvider]:
        """列出所有模型"""
        cache_key = f"list_{provider_type}_{only_enabled}"

        # 类似的缓存逻辑
        # ...

    async def refresh_provider(self, name: str):
        """刷新指定模型的配置"""
        if name in self._cache:
            del self._cache[name]
            del self._cache_expiry[name]

    async def refresh_all(self):
        """刷新所有配置"""
        self._cache.clear()
        self._cache_expiry.clear()

    async def watch_changes(self):
        """监听数据库配置变更（PostgreSQL NOTIFY/LISTEN）"""
        # 实现配置变更的实时监听
        # 当配置表更新时，自动清除缓存
        pass
```

### 2. DynamicErrorHandler (动态错误处理器)

```python
from app.models.model_registry import ModelRegistry

class DynamicErrorHandler:
    """动态错误处理器 - 从数据库加载配置"""

    def __init__(self, model_registry: ModelRegistry):
        self.registry = model_registry

    async def classify_error(
        self,
        provider_name: str,
        error: Exception,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None
    ) -> ErrorContext:
        """使用数据库配置进行错误分类"""
        provider = await self.registry.get_provider(provider_name)

        if not provider:
            # 降级到默认分类器
            return self._default_classify(error, status_code, response_text)

        # 1. 尝试 HTTP 状态码匹配
        if status_code:
            pattern = self._find_pattern_by_status(
                provider.error_patterns,
                status_code
            )
            if pattern:
                return ErrorContext(
                    error_type=ErrorType(pattern['error_type']),
                    original_error=error,
                    provider=provider_name,
                    request_params={},
                    status_code=status_code,
                    extracted_data=pattern.get('extract_fields')
                )

        # 2. 尝试响应文本匹配
        if response_text:
            pattern = self._find_pattern_by_message(
                provider.error_patterns,
                response_text
            )
            if pattern:
                return ErrorContext(
                    error_type=ErrorType(pattern['error_type']),
                    original_error=error,
                    provider=provider_name,
                    request_params={},
                    response_text=response_text,
                    extracted_data=self._extract_fields(
                        pattern['extract_fields'],
                        response_text
                    )
                )

        # 3. 降级到默认分类器
        return self._default_classify(error, status_code, response_text)

    async def get_retry_strategy(
        self,
        provider_name: str,
        error_type: ErrorType
    ) -> Optional[RetryStrategy]:
        """从数据库获取重试策略"""
        provider = await self.registry.get_provider(provider_name)

        if not provider:
            return None

        config = provider.error_config.get(error_type.value, {})
        retry_config = config.get('retry', {})

        if not retry_config.get('enabled'):
            return None

        return RetryStrategy(
            max_attempts=retry_config.get('max_attempts', 3),
            base_wait=retry_config.get('base_wait', 1.0),
            max_wait=retry_config.get('max_wait', 60.0),
            exponential_base=retry_config.get('exponential_base', 2.0)
        )

    async def fix_parameter(
        self,
        provider_name: str,
        param_name: str,
        param_value: Any,
        error_type: ErrorType
    ) -> tuple[bool, Any, str]:
        """使用数据库配置修正参数"""
        provider = await self.registry.get_provider(provider_name)

        if not provider:
            return False, param_value, "未找到模型配置"

        config = provider.error_config.get(error_type.value, {})
        fix_config = config.get('auto_fix', {})

        if not fix_config.get('enabled'):
            return False, param_value, "该参数不支持自动修正"

        fix_rules = fix_config.get('rules', {})
        param_rule = fix_rules.get(param_name)

        if not param_rule:
            return False, param_value, f"未找到参数 {param_name} 的修正规则"

        # 执行修正
        strategy = param_rule.get('strategy', 'fallback')
        supported = param_rule.get('supported', [])
        fallback = param_rule.get('fallback')

        if strategy == 'closest_match':
            # 找到最接近的值
            fixed_value = self._find_closest_match(param_value, supported)
            if fixed_value != param_value:
                return True, fixed_value, f"参数已从 '{param_value}' 调整为 '{fixed_value}'"

        elif strategy == 'fallback':
            # 使用默认值
            if param_value not in supported:
                return True, fallback, f"参数 '{param_value}' 不支持，使用默认值 '{fallback}'"

        return False, param_value, "参数无需修正"

    async def translate_error(
        self,
        provider_name: str,
        error_type: ErrorType,
        language: str = 'zh',
        context: Optional[Dict] = None
    ) -> Dict:
        """从数据库加载错误消息模板"""
        provider = await self.registry.get_provider(provider_name)

        if not provider:
            return self._default_translate(error_type, language, context)

        # 从数据库查询模板
        query = """
            SELECT user_message_template, suggestions
            FROM error_message_templates
            WHERE provider_id = $1
              AND error_type = $2
              AND language = $3
        """
        row = await self.registry.db.fetch_one(
            query,
            provider.id,
            error_type.value,
            language
        )

        if row:
            # 填充模板
            message = row['user_message_template'].format(**(context or {}))
            return {
                'user_message': message,
                'suggestions': row['suggestions']
            }

        # 降级到默认翻译
        return self._default_translate(error_type, language, context)
```

## Admin UI 设计

### 1. 模型管理界面

#### 模型列表页面

```
┌─────────────────────────────────────────────────────────────────────┐
│  AI 服务管理                                    [添加模型] [刷新]  │
├─────────────────────────────────────────────────────────────────────┤
│  搜索: [____________] 类型: [全部▼] 状态: [全部▼]                  │
├──────┬────────────┬──────────┬────────┬──────────┬────────┬────────┤
│ 名称 │ 显示名称   │ 类型     │ 状态   │ 优先级   │ 统计   │ 操作   │
├──────┼────────────┼──────────┼────────┼──────────┼────────┼────────┤
│ dal  │ DALL-E 3   │ 图像     │ ●启用  │ 10       │ 查看   │ 编辑   │
│      │            │          │        │          │        │ 禁用   │
│      │            │          │        │          │        │ 测试   │
├──────┼────────────┼──────────┼────────┼──────────┼────────┼────────┤
│ stab │ Stable Dif │ 图像     │ ●启用  │ 8        │ 查看   │ 编辑   │
│      │ fusion XL  │          │        │          │        │ 禁用   │
│      │            │          │        │          │        │ 测试   │
├──────┼────────────┼──────────┼────────┼──────────┼────────┼────────┤
│ runw │ Runway     │ 视频     │ ○禁用  │ 5        │ 查看   │ 编辑   │
│      │ Gen-2      │          │        │          │        │ 启用   │
│      │            │          │        │          │        │ 测试   │
└──────┴────────────┴──────────┴────────┴──────────┴────────┴────────┘
```

#### 添加/编辑模型表单

```
┌─────────────────────────────────────────────────────────────────────┐
│  添加/编辑模型                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  基本信息                                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 模型标识: [dalle-3____________]  (唯一标识，用于代码引用)      │  │
│  │ 显示名称: [DALL-E 3__________]  (用户看到的名称)              │  │
│  │ 描述:     [OpenAI 的图像生成模型_________________]            │  │
│  │ 类型:     ○ 图像  ○ 视频  ○ 音频  ○ 文本                     │  │
│  │ 分类:     [openai▼]                                          │  │
│  │ 优先级:   [10____] (数字越大越优先)                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  API 配置                                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ API 端点: [https://api.openai.com/v1/images/generations_]    │  │
│  │ HTTP 方法: [POST▼]                                           │  │
│  │ 超时时间: [30__] 秒                                           │  │
│  │ 最大并发: [10__]                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  认证配置                                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 认证类型: [Bearer Token▼]                                    │  │
│  │          ○ Bearer Token  ○ API Key  ○ Basic Auth            │  │
│  │ Token 位置: ○ Header  ● Query  ○ Body                       │  │
│  │ Header 名称: [Authorization___________]                      │  │
│  │ Token 前缀: [Bearer _________________]                       │  │
│  │                                                                 │  │
│  │ API Key: [sk-**********************]  [管理 API Keys]        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  参数定义 (JSON Schema)                                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ {                                                              │  │
│  │   "type": "object",                                            │  │
│  │   "properties": {                                              │  │
│  │     "size": {                                                  │  │
│  │       "type": "string",                                        │  │
│  │       "enum": ["1024x1024", "1792x1024", "1024x1792"],        │  │
│  │       "default": "1024x1024"                                   │  │
│  │     }                                                           │  │
│  │   }                                                             │  │
│  │ }                                                              │  │
│  │                                      [验证 JSON] [格式化]      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  参数映射                                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ prompt      → [prompt_____________]  (用户输入)               │  │
│  │ size        → [size_______________]                           │  │
│  │ quality     → [quality____________]                           │  │
│  │ style       → [options.style______]  (嵌套映射)               │  │
│  │                                            [+ 添加映射]      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  响应映射 (JSONPath)                                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ image_url       → [data.0.url________________]               │  │
│  │ revised_prompt  → [data.0.revised_prompt_________]           │  │
│  │                                              [+ 添加映射]    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  [取消]  [保存并测试]  [保存]                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. 错误处理配置界面

```
┌─────────────────────────────────────────────────────────────────────┐
│  错误处理配置 - DALL-E 3                          [返回模型列表]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  标签页: [重试策略] [参数修正] [错误模式] [消息模板]                  │
│                                                                       │
│  ┌─ 重试策略 ────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  错误类型: [全部▼]                                              │  │
│  │                                                                  │  │
│  │  ┌─ RATE_LIMIT_EXCEEDED (速率限制) ─────────────────────────┐  │  │
│  │  │                                                             │  │
│  │  │  ● 启用重试                                                │  │
│  │  │                                                             │  │
│  │  │  最大重试次数: [5__] 次                                    │  │
│  │  │  基础等待时间: [5__] 秒                                    │  │
│  │  │  最大等待时间: [120__] 秒                                  │  │
│  │  │  指数退避基数: [2__]  (等待时间 = base_wait * 2^attempt) │  │
│  │  │                                                             │  │
│  │  │  预估等待时间:                                              │  │
│  │  │    第1次: 5秒                                              │  │
│  │  │    第2次: 10秒                                             │  │
│  │  │    第3次: 20秒                                             │  │
│  │  │    第4次: 40秒                                             │  │
│  │  │    第5次: 80秒                                             │  │
│  │  │                                                             │  │
│  │  │  [取消] [保存]                                              │  │
│  │  └─────────────────────────────────────────────────────────────┘  │
│  │                                                                  │  │
│  │  ┌─ TIMEOUT (超时) ──────────────────────────────────────────┐  │
│  │  │                                                             │  │
│  │  │  ● 启用重试                                                │  │
│  │  │  最大重试次数: [4__] 次                                    │  │
│  │  │  基础等待时间: [1__] 秒                                    │  │
│  │  │  ...                                                       │  │
│  │  │                                                             │  │
│  │  │  [取消] [保存]                                              │  │
│  │  └─────────────────────────────────────────────────────────────┘  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ 参数修正 ────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  ● 启用参数自动修正                                              │  │
│  │                                                                  │  │
│  │  ┌─ size (尺寸) ─────────────────────────────────────────────┐  │
│  │  │                                                             │  │
│  │  │  ● 启用自动修正                                            │  │
│  │  │  修正策略: ○ 最接近匹配  ● 使用默认值  ○ 严格模式        │  │
│  │  │                                                             │  │
│  │  │  支持的尺寸:                                                │  │
│  │  │    ┌──────────────────────────────────────────────────┐  │  │
│  │  │    │ 1024x1024  (默认)  [删除]                         │  │  │
│  │  │    │ 1792x1024                 [删除]                  │  │  │
│  │  │    │ 1024x1792                 [删除]                  │  │  │
│  │  │    │ [+ 添加尺寸]                                     │  │  │
│  │  │    └──────────────────────────────────────────────────┘  │  │
│  │  │                                                             │  │
│  │  │  [测试修正] 输入: "1920x1080" → 预期输出: "1792x1024"      │  │
│  │  │                                                             │  │
│  │  │  [取消] [保存]                                              │  │
│  │  └─────────────────────────────────────────────────────────────┘  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ 错误模式 ────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  [+ 添加错误模式]                                                │  │
│  │                                                                  │  │
│  │  ┌─ 429 Too Many Requests ─────────────────────────────────┐  │
│  │  │                                                             │  │
│  │  │  类型: ● HTTP 状态码  ○ 错误码  ○ 消息模式  ○ 正则      │  │
│  │  │  模式值: [429________]                                     │  │
│  │  │  映射到: [RATE_LIMIT_EXCEEDED▼]                           │  │
│  │  │  优先级: [10____]                                          │  │
│  │  │                                                             │  │
│  │  │  提取字段:                                                  │  │
│  │  │    retry_after → {headers.Retry-After}                     │  │
│  │  │    [+ 添加提取]                                            │  │
│  │  │                                                             │  │
│  │  │  [测试模式] 输入: "HTTP 429" → 匹配: ✓                      │  │
│  │  │                                                             │  │
│  │  │  [取消] [保存]  [删除]                                      │  │
│  │  └─────────────────────────────────────────────────────────────┘  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ 消息模板 ────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  语言: [全部▼]                                                  │  │
│  │                                                                  │  │
│  │  ┌─ RATE_LIMIT_EXCEEDED (中文) ─────────────────────────────┐  │
│  │  │                                                             │  │
│  │  │  用户消息:                                                  │  │
│  │  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  │ 请求过于频繁，请稍后再试                             │  │
│  │  │  │ （已自动重试，请耐心等待）                           │  │
│  │  │  └────────────────────────────────────────────────────┘  │  │
│  │  │                                                             │  │
│  │  │  技术详情:                                                  │  │
│  │  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  │ Rate limit exceeded. Please try again later.       │  │
│  │  │  └────────────────────────────────────────────────────┘  │  │
│  │  │                                                             │  │
│  │  │  解决建议:                                                  │  │
│  │  │    ┌──────────────────────────────────────────────────┐  │  │
│  │  │    │ 1. 减少并发请求数量                              │  │
│  │  │    │ 2. 等待 1-2 分钟后重试                           │  │
│  │  │    │ 3. 考虑升级 API 套餐                            │  │
│  │  │    │ [+ 添加建议]                                     │  │
│  │  │    └──────────────────────────────────────────────────┘  │  │
│  │  │                                                             │  │
│  │  │  可用变量: {retry_after}, {max_wait}                       │  │
│  │  │                                                             │  │
│  │  │  [预览] [取消] [保存]                                      │  │
│  │  └─────────────────────────────────────────────────────────────┘  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  [导出配置] [导入配置]                                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. 测试连接功能

```
┌─────────────────────────────────────────────────────────────────────┐
│  测试 API 连接 - DALL-E 3                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  测试参数:                                                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 提示词: [a beautiful sunset over the ocean___________]       │  │
│  │ 尺寸:   [1024x1024▼]                                         │  │
│  │ 质量:   [standard▼]                                          │  │
│  │                                                              │  │
│  │                     [发送测试请求]                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  测试结果:                                                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 状态: ✓ 成功                                                  │  │
│  │                                                              │  │
│  │ 请求时间: 2024-01-15 10:30:25                                │  │
│  │ 响应时间: 2.3 秒                                              │  │
│  │                                                              │  │
│  │ 请求详情:                                                      │  │
│  │   POST https://api.openai.com/v1/images/generations         │  │
│  │   Headers:                                                   │  │
│  │     Authorization: Bearer sk-***                             │  │
│  │     Content-Type: application/json                           │  │
│  │   Body: {                                                    │  │
│  │     "model": "dall-e-3",                                     │  │
│  │     "prompt": "a beautiful sunset...",                       │  │
│  │     "size": "1024x1024",                                     │  │
│  │     "quality": "standard"                                    │  │
│  │   }                                                          │  │
│  │                                                              │  │
│  │ 响应详情:                                                      │  │
│  │   Status: 200 OK                                             │  │
│  │   Body: {                                                    │  │
│  │     "created": 1705304625,                                   │  │
│  │     "data": [{                                               │  │
│  │       "url": "https://...",                                  │  │
│  │       "revised_prompt": "..."                                │  │
│  │     }]                                                       │  │
│  │   }                                                          │  │
│  │                                                              │  │
│  │ 生成的图片:                                                    │  │
│  │   ┌────────────────────────────────────────────────────┐   │  │
│  │   │                                                    │   │  │
│  │   │         [生成的图片预览]                           │   │  │
│  │   │                                                    │   │  │
│  │   └────────────────────────────────────────────────────┘   │  │
│  │   [在浏览器中打开] [下载]                                    │  │
│  │                                                              │  │
│  │                    [关闭] [保存配置]                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## API 接口设计

### 模型管理 API

```python
# 1. 列出所有模型
GET /api/v1/admin/models
Query Parameters:
  - type: str (image | video)
  - enabled: bool
  - search: str

Response:
{
  "models": [
    {
      "id": "uuid",
      "name": "dalle-3",
      "display_name": "DALL-E 3",
      "type": "image",
      "is_enabled": true,
      "is_available": true,
      "priority": 10,
      "stats": {
        "total_calls": 1000,
        "success_rate": 0.95,
        "avg_response_time": 2.5
      }
    }
  ]
}

# 2. 获取单个模型详情
GET /api/v1/admin/models/{model_id}

# 3. 创建模型
POST /api/v1/admin/models
Body:
{
  "name": "dalle-3",
  "display_name": "DALL-E 3",
  "type": "image",
  "api_endpoint": "https://api.openai.com/v1/images/generations",
  "auth_config": {...},
  "parameter_schema": {...},
  "parameter_mapping": {...},
  "response_mapping": {...}
}

# 4. 更新模型
PUT /api/v1/admin/models/{model_id}

# 5. 删除模型
DELETE /api/v1/admin/models/{model_id}

# 6. 启用/禁用模型
PATCH /api/v1/admin/models/{model_id}/toggle
Body: {"is_enabled": true}

# 7. 测试模型连接
POST /api/v1/admin/models/{model_id}/test
Body: {
  "test_prompt": "a cat",
  "parameters": {"size": "1024x1024"}
}
```

### 错误处理配置 API

```python
# 1. 获取模型的错误处理配置
GET /api/v1/admin/models/{model_id}/error-config

# 2. 更新重试策略
PUT /api/v1/admin/models/{model_id}/error-config/retry
Body: {
  "error_type": "RATE_LIMIT_EXCEEDED",
  "retry_enabled": true,
  "max_attempts": 5,
  "base_wait_time": 5.0,
  "max_wait_time": 120.0
}

# 3. 更新参数修正规则
PUT /api/v1/admin/models/{model_id}/error-config/fix-rules
Body: {
  "error_type": "INVALID_SIZE",
  "auto_fix_enabled": true,
  "fix_rules": {
    "size": {
      "strategy": "closest_match",
      "supported": ["1024x1024", "1792x1024"],
      "fallback": "1024x1024"
    }
  }
}

# 4. 添加错误模式
POST /api/v1/admin/models/{model_id}/error-patterns
Body: {
  "pattern_type": "status_code",
  "pattern_value": "429",
  "error_type": "RATE_LIMIT_EXCEEDED",
  "priority": 10
}

# 5. 更新错误消息模板
PUT /api/v1/admin/models/{model_id}/error-messages/{error_type}
Body: {
  "language": "zh",
  "user_message_template": "请求过于频繁...",
  "suggestions": ["建议1", "建议2"]
}
```

### 配置导入/导出 API

```python
# 导出模型配置
GET /api/v1/admin/models/{model_id}/export
Response: 完整的模型配置 JSON

# 导入模型配置
POST /api/v1/admin/models/import
Body: 完整的模型配置 JSON

# 批量导出
GET /api/v1/admin/models/export-all

# 批量导入
POST /api/v1/admin/models/import-batch
Body: {"models": [...]}
```

## 配置示例

### 完整的 DALL-E 3 配置

```json
{
  "model": {
    "name": "dalle-3",
    "display_name": "DALL-E 3",
    "description": "OpenAI 的图像生成模型",
    "type": "image",
    "category": "openai",
    "api_endpoint": "https://api.openai.com/v1/images/generations",
    "http_method": "POST",
    "priority": 10,
    "cost_per_request": 0.04,
    "cost_per_image": 0.04,
    "rate_limit": 60,
    "max_concurrent": 10
  },
  "auth_config": {
    "type": "bearer",
    "header_name": "Authorization",
    "token_prefix": "Bearer ",
    "key_location": "header"
  },
  "request_config": {
    "headers": {
      "Content-Type": "application/json"
    },
    "timeout": 30,
    "max_retries": 3
  },
  "parameter_schema": {
    "type": "object",
    "properties": {
      "size": {
        "type": "string",
        "enum": ["1024x1024", "1792x1024", "1024x1792"],
        "default": "1024x1024",
        "description": "图片尺寸"
      },
      "quality": {
        "type": "string",
        "enum": ["standard", "hd"],
        "default": "standard",
        "description": "图片质量"
      },
      "style": {
        "type": "string",
        "enum": ["vivid", "natural"],
        "default": "vivid",
        "description": "生成风格"
      }
    },
    "required": ["prompt"]
  },
  "parameter_mapping": {
    "prompt": "prompt",
    "size": "size",
    "quality": "quality",
    "style": "style"
  },
  "response_mapping": {
    "image_url": "data.0.url",
    "revised_prompt": "data.0.revised_prompt"
  },
  "error_handling": {
    "retry_config": {
      "RATE_LIMIT_EXCEEDED": {
        "retry_enabled": true,
        "max_attempts": 5,
        "base_wait_time": 5.0,
        "max_wait_time": 120.0,
        "exponential_base": 2.0
      },
      "TIMEOUT": {
        "retry_enabled": true,
        "max_attempts": 4,
        "base_wait_time": 1.0,
        "max_wait_time": 30.0,
        "exponential_base": 2.0
      }
    },
    "fix_rules": {
      "INVALID_SIZE": {
        "auto_fix_enabled": true,
        "fix_rules": {
          "size": {
            "strategy": "closest_match",
            "supported": ["1024x1024", "1792x1024", "1024x1792"],
            "fallback": "1024x1024"
          }
        }
      }
    },
    "error_patterns": [
      {
        "pattern_type": "status_code",
        "pattern_value": "429",
        "error_type": "RATE_LIMIT_EXCEEDED",
        "priority": 10,
        "extract_fields": {
          "retry_after": "{headers.Retry-After}"
        }
      },
      {
        "pattern_type": "message_pattern",
        "pattern_value": "invalid size",
        "error_type": "INVALID_SIZE",
        "priority": 5
      }
    ],
    "message_templates": {
      "RATE_LIMIT_EXCEEDED": {
        "zh": {
          "user_message": "请求过于频繁，请稍后再试（已自动重试，请耐心等待）",
          "suggestions": [
            "减少并发请求数量",
            "等待 1-2 分钟后重试",
            "考虑升级 API 套餐"
          ]
        },
        "en": {
          "user_message": "Rate limit exceeded. Please try again later",
          "suggestions": [
            "Reduce concurrent requests",
            "Wait 1-2 minutes before retrying",
            "Consider upgrading your API plan"
          ]
        }
      },
      "INVALID_SIZE": {
        "zh": {
          "user_message": "尺寸 '{size}' 不受支持，已自动调整为 '{adjusted_size}'",
          "suggestions": [
            "使用推荐的尺寸: 1024x1024",
            "查看文档了解支持的尺寸列表"
          ]
        }
      }
    }
  }
}
```

## 通用 API 调用器实现

```python
class GenericAPIAdapter:
    """通用 API 适配器 - 根据配置动态调用"""

    def __init__(self, model_registry: ModelRegistry):
        self.registry = model_registry
        self.error_handler = DynamicErrorHandler(model_registry)

    async def call(
        self,
        provider_name: str,
        prompt: str,
        **user_params
    ) -> dict:
        """
        通用 API 调用方法

        Args:
            provider_name: 模型名称
            prompt: 用户提示词
            **user_params: 用户提供的参数

        Returns:
            调用结果或错误信息
        """
        # 1. 加载模型配置
        provider = await self.registry.get_provider(provider_name)
        if not provider:
            return {
                "success": False,
                "error": {
                    "type": "model_not_found",
                    "message": f"未找到模型: {provider_name}"
                }
            }

        # 2. 参数映射
        request_params = self._map_parameters(
            provider.parameter_mapping,
            prompt,
            user_params
        )

        # 3. 构建请求
        headers = self._build_headers(provider)
        api_key = await self._get_api_key(provider.id)

        # 4. 添加认证
        headers = self._add_auth(
            headers,
            provider.auth_config,
            api_key
        )

        # 5. 执行调用（带错误处理）
        return await self._execute_with_error_handling(
            provider,
            headers,
            request_params
        )

    def _map_parameters(
        self,
        mapping: dict,
        prompt: str,
        user_params: dict
    ) -> dict:
        """根据映射规则转换参数"""
        result = {}

        # 添加 prompt
        if 'prompt' in mapping:
            result[mapping['prompt']] = prompt

        # 映射其他参数
        for key, value in user_params.items():
            if key in mapping:
                # 支持嵌套映射，如 "options.style"
                mapped_key = mapping[key]
                self._set_nested_param(result, mapped_key, value)

        return result

    def _set_nested_param(self, params: dict, key: str, value: any):
        """设置嵌套参数"""
        keys = key.split('.')
        for k in keys[:-1]:
            if k not in params:
                params[k] = {}
            params = params[k]
        params[keys[-1]] = value

    def _build_headers(self, provider) -> dict:
        """构建请求头"""
        return provider.request_config.get('headers', {}).copy()

    def _add_auth(
        self,
        headers: dict,
        auth_config: dict,
        api_key: str
    ) -> dict:
        """添加认证信息"""
        auth_type = auth_config.get('type')

        if auth_type == 'bearer':
            header_name = auth_config.get('header_name', 'Authorization')
            token_prefix = auth_config.get('token_prefix', 'Bearer ')
            headers[header_name] = f"{token_prefix}{api_key}"

        elif auth_type == 'api_key':
            header_name = auth_config.get('header_name', 'X-API-Key')
            headers[header_name] = api_key

        return headers

    async def _execute_with_error_handling(
        self,
        provider,
        headers: dict,
        request_params: dict
    ) -> dict:
        """执行 API 调用并处理错误"""
        task_id = str(uuid.uuid4())

        try:
            # 使用动态错误处理器执行调用
            result = await self.error_handler.execute_with_retry(
                task_id,
                provider.name,
                lambda: self._make_http_request(
                    provider.api_endpoint,
                    headers,
                    request_params,
                    provider.request_config.get('timeout', 30)
                )
            )

            # 提取响应
            response_data = self._extract_response(
                result,
                provider.response_mapping
            )

            return {
                "success": True,
                "result": response_data,
                "provider": provider.name
            }

        except Exception as e:
            # 错误已经被错误处理器处理
            return {
                "success": False,
                "error": e.to_dict() if hasattr(e, 'to_dict') else {
                    "message": str(e)
                }
            }

    async def _make_http_request(
        self,
        url: str,
        headers: dict,
        params: dict,
        timeout: int
    ) -> dict:
        """发起 HTTP 请求"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=params,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

    def _extract_response(
        self,
        response: dict,
        mapping: dict
    ) -> dict:
        """从响应中提取需要的字段"""
        result = {}

        for key, path in mapping.items():
            # 使用 JSONPath 提取
            value = self._get_by_path(response, path)
            if value is not None:
                result[key] = value

        return result

    def _get_by_path(self, data: dict, path: str) -> any:
        """按路径获取值"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            else:
                return None
        return value

    async def _get_api_key(self, provider_id: str) -> str:
        """获取可用的 API Key（轮询负载均衡）"""
        query = """
            SELECT api_key_encrypted
            FROM api_keys
            WHERE provider_id = $1
              AND is_active = true
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY priority DESC, quota_used ASC
            LIMIT 1
        """
        row = await self.registry.db.fetch_one(query, provider_id)

        if not row:
            raise Exception("No available API key")

        # 解密 API Key
        return decrypt_api_key(row['api_key_encrypted'])
```

## 使用流程

### 1. 添加新模型的完整流程

```
1. 访问 Admin UI → 模型管理 → 添加模型

2. 填写基本信息:
   - 模型标识: "midjourney"
   - 显示名称: "Midjourney"
   - 类型: "图像"
   - API 端点: "https://api.midjourney.com/v1/imagine"

3. 配置认证:
   - 选择认证类型 (Bearer Token / API Key)
   - 管理或添加 API Key

4. 定义参数:
   - 编写 JSON Schema 定义支持的参数
   - 设置参数映射规则

5. 配置响应映射:
   - 定义如何从 API 响应提取结果

6. 配置错误处理:
   - 设置重试策略
   - 配置参数修正规则
   - 添加错误模式映射
   - 编写错误消息模板

7. 测试连接:
   - 发送测试请求验证配置
   - 查看生成的结果

8. 保存并启用:
   - 配置立即生效
   - Agent 可以使用新模型
```

### 2. 在 Agent 中使用

```python
# Agent 节点中调用
async def executor_node(state: AgentState):
    """执行节点 - 动态选择模型并调用"""

    # 根据任务类型选择最佳模型
    provider = await model_registry.get_best_provider(
        type="image",
        capabilities=["high_quality"]
    )

    # 使用通用适配器调用
    adapter = GenericAPIAdapter(model_registry)

    result = await adapter.call(
        provider_name=provider.name,
        prompt=state["prompt"],
        **state["parameters"]
    )

    if result["success"]:
        state["result"] = result["result"]
    else:
        state["error"] = result["error"]

    return state
```

## 最佳实践

### 1. 配置管理

- ✅ 所有配置都存储在数据库，不硬编码
- ✅ 使用事务确保配置的原子性更新
- ✅ 实现配置的版本控制和回滚
- ✅ 配置变更后通知相关服务清除缓存

### 2. API Key 管理

- ✅ 加密存储 API Key
- ✅ 支持多个 API Key 轮询负载均衡
- ✅ 记录每个 Key 的使用配额
- ✅ 设置 Key 的过期时间自动切换

### 3. 错误处理配置

- ✅ 根据服务商特性定制错误处理策略
- ✅ 测试错误模式的匹配规则
- ✅ 提供多语言的错误消息
- ✅ 定期分析错误统计优化配置

### 4. 性能优化

- ✅ 实现配置缓存减少数据库查询
- ✅ 使用 PostgreSQL NOTIFY/LISTEN 实现配置热更新
- ✅ 监控模型调用性能动态调整优先级
- ✅ 根据成本和性能自动选择最佳模型

## 监控和分析

### 关键指标

| 指标 | 说明 | 用途 |
|------|------|------|
| 模型可用性 | 模型健康检查通过率 | 选择可用模型 |
| 调用成功率 | 成功调用 / 总调用 | 评估模型稳定性 |
| 平均响应时间 | API 调用的平均耗时 | 性能优化 |
| 错误分布 | 各类错误的发生次数 | 优化错误处理 |
| 修正成功率 | 参数修正后成功的比例 | 评估修正规则 |
| 重试成功率 | 重试后成功的比例 | 调整重试策略 |
| 成本效率 | 单次请求的平均成本 | 成本控制 |

### 统计仪表盘

```
┌─────────────────────────────────────────────────────────────┐
│  模型统计仪表盘                             [导出报告]      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  模型选择: [全部▼]  时间范围: [最近7天▼]                     │
│                                                               │
│  ┌─ 总览 ─────────────────────────────────────────────────┐ │
│  │  总调用次数: 50,123    成功率: 96.5%                   │ │
│  │  平均响应时间: 2.3秒    总成本: $1,234.56              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ 调用趋势 ─────────────────────────────────────────────┐ │
│  │  [折线图：每日调用次数和成功率]                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ 模型对比 ─────────────────────────────────────────────┐ │
│  │  模型名称      调用次数  成功率  响应时间  成本         │ │
│  │  DALL-E 3      25,000   97.5%   2.1秒     $800         │ │
│  │  Stable Diff   15,000   95.2%   3.5秒     $300         │ │
│  │  Midjourney    10,123   96.8%   5.2秒     $134.56      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ 错误分布 ─────────────────────────────────────────────┐ │
│  │  [饼图：各类错误占比]                                   │ │
│  │  - RATE_LIMIT_EXCEEDED: 45%                            │ │
│  │  - TIMEOUT: 30%                                        │ │
│  │  - INVALID_SIZE: 15%                                   │ │
│  │  - 其他: 10%                                           │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ 错误处理效果 ─────────────────────────────────────────┐ │
│  │  参数修正成功率: 92.3%                                  │ │
│  │  重试成功率: 87.5%                                      │ │
│  │  自动恢复率: 95.8% (修正 + 重试)                        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 总结

通过这套模型可配置化系统：

1. **完全外部化**: 所有模型配置和错误处理策略都存储在数据库
2. **动态加载**: 运行时从数据库加载配置，支持热更新
3. **UI 管理**: 提供可视化管理界面，无需修改代码
4. **灵活扩展**: 轻松添加新模型、新错误处理规则
5. **智能优化**: 根据统计数据自动选择最佳模型
6. **完整监控**: 详细的调用统计和错误分析

这样实现了：
- ✅ 无需重启即可添加/修改模型
- ✅ 每个模型的错误处理策略可独立配置
- ✅ 通过 UI 可视化管理所有配置
- ✅ 支持配置的导入导出和版本管理
- ✅ 完整的监控和分析能力
