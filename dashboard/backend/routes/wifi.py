"""WiFi management API routes."""

import subprocess
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter()


class WiFiNetwork(BaseModel):
    ssid: str
    signal: int  # Signal strength in dBm (negative)
    security: str  # "open", "wpa", "wpa2", etc.
    connected: bool = False


class WiFiConnectRequest(BaseModel):
    ssid: str
    password: Optional[str] = None


class WiFiStatus(BaseModel):
    connected: bool
    ssid: Optional[str] = None
    ip_address: Optional[str] = None
    signal: Optional[int] = None
    hotspot_active: bool = False


def run_command(args: list, timeout: int = 30) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def get_current_ssid() -> Optional[str]:
    """Get currently connected WiFi SSID."""
    code, out, _ = run_command(["iwgetid", "-r"])
    if code == 0 and out:
        return out
    return None


def get_ip_address() -> Optional[str]:
    """Get current IP address."""
    code, out, _ = run_command(["hostname", "-I"])
    if code == 0 and out:
        return out.split()[0]
    return None


def get_signal_strength() -> Optional[int]:
    """Get current WiFi signal strength."""
    code, out, _ = run_command(["iwconfig", "wlan0"])
    if code == 0:
        match = re.search(r"Signal level=(-?\d+)", out)
        if match:
            return int(match.group(1))
    return None


def is_hotspot_active() -> bool:
    """Check if hotspot is active."""
    code, out, _ = run_command(["systemctl", "is-active", "hostapd"])
    return code == 0 and out == "active"


def parse_iwlist_output(output: str) -> List[WiFiNetwork]:
    """Parse iwlist scan output into network list."""
    networks = []
    current = {}

    for line in output.split("\n"):
        line = line.strip()

        if line.startswith("Cell"):
            if current.get("ssid"):
                networks.append(WiFiNetwork(**current))
            current = {"ssid": "", "signal": -100, "security": "open"}

        elif "ESSID:" in line:
            match = re.search(r'ESSID:"(.+)"', line)
            if match:
                current["ssid"] = match.group(1)

        elif "Signal level=" in line:
            match = re.search(r"Signal level=(-?\d+)", line)
            if match:
                current["signal"] = int(match.group(1))

        elif "Encryption key:on" in line:
            current["security"] = "wpa"

        elif "WPA2" in line:
            current["security"] = "wpa2"

    if current.get("ssid"):
        networks.append(WiFiNetwork(**current))

    # Sort by signal strength
    networks.sort(key=lambda x: x.signal, reverse=True)

    # Remove duplicates
    seen = set()
    unique = []
    for net in networks:
        if net.ssid and net.ssid not in seen:
            seen.add(net.ssid)
            unique.append(net)

    return unique


@router.get("/wifi/status", response_model=WiFiStatus)
async def wifi_status():
    """Get current WiFi status."""
    ssid = get_current_ssid()

    return WiFiStatus(
        connected=ssid is not None,
        ssid=ssid,
        ip_address=get_ip_address() if ssid else None,
        signal=get_signal_strength() if ssid else None,
        hotspot_active=is_hotspot_active(),
    )


@router.get("/wifi/networks")
async def scan_networks():
    """Scan for available WiFi networks."""
    # Need to temporarily stop hotspot to scan
    hotspot_was_active = is_hotspot_active()
    if hotspot_was_active:
        run_command(["sudo", "systemctl", "stop", "hostapd"])

    # Scan
    code, out, err = run_command(["sudo", "iwlist", "wlan0", "scan"], timeout=30)

    # Restart hotspot if it was active
    if hotspot_was_active:
        run_command(["sudo", "systemctl", "start", "hostapd"])

    if code != 0:
        logger.error(f"WiFi scan failed: {err}")
        raise HTTPException(status_code=500, detail="WiFi scan failed")

    networks = parse_iwlist_output(out)

    # Mark current network as connected
    current = get_current_ssid()
    for net in networks:
        if net.ssid == current:
            net.connected = True

    return {"networks": networks}


@router.post("/wifi/connect")
async def connect_to_wifi(request: WiFiConnectRequest):
    """Connect to a WiFi network."""
    ssid = request.ssid
    password = request.password

    logger.info(f"Attempting to connect to WiFi: {ssid}")

    # Stop hotspot if active
    if is_hotspot_active():
        run_command(["sudo", "systemctl", "stop", "hostapd"])
        run_command(["sudo", "systemctl", "stop", "dnsmasq"])

    # Create wpa_supplicant config entry
    if password:
        # Generate PSK
        code, psk, err = run_command(["wpa_passphrase", ssid, password])
        if code != 0:
            raise HTTPException(status_code=400, detail="Invalid password")

        # Extract PSK line
        psk_match = re.search(r"psk=([a-f0-9]+)", psk)
        if not psk_match:
            raise HTTPException(status_code=500, detail="Failed to generate PSK")

        network_block = f'''
network={{
    ssid="{ssid}"
    psk={psk_match.group(1)}
    key_mgmt=WPA-PSK
}}
'''
    else:
        network_block = f'''
network={{
    ssid="{ssid}"
    key_mgmt=NONE
}}
'''

    # Append to wpa_supplicant.conf
    try:
        wpa_conf = "/etc/wpa_supplicant/wpa_supplicant.conf"
        with open(wpa_conf, "a") as f:
            f.write(network_block)
    except PermissionError:
        # Use sudo
        code, _, err = run_command([
            "sudo", "sh", "-c",
            f'echo \'{network_block}\' >> /etc/wpa_supplicant/wpa_supplicant.conf'
        ])
        if code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to save config: {err}")

    # Reconfigure wpa_supplicant
    run_command(["wpa_cli", "-i", "wlan0", "reconfigure"])

    # Wait for connection
    import time
    for i in range(30):
        time.sleep(1)
        if get_current_ssid() == ssid:
            logger.info(f"Successfully connected to {ssid}")
            return {
                "success": True,
                "ssid": ssid,
                "ip_address": get_ip_address(),
            }

    # Failed to connect
    logger.error(f"Failed to connect to {ssid}")
    raise HTTPException(status_code=400, detail="Failed to connect to network")


@router.post("/wifi/hotspot/start")
async def start_hotspot():
    """Start WiFi hotspot for setup."""
    logger.info("Starting WiFi hotspot...")

    # Configure hostapd
    hostapd_conf = """
interface=wlan0
driver=nl80211
ssid=tars-wifi-setup
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=tarscoffee
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
"""

    try:
        code, _, err = run_command([
            "sudo", "sh", "-c",
            f'echo \'{hostapd_conf}\' > /etc/hostapd/hostapd.conf'
        ])
        if code != 0:
            raise HTTPException(status_code=500, detail=f"Failed to configure hostapd: {err}")

        # Start services
        run_command(["sudo", "systemctl", "start", "hostapd"])
        run_command(["sudo", "systemctl", "start", "dnsmasq"])

        return {
            "success": True,
            "ssid": "tars-wifi-setup",
            "password": "tarscoffee",
        }

    except Exception as e:
        logger.error(f"Failed to start hotspot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wifi/hotspot/stop")
async def stop_hotspot():
    """Stop WiFi hotspot."""
    logger.info("Stopping WiFi hotspot...")

    run_command(["sudo", "systemctl", "stop", "hostapd"])
    run_command(["sudo", "systemctl", "stop", "dnsmasq"])

    return {"success": True}
