"""
WiFi Manager for TARS first-boot setup.

Handles:
- Detecting if WiFi is configured
- Starting hotspot for initial setup
- Connecting to user's WiFi network
"""

import subprocess
import time
from pathlib import Path
from typing import Optional

from loguru import logger


class WiFiManager:
    """Manages WiFi connection and hotspot for TARS."""

    HOSTAPD_CONF = Path("/etc/hostapd/hostapd.conf")
    WPA_CONF = Path("/etc/wpa_supplicant/wpa_supplicant.conf")
    SETUP_FLAG = Path("/var/lib/tars/wifi_configured")

    HOTSPOT_SSID = "tars-wifi-setup"
    HOTSPOT_PASSWORD = "tarscoffee"

    def __init__(self):
        self._hotspot_active = False

    def is_connected(self) -> bool:
        """Check if connected to a WiFi network."""
        try:
            result = subprocess.run(
                ["iwgetid", "-r"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def get_current_ssid(self) -> Optional[str]:
        """Get currently connected SSID."""
        try:
            result = subprocess.run(
                ["iwgetid", "-r"],
                capture_output=True,
                text=True,
                timeout=5
            )
            ssid = result.stdout.strip()
            return ssid if ssid else None
        except Exception:
            return None

    def is_configured(self) -> bool:
        """Check if WiFi has been configured (not first boot)."""
        return self.SETUP_FLAG.exists()

    def mark_configured(self):
        """Mark WiFi as configured."""
        self.SETUP_FLAG.parent.mkdir(parents=True, exist_ok=True)
        self.SETUP_FLAG.touch()

    def needs_setup(self) -> bool:
        """Check if we need to run setup wizard."""
        # If already connected, no setup needed
        if self.is_connected():
            return False

        # If never configured, need setup
        if not self.is_configured():
            return True

        # Configured but not connected - might need reconnect
        return False

    def start_hotspot(self) -> bool:
        """Start access point for setup."""
        logger.info(f"Starting hotspot: {self.HOTSPOT_SSID}")

        # Configure hostapd
        hostapd_config = f"""
interface=wlan0
driver=nl80211
ssid={self.HOTSPOT_SSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self.HOTSPOT_PASSWORD}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
"""

        try:
            # Write config
            subprocess.run(
                ["sudo", "sh", "-c", f"echo '{hostapd_config}' > /etc/hostapd/hostapd.conf"],
                check=True,
                timeout=10
            )

            # Configure dnsmasq for DHCP
            dnsmasq_config = """
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/tars.local/192.168.4.1
"""
            subprocess.run(
                ["sudo", "sh", "-c", f"echo '{dnsmasq_config}' > /etc/dnsmasq.d/tars-hotspot.conf"],
                check=True,
                timeout=10
            )

            # Set static IP
            subprocess.run(
                ["sudo", "ip", "addr", "add", "192.168.4.1/24", "dev", "wlan0"],
                timeout=10
            )

            # Start services
            subprocess.run(["sudo", "systemctl", "start", "hostapd"], check=True, timeout=30)
            subprocess.run(["sudo", "systemctl", "start", "dnsmasq"], check=True, timeout=30)

            self._hotspot_active = True
            logger.info("Hotspot started successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start hotspot: {e}")
            return False
        except Exception as e:
            logger.error(f"Hotspot error: {e}")
            return False

    def stop_hotspot(self) -> bool:
        """Stop access point."""
        logger.info("Stopping hotspot...")

        try:
            subprocess.run(["sudo", "systemctl", "stop", "hostapd"], timeout=30)
            subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"], timeout=30)
            subprocess.run(
                ["sudo", "ip", "addr", "del", "192.168.4.1/24", "dev", "wlan0"],
                timeout=10
            )

            self._hotspot_active = False
            logger.info("Hotspot stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop hotspot: {e}")
            return False

    def connect(self, ssid: str, password: str) -> bool:
        """Connect to a WiFi network."""
        logger.info(f"Connecting to WiFi: {ssid}")

        # Stop hotspot first
        if self._hotspot_active:
            self.stop_hotspot()

        try:
            # Generate PSK
            result = subprocess.run(
                ["wpa_passphrase", ssid, password],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error("Failed to generate PSK")
                return False

            # Extract network block
            network_block = result.stdout

            # Append to wpa_supplicant.conf
            subprocess.run(
                ["sudo", "sh", "-c", f"echo '{network_block}' >> /etc/wpa_supplicant/wpa_supplicant.conf"],
                check=True,
                timeout=10
            )

            # Reconfigure
            subprocess.run(["wpa_cli", "-i", "wlan0", "reconfigure"], timeout=10)

            # Wait for connection
            for i in range(30):
                time.sleep(1)
                if self.get_current_ssid() == ssid:
                    logger.info(f"Connected to {ssid}")
                    self.mark_configured()
                    return True

            logger.error(f"Failed to connect to {ssid}")
            return False

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    @property
    def is_hotspot_active(self) -> bool:
        """Check if hotspot is currently active."""
        if self._hotspot_active:
            return True

        try:
            result = subprocess.run(
                ["systemctl", "is-active", "hostapd"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False
