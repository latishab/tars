"""
TARS Audio Module
Handles microphone input and speaker output via USB soundcard
"""

import numpy as np
import sounddevice as sd
import threading
import queue
import wave
import io
from typing import Optional

class AudioModule:
    def __init__(
        self,
        input_device: Optional[int] = None,
        output_device: Optional[int] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1600,  # 100ms at 16kHz
        dtype: str = 'int16'
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.dtype = dtype

        # Find USB soundcard if not specified
        self.input_device = input_device or self._find_usb_input()
        self.output_device = output_device or self._find_usb_output()

        # Recording state
        self.is_recording = False
        self._record_queue: queue.Queue = queue.Queue()
        self._record_stream: Optional[sd.InputStream] = None

        # Playback state
        self.is_playing = False
        self._play_queue: queue.Queue = queue.Queue()
        self._play_thread: Optional[threading.Thread] = None

        print(f"Audio input device: {self.input_device}")
        print(f"Audio output device: {self.output_device}")

    def _find_usb_input(self) -> Optional[int]:
        """Find USB soundcard input device"""
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            name = dev['name'].lower()
            if dev['max_input_channels'] > 0:
                if 'usb' in name or 'sound' in name:
                    return i
        # Fallback to default
        return sd.default.device[0]

    def _find_usb_output(self) -> Optional[int]:
        """Find USB soundcard output device"""
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            name = dev['name'].lower()
            if dev['max_output_channels'] > 0:
                if 'usb' in name or 'sound' in name:
                    return i
        # Fallback to default
        return sd.default.device[1]

    def get_device_info(self) -> dict:
        """Get info about selected audio devices"""
        info = {"input": None, "output": None}
        try:
            if self.input_device is not None:
                dev = sd.query_devices(self.input_device)
                info["input"] = {"id": self.input_device, "name": dev['name']}
            if self.output_device is not None:
                dev = sd.query_devices(self.output_device)
                info["output"] = {"id": self.output_device, "name": dev['name']}
        except Exception as e:
            info["error"] = str(e)
        return info

    # ============== Recording ==============

    def start_recording(self):
        """Start recording from microphone"""
        if self.is_recording:
            return

        def callback(indata, frames, time, status):
            if status:
                print(f"Recording status: {status}")
            self._record_queue.put(indata.copy())

        self._record_stream = sd.InputStream(
            device=self.input_device,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=self.chunk_size,
            callback=callback
        )
        self._record_stream.start()
        self.is_recording = True
        print("Recording started")

    def stop_recording(self):
        """Stop recording"""
        if not self.is_recording:
            return

        if self._record_stream:
            self._record_stream.stop()
            self._record_stream.close()
            self._record_stream = None

        self.is_recording = False
        # Clear queue
        while not self._record_queue.empty():
            try:
                self._record_queue.get_nowait()
            except queue.Empty:
                break
        print("Recording stopped")

    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """Get next audio chunk from recording queue"""
        try:
            return self._record_queue.get_nowait()
        except queue.Empty:
            return None

    # ============== Playback ==============

    def play_pcm(self, audio_bytes: bytes, sample_rate: int = 24000):
        """Play raw PCM audio bytes"""
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16)

        # Resample if needed
        if sample_rate != self.sample_rate:
            from scipy import signal
            num_samples = int(len(audio_data) * self.sample_rate / sample_rate)
            audio_data = signal.resample(audio_data, num_samples).astype(np.int16)

        self._play_audio(audio_data)

    def play_wav(self, wav_bytes: bytes):
        """Play WAV audio bytes"""
        with io.BytesIO(wav_bytes) as wav_buffer:
            with wave.open(wav_buffer, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                audio_data = np.frombuffer(
                    wav_file.readframes(wav_file.getnframes()),
                    dtype=np.int16
                )

        # Resample if needed
        if sample_rate != self.sample_rate:
            from scipy import signal
            num_samples = int(len(audio_data) * self.sample_rate / sample_rate)
            audio_data = signal.resample(audio_data, num_samples).astype(np.int16)

        self._play_audio(audio_data)

    def _play_audio(self, audio_data: np.ndarray):
        """Internal: play audio array"""
        self.is_playing = True
        try:
            sd.play(audio_data, samplerate=self.sample_rate, device=self.output_device)
            sd.wait()
        finally:
            self.is_playing = False

    def stop_playback(self):
        """Stop any currently playing audio"""
        sd.stop()
        self.is_playing = False

    # ============== Cleanup ==============

    def close(self):
        """Release audio resources"""
        self.stop_recording()
        self.stop_playback()
