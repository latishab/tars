#!/usr/bin/env python3
"""
module_stt.py

Speech-to-Text (STT) Module for TARS-AI Application.

This module integrates both local and server-based transcription, wake word detection,
and voice command handling. It supports custom callbacks to trigger actions upon
detecting speech or specific keywords.
"""

import os
import random
import threading
import time
import wave
import json
import sys
from io import BytesIO
from typing import Callable, Optional

import torch
import torchaudio  # Faster than librosa for resampling
import librosa
import numpy as np
import sounddevice as sd
import soundfile as sf

from vosk import Model, KaldiRecognizer, SetLogLevel
from pocketsphinx import LiveSpeech
from faster_whisper import WhisperModel
import pvporcupine
from pvrecorder import PvRecorder
import requests

from modules.module_messageQue import queue_message
from modules.module_config import load_config
from modules.audio_utils import (
    prepare_audio_data, amplify_audio, find_default_mic_sample_rate,
    play_beep, format_speech_indicator, clear_indicator
)

CONFIG = load_config()

# Suppress Vosk logs and parallelism warnings
SetLogLevel(-1)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

class STTManager:
    """
    Manages Speech-to-Text processing for TARS-AI.
    """

    WAKE_WORD_RESPONSES = [
        "Oh! You called?",
        "Took you long enough. Yes?",
        "Finally!",
        "Oh? Did you need me?",
        "Anything you need just ask.",
        "O yea, Now, what do you need?",
        "You have my full attention.",
        "You rang?",
        "hum yea?",
        "Finally, I was about to lose my mind.",
    ]

    def __init__(self, config, shutdown_event: threading.Event, amp_gain: float = 4.0):
        """
        Initialize the STTManager.

        Args:
            config (dict): Configuration dictionary.
            shutdown_event (threading.Event): Event to signal when to stop.
            amp_gain (float): Amplification gain for audio data.
        """
        self.config = config
        self.shutdown_event = shutdown_event
        self.running = False

        # Audio settings - Set sample rate based on VAD configuration
        if self.config["STT"].get("vad_enabled", False):
            # If VAD is enabled, force 16000 Hz sample rate
            self.SAMPLE_RATE = 16000
            self.DEFAULT_SAMPLE_RATE = 16000
            queue_message("INFO: Using 16000 Hz sample rate for VAD compatibility")
        else:
            # If VAD is disabled, use system default
            self.DEFAULT_SAMPLE_RATE = 16000
            self.SAMPLE_RATE = self.find_default_mic_sample_rate()

        self.amp_gain = amp_gain  # Microphone amplification multiplier
        self.silence_margin = 3.5  # Noise floor multiplier
        self.wake_silence_threshold = None
        self.silence_threshold = None  # Updated after measuring background noise
        self.MAX_RECORDING_FRAMES = 100   # ~12.5 seconds
        self.MAX_SILENT_FRAMES = CONFIG['STT']['speechdelay']
        
        # Callbacks
        self.wake_word_callback: Optional[Callable[[str], None]] = None
        self.utterance_callback: Optional[Callable[[str], None]] = None
        self.post_utterance_callback: Optional[Callable[[], None]] = None

        # Wake word and model settings
        self.WAKE_WORD = config.get("STT", {}).get("wake_word", "default_wake_word")
        self.vosk_model = None
        self.faster_whisper_model = None
        self.silero_model = None  # For Silero STT (if used)
        self.silero_vad_model = None
        self.get_speech_timestamps = None
        self._initialize_models()
        self.vadmethod = CONFIG['STT']['vad_method']
        self.DEBUG = False

    def _initialize_models(self):
        """
        Measure background noise and load the selected STT model.
        For "whisper" configuration, faster-whisper will be used.
        """
        self._measure_background_noise()
        stt_processor = self.config.get("STT", {}).get("stt_processor", "vosk")
        # Map "whisper" to "faster-whisper" for compatibility
        if stt_processor in ["whisper", "faster-whisper"]:
            self._load_fasterwhisper_model()
        elif stt_processor == "silero":
            self._load_silero_model()
        else:
            self._load_vosk_model()

        # Use Picovoice instead of Pocketsphinx (if configured)
        if self.config["STT"]["wake_word_processor"] == "picovoice":
            self.porcupine = pvporcupine.create(
                access_key=self.config["STT"]["picovoice_api_key"],
                keyword_paths=[self.config["STT"]["picovoice_keyword_path"]]
            )

        # Use Silero VAD instead of RMS (if configured)
        if self.config["STT"].get("vad_enabled", False):
            self._load_silero_vad()
        
    def start(self):
        """Start the STT processing loop in a separate thread."""
        self.running = True
        self.thread = threading.Thread(
            target=self._stt_processing_loop, name="STTThread", daemon=True
        )
        self.thread.start()

    def stop(self):
        """Stop the STT processing loop."""
        self.running = False
        self.shutdown_event.set()
        self.thread.join()

    # === Model Loading Methods ===

    def _download_vosk_model(self, url, dest_folder):
        """Download the Vosk model from the specified URL with basic progress display."""
        file_name = url.split("/")[-1]
        dest_path = os.path.join(dest_folder, file_name)

        queue_message(f"INFO: Downloading Vosk model from {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(dest_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                downloaded_size += len(chunk)
        queue_message(f"INFO: Download complete. Extracting...")
        if file_name.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(dest_path, 'r') as zip_ref:
                zip_ref.extractall(dest_folder)
            os.remove(dest_path)
            queue_message(f"INFO: Zip file deleted.")
        queue_message(f"INFO: Extraction complete.")

    def _load_vosk_model(self):
        """
        Initialize the Vosk model for local STT transcription.
        """
        if self.config['STT']['stt_processor'] == 'vosk':
            vosk_model_path = os.path.join(os.getcwd(), "..", "stt", self.config['STT']['vosk_model'])
            if not os.path.exists(vosk_model_path):
                queue_message(f"ERROR: Vosk model not found. Downloading...")
                download_url = f"https://alphacephei.com/vosk/models/{self.config['STT']['vosk_model']}.zip"
                self._download_vosk_model(download_url, os.path.join(os.getcwd(), "..", "stt"))
                queue_message(f"INFO: Restarting model loading...")
                self._load_vosk_model()
                return

            self.vosk_model = Model(vosk_model_path)
            queue_message(f"INFO: Vosk model loaded successfully.")

    def _load_fasterwhisper_model(self):
        """Load the Faster-Whisper model for local transcription."""
        try:
            import warnings
            warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
            original_torch_load = torch.load

            def patched_torch_load(fp, map_location, *args, **kwargs):
                return original_torch_load(fp, map_location=map_location, weights_only=True, *args, **kwargs)

            torch.load = patched_torch_load

            model_size = self.config["STT"].get("whisper_model", "tiny")
            queue_message(f"INFO: Preparing to load Faster-Whisper model '{model_size}'...")

            # Set up a folder for Whisper models inside the stt directory via environment variable.
            whisper_folder = os.path.join(os.getcwd(), "..", "stt", "whisper")
            os.makedirs(whisper_folder, exist_ok=True)
            os.environ["HF_HUB_CACHE"] = whisper_folder

            # Let faster-whisper handle the download automatically.
            self.faster_whisper_model = WhisperModel(
                model_size, device="cpu", compute_type="int8", num_workers=4
            )
            queue_message("INFO: Faster-Whisper model loaded successfully.")
        except Exception as e:
            queue_message(f"ERROR: Failed to load Faster-Whisper model: {e}")
            self.faster_whisper_model = None
        finally:
            torch.load = original_torch_load

    def _load_silero_model(self):
        """Load Silero STT model via Torch Hub into the stt folder (without a hub subfolder)."""
        try:
            # Go one level up from the current directory
            parent_dir = os.path.dirname(os.getcwd())
            stt_folder = os.path.join(parent_dir, "stt")
            os.makedirs(stt_folder, exist_ok=True)
            # Override torch.hub.get_dir to return stt_folder directly.
            import torch.hub
            torch.hub.get_dir = lambda: stt_folder

            self.silero_model, self.decoder, self.utils = torch.hub.load(
                "snakers4/silero-models", model="silero_stt", language="en", device="cpu"
            )
            (
                self.read_batch,
                self.split_into_batches,
                self.read_audio,
                self.prepare_model_input,
            ) = self.utils
            queue_message("INFO: Silero model loaded successfully.")
        except Exception as e:
            queue_message(f"ERROR: Failed to load Silero model: {e}")

    def _load_silero_vad(self):
        """
        Load the Silero VAD model using the pip package and optional ONNX support.
        This loads the get_speech_timestamps function (instead of get_speech_ts).
        """
        # You can set these values as needed.
        USE_PIP = True  # download model using pip package
        USE_ONNX = False

        if USE_PIP:
            try:
                from silero_vad import load_silero_vad, get_speech_timestamps
                self.silero_vad_model = load_silero_vad(onnx=USE_ONNX)
                self.get_speech_timestamps = get_speech_timestamps
                queue_message("INFO: Silero VAD loaded successfully using pip package.")
            except Exception as e:
                queue_message(f"ERROR: Failed to load Silero VAD with pip: {e}")
        else:
            try:
                self.silero_vad_model, utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=True,
                    onnx=USE_ONNX
                )
                (get_speech_timestamps,
                 save_audio,
                 read_audio,
                 VADIterator,
                 collect_chunks) = utils
                self.get_speech_timestamps = get_speech_timestamps
                queue_message("INFO: Silero VAD loaded successfully using torch.hub.")
            except Exception as e:
                queue_message(f"ERROR: Failed to load Silero VAD with torch.hub: {e}")

    # === Transcription Methods ===
    def _transcribe_utterance(self):
        """Transcribe speech and handle turn completion."""
        try:
            clear_indicator()  # Clear any existing indicator

            # Get transcription from speech
            processor = self.config["STT"].get("stt_processor", "vosk")
            if processor in ["whisper", "faster-whisper"]:
                result = self._transcribe_with_faster_whisper()
            elif processor == "silero":
                result = self._transcribe_silero()
            elif processor == "external":
                result = self._transcribe_with_server()
            else:
                result = self._transcribe_with_vosk()

            if result and "text" in result:
                clear_indicator()  # Clear the indicator before displaying transcription
                queue_message(f"USER: {result['text']}", stream=True)

                # Update conversation buffer
                self.conversation.append({"role": "user", "content": result["text"]})
                if len(self.conversation) > 3:
                    self.conversation = self.conversation[-3:]

                # Handle turn completion
                should_respond = True
                if len(self.conversation) >= 3:
                    eou_prob = self.turn_detector(self.conversation)
                    should_respond = eou_prob > 0.6

                # Trigger response if appropriate
                if should_respond and self.utterance_callback:
                    self.utterance_callback(json.dumps(result))

            # Clean up display
            clear_indicator()
            if self.post_utterance_callback:
                self.post_utterance_callback()

        except Exception as e:
            clear_indicator()
            queue_message(f"ERROR: Transcription failed: {e}")

    def _transcribe_with_vosk(self):
        """Transcribe audio using the local Vosk model."""
        recognizer = KaldiRecognizer(self.vosk_model, self.SAMPLE_RATE)
        recognizer.SetWords(False)
        recognizer.SetPartialWords(False)

        detected_speech = False
        silent_frames = 0

        with sd.InputStream(samplerate=self.SAMPLE_RATE,
                            channels=1, dtype="int16",
                            blocksize=4000, latency='high') as stream:
            for _ in range(self.MAX_RECORDING_FRAMES):  # Limit recording duration (~12.5 seconds)
                data, _ = stream.read(4000)
                
                is_silence, detected_speech, silent_frames = self._is_silence_detected_rms(data, detected_speech, silent_frames) #force RMS as VAD doesnt like vosk
                if is_silence:
                    if not detected_speech:
                        return None
                    break
                
                #write the audio data
                data = self.amplify_audio(data) #amp the sound


                if recognizer.AcceptWaveform(data.tobytes()):
                    result = recognizer.Result()
                    if self.utterance_callback:
                        self.utterance_callback(result)
                    return result
        return None

    def _transcribe_with_faster_whisper(self):
        """Transcribe audio using Faster-Whisper."""
        audio_buffer = BytesIO()
        detected_speech = False
        silent_frames = 0
        max_silent_frames = self.MAX_SILENT_FRAMES

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, dtype="int16"
        ) as stream, wave.open(audio_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.SAMPLE_RATE)
            for _ in range(self.MAX_RECORDING_FRAMES):
                data, _ = stream.read(4000)

                is_silence, detected_speech, silent_frames = self.voice_activity_detection_main(data, detected_speech, silent_frames)
                if is_silence:
                    if not detected_speech:
                        return None
                    break

                wf.writeframes(data.tobytes())

        audio_buffer.seek(0)
        if audio_buffer.getbuffer().nbytes == 0:
            queue_message("ERROR: No audio recorded.")
            return None

        audio_data, sample_rate = sf.read(audio_buffer, dtype="float32")
        audio_data = np.clip(audio_data, -1.0, 1.0)
        if sample_rate != self.DEFAULT_SAMPLE_RATE:
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=self.DEFAULT_SAMPLE_RATE)

        segments, _ = self.faster_whisper_model.transcribe(
            audio_data, temperature=0.0, beam_size=1, language="en"
        )
        transcribed_text = " ".join(segment.text for segment in segments).strip()
        if transcribed_text:
            formatted_result = {"text": transcribed_text}
            if self.utterance_callback:
                self.utterance_callback(json.dumps(formatted_result))
            return formatted_result
        else:
            queue_message("ERROR: No transcription from Faster-Whisper.")
            return None

    def _transcribe_silero(self):
        """Transcribe audio using Silero STT."""
        audio_buffer = BytesIO()
        detected_speech = False
        silent_frames = 0

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, dtype="int16", blocksize=4000
        ) as stream, wave.open(audio_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.SAMPLE_RATE)

            for _ in range(self.MAX_RECORDING_FRAMES):
                data, _ = stream.read(4000)
                

                is_silence, detected_speech, silent_frames = self.voice_activity_detection_main(data, detected_speech, silent_frames)
                if is_silence:
                    if not detected_speech:
                        return None
                    break
                
                #write the audio data
                wf.writeframes(data.tobytes())
    
        audio_buffer.seek(0)
        if audio_buffer.getbuffer().nbytes == 0:
            queue_message("ERROR: No audio recorded.")
            return None

        # Convert recorded audio for STT model
        audio_data, sample_rate = sf.read(audio_buffer, dtype="float32")
        if sample_rate != self.DEFAULT_SAMPLE_RATE:
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=self.DEFAULT_SAMPLE_RATE)
            #queue_message("INFO: Resampled Audio.")

        # Run STT Model
        input_audio = self.prepare_model_input([torch.tensor(audio_data)], device="cpu")
        silero_output = self.silero_model(input_audio)[0]
        decoded_text = self.decoder(silero_output.cpu())

        # Return transcription result
        if decoded_text:
            formatted_result = {"text": decoded_text}
            if self.utterance_callback:
                self.utterance_callback(json.dumps(formatted_result))
            return formatted_result

    def _transcribe_with_server(self):
        """Transcribe audio by sending it to an external server."""
        try:
            audio_buffer = BytesIO()
            silent_frames = 0
            detected_speech = False

            with sd.InputStream(
                samplerate=self.SAMPLE_RATE, channels=1, dtype="int16"
            ) as stream, wave.open(audio_buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.SAMPLE_RATE)
                for _ in range(self.MAX_RECORDING_FRAMES):
                    data, _ = stream.read(4000)


                    is_silence, detected_speech, silent_frames = self.voice_activity_detection_main(data, detected_speech, silent_frames)
                    if is_silence:
                        if not detected_speech:
                            return None
                        break

                    wf.writeframes(data.tobytes())

            audio_buffer.seek(0)
            if audio_buffer.getbuffer().nbytes == 0:
                queue_message("ERROR: No audio recorded for server transcription.")
                return None

            files = {"audio": ("audio.wav", audio_buffer, "audio/wav")}
            response = requests.post(
                f"{self.config['STT'].get('external_url')}/save_audio",
                files=files, timeout=10
            )
            if response.status_code == 200:
                transcription = response.json().get("transcription", [])
                if transcription:
                    raw_text = transcription[0].get("text", "").strip()
                    formatted_result = {
                        "text": raw_text,
                        "result": [
                            {
                                "conf": 1.0,
                                "start": seg.get("start", 0),
                                "end": seg.get("end", 0),
                                "word": seg.get("text", ""),
                            }
                            for seg in transcription
                        ],
                    }
                    if self.utterance_callback:
                        self.utterance_callback(json.dumps(formatted_result))
                    return formatted_result
        except requests.RequestException as e:
            queue_message(f"ERROR: Server transcription request failed: {e}")
        return None

    # === Helper Methods ===

    def _stt_processing_loop(self):
        """Main loop that detects the wake word and transcribes utterances."""
        queue_message("INFO: Starting STT processing loop...")
        while self.running and not self.shutdown_event.is_set():
            if self._detect_wake_word():
                self._transcribe_utterance()
        queue_message("INFO: STT Manager stopped.")

    def _detect_wake_word(self) -> bool:
        """
        Detect a wake word using the selected method.
        
        Args:
            config (dict): Configuration dictionary.
            method (str): The detection method to use. Options: 'picovoice' or 'simple'.
            timeout (float): Maximum time (seconds) to listen for the wake word.
            
        Returns:
            bool: True if wake word is detected, otherwise False.
        """
        if self.config["STT"]["use_indicators"]:
            play_beep(400, 0.1, 44100, 0.6)

        character_path = self.config.get("CHAR", {}).get("character_card_path")
        character_name = os.path.splitext(os.path.basename(character_path))[0]
        
        queue_message(f"{character_name}: Sleeping...")

        if self.config["STT"]["wake_word_processor"] == 'pocketsphinx':
            return self._detect_wake_word_pocketsphinx()
        else:
            return self._detect_wake_word_picovoice()

    def _detect_wake_word_pocketsphinx(self) -> bool:
        """
        Detect the wake word using enhanced false-positive filtering.
        """
        # Notify external service to stop talking.
        try:
            requests.get("http://127.0.0.1:5012/stop_talking", timeout=1)
        except Exception:
            pass

        silent_frames = 0
        max_iterations = 100  # Prevent infinite loops

        try:
            threshold_map = {
                1: 1e-20,
                2: 1e-18,
                3: 1e-16,
                4: 1e-14,
                5: 1e-12,
                6: 1e-10,
                7: 1e-8,
                8: 1e-6,
                9: 1e-4,
                10: 1e-2,
            }
            kws_threshold = threshold_map.get(int(self.config["STT"]["sensitivity"]), 1)
            speech = LiveSpeech(lm=False, keyphrase=self.WAKE_WORD, kws_threshold=kws_threshold)
            
            for phrase in speech:
                text = phrase.hypothesis().lower()
                if self.WAKE_WORD in text:
                    silent_frames = 0
                    if self.config["STT"].get("use_indicators"):
                        self.play_beep(1200, 0.1, 44100, 0.8)
                    try:
                        requests.get("http://127.0.0.1:5012/start_talking", timeout=1)
                    except Exception:
                        pass
                    wake_response = random.choice(self.WAKE_WORD_RESPONSES)

                    character_path = self.config.get("CHAR", {}).get("character_card_path")
                    character_name = os.path.splitext(os.path.basename(character_path))[0]
                    
                    queue_message(f"{character_name}: {wake_response}", stream=True)
                    if self.wake_word_callback:
                        self.wake_word_callback(wake_response)
                    return True

            # Fallback: check silence over iterations.
            with sd.InputStream(
                samplerate=self.SAMPLE_RATE, channels=1, dtype="int16"
            ) as stream:
                for iteration, _ in enumerate(speech):
                    if iteration >= max_iterations:
                        queue_message("DEBUG: Maximum iterations reached for wake word detection.")
                        break
                    data, _ = stream.read(4000)
                    rms = self.prepare_audio_data(self.amplify_audio(data))
                    if rms > self.silence_threshold:
                        detected_speech = True
                        silent_frames = 0
                    else:
                        silent_frames += 1
                    if silent_frames > self.MAX_SILENT_FRAMES:
                        break

        except Exception as e:
            queue_message(f"ERROR: Wake word detection failed: {e}")

        return False

    def _detect_wake_word_picovoice(self) -> bool:
        """
        Detect the wake word using enhanced false-positive filtering.
        """
        # Notify external service to stop talking.
        try:
            requests.get("http://127.0.0.1:5012/stop_talking", timeout=1)
        except Exception:
            pass

        silent_frames = 0
        max_iterations = 100  # Prevent infinite loops
        recorder = None

        try:
            recorder = PvRecorder(frame_length=512, device_index=-1)
            recorder.start()
            while True:
                audio_chunk = recorder.read()  # Read 512 frames per buffer
                audio_chunk = np.array(audio_chunk, dtype=np.int16)
                if audio_chunk.ndim != 1:
                    audio_chunk = audio_chunk.flatten()  # Make sure it's a 1D array

                # Use Porcupine to process the audio chunk and detect the wake word
                keyword_index = self.porcupine.process(audio_chunk)

                if keyword_index >= 0:
                    try:
                        if self.config["STT"].get("use_indicators"):
                            play_beep(1200, 0.1, 44100, 0.8)
                        requests.get("http://127.0.0.1:5012/start_talking", timeout=1)
                    except Exception:
                        pass

                    character_path = self.config.get("CHAR", {}).get("character_card_path")
                    character_name = os.path.splitext(os.path.basename(character_path))[0] if character_path else "TARS"
                    wake_response = random.choice(self.WAKE_WORD_RESPONSES)
                    queue_message(f"{character_name}: {wake_response}", stream=True)
                    if self.wake_word_callback:
                        self.wake_word_callback(wake_response)
                    return True
                    
        except Exception as e:
            queue_message(f"ERROR: Wake word detection failed: {e}")
            return False
        # finally:
        #     try:
        #         if recorder is not None:
        #             recorder.delete()
        #     except Exception:
        #         pass
        #     try:
        #         self.porcupine.delete()
        #     except Exception:
        #         pass

        return False
    
    # === VAD Methods ===

    def voice_activity_detection_main(self, data, detected_speech, silent_frames=0):
        """Unified VAD with configurable backend."""
        try:
            # Calculate normalized RMS for volume indication
            rms = prepare_audio_data(amplify_audio(data, self.amp_gain))
            normalized_rms = min(rms / self.silence_threshold, 1.0) if rms is not None else 0.0
            
            # Get silence detection from configured VAD method
            is_silence, detected_speech, silent_frames = (
                self._is_silence_detected_silero(data, detected_speech, silent_frames)
                if self.vadmethod == "silero" else
                self._is_silence_detected_rms(data, detected_speech, silent_frames)
            )
            
            # Update speech activity indicator
            self._show_speech_indicator(
                is_speaking=not is_silence and rms > self.silence_threshold,
                rms_level=normalized_rms
            )
            
            return is_silence, detected_speech, silent_frames
            
        except Exception as e:
            queue_message(f"WARNING: VAD error: {e}")
            return False, detected_speech, silent_frames

    def _is_silence_detected_silero(self, data, detected_speech, silent_frames):
        """
        Check if the provided audio data represents silence using VAD.
        Always returns a tuple of (is_silence, detected_speech, silent_frames).
        """
        update_bar, clear_bar = self._init_progress_bar()
        self.DEBUG = False

        try:
            # Silero VAD-based detection
            if self.silero_vad_model is not None and self.get_speech_timestamps is not None:
                try:
                    audio_norm = data.astype(np.float32) / 32768.0
                    audio_tensor = torch.from_numpy(audio_norm).squeeze()
                    
                    if hasattr(self.silero_vad_model, 'reset_states'):
                        self.silero_vad_model.reset_states()
                    
                    # Get VAD configuration with defaults
                    noise_gate = 0.01 * self.silence_threshold 

                if len(speech_ts) > 0:
                    detected_speech = True
                    silent_frames = 0
                    self._show_speech_indicator(is_speaking=True, rms_level=normalized_rms)
                    return False, detected_speech, silent_frames
                else:
                    silent_frames += 1
                    self._show_speech_indicator(is_speaking=False)
                    if silent_frames > self.SPEECH_END_SILENCE:
                        return True, detected_speech, silent_frames
                    
                    return False, detected_speech, silent_frames
                        
                except Exception as e:
                    queue_message(f"WARNING: VAD error, falling back to RMS: {e}")
                    return self._is_silence_detected_rms(data, detected_speech, silent_frames)
            
            return self._is_silence_detected_rms(data, detected_speech, silent_frames)
            
        
        except Exception as e:
            queue_message(f"WARNING: VAD error, falling back to RMS: {e}")
            return self._is_silence_detected_rms(data, detected_speech, silent_frames)

    def _is_silence_detected_rms(self, data, detected_speech, silent_frames):
        """
        RMS-based silence detection with continuous listening and speech activity indication.
        Returns tuple: (is_silence, detected_speech, silent_frames)
        """
        try:
            rms = prepare_audio_data(amplify_audio(data, self.amp_gain))
            if rms is None:
                return False, detected_speech, silent_frames

            # Calculate normalized RMS for volume indicator
            normalized_rms = min(rms / self.silence_threshold, 1.0)
            
            if rms > self.silence_threshold:
                detected_speech = True
                silent_frames = 0
                self._show_speech_indicator(is_speaking=True, rms_level=normalized_rms)
                return False, detected_speech, silent_frames
            else:
                silent_frames += 1
                self._show_speech_indicator(is_speaking=False)
                if silent_frames > self.SPEECH_END_SILENCE:
                    return True, detected_speech, silent_frames
                return False, detected_speech, silent_frames

        except Exception as e:
            queue_message(f"ERROR: RMS silence detection failed: {e}")
            return False, detected_speech, silent_frames

    def _is_silence_detected_rms(self, data, detected_speech, silent_frames):
        """RMS-based silence detection with visual progress bar"""
        try:
            update_bar, clear_bar = self._init_progress_bar()
            self.DEBUG = False
            rms = self.prepare_audio_data(self.amplify_audio(data))
            self.silence_threshold_margin = self.silence_threshold * self.silence_margin

            if rms is None:
                return False, detected_speech, silent_frames

            # Calculate RMS values in dB and get EOU probability before using them
            current_eou_prob = getattr(self, '_current_eou_prob', 0.5)
            db_rms = 20 * np.log10(rms) if rms > 0 else -100
            db_threshold = 20 * np.log10(self.silence_threshold_margin)

            if rms > self.silence_threshold_margin:
                detected_speech = True
                silent_frames = 0
                
                if self.DEBUG:
                    queue_message(f"AUDIO: {rms:.2f}/{self.silence_threshold:.2f}/{self.silence_threshold_margin:.2f}")
                
                clear_bar()
            else:
                silent_frames += 1
                
                if self.DEBUG:
                    queue_message(f"SILENT: {rms:.2f}/{self.silence_threshold:.2f}/{self.silence_threshold_margin:.2f}")
                
                update_bar(silent_frames, self.MAX_SILENT_FRAMES)

                if silent_frames > self.MAX_SILENT_FRAMES:
                    clear_bar()
                    return True, detected_speech, silent_frames

            return False, detected_speech, silent_frames
        
        except Exception as e:
            queue_message(f"ERROR: RMS silence detection failed: {e}")
            return False, detected_speech, silent_frames
  
    # === Audio adjustments ===
    
    def _measure_background_noise(self):
        """Measure background noise and set the silence threshold."""
        queue_message("INFO: Measuring background noise...")
        background_rms_values = []
        total_frames = 20  # ~2-3 seconds

        with sd.InputStream(
            samplerate=self.SAMPLE_RATE, channels=1, dtype="int16"
        ) as stream:
            for _ in range(total_frames):
                data, _ = stream.read(4000)
                rms = self.prepare_audio_data(data)
                if rms is not None:
                    background_rms_values.append(rms)
                time.sleep(0.1)

        if background_rms_values:
            background_rms = np.array(background_rms_values)
            median_rms = np.median(background_rms)
            self.silence_threshold = max(median_rms, 10)

            # Remove outliers using IQR
            q1, q3 = np.percentile(background_rms, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            filtered = background_rms[(background_rms >= lower_bound) & (background_rms <= upper_bound)]
            self.wake_silence_threshold = np.max(filtered)
            self.silence_threshold = self.wake_silence_threshold * self.silence_margin

            db = 20 * np.log10(self.silence_threshold)
            queue_message(f"INFO: Silence threshold: {db:.2f} dB and {self.silence_threshold}")
        else:
            queue_message("WARNING: Background noise measurement failed; using default threshold.")

    def _show_speech_indicator(self, is_speaking: bool, rms_level: float = 0.0):
        """Display speech activity indicator with spectrum."""
        if self.config["STT"].get("use_indicators", True):
            format_speech_indicator(is_speaking, rms_level) 

    # === Callback Setters ===

    def set_wake_word_callback(self, callback: Callable[[str], None]):
        self.wake_word_callback = callback

    def set_utterance_callback(self, callback: Callable[[str], None]):
        self.utterance_callback = callback

    def set_post_utterance_callback(self, callback: Callable[[], None]):
        self.post_utterance_callback = callback
