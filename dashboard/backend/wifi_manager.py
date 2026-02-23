"""
WiFi Manager for TARS using NetworkManager.

Handles:
- Scanning for available networks
- Connecting to WiFi networks
- Starting/stopping setup hotspot
- Getting connection status
"""

import subprocess
import re
from typing import Dict, List, Optional

from loguru import logger


class WiFiManager:
    """Manages WiFi connection and hotspot using NetworkManager."""

    HOTSPOT_SSID = "TARS-Setup"
    HOTSPOT_PASSWORD = "tars1234"
    HOTSPOT_IP = "10.42.0.1"
    CONNECTION_NAME = "TARS-Setup"

    def __init__(self):
        """Initialize WiFi manager and ensure hotspot connection exists."""
        self._ensure_hotspot_connection()

    def _run_command(
        self, 
        args: List[str], 
        timeout: int = 30,
        check: bool = False,
        use_sudo: bool = False
    ) -> tuple[int, str, str]:
        """
        Run a command and return (returncode, stdout, stderr).
        
        Args:
            args: Command and arguments as list
            timeout: Command timeout in seconds
            check: Raise exception on non-zero exit code
            use_sudo: Prepend sudo to command
            
        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        if use_sudo:
            args = ["sudo"] + args
            
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(args)}")
            return -1, "", "Command timed out"
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(args)}")
            return e.returncode, e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else ""
        except Exception as e:
            logger.error(f"Command error: {e}")
            return -1, "", str(e)

    def _ensure_hotspot_connection(self) -> bool:
        """
        Ensure the TARS-Setup hotspot connection exists.
        Creates it if it doesn't exist.
        
        Returns:
            True if connection exists or was created successfully
        """
        code, out, _ = self._run_command(
            ["nmcli", "-t", "-f", "NAME", "connection", "show"],
            timeout=5
        )
        
        if code == 0 and self.CONNECTION_NAME in out.split("\n"):
            logger.debug(f"Hotspot connection '{self.CONNECTION_NAME}' already exists")
            return True
        
        logger.info(f"Creating hotspot connection '{self.CONNECTION_NAME}'")
        
        # Create the connection (needs sudo)
        code, out, err = self._run_command([
            "nmcli", "connection", "add",
            "type", "wifi",
            "ifname", "wlan0",
            "con-name", self.CONNECTION_NAME,
            "autoconnect", "no",
            "ssid", self.HOTSPOT_SSID
        ], timeout=10, use_sudo=True)
        
        if code != 0:
            logger.error(f"Failed to create hotspot connection: {err}")
            return False
        
        # Configure as access point (needs sudo)
        code, out, err = self._run_command([
            "nmcli", "connection", "modify", self.CONNECTION_NAME,
            "802-11-wireless.mode", "ap",
            "802-11-wireless.band", "bg",
            "ipv4.method", "shared"
        ], timeout=10, use_sudo=True)
        
        if code != 0:
            logger.error(f"Failed to configure hotspot mode: {err}")
            return False
        
        # Set password (needs sudo)
        code, out, err = self._run_command([
            "nmcli", "connection", "modify", self.CONNECTION_NAME,
            "wifi-sec.key-mgmt", "wpa-psk",
            "wifi-sec.psk", self.HOTSPOT_PASSWORD
        ], timeout=10, use_sudo=True)
        
        if code != 0:
            logger.error(f"Failed to set hotspot password: {err}")
            return False
        
        logger.info("Hotspot connection created successfully")
        return True

    def scan_networks(self, rescan: bool = True) -> List[Dict[str, any]]:
        """
        Scan for available WiFi networks.
        
        Args:
            rescan: If True, force a fresh scan. If False, use cached results.
            
        Returns:
            List of network dictionaries with ssid, signal, and security fields
        """
        logger.debug(f"Scanning WiFi networks (rescan={rescan})")
        
        # Trigger rescan if requested
        if rescan:
            code, _, err = self._run_command(
                ["nmcli", "device", "wifi", "list", "--rescan", "yes"],
                timeout=30
            )
            if code != 0:
                logger.warning(f"Rescan failed, using cached results: {err}")
        
        # Get network list
        code, out, err = self._run_command(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
            timeout=10
        )
        
        if code != 0:
            logger.error(f"Failed to list WiFi networks: {err}")
            return []
        
        networks = []
        seen_ssids = set()
        
        for line in out.split("\n"):
            if not line.strip():
                continue
            
            parts = line.split(":")
            if len(parts) < 3:
                continue
            
            ssid = parts[0].strip()
            signal_str = parts[1].strip()
            security = parts[2].strip()
            
            # Skip empty SSIDs (hidden networks)
            if not ssid or ssid == "--":
                continue
            
            # Skip duplicates (same SSID from multiple APs)
            if ssid in seen_ssids:
                continue
            seen_ssids.add(ssid)
            
            # Parse signal strength
            try:
                signal = int(signal_str)
            except ValueError:
                signal = 0
            
            # Normalize security field
            if not security or security == "--":
                security = "open"
            elif "WPA2" in security or "WPA3" in security:
                security = "WPA2"
            elif "WPA" in security:
                security = "WPA"
            else:
                security = "open"
            
            networks.append({
                "ssid": ssid,
                "signal": signal,
                "security": security
            })
        
        # Sort by signal strength (highest first)
        networks.sort(key=lambda x: x["signal"], reverse=True)
        
        logger.debug(f"Found {len(networks)} networks")
        return networks

    def connect(self, ssid: str, password: str) -> bool:
        """
        Connect to a WiFi network.
        
        NetworkManager will automatically deactivate the hotspot when connecting
        to a client network.
        
        Args:
            ssid: Network SSID
            password: Network password (can be empty for open networks)
            
        Returns:
            True if connection successful, False otherwise
        """
        logger.info(f"Connecting to WiFi: {ssid}")
        
        # Build command (needs sudo)
        cmd = ["nmcli", "--wait", "30", "device", "wifi", "connect", ssid]
        if password:
            cmd.extend(["password", password])
        
        code, out, err = self._run_command(cmd, timeout=35, use_sudo=True)
        
        if code == 0:
            logger.info(f"Successfully connected to {ssid}")
            return True
        
        # Parse error message
        error_msg = err or out
        if "Secrets were required" in error_msg or "wrong password" in error_msg.lower():
            logger.error(f"Wrong password for {ssid}")
        elif "No network with SSID" in error_msg:
            logger.error(f"Network {ssid} not found")
        elif "timeout" in error_msg.lower():
            logger.error(f"Connection timeout for {ssid}")
        else:
            logger.error(f"Failed to connect to {ssid}: {error_msg}")
        
        return False

    def start_hotspot(self) -> bool:
        """
        Start the TARS-Setup hotspot.
        
        Returns:
            True if hotspot started successfully
        """
        logger.info(f"Starting hotspot: {self.HOTSPOT_SSID}")
        
        # Ensure connection exists
        if not self._ensure_hotspot_connection():
            return False
        
        # Activate the connection (needs sudo)
        code, out, err = self._run_command(
            ["nmcli", "connection", "up", self.CONNECTION_NAME],
            timeout=15,
            use_sudo=True
        )
        
        if code == 0:
            logger.info("Hotspot started successfully")
            return True
        
        error_msg = err or out
        logger.error(f"Failed to start hotspot: {error_msg}")
        return False

    def stop_hotspot(self) -> bool:
        """
        Stop the TARS-Setup hotspot.
        
        Returns:
            True if hotspot stopped successfully
        """
        logger.info("Stopping hotspot")
        
        # Deactivate the connection (needs sudo)
        code, out, err = self._run_command(
            ["nmcli", "connection", "down", self.CONNECTION_NAME],
            timeout=10,
            use_sudo=True
        )
        
        if code == 0:
            logger.info("Hotspot stopped successfully")
            return True
        
        # Connection might not be active, which is fine
        error_msg = err or out
        if "not active" in error_msg.lower():
            logger.debug("Hotspot was not active")
            return True
        
        logger.error(f"Failed to stop hotspot: {error_msg}")
        return False

    def get_status(self) -> Dict[str, any]:
        """
        Get current WiFi connection status.
        
        Returns:
            Dictionary with mode, ssid, and ip fields:
            - mode: "hotspot", "wlan", or "disconnected"
            - ssid: Current network SSID (if connected)
            - ip: Current IP address (if connected)
        """
        code, out, err = self._run_command(
            ["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device"],
            timeout=5
        )
        
        if code != 0:
            logger.error(f"Failed to get device status: {err}")
            return {
                "mode": "disconnected",
                "ssid": None,
                "ip": None
            }
        
        # Parse device output
        for line in out.split("\n"):
            parts = line.split(":")
            if len(parts) < 3:
                continue
            
            dev_type = parts[0].strip()
            state = parts[1].strip()
            connection = parts[2].strip()
            
            # Look for wifi device
            if dev_type != "wifi":
                continue
            
            # Check if connected
            if state != "connected":
                continue
            
            # Check if it's the hotspot
            if connection == self.CONNECTION_NAME:
                return {
                    "mode": "hotspot",
                    "ssid": self.HOTSPOT_SSID,
                    "ip": self.HOTSPOT_IP
                }
            
            # It's a client connection
            # Get IP address
            ip = self._get_ip_address()
            
            return {
                "mode": "wlan",
                "ssid": connection,
                "ip": ip
            }
        
        # No active connection
        return {
            "mode": "disconnected",
            "ssid": None,
            "ip": None
        }

    def _get_ip_address(self) -> Optional[str]:
        """
        Get the current IP address of wlan0.
        
        Returns:
            IP address string or None if not assigned
        """
        code, out, _ = self._run_command(
            ["ip", "-4", "addr", "show", "wlan0"],
            timeout=5
        )
        
        if code != 0:
            return None
        
        # Parse IP from output like: "inet 192.168.1.100/24"
        match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", out)
        if match:
            return match.group(1)
        
        return None


    def connect_enterprise(self, ssid: str, username: str, password: str, eap_method: str = "peap", phase2_auth: str = "mschapv2") -> bool:
        """
        Connect to a WPA Enterprise network (802.1X).
        
        Args:
            ssid: Network SSID
            username: Enterprise username/identity
            password: Enterprise password
            eap_method: EAP method (peap, ttls, tls)
            phase2_auth: Phase 2 authentication (mschapv2, md5, gtc)
            
        Returns:
            True if connection successful, False otherwise
        """
        logger.info(f"Connecting to enterprise WiFi: {ssid} (user: {username})")
        
        # First, create or update the connection profile
        # Check if connection already exists
        code, out, _ = self._run_command(
            ["nmcli", "-t", "-f", "NAME", "connection", "show"],
            timeout=5
        )
        
        connection_exists = ssid in out.split("\n") if code == 0 else False
        
        if connection_exists:
            # Modify existing connection
            logger.debug(f"Modifying existing connection: {ssid}")
            
            # Update to enterprise settings
            code, out, err = self._run_command([
                "nmcli", "connection", "modify", ssid,
                "802-11-wireless-security.key-mgmt", "wpa-eap",
                "802-1x.eap", eap_method,
                "802-1x.phase2-auth", phase2_auth,
                "802-1x.identity", username,
                "802-1x.password", password
            ], timeout=10, use_sudo=True)
            
            if code != 0:
                logger.error(f"Failed to modify connection: {err}")
                return False
        else:
            # Create new enterprise connection
            logger.debug(f"Creating new enterprise connection: {ssid}")
            
            code, out, err = self._run_command([
                "nmcli", "connection", "add",
                "type", "wifi",
                "ifname", "wlan0",
                "con-name", ssid,
                "ssid", ssid,
                "802-11-wireless-security.key-mgmt", "wpa-eap",
                "802-1x.eap", eap_method,
                "802-1x.phase2-auth", phase2_auth,
                "802-1x.identity", username,
                "802-1x.password", password
            ], timeout=10, use_sudo=True)
            
            if code != 0:
                logger.error(f"Failed to create connection: {err}")
                return False
        
        # Now connect
        code, out, err = self._run_command(
            ["nmcli", "--wait", "30", "connection", "up", ssid],
            timeout=35,
            use_sudo=True
        )
        
        if code == 0:
            logger.info(f"Successfully connected to {ssid}")
            
            # Enable autoconnect
            code2, _, err2 = self._run_command([
                "nmcli", "connection", "modify", ssid,
                "autoconnect", "yes"
            ], timeout=5, use_sudo=True)
            
            if code2 == 0:
                logger.debug(f"Enabled autoconnect for {ssid}")
            else:
                logger.warning(f"Failed to enable autoconnect for {ssid}: {err2}")
            
            return True
        
        # Parse error message
        error_msg = err or out
        if "Secrets were required" in error_msg or "wrong password" in error_msg.lower():
            logger.error(f"Wrong credentials for {ssid}")
        elif "No network with SSID" in error_msg:
            logger.error(f"Network {ssid} not found")
        elif "timeout" in error_msg.lower():
            logger.error(f"Connection timeout for {ssid}")
        else:
            logger.error(f"Failed to connect to {ssid}: {error_msg}")
        
        return False


    def is_connected(self) -> bool:
        """
        Check if connected to a WiFi network (client mode, not hotspot).
        
        Returns:
            True if connected to a client network, False otherwise
        """
        status = self.get_status()
        return status["mode"] == "wlan"
