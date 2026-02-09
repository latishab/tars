"""
Speaker audio output for WebRTC
Plays TTS audio received from host computer through USB soundcard
"""

import queue
import threading
import numpy as np
from typing import Optional
from loguru import logger

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    logger.warning("sounddevice not available - speaker playback disabled")


class SpeakerOutput:
    """
    Plays audio through speaker.

    Receives audio data from WebRTC and plays it through the USB soundcard.
    Uses a queue to buffer audio and prevent underruns.
    """

    def __init__(
        self,
        sample_rate: int = 24000,
        channels: int = 1,
        device: Optional[str] = None,
        buffer_size: int = 10,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device

        # Audio queue
        self._queue = queue.Queue(maxsize=buffer_size)
        self._stream: Optional[sd.OutputStream] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _audio_callback(self, outdata, frames, time_info, status):
        """Callback from sounddevice when audio is needed"""
        if status:
            logger.warning(f"Speaker playback status: {status}")

        try:
            # Get audio from queue
            data = self._queue.get_nowait()

            # Ensure correct shape
            if data.shape[0] < frames:
                # Pad with zeros if not enough data
                padding = np.zeros((frames - data.shape[0], self.channels), dtype=np.float32)
                data = np.vstack([data, padding])
            elif data.shape[0] > frames:
                # Truncate if too much data
                data = data[:frames]

            outdata[:] = data

        except queue.Empty:
            # No audio available - output silence
            outdata[:] = np.zeros((frames, self.channels), dtype=np.float32)

    def start(self):
        """Start speaker output"""
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("sounddevice not available")

        if self._running:
            return

        logger.info(f"Starting speaker output: {self.sample_rate}Hz, {self.channels}ch")

        self._stream = sd.OutputStream(
            device=self.device,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=np.float32,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._running = True

        logger.info(f"Speaker started: device={self._stream.device}")

    def stop(self):
        """Stop speaker output"""
        if not self._running:
            return

        self._running = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Clear queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

        logger.info("Speaker stopped")

    def play(self, audio_bytes: bytes):
        """
        Queue audio for playback.

        Args:
            audio_bytes: PCM audio data (int16 format)
        """
        if not self._running:
            logger.warning("Speaker not started - cannot play audio")
            return

        # Convert bytes to numpy array
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)

        # Convert to float32 [-1, 1]
        audio_float = audio_int16.astype(np.float32) / 32768.0

        # Reshape for channels
        if self.channels == 1:
            audio_float = audio_float.reshape(-1, 1)
        else:
            audio_float = audio_float.reshape(-1, self.channels)

        # Add to queue (non-blocking)
        try:
            self._queue.put_nowait(audio_float)
        except queue.Full:
            logger.warning("Speaker queue full - dropping audio")

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        return self._running and not self._queue.empty()
