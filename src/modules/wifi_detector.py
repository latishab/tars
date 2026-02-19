#!/usr/bin/env python3
"""
WiFi Status Detection for TARS

Detects WiFi connection mode (hotspot, wlan, disconnected) on Raspberry Pi.
"""

import subprocess
import re
from typing import Tuple, Optional


def get_wifi_status() -> Tuple[str, Optional[str]]:
    """
    Detect WiFi status and return (mode, ssid).

    Returns:
        mode: "hotspot", "wlan", or "disconnected"
        ssid: Network name if connected, None otherwise
    """
    # Check if hostapd is running (hotspot mode)
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "hostapd"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip() == "active":
            # Hotspot is active - get SSID from hostapd.conf
            ssid = _get_hotspot_ssid()
            return ("hotspot", ssid)
    except Exception:
        pass

    # Check if connected to WiFi network
    try:
        # Use iwgetid to get current SSID
        result = subprocess.run(
            ["iwgetid", "-r"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            ssid = result.stdout.strip()
            if ssid:
                return ("wlan", ssid)
    except Exception:
        pass

    # Fallback: check nmcli
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line.startswith("yes:"):
                    ssid = line.split(":", 1)[1]
                    return ("wlan", ssid)
    except Exception:
        pass

    # Not connected
    return ("disconnected", None)


def _get_hotspot_ssid() -> Optional[str]:
    """Extract SSID from hostapd.conf."""
    try:
        with open("/etc/hostapd/hostapd.conf", "r") as f:
            for line in f:
                if line.strip().startswith("ssid="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


if __name__ == "__main__":
    mode, ssid = get_wifi_status()
    print(f"Mode: {mode}")
    if ssid:
        print(f"SSID: {ssid}")
