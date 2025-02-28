#!/usr/bin/env python3
"""
audio_utils.py

This module provides various audio utility functions that are used across the application.
Functions included:

- prepare_audio_data: Compute the RMS value from raw audio data.
- amplify_audio: Amplify audio data with a specified gain.
- find_default_mic_sample_rate: Retrieve the default microphone's sample rate.
- play_beep: Play a beep sound to indicate state changes.
- init_progress_bar: Initialize a simple visual progress bar for audio silence detection.

These utility functions help standardize audio processing throughout the TARS system.
"""

import sys
import time
import numpy as np
import sounddevice as sd
from typing import Optional, Callable, Tuple

def prepare_audio_data(data: np.ndarray) -> Optional[float]:
    """
    Compute the RMS (root mean square) of the audio data.

    Args:
        data (np.ndarray): A numpy array containing audio samples.

    Returns:
        Optional[float]: The computed RMS value, or None if the audio data is silent or invalid.
    """
    if data.size == 0:
        print("WARNING: Empty audio data received.")
        return None
    data = data.reshape(-1).astype(np.float64)
    data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    data = np.clip(data, -32000, 32000)
    if np.all(data == 0):
        print("WARNING: Audio data is silent or all zeros.")
        return None
    try:
        return np.sqrt(np.mean(np.square(data)))
    except Exception as e:
        print(f"ERROR: RMS calculation failed: {e}")
        return None

def amplify_audio(data: np.ndarray, gain: float) -> np.ndarray:
    """
    Amplify the input audio data using the specified gain.

    Args:
        data (np.ndarray): A numpy array containing audio samples.
        gain (float): The amplification gain to apply.

    Returns:
        np.ndarray: The amplified audio data as a numpy array.
    """
    return np.clip(data * gain, -32768, 32767).astype(np.int16)

def find_default_mic_sample_rate() -> int:
    """
    Retrieve the default microphone's sample rate.

    Returns:
        int: The sample rate in Hz.
    """
    try:
        default_index = sd.default.device[0]
        if default_index is None:
            raise ValueError("No default microphone detected.")
        device_info = sd.query_devices(default_index, kind="input")
        return int(device_info.get("default_samplerate", 16000))
    except Exception as e:
        print(f"ERROR: Unable to determine microphone sample rate: {e}")
        return 16000

def play_beep(frequency: int, duration: float, sample_rate: int, volume: float) -> None:
    """
    Play a beep sound to indicate state changes.

    Args:
        frequency (int): The frequency of the beep in Hz.
        duration (float): The duration of the beep in seconds.
        sample_rate (int): The audio sample rate.
        volume (float): The volume multiplier for the beep.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sine_wave = volume * np.sin(2 * np.pi * frequency * t)
    sd.play(sine_wave, samplerate=sample_rate)
    sd.wait()

def init_progress_bar() -> Tuple[Callable[[int, int], None], Callable[[], None]]:
    """
    Initialize a progress bar that can be used to visually track the audio silence detection.

    Returns:
        Tuple containing:
            - update_progress_bar: Function to update the progress bar.
            - clear_progress_bar: Function to clear the progress bar.
    """
    bar_length = 10  
    show_progress = True

    def flush_all():
        sys.stdout.flush()
        sys.stderr.flush()
        time.sleep(0.01)  # Small delay to ensure flushing

    def update_progress_bar(frames: int, max_frames: int) -> None:
        if show_progress:
            progress = int((frames / max_frames) * bar_length)
            filled = "#" * progress
            empty = "-" * (bar_length - progress)
            bar = f"\r[SILENCE: {filled}{empty}] {frames}/{max_frames}"
            sys.stdout.write(bar)
            sys.stdout.flush()
            flush_all()

    def clear_progress_bar() -> None:
        if show_progress:
            sys.stdout.write("\r" + " " * (bar_length + 30) + "\r")
            sys.stdout.flush()
            flush_all()

    return update_progress_bar, clear_progress_bar