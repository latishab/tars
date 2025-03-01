import numpy as np
import sounddevice as sd
import sys
from typing import Optional, Tuple

def prepare_audio_data(data: np.ndarray) -> Optional[float]:
    """
    Compute the RMS of the audio data.
    Returns:
        float or None: RMS value or None if invalid.
    """
    if data.size == 0:
        return None
    data = data.reshape(-1).astype(np.float64)
    data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    data = np.clip(data, -32000, 32000)
    if np.all(data == 0):
        return None
    try:
        return np.sqrt(np.mean(np.square(data)))
    except Exception:
        return None

def amplify_audio(data: np.ndarray, amp_gain: float) -> np.ndarray:
    """
    Amplify the input audio data using the configured amplification gain.
    """
    return np.clip(data * amp_gain, -32768, 32767).astype(np.int16)

def find_default_mic_sample_rate() -> int:
    """
    Retrieve the default microphone's sample rate.
    Returns:
        int: The sample rate.
    """
    try:
        default_index = sd.default.device[0]
        if default_index is None:
            raise ValueError("No default microphone detected.")
        device_info = sd.query_devices(default_index, kind="input")
        return int(device_info.get("default_samplerate", 16000))
    except Exception:
        return 16000

def play_beep(frequency: int, duration: float, sample_rate: int, volume: float):
    """
    Play a beep sound to indicate state changes.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sine_wave = volume * np.sin(2 * np.pi * frequency * t)
    sd.play(sine_wave, samplerate=sample_rate)
    sd.wait()

def clear_indicator():
    """Clear the current line in the terminal."""
    sys.stdout.write('\r' + ' ' * 60 + '\r')
    sys.stdout.flush()

def create_spectrum_indicator(rms_level: float, width: int = 30) -> str:
    """
    Create a spectrum-style volume indicator.
    Args:
        rms_level: Normalized RMS level (0.0 to 1.0)
        width: Base width of the indicator in characters
    Returns:
        str: ASCII spectrum indicator
    """
    # Calculate dynamic width based on volume
    dynamic_width = min(width + int(rms_level * 20), 50)  # Max width of 50 chars
    
    # Define characters for different volume levels
    chars = [' ', '░', '▒', '▓', '█']
    
    # Calculate how many blocks to fill
    filled = int(rms_level * dynamic_width)
    
    # Create gradient effect
    indicator = []
    for i in range(dynamic_width):
        if i > filled:
            indicator.append(chars[0])  # Empty
        else:
            # Calculate intensity for gradient effect
            intensity = min(len(chars) - 1, 
                          int((1 - (i / dynamic_width)) * (len(chars) - 1)))
            indicator.append(chars[intensity])
    
    return ''.join(indicator)

def format_speech_indicator(is_speaking: bool, rms_level: float) -> str:
    """
    Format a speech activity indicator with spectrum and handle display.
    Args:
        is_speaking: Whether speech is currently detected
        rms_level: Normalized RMS level (0.0 to 1.0)
    Returns:
        str: Formatted indicator string
    """
    spectrum = create_spectrum_indicator(rms_level)
    status = "[MIC]" if is_speaking else "[---]"
    indicator = f"\r{status} {spectrum}"
    
    # Write and flush the indicator
    sys.stdout.write(indicator)
    sys.stdout.flush()
    
    return indicator 