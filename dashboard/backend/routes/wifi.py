"""WiFi management API routes using NetworkManager."""

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from ..wifi_manager import WiFiManager


router = APIRouter()
wifi_manager = WiFiManager()


class WiFiNetwork(BaseModel):
    """WiFi network information."""
    ssid: str
    signal: int
    security: str


class WiFiConnectRequest(BaseModel):
    """Request to connect to a WiFi network."""
    ssid: str
    password: Optional[str] = ""
    # Enterprise WiFi fields
    is_enterprise: bool = False
    username: Optional[str] = None
    eap_method: Optional[str] = "peap"
    phase2_auth: Optional[str] = "mschapv2"


class HotspotRequest(BaseModel):
    """Request to toggle WiFi hotspot."""
    enabled: bool


class WiFiStatus(BaseModel):
    """Current WiFi connection status."""
    mode: str  # "hotspot", "client", or "disconnected"
    ssid: Optional[str] = None
    ip: Optional[str] = None
    tailscale_ip: Optional[str] = None


class WiFiNetworksResponse(BaseModel):
    """Response containing list of available networks."""
    networks: list[WiFiNetwork]


class WiFiConnectResponse(BaseModel):
    """Response from connect attempt."""
    success: bool
    message: str


class WiFiHotspotResponse(BaseModel):
    """Response from hotspot operation."""
    success: bool
    message: Optional[str] = None


@router.get("/status", response_model=WiFiStatus)
async def get_wifi_status():
    """
    Get current WiFi connection status.
    
    Returns:
        WiFiStatus with mode ("hotspot", "client", or "disconnected"), 
        optional SSID, IP address, and Tailscale IP
    """
    try:
        status = await asyncio.to_thread(wifi_manager.get_status)
        
        # Get Tailscale IP if available
        try:
            import subprocess
            result = subprocess.run(
                ["tailscale", "ip", "-4"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                status["tailscale_ip"] = result.stdout.strip()
        except Exception:
            pass
        
        return WiFiStatus(**status)
    except Exception as e:
        logger.error(f"Failed to get WiFi status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get WiFi status: {str(e)}"
        )


@router.get("/networks", response_model=WiFiNetworksResponse)
async def scan_wifi_networks(rescan: bool = True):
    """
    Scan for available WiFi networks.
    
    Args:
        rescan: If true, force a fresh scan. If false, use cached results.
        
    Returns:
        List of available WiFi networks with SSID, signal strength, and security type
    """
    try:
        logger.debug(f"Scanning WiFi networks (rescan={rescan})")
        networks = await asyncio.to_thread(wifi_manager.scan_networks, rescan)
        
        # Convert to response models
        network_list = [
            WiFiNetwork(
                ssid=net["ssid"],
                signal=net["signal"],
                security=net["security"]
            )
            for net in networks
        ]
        
        return WiFiNetworksResponse(networks=network_list)
    except Exception as e:
        logger.error(f"WiFi scan failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"WiFi scan failed: {str(e)}"
        )


@router.post("/connect", response_model=WiFiConnectResponse)
async def connect_to_wifi(request: WiFiConnectRequest):
    """
    Connect to a WiFi network (Personal or Enterprise).
    
    Args:
        request: Connection request with SSID and credentials
        
    Returns:
        Success status and message
        
    Raises:
        HTTPException: If connection fails
    """
    ssid = request.ssid
    
    logger.info(f"Attempting to connect to WiFi: {ssid} (enterprise={request.is_enterprise})")
    
    try:
        if request.is_enterprise:
            # Enterprise WiFi (802.1X)
            if not request.username:
                raise HTTPException(
                    status_code=400,
                    detail="Username required for enterprise WiFi"
                )
            
            success = await asyncio.to_thread(
                wifi_manager.connect_enterprise,
                ssid,
                request.username,
                request.password or "",
                request.eap_method or "peap",
                request.phase2_auth or "mschapv2"
            )
        else:
            # Personal WiFi (WPA-PSK)
            password = request.password or ""
            success = await asyncio.to_thread(wifi_manager.connect, ssid, password)
        
        if success:
            return WiFiConnectResponse(
                success=True,
                message=f"Connected to {ssid}"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to connect to {ssid}. Check credentials or signal strength."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WiFi connection error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"WiFi connection error: {str(e)}"
        )


@router.put("/hotspot", response_model=WiFiHotspotResponse)
async def toggle_wifi_hotspot(request: HotspotRequest):
    """
    Enable or disable the TARS-Setup WiFi hotspot.

    Args:
        enabled: True to start hotspot, False to stop

    Returns:
        Success status and message
    """
    logger.info(f"WiFi hotspot: {'starting' if request.enabled else 'stopping'}")

    try:
        if request.enabled:
            success = await asyncio.to_thread(wifi_manager.start_hotspot)
            if success:
                return WiFiHotspotResponse(
                    success=True,
                    message=f"Hotspot started: {wifi_manager.HOTSPOT_SSID}"
                )
            else:
                raise HTTPException(500, "Failed to start hotspot")
        else:
            success = await asyncio.to_thread(wifi_manager.stop_hotspot)
            return WiFiHotspotResponse(
                success=True,
                message="Hotspot stopped" if success else "Hotspot already stopped"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hotspot toggle error: {e}")
        raise HTTPException(500, f"Hotspot error: {str(e)}")
