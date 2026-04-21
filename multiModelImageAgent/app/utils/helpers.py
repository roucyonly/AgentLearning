import re
from typing import Any, Dict, Optional


def get_by_path(data: Dict[str, Any], path: str) -> Optional[Any]:
    """
    使用 JSONPath 风格从字典中获取值
    支持: "data.url" -> data["data"]["url"]
          "data[0].url" -> data["data"][0]["url"]
    """
    if not path or not data:
        return None

    # 解析路径
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

        if current is None:
            return None

    return current


def set_by_path(data: Dict[str, Any], path: str, value: Any) -> None:
    """
    使用 JSONPath 风格设置字典中的值
    """
    if not path:
        return

    # 解析路径
    parts = re.split(r'\.|\[|\]', path)
    parts = [p for p in parts if p]

    current = data
    for part in parts[:-1]:
        if part not in current:
            # 判断下一个路径部分是否是数字
            next_part = parts[parts.index(part) + 1] if parts.index(part) + 1 < len(parts) else None
            if next_part and next_part.isdigit():
                current[part] = []
            else:
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
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            return False

        field_schema = schema.get("properties", {}).get(field, {})
        value = data[field]

        # 类型检查
        expected_type = field_schema.get("type")
        if expected_type:
            type_map = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            expected_python_type = type_map.get(expected_type)
            if expected_python_type and not isinstance(value, expected_python_type):
                return False

    return True


def merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并两个字典"""
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
