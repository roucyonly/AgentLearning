from fastapi import APIRouter, Request, templating
from fastapi.responses import HTMLResponse
from app.api.dependencies import get_db
from app.repositories.model_provider import ModelProviderRepository
from app.repositories.task import TaskRepository

router = APIRouter()
templates = templating.Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """首页"""
    return templates.TemplateResponse("chat.html", {"request": request})


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """对话页面"""
    return templates.TemplateResponse("chat.html", {"request": request})


@router.get("/admin/models", response_class=HTMLResponse)
async def admin_models_page(request: Request):
    """模型管理页面"""
    return templates.TemplateResponse("admin_models.html", {"request": request})


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """任务页面"""
    return templates.TemplateResponse("tasks.html", {"request": request})
