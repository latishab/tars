"""System management API routes."""

from fastapi import APIRouter
from loguru import logger

router = APIRouter()

# Import existing route modules
from . import settings as settings_module
from . import updates as updates_module
from . import setup as setup_module

# Re-export routes under /system
router.include_router(settings_module.router, tags=["System"])
router.include_router(updates_module.router, prefix="/updates", tags=["System"])
router.include_router(setup_module.router, prefix="/setup", tags=["System"])
