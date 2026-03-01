"""
Microphone audio track for WebRTC
Captures audio from USB soundcard and streams to host computer
"""

import asyncio
import numpy as np
from typing import Optional
from loguru import logger

from aiortc import MediaStreamTrack
from av import AudioFrame

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    logger.warning("sounddevice not available - microphone capture disabled")


class MicrophoneTrack(MediaStreamTrack):
    """
    WebRTC audio track that captures from microphone.

    Captures PCM audio at 16kHz mono and packages it for WebRTC transmission.
    """

    kind = "audio"

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device: Optional[str] = None,
    ):
        super().__init__()

        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device

        # Audio buffer
        self._queue = asyncio.Queue(maxsize=100)
        self._loop = None
        self._stream: Optional[sd.InputStream] = None
        self._running = False

        # Frame counter for timestamps
        self._timestamp = 0
        self._samples_per_frame = int(sample_rate * 0.02)  # 20ms frames

        self._muted: bool = False

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback from sounddevice when audio is captured"""
        if status:
            logger.warning(f"Mic capture status: {status}")

        # Copy audio data (sounddevice reuses the buffer)
        audio_data = indata.copy()

        # put_nowait must be called from the asyncio thread — use call_soon_threadsafe
        try:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, audio_data)
        except Exception:
            pass  # Drop frame if queue is full or loop is closed

    async def start(self):
        """Start capturing from microphone"""
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("sounddevice not available")

        if self._running:
            return

        logger.info(f"Starting microphone capture: {self.sample_rate}Hz, {self.channels}ch")

        self._loop = asyncio.get_event_loop()
        self._stream = sd.InputStream(
            device=self.device,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=np.float32,
            blocksize=self._samples_per_frame,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._running = True

        logger.info(f"Microphone started: device={self._stream.device}")

    async def stop(self):
        """Stop capturing"""
        if not self._running:
            return

        self._running = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        logger.info("Microphone stopped")

    def mute(self, muted: bool) -> None:
        self._muted = muted

    async def recv(self) -> AudioFrame:
        """
        Receive next audio frame for WebRTC transmission.
        Called by aiortc when it needs audio data.
        """

        # Wait for mic to start — aiortc calls recv() before connectionstatechange fires
        waited = 0
        while not self._running:
            await asyncio.sleep(0.05)
            waited += 1
            if waited == 1:
                logger.debug(f"[MicTrack] recv() waiting for start...")

        # Get audio data from queue; drain while muted to prevent queue fill
        _got = getattr(self, "_recv_count", 0) + 1
        self._recv_count = _got
        if _got <= 3 or _got % 200 == 0:
            logger.debug(f"[MicTrack] recv() #{_got}, queue size={self._queue.qsize()}")
        while True:
            audio_data = await self._queue.get()
            if not self._muted:
                break
            # discard frame — mic is muted, keep draining to avoid queue fill

        # Convert float32 [-1, 1] to int16, flatten to 1D (s16 interleaved)
        audio_int16 = (audio_data * 32768).astype(np.int16).flatten()
        samples = len(audio_int16) // self.channels

        # aiortc Opus encoder requires s16 (interleaved) format
        frame = AudioFrame.from_ndarray(
            audio_int16.reshape(1, -1),
            format="s16",
            layout="mono" if self.channels == 1 else "stereo"
        )
        frame.sample_rate = self.sample_rate
        frame.pts = self._timestamp

        # Increment timestamp
        self._timestamp += samples

        return frame
