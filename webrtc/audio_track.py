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
        self._stream: Optional[sd.InputStream] = None
        self._running = False

        # Frame counter for timestamps
        self._timestamp = 0
        self._samples_per_frame = int(sample_rate * 0.02)  # 20ms frames

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback from sounddevice when audio is captured"""
        if status:
            logger.warning(f"Mic capture status: {status}")

        # Copy audio data (sounddevice reuses the buffer)
        audio_data = indata.copy()

        # Put in queue (non-blocking)
        try:
            self._queue.put_nowait(audio_data)
        except asyncio.QueueFull:
            pass  # Drop frame if queue is full

    async def start(self):
        """Start capturing from microphone"""
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("sounddevice not available")

        if self._running:
            return

        logger.info(f"Starting microphone capture: {self.sample_rate}Hz, {self.channels}ch")

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

    async def recv(self) -> AudioFrame:
        """
        Receive next audio frame for WebRTC transmission.
        Called by aiortc when it needs audio data.
        """
        if not self._running:
            raise Exception("Microphone not started")

        # Get audio data from queue
        audio_data = await self._queue.get()

        # Convert float32 [-1, 1] to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # Reshape if mono
        if audio_int16.ndim == 1:
            audio_int16 = audio_int16.reshape(-1, 1)

        # Create AudioFrame
        frame = AudioFrame.from_ndarray(
            audio_int16,
            format="s16",
            layout="mono" if self.channels == 1 else "stereo"
        )
        frame.sample_rate = self.sample_rate
        frame.pts = self._timestamp

        # Increment timestamp
        self._timestamp += audio_int16.shape[0]

        return frame
