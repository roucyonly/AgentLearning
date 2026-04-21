from typing import Dict, Any, Optional
from app.models.error_handling import ErrorHandlingConfig


class ParameterFixer:
    """参数修正器"""

    # 通用尺寸映射 (DALL-E 不支持的尺寸映射到支持尺寸)
    SIZE_MAPPING = {
        "1792x1024": "1024x1024",
        "1024x1792": "1024x1024",
        "256x256": "1024x1024",  # 太小了
        "512x512": "1024x1024",   # 不是标准尺寸
    }

    # 质量参数映射
    QUALITY_MAPPING = {
        "standard": "standard",
        "hd": "hd",
        "high": "hd",
        "low": "standard",
    }

    def __init__(self):
        pass

    async def fix_parameters(
        self,
        params: Dict[str, Any],
        error_type: str,
        config: Optional[ErrorHandlingConfig] = None
    ) -> Dict[str, Any]:
        """修正参数"""
        if not config or not config.auto_fix_enabled:
            return params

        fixed_params = params.copy()
        fix_rules = config.fix_rules or {}

        for param_name, rules in fix_rules.items():
            if param_name in fixed_params:
                old_value = fixed_params[param_name]
                new_value = self._apply_fix_rule(param_name, old_value, rules)
                if new_value != old_value:
                    fixed_params[param_name] = new_value

        return fixed_params

    def _apply_fix_rule(
        self,
        param_name: str,
        old_value: Any,
        rules: Any
    ) -> Any:
        """应用修正规则"""
        if isinstance(rules, dict):
            # 映射表形式: {"1792x1024": "1024x1024"}
            return rules.get(old_value, old_value)
        elif isinstance(rules, list):
            # 列表形式: ["auto", "standard"]
            return rules[0] if rules else old_value
        elif callable(rules):
            # 函数形式
            return rules(old_value)
        return old_value

    def fix_size(self, size: str) -> str:
        """修正尺寸参数"""
        return self.SIZE_MAPPING.get(size, size)

    def fix_quality(self, quality: str) -> str:
        """修正质量参数"""
        return self.QUALITY_MAPPING.get(quality.lower(), "standard")

    def fix_style(self, style: str) -> str:
        """修正风格参数"""
        valid_styles = ["vivid", "natural"]
        return style if style in valid_styles else "vivid"

    def fix_n(self, n: int) -> int:
        """修正数量参数"""
        if n < 1:
            return 1
        if n > 10:
            return 10
        return n
