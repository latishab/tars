"""System updates API routes."""

import subprocess
import json
import urllib.request
from typing import Optional
from pathlib import Path

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
PYPI_URL = "https://pypi.org/pypi/tars-robot/json"


class UpdateCheckResponse(BaseModel):
    current_version: str
    latest_version: str
    update_available: bool
    release_notes: str = ""
    release_url: str = ""
    update_source: str = "auto"


class UpdateInstallResponse(BaseModel):
    success: bool
    message: str
    requires_restart: bool = False


def get_install_mode() -> str:
    """
    Auto-detect install mode.
    Returns: "git" if running from cloned repo, "pypi" if installed from PyPI
    """
    try:
        import tars_sdk
        package_path = Path(tars_sdk.__file__).parent
        
        # Check if we're in an editable install (git repo nearby)
        for parent in package_path.parents:
            if (parent / ".git").exists():
                return "git"
            # Stop at home directory
            if parent == Path.home():
                break
        
        return "pypi"
    except:
        return "pypi"


def fetch_latest_version() -> tuple[Optional[str], str]:
    """
    Fetch latest version based on install mode.
    Returns: (version, release_notes)
    """
    mode = get_install_mode()
    
    if mode == "pypi":
        try:
            req = urllib.request.Request(PYPI_URL)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                version = data["info"]["version"]
                return version, ""
        except Exception as e:
            logger.error(f"Failed to check PyPI: {e}")
            return None, ""
    else:
        # Git mode - check local git tags
        try:
            import tars_sdk
            repo_dir = None
            for parent in Path(tars_sdk.__file__).parents:
                if (parent / ".git").exists():
                    repo_dir = parent
                    break
            
            if not repo_dir:
                logger.error("Git repo not found")
                return None, ""
            
            # Get latest tag from remote
            code, _, _ = run_git_command(["fetch", "--tags"], cwd=repo_dir)
            
            # Get the commit of the latest tag
            code, latest_commit, _ = run_git_command(
                ["rev-list", "--tags", "--max-count=1"],
                cwd=repo_dir
            )
            
            if code != 0 or not latest_commit:
                logger.error("No tags found in repository")
                return None, ""
            
            # Get the tag name for that commit
            code, latest_tag, _ = run_git_command(
                ["describe", "--tags", "--abbrev=0", latest_commit],
                cwd=repo_dir
            )
            
            if code == 0 and latest_tag:
                version = latest_tag.lstrip("v")
                return version, f"Release {latest_tag}"
            else:
                logger.error("No git tags found")
                return None, ""
                
        except Exception as e:
            logger.error(f"Failed to check git tags: {e}")
            return None, ""


def compare_versions(current: str, latest: str) -> bool:
    """Return True if latest is newer than current."""
    def parse(v):
        return tuple(int(x) for x in v.lstrip("v").split(".")[:3])

    try:
        return parse(latest) > parse(current)
    except (ValueError, IndexError):
        return False


def run_git_command(args: list, cwd=None) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


@router.get("/check", response_model=UpdateCheckResponse)
async def check_updates():
    """Check for available updates from appropriate source."""
    mode = get_install_mode()
    latest_version, release_notes = fetch_latest_version()

    if not latest_version:
        return UpdateCheckResponse(
            current_version=__version__,
            latest_version=__version__,
            update_available=False,
            release_notes="Unable to check for updates",
            update_source=mode,
        )

    update_available = compare_versions(__version__, latest_version)

    return UpdateCheckResponse(
        current_version=__version__,
        latest_version=latest_version,
        update_available=update_available,
        release_notes=release_notes,
        update_source=mode,
    )


@router.get("/current")
async def get_current_version():
    """Get current version info including install mode."""
    mode = get_install_mode()
    
    info = {
        "version": __version__,
        "install_mode": mode,
    }
    
    if mode == "git":
        code, commit, _ = run_git_command(["rev-parse", "--short", "HEAD"])
        code2, branch, _ = run_git_command(["branch", "--show-current"])
        info["git_commit"] = commit if code == 0 else None
        info["git_branch"] = branch if code2 == 0 else None
    
    return info


async def perform_update():
    """Perform update based on install mode, then restart service."""
    import sys
    import os
    import signal

    mode = get_install_mode()
    logger.info(f"Starting system update (mode: {mode})...")

    if mode == "git":
        import tars_sdk
        repo_dir = None
        for parent in Path(tars_sdk.__file__).parents:
            if (parent / ".git").exists():
                repo_dir = parent
                break

        if not repo_dir:
            logger.error("Git repo not found")
            return False

        # Stay on main branch — pull to latest tag via merge, never checkout tag
        # (checkout tag → detached HEAD breaks future pulls)
        code, _, err = run_git_command(["fetch", "--all", "--tags"], cwd=repo_dir)
        if code != 0:
            logger.error(f"Git fetch failed: {err}")
            return False

        code, out, err = run_git_command(["pull", "--ff-only", "origin", "main"], cwd=repo_dir)
        if code != 0:
            logger.error(f"Git pull failed: {err}")
            return False
        logger.info(f"Git pull: {out}")

        # Use venv python explicitly so pip targets the right environment
        pip_cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
        try:
            result = subprocess.run(
                pip_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(repo_dir)
            )
            if result.returncode != 0:
                logger.error(f"pip install -e failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"pip install error: {e}")
            return False

    else:
        # PyPI mode: upgrade installed package
        pip_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "tars-robot[daemon]"]
        try:
            result = subprocess.run(
                pip_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                logger.error(f"pip upgrade failed: {result.stderr}")
                return False
            logger.info(f"pip upgrade: {result.stdout[-500:] if result.stdout else 'ok'}")
        except subprocess.TimeoutExpired:
            logger.error("pip upgrade timed out")
            return False
        except Exception as e:
            logger.error(f"pip upgrade error: {e}")
            return False

    logger.info("Update complete — scheduling restart")

    # Non-blocking restart: spawn a subprocess that waits for this process to
    # finish its current work (3s), then asks systemd to restart the service.
    # This avoids the race where systemd starts a new instance before the old
    # one has released port 8000.
    try:
        subprocess.Popen(
            ["bash", "-c", "sleep 3 && sudo systemctl restart tars"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # detach from our process group
        )
        # Give the Popen a moment to register, then SIGTERM self cleanly
        import time
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)
    except Exception as e:
        logger.warning(f"Restart scheduling failed: {e}")
        os.kill(os.getpid(), signal.SIGTERM)

    return True


@router.post("/install", response_model=UpdateInstallResponse)
async def install_update(background_tasks: BackgroundTasks):
    """Install available update."""
    mode = get_install_mode()
    latest_version, _ = fetch_latest_version()
    
    if not latest_version:
        raise HTTPException(status_code=503, detail="Unable to check for updates")

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


@router.post("/restart")
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
