from fastapi import APIRouter
from app.api.v1.admin import models, error_config

router = APIRouter(prefix="/admin", tags=["admin"])

router.include_router(models.router, prefix="/models")
router.include_router(error_config.router)
