# 阶段 7: 工具和辅助功能

**预估时间**: 1-2天

**目标**: 实现加密、日志和辅助函数

---

## 7.1 加密工具

**文件**: `app/utils/crypto.py`

**任务**:
- [ ] 实现 `encrypt_api_key()` 函数
- [ ] 实现 `decrypt_api_key()` 函数
- [ ] 实现 `hash_api_key()` 函数（用于验证）

**代码框架**:
```python
from cryptography.fernet import Fernet
import base64
import hashlib

def get_encryption_key(secret: str) -> bytes:
    """生成加密密钥"""
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())

def encrypt_api_key(api_key: str, secret: str) -> str:
    """加密 API Key"""
    key = get_encryption_key(secret)
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted: str, secret: str) -> str:
    """解密 API Key"""
    key = get_encryption_key(secret)
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()

def hash_api_key(api_key: str) -> str:
    """哈希 API Key 用于验证"""
    return hashlib.sha256(api_key.encode()).hexdigest()
```

**测试**: `tests/unit/utils/test_crypto.py`

---

## 7.2 日志工具

**文件**: `app/utils/logger.py`

**任务**:
- [ ] 配置 `loguru` 日志
- [ ] 实现结构化日志输出
- [ ] 实现日志轮转

**代码框架**:
```python
from loguru import logger
import sys

def setup_logger(log_level: str = "INFO"):
    """配置日志"""
    logger.remove()
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        level="DEBUG"
    )

def get_logger(name: str = None):
    """获取日志记录器"""
    return logger.bind(name=name) if name else logger
```

---

## 7.3 辅助函数

**文件**: `app/utils/helpers.py`

**任务**:
- [ ] 实现 `get_by_path()` 函数 (JSONPath)
- [ ] 实现 `set_by_path()` 函数
- [ ] 实现 `validate_json_schema()` 函数

**代码框架**:
```python
import re
from typing import Any, Dict, Optional
import json

def get_by_path(data: Dict[str, Any], path: str) -> Optional[Any]:
    """
    使用 JSONPath 风格从字典中获取值
    支持: "data.url" -> data["data"]["url"]
          "data[0].url" -> data["data"][0]["url"]
    """
    parts = re.split(r'\.|\[|\]', path)
    parts = [p for p in parts if p]

    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                index = int(part)
                current = current[index]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current

def set_by_path(data: Dict[str, Any], path: str, value: Any) -> None:
    """
    使用 JSONPath 风格设置字典中的值
    """
    parts = re.split(r'\.|\[|\]', path)
    parts = [p for p in parts if p]

    current = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    last_part = parts[-1]
    if last_part.isdigit():
        index = int(last_part)
        while len(current) <= index:
            current.append(None)
        current[index] = value
    else:
        current[last_part] = value

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """简单验证 JSON 数据是否符合 schema"""
    # 简化实现，可使用 jsonschema 库
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            return False
    return True
```

**测试**: `tests/unit/utils/test_helpers.py`

---

## 7.4 __init__.py 文件

**文件**: `app/utils/__init__.py`

```python
from app.utils.logger import setup_logger, get_logger
from app.utils.crypto import encrypt_api_key, decrypt_api_key, hash_api_key
from app.utils.helpers import get_by_path, set_by_path, validate_json_schema

__all__ = [
    "setup_logger",
    "get_logger",
    "encrypt_api_key",
    "decrypt_api_key",
    "hash_api_key",
    "get_by_path",
    "set_by_path",
    "validate_json_schema",
]
```

---

## 验收标准

- [ ] 加密/解密功能正确
- [ ] 日志配置正确
- [ ] JSONPath 辅助函数正确
- [ ] 单元测试覆盖所有工具函数
