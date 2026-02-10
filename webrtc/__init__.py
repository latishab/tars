"""
WebRTC for TARS
- Server: RPi waits for connections (new architecture)
- Client: RPi connects to host (legacy, for backward compatibility)
"""

from .client import WebRTCClient
from .server import WebRTCServer

__all__ = ["WebRTCClient", "WebRTCServer"]
