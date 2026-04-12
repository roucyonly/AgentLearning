# src/tools/base.py
"""
工具基类
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """工具基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行工具"""
        pass

    def to_langchain_tool(self):
        """转换为 LangChain Tool 格式"""
        from langchain_core.tools import StructuredTool
        return StructuredTool(
            name=self.name,
            description=self.description,
            func=self.execute
        )
