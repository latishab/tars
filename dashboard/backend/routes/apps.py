"""Apps API routes."""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

# Constants
APPS_DIR = Path.home() / "tars-apps"
OFFICIAL_APPS = [
    {
        "id": "tars-conversation",
        "name": "TARS Conversation App",
        "description": "Talk naturally with TARS using LLMs",
        "author": "latishab",
        "url": "https://huggingface.co/spaces/latishab/tars-conversation-app",
        "repository": "https://github.com/latishab/tars-conversation-app.git",
        "official": True,
        "featured": True,
    }
]


class InstallRequest(BaseModel):
    app_id: str
    repository: str


class AppAction(BaseModel):
    app_id: str


def read_app_json(app_path: Path) -> Dict[str, Any]:
    """Read app.json from app directory."""
    app_json_path = app_path / "app.json"
    if not app_json_path.exists():
        return {}
    try:
        with open(app_json_path) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read {app_json_path}: {e}")
        return {}


def get_installed_apps() -> List[Dict[str, Any]]:
    """Get list of installed apps from ~/tars-apps/."""
    if not APPS_DIR.exists():
        return []

    apps = []
    for app_dir in APPS_DIR.iterdir():
        if not app_dir.is_dir():
            continue

        app_data = read_app_json(app_dir)
        if not app_data:
            continue

        apps.append({
            "id": app_dir.name,
            "name": app_data.get("name", app_dir.name),
            "version": app_data.get("version", "unknown"),
            "description": app_data.get("description", ""),
            "author": app_data.get("author", ""),
            "repository": app_data.get("repository", ""),
            "installed": True,
            "running": is_app_running(app_dir.name),
            "path": str(app_dir),
        })

    return apps


def is_app_running(app_id: str) -> bool:
    """Check if app is currently running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", app_id],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


@router.get("")
async def list_apps():
    """Get all available apps (official + community)."""
    installed = get_installed_apps()
    installed_ids = {app["id"] for app in installed}

    # Merge official apps with installation status
    all_apps = []
    for official_app in OFFICIAL_APPS:
        app_id = official_app["id"]
        if app_id in installed_ids:
            # Find the installed app and merge
            installed_app = next(a for a in installed if a["id"] == app_id)
            all_apps.append({**official_app, **installed_app})
        else:
            all_apps.append({**official_app, "installed": False, "running": False})

    return {
        "official": [a for a in all_apps if a.get("official")],
        "community": [],  # TODO: Fetch from HuggingFace API
        "installed": installed,
    }


@router.get("/installed")
async def list_installed():
    """Get list of installed apps."""
    return get_installed_apps()


@router.post("/install")
async def install_app(req: InstallRequest):
    """Install an app from git repository."""
    try:
        app_path = APPS_DIR / req.app_id
        if app_path.exists():
            raise HTTPException(status_code=400, detail="App already installed")

        APPS_DIR.mkdir(parents=True, exist_ok=True)

        logger.info(f"Installing {req.app_id} from {req.repository}")
        result = subprocess.run(
            ["git", "clone", req.repository, str(app_path)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Git clone failed: {result.stderr}"
            )

        # Run install script if exists
        install_script = app_path / "install.sh"
        if install_script.exists():
            logger.info(f"Running install script for {req.app_id}")
            result = subprocess.run(
                ["bash", str(install_script)],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                logger.warning(f"Install script failed: {result.stderr}")

        return {"status": "success", "message": f"Installed {req.app_id}"}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Installation timeout")
    except Exception as e:
        logger.error(f"Install error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/uninstall")
async def uninstall_app(req: AppAction):
    """Uninstall an app."""
    try:
        app_path = APPS_DIR / req.app_id
        if not app_path.exists():
            raise HTTPException(status_code=404, detail="App not found")

        # Run uninstall script if exists
        uninstall_script = app_path / "uninstall.sh"
        if uninstall_script.exists():
            logger.info(f"Running uninstall script for {req.app_id}")
            subprocess.run(
                ["bash", str(uninstall_script)],
                cwd=str(app_path),
                capture_output=True,
                text=True,
                timeout=300
            )

        # Remove directory
        import shutil
        shutil.rmtree(app_path)

        return {"status": "success", "message": f"Uninstalled {req.app_id}"}

    except Exception as e:
        logger.error(f"Uninstall error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_app(req: AppAction):
    """Run an installed app."""
    try:
        app_path = APPS_DIR / req.app_id
        if not app_path.exists():
            raise HTTPException(status_code=404, detail="App not found")

        app_data = read_app_json(app_path)
        main_script = app_data.get("main", "main.py")

        logger.info(f"Starting {req.app_id}")
        subprocess.Popen(
            ["python", main_script],
            cwd=str(app_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        return {"status": "success", "message": f"Started {req.app_id}"}

    except Exception as e:
        logger.error(f"Run error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_app(req: AppAction):
    """Stop a running app."""
    try:
        logger.info(f"Stopping {req.app_id}")
        result = subprocess.run(
            ["pkill", "-f", req.app_id],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return {"status": "success", "message": f"Stopped {req.app_id}"}
        else:
            return {"status": "success", "message": "App not running"}

    except Exception as e:
        logger.error(f"Stop error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
