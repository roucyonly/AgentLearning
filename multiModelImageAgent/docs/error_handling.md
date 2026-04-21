# 错误处理与自动恢复机制

## 概述

本文档描述 MultiModel Image Agent 的完整错误处理和自动恢复机制。系统通过智能错误分类、自动参数修正、指数退避重试和友好错误提示，提供高可靠性的 API 调用能力。

### 核心能力

- **智能错误分类**: 自动识别错误类型并采取相应策略
- **自动参数修正**: 参数错误时尝试自动调整并重试
- **指数退避重试**: 根据错误类型使用不同的重试策略
- **友好错误提示**: 将技术错误翻译成用户友好的中文提示
- **完整追踪记录**: 记录所有重试历史和修正过程

## 架构设计

### 整体架构

```
API 调用
    │
    ▼
┌─────────────────┐
│  通用 API 调用器 │
└────────┬────────┘
         │
         ▼
    [错误发生]
         │
         ▼
┌───────────────────────────────────────┐
│         错误分类器                     │
│  ┌────────────┬────────────┬─────────┐│
│  │ 可修正错误 │ 可重试错误 │ 需要处理 ││
│  └────────────┴────────────┴─────────┘│
└───┬──────────────┬──────────┬─────────┘
    │              │          │
    ▼              ▼          ▼
┌─────────┐   ┌─────────┐  ┌──────────┐
│参数修正器│   │重试管理器│  │错误翻译器│
└────┬────┘   └────┬────┘  └─────┬────┘
     │             │             │
     ▼             ▼             ▼
  重新调用      指数退避      友好提示
     │             │             │
     └──────────┬───┴─────────────┘
                ▼
         返回给用户
```

### 模块职责

| 模块 | 职责 |
|------|------|
| **ErrorClassifier** | 分析错误，分类错误类型 |
| **ParameterFixer** | 自动修正不合法的参数 |
| **RetryManager** | 管理重试策略和指数退避 |
| **ErrorTranslator** | 翻译错误消息，生成友好提示 |
| **ErrorHandler** | 协调所有模块，处理完整流程 |

## 错误分类体系

### 错误类型定义

```python
from enum import Enum

class ErrorType(Enum):
    """错误类型分类"""

    # ===== 可修正的错误 =====
    INVALID_PARAMETER = "invalid_parameter"
    # 说明: 参数错误，可根据错误信息修正

    INVALID_SIZE = "invalid_size"
    # 说明: 图片尺寸不支持，可映射到支持的尺寸

    INVALID_FORMAT = "invalid_format"
    # 说明: 格式不支持，可转换为支持的格式

    # ===== 可重试的错误 =====
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    # 说明: API 调用频率超限，需要等待后重试

    SERVER_ERROR = "server_error"
    # 说明: 服务器错误（5xx），可以重试

    TIMEOUT = "timeout"
    # 说明: 请求超时，可以重试

    NETWORK_ERROR = "network_error"
    # 说明: 网络连接错误，可以重试

    # ===== 需要人工处理 =====
    AUTHENTICATION_FAILED = "auth_failed"
    # 说明: API Key 认证失败，需要检查配置

    QUOTA_EXCEEDED = "quota_exceeded"
    # 说明: API 配额用完，需要充值或升级

    INVALID_API_KEY = "invalid_api_key"
    # 说明: API Key 无效或过期

    CONTENT_MODERATION = "content_moderation"
    # 说明: 生成内容违规，需要修改提示词

    # ===== 未知错误 =====
    UNKNOWN = "unknown"
```

### 错误分类策略

错误分类器按以下优先级判断：

1. **HTTP 状态码**: 快速判断错误类型
2. **响应文本**: 详细分析错误原因
3. **异常类型**: 判断底层错误类型

#### HTTP 状态码映射

| 状态码 | 错误类型 | 可重试 |
|--------|----------|--------|
| 400 | INVALID_PARAMETER | ❌ |
| 401 | AUTHENTICATION_FAILED | ❌ |
| 403 | QUOTA_EXCEEDED | ❌ |
| 429 | RATE_LIMIT_EXCEEDED | ✅ |
| 500 | SERVER_ERROR | ✅ |
| 502 | SERVER_ERROR | ✅ |
| 503 | SERVER_ERROR | ✅ |
| 504 | TIMEOUT | ✅ |

#### 服务商特定错误码

```python
# OpenAI
ERROR_PATTERNS = {
    "openai": {
        "invalid_request_error": INVALID_PARAMETER,
        "rate_limit_exceeded": RATE_LIMIT_EXCEEDED,
        "server_error": SERVER_ERROR,
        "content_policy_violation": CONTENT_MODERATION,
    }
}

# Stability AI
ERROR_PATTERNS = {
    "stability": {
        "invalid_size": INVALID_SIZE,
        "rate_limit": RATE_LIMIT_EXCEEDED,
        "500": SERVER_ERROR,
        "503": SERVER_ERROR,
    }
}

# Runway
ERROR_PATTERNS = {
    "runway": {
        "unauthorized": AUTHENTICATION_FAILED,
        "quota_exceeded": QUOTA_EXCEEDED,
        "timeout": TIMEOUT,
    }
}
```

## 自动参数修正

### 支持的修正类型

#### 1. 尺寸修正 (Size Fixing)

将不支持的尺寸映射到最接近的支持尺寸。

```python
# DALL-E 3 支持的尺寸
DALLE_SUPPORTED_SIZES = ["1024x1024", "1792x1024", "1024x1792"]

# 示例修正逻辑
输入: "1920x1080"
分析: 宽度接近 1792，高度接近 1024
修正: "1792x1024"
说明: "尺寸 '1920x1080' 不支持，自动调整为 '1792x1024'"
```

#### 2. 格式修正 (Format Fixing)

```python
# DALL-E 支持的格式
DALLE_SUPPORTED_FORMATS = ["png", "url"]

输入: "jpg"
修正: "url"
说明: "格式 'jpg' 不支持，使用默认值"
```

#### 3. 质量修正 (Quality Fixing)

```python
# DALL-E 支持的质量
DALLE_SUPPORTED_QUALITIES = ["standard", "hd"]

输入: "high"
修正: "hd"
说明: "质量 'high' 不支持，使用默认值"
```

### 参数修正规则配置

```python
FIX_RULES = {
    "size": {
        "dalle": {
            "supported": ["1024x1024", "1792x1024", "1024x1792"],
            "fallback": "1024x1024",
            "auto_fix": True
        },
        "stability": {
            "supported": ["512x512", "768x768", "1024x1024", "1152x896"],
            "fallback": "1024x1024",
            "auto_fix": True
        }
    },
    "format": {
        "dalle": {
            "supported": ["png", "url"],
            "fallback": "url",
            "auto_fix": True
        }
    },
    "quality": {
        "dalle": {
            "supported": ["standard", "hd"],
            "fallback": "standard",
            "auto_fix": True
        }
    }
}
```

## 智能重试机制

### 重试策略配置

不同错误类型使用不同的重试策略：

| 错误类型 | 最大重试次数 | 基础等待时间 | 最大等待时间 | 说明 |
|----------|--------------|--------------|--------------|------|
| SERVER_ERROR | 3 | 2秒 | 60秒 | 服务器不稳定 |
| TIMEOUT | 4 | 1秒 | 30秒 | 超时需要快速重试 |
| RATE_LIMIT_EXCEEDED | 5 | 5秒 | 120秒 | 需要较长等待 |
| NETWORK_ERROR | 3 | 1秒 | 20秒 | 网络波动 |

### 指数退避算法

等待时间计算公式：

```
wait_time = min(base_wait * (2 ^ attempt), max_wait)
```

**示例计算 (SERVER_ERROR):**

| 尝试次数 | 等待时间计算 | 实际等待 |
|----------|--------------|----------|
| 第1次 | min(2 * 2^0, 60) = min(2, 60) | 2秒 |
| 第2次 | min(2 * 2^1, 60) = min(4, 60) | 4秒 |
| 第3次 | min(2 * 2^2, 60) = min(8, 60) | 8秒 |

### 速率限制特殊处理

当遇到 `429 Too Many Requests` 时：

1. 尝试从响应头 `Retry-After` 获取建议等待时间
2. 尝试从错误消息中提取等待时间（如 "try again in 5 seconds"）
3. 如果获取到，使用该时间；否则使用配置的基础等待时间

### 重试历史记录

每次重试都会记录：

```python
{
    "task_id": "task_123",
    "attempts": [
        {
            "attempt": 1,
            "success": False,
            "error": "Rate limit exceeded",
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "attempt": 2,
            "success": False,
            "error": "Rate limit exceeded",
            "timestamp": "2024-01-15T10:00:05Z"
        },
        {
            "attempt": 3,
            "success": True,
            "timestamp": "2024-01-15T10:00:10Z"
        }
    ]
}
```

## 错误消息本地化

### 消息翻译策略

#### 1. 基础消息模板

```python
ERROR_MESSAGES = {
    INVALID_SIZE: {
        "en": "Size '{size}' is not supported",
        "zh": "尺寸 '{size}' 不受支持，已自动调整为 '{adjusted_size}'"
    },
    RATE_LIMIT_EXCEEDED: {
        "en": "Rate limit exceeded. Please try again later",
        "zh": "请求过于频繁，请稍后再试（已自动重试，请耐心等待）"
    },
    SERVER_ERROR: {
        "en": "Server error. The service is temporarily unavailable",
        "zh": "服务商暂时不可用，正在自动重试..."
    }
}
```

#### 2. 模式匹配翻译

使用正则表达式匹配常见错误模式：

```python
PATTERN_TRANSLATIONS = {
    r"invalid.*size.*(\d+x\d+)": "尺寸 {match} 不支持",
    r"unsupported.*format": "不支持的格式",
    r"rate.*limit": "请求频率超限",
    r"quota.*exceeded": "配额已用尽",
    r"unauthorized": "未授权",
    r"timeout": "请求超时",
}
```

### 智能建议生成

根据错误类型提供解决建议：

| 错误类型 | 建议 |
|----------|------|
| INVALID_SIZE | 尝试使用 1024x1024（最常用的尺寸） |
| QUOTA_EXCEEDED | 检查账户余额、考虑升级套餐 |
| AUTHENTICATION_FAILED | 检查 API Key 配置、确认未过期 |
| CONTENT_MODERATION | 修改提示词，避免敏感内容 |

### 返回格式

```python
{
    "success": False,
    "error": {
        "type": "invalid_size",
        "user_message": "尺寸 '1920x1080' 不受支持，已自动调整为 '1792x1024'",
        "technical_message": "Invalid size: 1920x1080",
        "suggestions": [
            "尝试使用 1024x1024（最常用的尺寸）"
        ],
        "can_retry": False,
        "auto_fixing": True,
        "retry_history": [...]
    }
}
```

## 完整处理流程

### 流程图

```
开始 API 调用
    │
    ▼
┌─────────────────────┐
│ 首次尝试调用        │
└──────────┬──────────┘
           │
           ├───────── 成功 ──────────┐
           │                        ▼
           │                   返回结果
           │
           ▼ 失败
    ┌──────────────┐
    │ 错误分类     │
    └──────┬───────┘
           │
           ├─── 可修正错误 ───┐
           │                 ▼
           │          ┌──────────────┐
           │          │ 参数修正     │
           │          └──────┬───────┘
           │                 │
           │                 ▼
           │          重新调用 API
           │                 │
           │          ┌──────┴───────┐
           │          │              │
           │      成功 │          │ 失败
           │          ▼             ▼
           │     返回结果    继续错误处理
           │
           ├─── 可重试错误 ───┐
           │                 ▼
           │          ┌──────────────┐
           │          │ 指数退避重试 │
           │          │ （最多N次）  │
           │          └──────┬───────┘
           │                 │
           │          ┌──────┴───────┐
           │          │              │
           │      成功 │          │ 失败
           │          ▼             ▼
           │     返回结果    继续错误处理
           │
           └─── 其他错误 ────┐
                             ▼
                      ┌──────────────┐
                      │ 消息翻译     │
                      └──────┬───────┘
                             │
                             ▼
                      返回友好错误
```

### 伪代码

```python
async def handle_api_call(provider, api_func, prompt, **params):
    task_id = generate_task_id()

    try:
        # 1. 首次尝试（包含自动重试逻辑）
        result = await retry_manager.execute_with_retry(
            task_id,
            ErrorContext(UNKNOWN_ERROR, Exception(), provider, params),
            api_func,
            prompt,
            **params
        )

        return {"success": True, "result": result}

    except Exception as e:
        # 2. 错误分类
        error_context = classifier.classify(provider, e)

        # 3. 尝试参数修正
        if error_context.type in [INVALID_SIZE, INVALID_FORMAT]:
            fixed, new_value, message = fixer.fix_parameter(...)
            if fixed:
                # 修正后重试
                try:
                    result = await api_func(prompt, **fixed_params)
                    return {
                        "success": True,
                        "result": result,
                        "message": f"{message}，任务已完成"
                    }
                except:
                    pass  # 继续错误处理

        # 4. 翻译错误消息
        translated = translator.translate(error_context, language="zh")

        # 5. 返回友好错误
        return {
            "success": False,
            "error": {
                "user_message": translated["user_message"],
                "suggestions": translated["suggestions"],
                "can_retry": translated["can_retry"],
                "retry_history": get_retry_history(task_id)
            }
        }
```

## 代码结构

### 文件组织

```
app/
├── error_handling/
│   ├── __init__.py
│   ├── classifier.py       # 错误分类器
│   ├── fixer.py            # 参数修正器
│   ├── retry_manager.py    # 重试管理器
│   ├── translator.py       # 错误翻译器
│   ├── handler.py          # 统一错误处理器
│   └── config.py           # 错误处理配置
```

### 模块接口

#### ErrorClassifier

```python
class ErrorClassifier:
    def classify(
        self,
        provider: str,
        error: Exception,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None
    ) -> ErrorContext:
        """分类错误并返回错误上下文"""
        pass
```

#### ParameterFixer

```python
class ParameterFixer:
    def fix_parameter(
        self,
        provider: str,
        param_name: str,
        param_value: Any,
        error_context: ErrorContext
    ) -> tuple[bool, Any, str]:
        """
        修正参数

        返回: (是否修正, 修正后的值, 修正说明)
        """
        pass
```

#### RetryManager

```python
class RetryManager:
    async def execute_with_retry(
        self,
        task_id: str,
        error_context: ErrorContext,
        func: callable,
        *args,
        **kwargs
    ) -> Any:
        """执行函数并根据错误类型自动重试"""
        pass

    def get_retry_history(self, task_id: str) -> list:
        """获取重试历史"""
        pass
```

#### ErrorTranslator

```python
class ErrorTranslator:
    def translate(
        self,
        error_context: ErrorContext,
        language: str = "zh",
        fix_info: Optional[dict] = None
    ) -> dict:
        """
        翻译错误消息

        返回: {
            "user_message": str,
            "technical_message": str,
            "suggestions": list[str],
            "can_retry": bool
        }
        """
        pass
```

#### ErrorHandler

```python
class ErrorHandler:
    async def handle_api_call(
        self,
        provider: str,
        api_func: callable,
        prompt: str,
        **params
    ) -> dict:
        """处理完整的 API 调用流程"""
        pass
```

## 配置示例

### 错误处理配置 (config.py)

```python
# 重试配置
RETRY_CONFIG = {
    "server_error": {
        "max_attempts": 3,
        "base_wait": 2,
        "max_wait": 60,
        "exponential_base": 2
    },
    "timeout": {
        "max_attempts": 4,
        "base_wait": 1,
        "max_wait": 30,
        "exponential_base": 2
    },
    "rate_limit": {
        "max_attempts": 5,
        "base_wait": 5,
        "max_wait": 120,
        "exponential_base": 2
    }
}

# 参数修正规则
FIX_RULES = {
    "size": {
        "dalle": {
            "supported": ["1024x1024", "1792x1024", "1024x1792"],
            "fallback": "1024x1024",
            "auto_fix": True
        },
        "stability": {
            "supported": ["512x512", "768x768", "1024x1024"],
            "fallback": "1024x1024",
            "auto_fix": True
        }
    }
}

# 错误消息模板
ERROR_MESSAGES = {
    "invalid_size": {
        "zh": "尺寸 '{size}' 不受支持，已自动调整为 '{adjusted_size}'",
        "en": "Size '{size}' is not supported"
    },
    ...
}
```

## 使用示例

### 在 API 适配器中使用

```python
from app.error_handling import ErrorHandler

class DALLEAdapter(BaseAPIAdapter):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.error_handler = ErrorHandler()

    async def generate_image(self, prompt: str, **params) -> dict:
        async def _api_call(prompt, **params):
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                **params
            )
            return {
                "url": response.data[0].url,
                "revised_prompt": response.data[0].revised_prompt
            }

        result = await self.error_handler.handle_api_call(
            provider="dalle",
            api_func=_api_call,
            prompt=prompt,
            **params
        )

        if result["success"]:
            return result["result"]
        else:
            # 返回给用户友好的错误信息
            raise UserFriendlyError(
                message=result["error"]["user_message"],
                suggestions=result["error"]["suggestions"]
            )
```

### 在 Agent 中使用

```python
from app.error_handling import ErrorHandler

async def executor_node(state: AgentState):
    """执行节点 - 调用 API"""
    error_handler = ErrorHandler()

    provider = state["selected_provider"]
    prompt = state["prompt"]
    params = state["task_params"]

    # 获取适配器
    adapter = adapter_factory.get_adapter(provider)

    # 调用 API（自动包含错误处理）
    result = await error_handler.handle_api_call(
        provider=provider,
        api_func=adapter.generate_image,
        prompt=prompt,
        **params
    )

    if result["success"]:
        state["api_response"] = result["result"]
        state["error"] = None
    else:
        state["api_response"] = None
        state["error"] = result["error"]

    return state
```

### 在 API 接口中返回

```python
@app.post("/api/v1/tasks")
async def create_task(task_request: TaskRequest):
    result = await error_handler.handle_api_call(
        provider=task_request.provider,
        api_func=generate_image,
        prompt=task_request.prompt,
        **task_request.parameters
    )

    if result["success"]:
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result["result"]
        }
    else:
        return JSONResponse(
            status_code=400,
            content={
                "task_id": task_id,
                "status": "failed",
                "error": result["error"]
            }
        )
```

## 监控和日志

### 关键指标

| 指标 | 说明 | 用途 |
|------|------|------|
| 错误分类准确率 | 分类器正确分类错误的比例 | 优化分类规则 |
| 参数修正成功率 | 修正后成功完成请求的比例 | 优化修正策略 |
| 重试成功率 | 重试后成功完成请求的比例 | 调整重试次数 |
| 平均重试次数 | 每个任务的平均重试次数 | 评估服务稳定性 |
| 错误类型分布 | 各类错误的发生频率 | 识别系统性问题 |

### 日志格式

```python
# 成功日志
{
    "level": "INFO",
    "event": "api_call_success",
    "provider": "dalle",
    "task_id": "task_123",
    "attempts": 1,
    "duration": 2.5
}

# 参数修正日志
{
    "level": "INFO",
    "event": "parameter_fixed",
    "provider": "dalle",
    "task_id": "task_123",
    "parameter": "size",
    "original_value": "1920x1080",
    "fixed_value": "1792x1024",
    "reason": "尺寸不支持，自动调整"
}

# 重试日志
{
    "level": "WARNING",
    "event": "api_call_retry",
    "provider": "dalle",
    "task_id": "task_123",
    "attempt": 2,
    "error_type": "server_error",
    "wait_time": 4
}

# 失败日志
{
    "level": "ERROR",
    "event": "api_call_failed",
    "provider": "dalle",
    "task_id": "task_123",
    "error_type": "quota_exceeded",
    "total_attempts": 3,
    "user_message": "API 配额已用完，请检查账户余额"
}
```

## 最佳实践

### 1. 错误分类

- ✅ 优先使用 HTTP 状态码快速分类
- ✅ 为每个服务商维护特定的错误码映射
- ✅ 定期更新错误模式以适应 API 变化
- ❌ 不要仅依赖异常类型判断

### 2. 参数修正

- ✅ 只修正明确的、低风险的参数
- ✅ 记录所有修正操作供后续分析
- ❌ 不要自动修正可能导致意外结果的参数
- ❌ 不要无限循环修正

### 3. 重试策略

- ✅ 根据错误类型设置合适的重试次数
- ✅ 使用指数退避避免服务器过载
- ✅ 尊重 API 返回的 Retry-After 头
- ❌ 不要对认证失败、配额超限等错误重试

### 4. 错误提示

- ✅ 使用用户友好的语言
- ✅ 提供具体的解决建议
- ✅ 说明系统已采取的行动（如"已自动重试"）
- ❌ 不要直接展示技术错误栈给用户

## 测试策略

### 单元测试

```python
# 测试错误分类器
def test_error_classifier():
    classifier = ErrorClassifier()

    # 测试 HTTP 状态码分类
    error = httpx.HTTPStatusError(
        "Rate limit",
        request=...,
        response=mock_response(status=429)
    )
    context = classifier.classify("openai", error, status_code=429)
    assert context.error_type == ErrorType.RATE_LIMIT_EXCEEDED

    # 测试响应文本分类
    context = classifier.classify(
        "dalle",
        Exception("invalid size 1920x1080"),
        response_text="invalid size 1920x1080"
    )
    assert context.error_type == ErrorType.INVALID_SIZE

# 测试参数修正器
def test_parameter_fixer():
    fixer = ParameterFixer()

    fixed, new_value, message = fixer.fix_parameter(
        "dalle", "size", "1920x1080", None
    )

    assert fixed == True
    assert new_value in ["1792x1024", "1024x1792"]

# 测试重试管理器
@pytest.mark.asyncio
async def test_retry_manager():
    manager = RetryManager()
    call_count = 0

    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Server error")
        return "success"

    result = await manager.execute_with_retry(
        "task_123",
        ErrorContext(ErrorType.SERVER_ERROR, Exception(), "dalle", {}),
        failing_func
    )

    assert result == "success"
    assert call_count == 3
```

### 集成测试

```python
@pytest.mark.asyncio
async def test_full_error_handling():
    handler = ErrorHandler()

    # 模拟 API 调用
    async def mock_api(prompt, **params):
        if params.get("size") == "invalid":
            raise Exception("invalid size invalid")
        return {"url": "https://..."}

    result = await handler.handle_api_call(
        provider="dalle",
        api_func=mock_api,
        prompt="a cat",
        size="invalid"
    )

    # 应该自动修正参数并成功
    assert result["success"] == True
```

## 扩展性

### 添加新的错误类型

```python
# 1. 在 ErrorType 中添加
class ErrorType(Enum):
    NEW_ERROR_TYPE = "new_error_type"

# 2. 在 ERROR_PATTERNS 中添加映射
ERROR_PATTERNS = {
    "provider_name": {
        "new_error_code": ErrorType.NEW_ERROR_TYPE
    }
}

# 3. 在 RETRY_CONFIG 中添加重试策略
RETRY_CONFIG = {
    ErrorType.NEW_ERROR_TYPE: {
        "max_attempts": 3,
        "base_wait": 2,
        "max_wait": 60
    }
}

# 4. 在 ERROR_MESSAGES 中添加翻译
ERROR_MESSAGES = {
    ErrorType.NEW_ERROR_TYPE: {
        "zh": "中文错误消息",
        "en": "English error message"
    }
}
```

### 添加新的参数修正规则

```python
# 在 FIX_RULES 中添加
FIX_RULES = {
    "new_parameter": {
        "provider_name": {
            "supported": ["value1", "value2"],
            "fallback": "value1",
            "auto_fix": True
        }
    }
}

# 实现修正逻辑
class ParameterFixer:
    def _fix_new_parameter(self, value, rules):
        # 实现修正逻辑
        pass
```

## 总结

本错误处理机制提供了：

1. **智能化**: 自动识别并分类错误
2. **自动化**: 参数修正和重试无需人工干预
3. **用户友好**: 清晰的中文错误提示和解决建议
4. **可观测**: 完整的重试历史和修正记录
5. **可扩展**: 易于添加新的错误类型和处理策略

通过这套机制，系统可以：
- 减少因临时性问题导致的失败
- 自动处理常见的参数错误
- 提供清晰的错误反馈
- 积累错误数据用于持续优化
