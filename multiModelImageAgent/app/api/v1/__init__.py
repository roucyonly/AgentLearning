from fastapi import APIRouter
from app.api.v1 import chat, tasks

router = APIRouter(prefix="/v1")

router.include_router(chat.router)
router.include_router(tasks.router)
