"""
WebRTC client for connecting to MacBook's pipecat pipeline
"""

import asyncio
import json
from typing import Optional, Callable
from loguru import logger

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.media import MediaPlayer
    import aiohttp
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    logger.warning("aiortc not available - WebRTC disabled")

from .audio_track import MicrophoneTrack
from .audio_output import SpeakerOutput


class WebRTCClient:
    """
    WebRTC client that connects RPi to MacBook's pipecat pipeline.

    Handles:
    - Audio capture from microphone
    - Audio playback to speaker
    - Data channel for state sync
    """

    def __init__(
        self,
        signaling_url: str,
        on_state_change: Optional[Callable[[str], None]] = None,
        on_emotion: Optional[Callable[[str], None]] = None,
        on_audio_level: Optional[Callable[[float, str], None]] = None,
    ):
        if not AIORTC_AVAILABLE:
            raise RuntimeError("aiortc not installed - cannot use WebRTC")

        self.signaling_url = signaling_url.rstrip("/")
        self.on_state_change = on_state_change
        self.on_emotion = on_emotion
        self.on_audio_level = on_audio_level

        self.pc: Optional[RTCPeerConnection] = None
        self.mic_track: Optional[MicrophoneTrack] = None
        self.speaker: Optional[SpeakerOutput] = None
        self.data_channel = None

        self._connected = False
        self._running = False
        self._reconnect_task = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self):
        """Connect to MacBook's pipecat WebRTC endpoint"""
        logger.info(f"Connecting to {self.signaling_url}...")

        # Create peer connection
        self.pc = RTCPeerConnection()

        # Initialize audio
        self.mic_track = MicrophoneTrack()
        self.speaker = SpeakerOutput()

        # Add microphone track
        self.pc.addTrack(self.mic_track)

        # Handle incoming audio
        @self.pc.on("track")
        async def on_track(track):
            if track.kind == "audio":
                logger.info("Receiving audio track from MacBook")
                asyncio.create_task(self._handle_audio_track(track))

        # Handle data channel
        @self.pc.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"Data channel opened: {channel.label}")
            self.data_channel = channel

            @channel.on("message")
            def on_message(message):
                self._handle_data_message(message)

        # Connection state
        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            state = self.pc.connectionState
            logger.info(f"WebRTC connection state: {state}")

            if state == "connected":
                self._connected = True
                await self.mic_track.start()
                self.speaker.start()
            elif state in ["failed", "closed", "disconnected"]:
                self._connected = False
                await self.mic_track.stop()
                self.speaker.stop()
                # Schedule reconnection
                if self._running:
                    self._schedule_reconnect()

        # Create and send offer
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.signaling_url}/api/offer",
                json={
                    "sdp": self.pc.localDescription.sdp,
                    "type": self.pc.localDescription.type,
                }
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Signaling failed: {await resp.text()}")

                answer_data = await resp.json()
                answer = RTCSessionDescription(
                    sdp=answer_data["sdp"],
                    type=answer_data["type"]
                )
                await self.pc.setRemoteDescription(answer)

        self._running = True
        logger.info("WebRTC connection established")

    async def _handle_audio_track(self, track):
        """Process incoming TTS audio"""
        while self._running:
            try:
                frame = await track.recv()

                # Convert frame to numpy array
                audio_array = frame.to_ndarray()

                # Handle stereo to mono conversion
                if audio_array.ndim > 1:
                    audio_array = audio_array.mean(axis=1)

                # Convert to int16 and bytes
                import numpy as np
                audio_int16 = (audio_array * 32767).astype(np.int16)
                self.speaker.play(audio_int16.tobytes())

            except Exception as e:
                if "MediaStreamError" not in str(type(e)):
                    logger.error(f"Audio track error: {e}")
                break

    def _handle_data_message(self, message: str):
        """Handle messages from pipecat"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "state" and self.on_state_change:
                self.on_state_change(data.get("state", "idle"))
            elif msg_type == "emotion" and self.on_emotion:
                self.on_emotion(data.get("emotion", "default"))
            elif msg_type == "audio_level" and self.on_audio_level:
                self.on_audio_level(data.get("level", 0), data.get("source", "none"))

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in data channel: {message}")
        except Exception as e:
            logger.error(f"Error handling data message: {e}")

    def _schedule_reconnect(self):
        """Schedule reconnection attempt"""
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self):
        """Attempt to reconnect periodically"""
        while self._running and not self._connected:
            logger.info("Attempting to reconnect...")
            try:
                await self.connect()
            except Exception as e:
                logger.warning(f"Reconnection failed: {e}")
                await asyncio.sleep(5)

    async def disconnect(self):
        """Close WebRTC connection"""
        self._running = False

        if self._reconnect_task:
            self._reconnect_task.cancel()

        if self.mic_track:
            await self.mic_track.stop()
        if self.speaker:
            self.speaker.stop()
        if self.pc:
            await self.pc.close()

        self._connected = False
        logger.info("WebRTC disconnected")

    def send_message(self, message_type: str, data: dict):
        """Send message to MacBook via data channel"""
        if not self.data_channel or self.data_channel.readyState != "open":
            logger.warning("Data channel not open - cannot send message")
            return

        message = json.dumps({"type": message_type, **data})
        self.data_channel.send(message)
