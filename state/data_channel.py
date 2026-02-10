"""
WebRTC DataChannel Handler

Manages bidirectional state synchronization between RPi and MacBook.
Handles incoming state messages from the AI brain and sends robot status.

Message Types from MacBook → RPi:
- eye_state: Set eye state (listening, thinking, speaking, idle)
- emotion: Set facial expression (happy, angry, tired, surprised, confused)
- transcript: User/assistant conversation text
- audio_level: Audio visualization level
- tts_state: Whether TTS is currently speaking

Message Types from RPi → MacBook:
- battery: Battery status (level, charging)
- connected: Connection confirmation
- movement_status: Movement execution status
- face_detected: Face tracking data
"""

import json
from typing import Optional, Callable, Dict, Any
from loguru import logger
from dataclasses import dataclass


@dataclass
class BatteryStatus:
    level: float  # 0-100
    voltage: float
    charging: bool


@dataclass
class MovementStatus:
    moving: bool
    movement: Optional[str] = None


class DataChannelHandler:
    """
    Handles WebRTC DataChannel messages for state synchronization.

    The DataChannel provides real-time, low-latency bidirectional
    communication for state that doesn't need HTTP request/response.
    """

    def __init__(
        self,
        on_state_change: Optional[Callable[[str], None]] = None,
        on_emotion: Optional[Callable[[str], None]] = None,
        on_audio_level: Optional[Callable[[float, str], None]] = None,
    ):
        # Callbacks for incoming messages
        self.on_state_change = on_state_change
        self.on_emotion = on_emotion
        self.on_audio_level = on_audio_level

        # Send function (set by WebRTC server)
        self._send_fn: Optional[Callable[[str, Dict], None]] = None

    def set_send_function(self, send_fn: Callable[[str, Dict], None]):
        """Set the function used to send messages via DataChannel"""
        self._send_fn = send_fn

    def handle_message(self, message: str):
        """
        Process incoming DataChannel message from MacBook.

        Args:
            message: JSON string from MacBook
        """
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            logger.debug(f"DataChannel RX: {msg_type}")

            # Dispatch to appropriate handler
            if msg_type == "eye_state":
                state = data.get("state", "idle")
                if self.on_state_change:
                    self.on_state_change(state)

            elif msg_type == "emotion":
                emotion = data.get("value", "default")
                if self.on_emotion:
                    self.on_emotion(emotion)

            elif msg_type == "audio_level":
                level = data.get("level", 0.0)
                source = data.get("source", "none")
                if self.on_audio_level:
                    self.on_audio_level(level, source)

            elif msg_type == "tts_state":
                speaking = data.get("speaking", False)
                if self.on_state_change:
                    self.on_state_change("speaking" if speaking else "idle")

            elif msg_type == "transcript":
                # Log transcript for debugging
                role = data.get("role", "unknown")
                text = data.get("text", "")
                logger.info(f"Transcript [{role}]: {text[:100]}...")

            else:
                logger.warning(f"Unknown DataChannel message type: {msg_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in DataChannel: {message}")
        except Exception as e:
            logger.error(f"Error handling DataChannel message: {e}")

    # === Outgoing Messages (RPi → MacBook) ===

    def send_battery_status(self, status: BatteryStatus):
        """Send battery status to MacBook"""
        if not self._send_fn:
            return

        self._send_fn("battery", {
            "level": status.level,
            "voltage": status.voltage,
            "charging": status.charging
        })

    def send_connected(self, client_name: str = "rpi"):
        """Notify MacBook that connection is established"""
        if not self._send_fn:
            return

        self._send_fn("connected", {
            "client": client_name
        })

    def send_movement_status(self, status: MovementStatus):
        """Send movement execution status"""
        if not self._send_fn:
            return

        self._send_fn("movement_status", {
            "moving": status.moving,
            "movement": status.movement
        })

    def send_face_detected(self, x: int, y: int, width: int, height: int):
        """Send face detection data to MacBook"""
        if not self._send_fn:
            return

        self._send_fn("face_detected", {
            "x": x,
            "y": y,
            "width": width,
            "height": height
        })

    def send_custom(self, message_type: str, data: Dict[str, Any]):
        """Send custom message"""
        if not self._send_fn:
            return

        self._send_fn(message_type, data)
