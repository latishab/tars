#!/usr/bin/env python3
"""Sync version across all files."""

import re
from pathlib import Path

def get_version_from_pyproject():
    """Get version from pyproject.toml."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject.read_text()
    match = re.search(r'version = "(.+?)"', content)
    if match:
        return match.group(1)
    raise ValueError("Version not found in pyproject.toml")

def update_dashboard_version(version):
    """Update version in dashboard server.py."""
    server_py = Path(__file__).parent.parent / "dashboard" / "backend" / "server.py"
    content = server_py.read_text()
    content = re.sub(
        r'version="[^"]+"',
        f'version="{version}"',
        content
    )
    server_py.write_text(content)
    print(f"Updated dashboard/backend/server.py to {version}")

if __name__ == "__main__":
    version = get_version_from_pyproject()
    update_dashboard_version(version)
    print(f"All versions synced to {version}")
