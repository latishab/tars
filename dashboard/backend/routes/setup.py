"""Setup wizard API routes."""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

CONFIG_FILE = Path("/etc/tars/config.json")


class SetupRequest(BaseModel):
    """Setup completion request."""
    wifi_ssid: str
    wifi_password: Optional[str] = None
    deepgram_api_key: Optional[str] = None
    tailscale_enabled: bool = False
    tailscale_auth_key: Optional[str] = None


def load_config():
    """Load TARS configuration."""
    if not CONFIG_FILE.exists():
        return {
            "wifi_configured": False,
            "connection_mode": "local",
            "tailscale_enabled": False,
            "first_boot": True,
        }
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def save_config(config):
    """Save TARS configuration."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        logger.info("Config saved")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise


@router.get("/status")
async def get_setup_status():
    """Get setup completion status."""
    config = load_config()
    return {
        "completed": config.get("wifi_configured", False),
        "first_boot": config.get("first_boot", True),
    }


@router.post("/complete")
async def complete_setup(request: SetupRequest):
    """Complete initial setup."""
    logger.info(f"Setup completion request for SSID: {request.wifi_ssid}")

    # Validate Tailscale settings
    if request.tailscale_enabled and not request.tailscale_auth_key:
        raise HTTPException(
            status_code=400,
            detail="Tailscale auth key required when Tailscale is enabled"
        )

    # Load existing config
    config = load_config()

    # Update config with setup data
    config.update({
        "wifi_ssid": request.wifi_ssid,
        "wifi_password": request.wifi_password,
        "wifi_configured": True,
        "deepgram_api_key": request.deepgram_api_key,
        "tailscale_enabled": request.tailscale_enabled,
        "tailscale_auth_key": request.tailscale_auth_key,
        "connection_mode": "tailscale" if request.tailscale_enabled else "local",
        "first_boot": True,  # firstboot script will clear this
    })

    # Save config
    try:
        save_config(config)
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        raise HTTPException(status_code=500, detail="Failed to save configuration")

    logger.info("Setup completed successfully")

    return {
        "success": True,
        "message": "Setup completed. TARS will connect to your WiFi network.",
        "connection_mode": config["connection_mode"],
    }
