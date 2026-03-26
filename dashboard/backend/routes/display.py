"""Display app and screensaver control routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from loguru import logger

router = APIRouter()


class AppLaunchRequest(BaseModel):
    name: str


class ScreensaverRequest(BaseModel):
    name: Optional[str] = None


def _display(req: Request):
    daemon = req.app.state.daemon
    if not daemon.display:
        raise HTTPException(status_code=503, detail="Display not available")
    return daemon.display


@router.get("/status")
async def get_display_status(req: Request):
    return _display(req).get_status()


@router.get("/apps")
async def list_apps(req: Request):
    return {"apps": _display(req).get_available_apps()}


@router.post("/apps/launch")
async def launch_app(req: Request, body: AppLaunchRequest):
    display = _display(req)
    success = display.launch_app(body.name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Unknown app: {body.name}")
    logger.info(f"Display: launched app '{body.name}'")
    return {"success": True, "active_app": body.name}


@router.get("/screensavers")
async def list_screensavers(req: Request):
    return {"screensavers": _display(req).get_available_screensavers()}


@router.post("/screensavers/activate")
async def activate_screensaver(req: Request, body: ScreensaverRequest):
    display = _display(req)
    display.activate_screensaver(body.name)
    name = display.screensaver_mgr.get_active_name() if display.screensaver_mgr else body.name
    logger.info(f"Display: activated screensaver '{name}'")
    return {"success": True, "active_screensaver": name}


@router.post("/screensavers/deactivate")
async def deactivate_screensaver(req: Request):
    _display(req).deactivate_screensaver()
    return {"success": True}
