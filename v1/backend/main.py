"""
高校教师数字分身系统 - FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.tracing import context_middleware
from app.api import auth, teachers, students, chat
import uvicorn

app = FastAPI(
    title="高校教师数字分身系统 API",
    description="基于多租户隔离的 AI 教师分身系统",
    version="1.0.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义追踪中间件
app.middleware("http")(context_middleware)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(teachers.router, prefix="/api/teachers", tags=["教师"])
app.include_router(students.router, prefix="/api/students", tags=["学生"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])

@app.get("/")
async def root():
    return {"message": "高校教师数字分身系统 API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
