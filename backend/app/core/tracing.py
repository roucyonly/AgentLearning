"""
追踪中间件 - 核心代码
实现多租户隔离、Trace-Id 全链路追踪
"""
import uuid
import logging
from contextvars import ContextVar
from fastapi import Request
from typing import Generator

# ContextVar 用于在异步上下文中传递租户信息
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")
tenant_id_ctx: ContextVar[str] = ContextVar("tenant_id", default="")
role_ctx: ContextVar[str] = ContextVar("role", default="STUDENT")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TraceLogger:
    """自定义日志适配器,自动添加 Trace-Id 和租户信息"""

    def __init__(self):
        self.logger = logger

    def _format_log(self, message: str) -> str:
        """格式化日志,添加上下文信息"""
        trace_id = trace_id_ctx.get()
        tenant_id = tenant_id_ctx.get()
        role = role_ctx.get()

        parts = [f"[{message}"]
        if trace_id:
            parts.append(f"trace_id={trace_id}")
        if tenant_id:
            parts.append(f"tenant_id={tenant_id}")
        if role:
            parts.append(f"role={role}")
        parts.append("]")

        return " ".join(parts)

    def info(self, message: str):
        self.logger.info(self._format_log(message))

    def error(self, message: str):
        self.logger.error(self._format_log(message))

    def warning(self, message: str):
        self.logger.warning(self._format_log(message))

    def debug(self, message: str):
        self.logger.debug(self._format_log(message))


# 全局日志实例
tracing_logger = TraceLogger()


async def context_middleware(request: Request, call_next):
    """
    FastAPI 中间件 - 注入租户上下文

    功能:
    1. 生成或读取 X-Trace-Id
    2. 提取 X-Tenant-Id (多租户隔离核心)
    3. 提取 X-Role (TEACHER / STUDENT)
    4. 将上下文存入 ContextVar
    5. 响应头返回 Trace-Id
    """
    # 从请求头读取或生成 Trace-Id
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())

    # 从请求头读取租户 ID 和角色
    tenant_id = request.headers.get("X-Tenant-Id", "default")
    role = request.headers.get("X-Role", "STUDENT")

    # 存入上下文变量 (线程/协程安全)
    trace_id_ctx.set(trace_id)
    tenant_id_ctx.set(tenant_id)
    role_ctx.set(role)

    # 记录请求日志
    tracing_logger.info(
        f"Request: {request.method} {request.url.path}"
    )

    # 调用下一个中间件/路由
    response = await call_next(request)

    # 在响应头返回 Trace-Id
    response.headers["X-Trace-Id"] = trace_id

    return response


def get_current_tenant_id() -> str:
    """
    获取当前租户 ID

    在数据库查询时必须调用此函数实现租户隔离
    """
    return tenant_id_ctx.get()


def get_current_role() -> str:
    """获取当前用户角色"""
    return role_ctx.get()


def get_trace_id() -> str:
    """获取当前 Trace-Id"""
    return trace_id_ctx.get()
