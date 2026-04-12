# src/agents/base.py
"""
Agent 基类
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAgent(ABC):
    """Agent 基类，定义统一接口"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        """执行 Agent"""
        pass

    @abstractmethod
    def get_tools(self) -> List[Any]:
        """获取可用的工具列表"""
        pass
