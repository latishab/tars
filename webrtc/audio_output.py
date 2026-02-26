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
    Uses a write-loop thread with sd.OutputStream.write() which blocks at
    real-time pace, preventing buffer overflow regardless of how fast TTS
    chunks arrive.
    """

    def __init__(
        self,
        sample_rate: int = 24000,
        channels: int = 1,
        device: Optional[str] = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device

        self._queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def _play_loop(self):
        """Background thread: drains queue and writes to sounddevice stream."""
        try:
            with sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                device=self.device,
                latency="low",
            ) as stream:
                logger.info(f"Speaker stream opened: device={stream.device}, rate={self.sample_rate}Hz")
                while self._running:
                    try:
                        audio_float = self._queue.get(timeout=0.05)
                        if audio_float is None:
                            break
        
                        stream.write(audio_float)
                    except queue.Empty:
                        pass
        except Exception as e:
            logger.error(f"Speaker play loop error: {e}")
        logger.info("Speaker play loop stopped")

    def start(self):
        """Start speaker output."""
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("sounddevice not available")

        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._play_loop, daemon=True)
        self._thread.start()
        logger.info(f"Speaker started: {self.sample_rate}Hz, {self.channels}ch")

    def stop(self):
        """Stop speaker output."""
        if not self._running:
            return

        self._running = False
        self._queue.put(None)  # unblock the loop

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        # Drain queue
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

        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / 32768.0
        audio_float = audio_float.reshape(-1, self.channels)

        self._queue.put(audio_float)

    @property
    def is_playing(self) -> bool:
        return self._running and not self._queue.empty()
