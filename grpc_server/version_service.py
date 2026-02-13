"""Version service for TARS gRPC server."""

import subprocess
import platform
import urllib.request
import json
from typing import Optional, Tuple
from loguru import logger

from tars_sdk._version import __version__, __minimum_compatible_client__, get_version_info


PYPI_PACKAGE_NAME = "tars-sdk"
GITHUB_REPO = "latishab/tars"


def get_git_commit() -> Optional[str]:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_build_date() -> str:
    """Get build/install date."""
    import datetime
    return datetime.datetime.now().isoformat()


def fetch_latest_pypi_version() -> Optional[str]:
    """Fetch latest version from PyPI."""
    try:
        url = f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("info", {}).get("version")
    except Exception as e:
        logger.debug(f"Failed to fetch PyPI version: {e}")
        return None


def fetch_latest_github_release() -> Optional[Tuple[str, str]]:
    """Fetch latest release from GitHub. Returns (version, release_notes)."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            tag = data.get("tag_name", "").lstrip("v")
            notes = data.get("body", "")[:200]  # Truncate to 200 chars
            return tag, notes
    except Exception as e:
        logger.debug(f"Failed to fetch GitHub release: {e}")
        return None


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two semantic versions.
    Returns: -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """
    def parse_version(v):
        parts = v.split(".")
        return tuple(int(p) for p in parts[:3])
    
    try:
        p1 = parse_version(v1)
        p2 = parse_version(v2)
        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1
        return 0
    except (ValueError, IndexError):
        return 0


def determine_update_severity(current: str, latest: str) -> str:
    """
    Determine update severity based on version difference.
    
    Returns: "none", "optional", "recommended", or "required"
    """
    if compare_versions(current, latest) >= 0:
        return "none"
    
    def parse_version(v):
        parts = v.split(".")
        return tuple(int(p) for p in parts[:3])
    
    try:
        c = parse_version(current)
        l = parse_version(latest)
        
        # Major version bump = required
        if l[0] > c[0]:
            return "required"
        
        # Minor version bump = recommended
        if l[1] > c[1]:
            return "recommended"
        
        # Patch version bump = optional
        return "optional"
    except (ValueError, IndexError):
        return "optional"


def check_for_update() -> dict:
    """
    Check for available updates.
    
    Returns dict with update info.
    """
    current = __version__
    
    # Try PyPI first
    latest = fetch_latest_pypi_version()
    release_notes = ""
    
    # Fall back to GitHub
    if not latest:
        gh_result = fetch_latest_github_release()
        if gh_result:
            latest, release_notes = gh_result
    
    if not latest:
        latest = current
    
    severity = determine_update_severity(current, latest)
    update_available = severity != "none"
    
    return {
        "update_available": update_available,
        "current_version": current,
        "latest_version": latest,
        "severity": severity,
        "release_notes": release_notes,
        "pypi_url": f"https://pypi.org/project/{PYPI_PACKAGE_NAME}/",
        "github_url": f"https://github.com/{GITHUB_REPO}/releases",
    }
