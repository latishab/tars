"""
Speaker audio output for WebRTC
Plays TTS audio received from host computer through USB soundcard
"""

import queue
import threading
import time
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
    Plays audio through speaker via a callback-based OutputStream.

    The callback runs on the hardware clock every blocksize samples.
    It reads from a queue; if empty, outputs silence. This means enqueuing
    silence frames (from WebRTC keepalive) never creates a backlog — the
    callback drains at real-time regardless of how fast play() is called.
    """

    BLOCK_SIZE = 960  # 20ms at 48kHz, matches WebRTC frame size

    def __init__(
        self,
        sample_rate: int = 24000,
        channels: int = 1,
        device: Optional[str] = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device

        self._queue: queue.Queue = queue.Queue(maxsize=1000)  # ~20s at 20ms/frame
        self._stream: Optional[sd.OutputStream] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

        # Diagnostics
        self._prev_was_silence = True
        self._silence_cb_count = 0

    def _audio_callback(self, outdata, frames, time_info, status):
        """Called by sounddevice on the hardware clock every `frames` samples."""
        if status:
            logger.warning(f"[AudioDiag] OutputStream status: {status}")

        try:
            data = self._queue.get_nowait()
            if self._prev_was_silence:
                logger.info(
                    f"[AudioDiag] callback: first non-silence, "
                    f"queue_depth={self._queue.qsize()}, "
                    f"silence_blocks_skipped={self._silence_cb_count}"
                )
                self._prev_was_silence = False
                self._silence_cb_count = 0

            # Pad or trim to exact frame size
            if len(data) < frames:
                data = np.pad(data, ((0, frames - len(data)), (0, 0)))
            elif len(data) > frames:
                data = data[:frames]
            outdata[:] = data

        except queue.Empty:
            outdata.fill(0)  # hardware clock ticks — output silence, no backlog
            self._prev_was_silence = True
            self._silence_cb_count += 1

    def _run_stream(self):
        """Background thread that keeps the OutputStream open."""
        try:
            with sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                device=self.device,
                blocksize=self.BLOCK_SIZE,
                latency="low",
                callback=self._audio_callback,
            ) as stream:
                logger.info(
                    f"[AudioDiag] Speaker stream opened (callback): "
                    f"device={stream.device}, rate={self.sample_rate}Hz, "
                    f"latency={stream.latency*1000:.1f}ms, blocksize={self.BLOCK_SIZE}"
                )
                while self._running:
                    time.sleep(0.05)
        except Exception as e:
            logger.error(f"Speaker stream error: {e}")
        logger.info("Speaker stream stopped")

    def start(self):
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("sounddevice not available")
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_stream, daemon=True)
        self._thread.start()
        logger.info(f"Speaker started: {self.sample_rate}Hz, {self.channels}ch (callback mode)")

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
        logger.info("Speaker stopped")

    def flush(self):
        """Discard queued audio (e.g. on interruption)."""
        drained = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                drained += 1
            except queue.Empty:
                break
        if drained:
            logger.info(f"[AudioDiag] Speaker queue flushed: {drained} frames discarded")

    def play(self, audio_bytes: bytes):
        """Queue audio for playback. Non-blocking: drops frames if queue is full."""
        if not self._running:
            logger.warning("Speaker not started - cannot play audio")
            return

        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / 32768.0
        audio_float = audio_float.reshape(-1, self.channels)

        try:
            self._queue.put_nowait(audio_float)
        except queue.Full:
            logger.warning("[AudioDiag] Speaker queue full — dropping frame")

    @property
    def is_playing(self) -> bool:
        return self._running and not self._queue.empty()
