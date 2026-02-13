"""System updates API routes."""

import subprocess
import json
import urllib.request
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

# Version info
try:
    from tars_sdk._version import __version__
except ImportError:
    __version__ = "unknown"

GITHUB_REPO = "latishab/tars"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class UpdateCheckResponse(BaseModel):
    current_version: str
    latest_version: str
    update_available: bool
    release_notes: str = ""
    release_url: str = ""


class UpdateInstallResponse(BaseModel):
    success: bool
    message: str
    requires_restart: bool = False


def fetch_latest_release() -> Optional[dict]:
    """Fetch latest release info from GitHub."""
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"Failed to fetch GitHub release: {e}")
        return None


def compare_versions(current: str, latest: str) -> bool:
    """Return True if latest is newer than current."""
    def parse(v):
        return tuple(int(x) for x in v.lstrip("v").split(".")[:3])

    try:
        return parse(latest) > parse(current)
    except (ValueError, IndexError):
        return False


def run_git_command(args: list) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


@router.get("/updates/check", response_model=UpdateCheckResponse)
async def check_updates():
    """Check for available updates."""
    release = fetch_latest_release()

    if not release:
        return UpdateCheckResponse(
            current_version=__version__,
            latest_version=__version__,
            update_available=False,
            release_notes="Unable to check for updates",
        )

    latest_version = release.get("tag_name", "").lstrip("v")
    release_notes = release.get("body", "")[:500]  # Truncate
    release_url = release.get("html_url", "")

    update_available = compare_versions(__version__, latest_version)

    return UpdateCheckResponse(
        current_version=__version__,
        latest_version=latest_version,
        update_available=update_available,
        release_notes=release_notes,
        release_url=release_url,
    )


@router.get("/updates/current")
async def get_current_version():
    """Get current version info."""
    # Get git info
    code, commit, _ = run_git_command(["rev-parse", "--short", "HEAD"])
    code2, branch, _ = run_git_command(["branch", "--show-current"])

    return {
        "version": __version__,
        "git_commit": commit if code == 0 else None,
        "git_branch": branch if code2 == 0 else None,
    }


async def perform_update():
    """Perform the actual update (runs in background)."""
    logger.info("Starting system update...")

    # Git fetch
    code, _, err = run_git_command(["fetch", "--all", "--tags"])
    if code != 0:
        logger.error(f"Git fetch failed: {err}")
        return False

    # Git pull
    code, out, err = run_git_command(["pull", "--ff-only"])
    if code != 0:
        logger.error(f"Git pull failed: {err}")
        return False

    logger.info(f"Git pull result: {out}")

    # Install dependencies
    try:
        result = subprocess.run(
            ["pip", "install", "-e", "."],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            logger.error(f"pip install failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"pip install error: {e}")
        return False

    logger.info("Update completed successfully")
    return True


@router.post("/updates/install", response_model=UpdateInstallResponse)
async def install_update(background_tasks: BackgroundTasks):
    """Install available update."""
    # Check if update is available first
    release = fetch_latest_release()
    if not release:
        raise HTTPException(status_code=503, detail="Unable to check for updates")

    latest_version = release.get("tag_name", "").lstrip("v")
    if not compare_versions(__version__, latest_version):
        return UpdateInstallResponse(
            success=True,
            message="Already up to date",
            requires_restart=False,
        )

    # Start update in background
    background_tasks.add_task(perform_update)

    return UpdateInstallResponse(
        success=True,
        message=f"Update to {latest_version} started. System will restart when complete.",
        requires_restart=True,
    )


@router.post("/updates/restart")
async def restart_service():
    """Restart the TARS service."""
    logger.info("Restart requested via dashboard")

    try:
        # Try systemctl first
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "tars"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return {"success": True, "message": "Service restarting..."}

        # Fallback: just exit and let supervisor restart
        import os
        import signal
        os.kill(os.getpid(), signal.SIGTERM)

        return {"success": True, "message": "Restarting..."}

    except Exception as e:
        logger.error(f"Restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
