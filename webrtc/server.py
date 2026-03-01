"""
WebRTC server for TARS robot (Raspberry Pi)

The RPi runs as a WebRTC server, waiting for connections from the MacBook.
This allows the robot to be self-contained and ready to accept connections
from multiple potential AI brains.

Architecture:
- RPi boots up and waits for connections
- MacBook creates SDP offer and sends to POST /api/offer
- RPi responds with SDP answer
- WebRTC P2P connection established
- Audio flows: RPi mic → MacBook, MacBook TTS → RPi speaker
- DataChannel for state synchronization
"""

import asyncio
import time
import json
from typing import Optional, Callable, Dict
from loguru import logger

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
    from aiortc.contrib.media import MediaRelay
    from aiortc.rtcrtpreceiver import RTCRtpReceiver
    from aiortc.jitterbuffer import JitterBuffer
    # Reduce audio jitter buffer prefetch from 4 packets (80ms) to 1 packet (20ms).
    # Safe for LAN/Tailscale where packet reordering is rare.
    _orig_rtp_receiver_init = RTCRtpReceiver.__init__
    def _patched_rtp_receiver_init(self, kind, transport):
        _orig_rtp_receiver_init(self, kind, transport)
        if kind == "audio":
            jb = JitterBuffer(capacity=16, prefetch=1)
            self.__dict__["_RTCRtpReceiver__jitter_buffer"] = jb
            # Log inside the patch so we know it fired for a real receiver, not just at import.
            logger.info(f"[JitterPatch] ✓ Applied to audio receiver: prefetch={jb._prefetch} capacity={jb._capacity}")
    RTCRtpReceiver.__init__ = _patched_rtp_receiver_init
    logger.info("[JitterPatch] Monkey-patch installed — will confirm when first audio receiver is created")
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    logger.warning("aiortc not available - WebRTC server disabled")

from .audio_track import MicrophoneTrack
from .audio_output import SpeakerOutput
import numpy as np


class WebRTCServer:
    """
    WebRTC server that accepts connections from host computers.

    The RPi is self-contained and waits for AI brains to connect.
    Handles:
    - Audio capture from microphone → send to client
    - Audio playback from client → speaker
    - Data channel for bidirectional state sync
    """

    def __init__(
        self,
        on_state_change: Optional[Callable[[str], None]] = None,
        on_emotion: Optional[Callable[[str], None]] = None,
        on_audio_level: Optional[Callable[[float, str], None]] = None,
        on_connected: Optional[Callable[[], None]] = None,
        on_disconnected: Optional[Callable[[], None]] = None,
        on_camera_log: Optional[Callable[[str], None]] = None,
    ):
        if not AIORTC_AVAILABLE:
            raise RuntimeError("aiortc not installed - cannot use WebRTC")

        # Callbacks
        self.on_state_change = on_state_change
        self.on_emotion = on_emotion
        self.on_audio_level = on_audio_level
        self.on_connected = on_connected
        self.on_disconnected = on_disconnected
        self.on_camera_log = on_camera_log

        # WebRTC components
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.mic_track: Optional[MicrophoneTrack] = None
        self.speaker: Optional[SpeakerOutput] = None
        self.data_channel: Optional = None
        self.relay = MediaRelay()

        # State
        self._running = False
        self._connection_id = 0

    @property
    def is_connected(self) -> bool:
        """Check if any peer is connected"""
        return any(
            pc.connectionState == "connected"
            for pc in self.peer_connections.values()
        )

    async def start(self):
        """Start the WebRTC server (prepare audio devices)"""
        if self._running:
            return

        logger.info("Starting WebRTC server...")

        # Initialize audio
        self.mic_track = MicrophoneTrack()
        self.speaker = SpeakerOutput(sample_rate=48000)

        self._running = True
        logger.info("✓ WebRTC server ready (waiting for connections)")

    async def handle_offer(self, offer_sdp: str, offer_type: str) -> dict:
        """
        Handle incoming SDP offer from client.

        This is called when POST /api/offer receives a connection request.
        Returns SDP answer to complete the WebRTC handshake.
        """
        if not self._running:
            raise RuntimeError("WebRTC server not started")

        # Generate connection ID
        self._connection_id += 1
        conn_id = f"conn_{self._connection_id}"

        logger.info(f"Processing offer from client [{conn_id}]")

        # Create peer connection
        pc = RTCPeerConnection(
            configuration=RTCConfiguration(
                iceServers=[RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
            )
        )
        self.peer_connections[conn_id] = pc

        # Add microphone track (RPi → MacBook)
        if self.mic_track:
            pc.addTrack(self.mic_track)
            logger.debug(f"Added microphone track to [{conn_id}]")

        # Handle incoming audio track (MacBook TTS → RPi speaker)
        @pc.on("track")
        async def on_track(track):
            if track.kind == "audio":
                logger.info(f"Receiving audio track from [{conn_id}]")
                asyncio.create_task(self._handle_audio_track(track, conn_id))

        # Handle data channel (state sync)
        @pc.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"Data channel opened: {channel.label} [{conn_id}]")
            self.data_channel = channel

            @channel.on("message")
            def on_message(message):
                self._handle_data_message(message, conn_id)

            @channel.on("close")
            def on_close():
                logger.info(f"Data channel closed [{conn_id}]")

        # Connection state monitoring
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            state = pc.connectionState
            logger.info(f"WebRTC connection state: {state} [{conn_id}]")

            if state == "connected":
                # Start audio devices
                await self.mic_track.start()
                self.speaker.start()

                if self.on_connected:
                    self.on_connected()

                logger.info(f"✓ Client connected [{conn_id}]")

            elif state in ["failed", "closed"]:
                # Stop audio if no other connections
                if not self.is_connected:
                    await self.mic_track.stop()
                    self.speaker.stop()

                    if self.on_disconnected:
                        self.on_disconnected()

                # Clean up peer connection
                if conn_id in self.peer_connections:
                    del self.peer_connections[conn_id]

                logger.info(f"✗ Client disconnected [{conn_id}]")

        # Process offer
        try:
            offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
            await pc.setRemoteDescription(offer)

            # Create answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            logger.info(f"Created answer for [{conn_id}]")

            return {
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type
            }

        except Exception as e:
            import traceback
            logger.error(f"Failed to process offer [{conn_id}]: {e}")
            logger.error(traceback.format_exc())
            if conn_id in self.peer_connections:
                await self.peer_connections[conn_id].close()
                del self.peer_connections[conn_id]
            raise

    async def _handle_audio_track(self, track, conn_id: str):
        """Process incoming TTS audio from MacBook"""
        logger.info(f"Started audio track handler [{conn_id}]")
        _silence_frames = 0
        _SILENCE_THRESHOLD = 50  # rms threshold (int16 scale)

        while self._running:
            try:
                frame = await track.recv()

                audio_array = frame.to_ndarray()
                fmt = frame.format.name
                incoming_rate = frame.sample_rate or 48000
                is_float = fmt.startswith("flt") or fmt.startswith("dbl")

                channels = len(frame.layout.channels)
                if channels > 1:
                    if fmt.endswith("p"):
                        audio_array = audio_array.mean(axis=0)
                    else:
                        audio_array = audio_array.reshape(-1, channels).mean(axis=1)
                else:
                    audio_array = audio_array.flatten()

                if is_float:
                    audio_int16 = (audio_array * 32768).astype(np.int16)
                else:
                    audio_int16 = audio_array.flatten().astype(np.int16)

                # Decimate to speaker rate if needed (Opus decodes at 48kHz)
                if self.speaker and incoming_rate != self.speaker.sample_rate:
                    ratio = incoming_rate // self.speaker.sample_rate
                    if ratio > 1:
                        audio_int16 = audio_int16[::ratio]

                if self.speaker:
                    rms = int(np.sqrt(np.mean(audio_int16.astype(np.float32) ** 2)))
                    if rms < _SILENCE_THRESHOLD:
                        _silence_frames += 1
                    else:
                        if _silence_frames >= 3:
                            logger.info(f"[AudioDiag] First non-silence frame after {_silence_frames} silence frames — play start")
                        _silence_frames = 0
                    self.speaker.play(audio_int16.tobytes())

            except Exception as e:
                if "MediaStreamError" not in str(type(e)):
                    logger.error(f"Audio track error [{conn_id}]: {e}")
                break

        logger.info(f"Audio track handler stopped [{conn_id}]")

    def _handle_data_message(self, message: str, conn_id: str):
        """Handle messages from MacBook via DataChannel"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            logger.debug(f"Data channel message [{conn_id}]: {msg_type}")

            # Dispatch to appropriate handler
            if msg_type == "eye_state" and self.on_state_change:
                self.on_state_change(data.get("state", "idle"))

            elif msg_type == "emotion" and self.on_emotion:
                self.on_emotion(data.get("value", "default"))

            elif msg_type == "audio_level" and self.on_audio_level:
                self.on_audio_level(data.get("level", 0), data.get("source", "none"))

            elif msg_type == "tts_state":
                # TTS speaking state
                speaking = data.get("speaking", False)
                if self.on_state_change:
                    self.on_state_change("speaking" if speaking else "idle")

            elif msg_type == "transcript":
                # Could be logged or displayed
                role = data.get("role", "unknown")
                text = data.get("text", "")
                logger.info(f"Transcript [{role}]: {text[:50]}...")

            elif msg_type == "camera_log" and self.on_camera_log:
                self.on_camera_log(data.get("text", ""))

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in data channel [{conn_id}]: {message}")
        except Exception as e:
            logger.error(f"Error handling data message [{conn_id}]: {e}")

    def send_message(self, message_type: str, data: dict):
        """Send message to all connected clients via data channel"""
        if not self.data_channel or self.data_channel.readyState != "open":
            logger.debug("Data channel not open - cannot send message")
            return

        message = json.dumps({"type": message_type, **data})
        try:
            self.data_channel.send(message)
            logger.debug(f"Sent data channel message: {message_type}")
        except Exception as e:
            logger.error(f"Failed to send data channel message: {e}")

    async def stop(self):
        """Stop the WebRTC server and close all connections"""
        logger.info("Stopping WebRTC server...")
        self._running = False

        # Close all peer connections
        for conn_id, pc in list(self.peer_connections.items()):
            try:
                await pc.close()
            except Exception as e:
                logger.error(f"Error closing peer connection [{conn_id}]: {e}")

        self.peer_connections.clear()

        # Stop audio
        if self.mic_track:
            await self.mic_track.stop()
        if self.speaker:
            self.speaker.stop()

        logger.info("✓ WebRTC server stopped")
