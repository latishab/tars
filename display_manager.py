"""
TARS Display Manager
Coordinates between eyes and spectrum modes
"""

import pygame
import threading
import time
from enum import Enum
from typing import Optional
from dataclasses import dataclass
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modules.modules_roboeyes import RoboEyes, Mood, EyeState
from modules.modules_spectrum import SpectrumVisualizer


class DisplayMode(Enum):
    EYES = "eyes"
    SPECTRUM = "spectrum"
    OFF = "off"


@dataclass
class DisplayState:
    mode: DisplayMode = DisplayMode.EYES
    eye_state: str = "idle"
    emotion: str = "default"
    audio_level: float = 0.0
    audio_source: str = "none"
    face_detected: bool = False
    face_x: float = 0.0
    face_y: float = 0.0


class DisplayManager:
    """Manages TARS display - switches between eyes and spectrum"""

    def __init__(self, width: int = 800, height: int = 480):
        self.width = width
        self.height = height
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # State
        self.state = DisplayState()

        # Modules (initialized in _run)
        self.eyes: Optional[RoboEyes] = None
        self.spectrum: Optional[SpectrumVisualizer] = None

        # Colors
        self.bg_color = (13, 17, 23)  # #0d1117

    def start(self):
        """Start display thread"""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop display"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    # ========== Mode Control ==========

    def set_mode(self, mode: str):
        with self._lock:
            self.state.mode = DisplayMode(mode)

    # ========== Eyes Control ==========

    def set_eye_state(self, state: str):
        """Set eye state: idle, listening, thinking, speaking"""
        with self._lock:
            self.state.eye_state = state
            if self.eyes:
                self.eyes.set_state(state)

    def set_emotion(self, emotion: str):
        """Set emotion: default, happy, angry, tired, surprised, confused"""
        with self._lock:
            self.state.emotion = emotion
            if self.eyes:
                self.eyes.set_mood(Mood[emotion.upper()])

    def set_look(self, x: float, y: float):
        """Set eye look direction (-1 to 1)"""
        with self._lock:
            if self.eyes:
                self.eyes.set_look(x, y)

    def blink(self):
        """Trigger blink"""
        with self._lock:
            if self.eyes:
                self.eyes.blink()

    def play_animation(self, animation: str):
        """Play animation: laugh, confused"""
        with self._lock:
            if self.eyes:
                if animation == "laugh":
                    self.eyes.anim_laugh()
                elif animation == "confused":
                    self.eyes.anim_confused()

    # ========== Audio ==========

    def set_audio_level(self, level: float, source: str):
        """Update audio level for visualization"""
        with self._lock:
            self.state.audio_level = level
            self.state.audio_source = source

            if self.eyes:
                self.eyes.set_audio_level(level, source)
            if self.spectrum:
                self.spectrum.set_level(level, source)

    # ========== Face Tracking ==========

    def set_face_position(self, x: int, y: int, frame_w: int, frame_h: int, detected: bool):
        """Update face position for eye tracking"""
        with self._lock:
            self.state.face_detected = detected

            if detected and self.eyes:
                # Convert to look direction
                look_x = (x / frame_w - 0.5) * 2
                look_y = (y / frame_h - 0.5) * 2
                look_x = max(-0.8, min(0.8, look_x))
                look_y = max(-0.5, min(0.5, look_y))

                self.state.face_x = look_x
                self.state.face_y = look_y
                self.eyes.set_look(look_x, look_y)

    # ========== Main Loop ==========

    def _run(self):
        """Main display loop"""
        pygame.init()

        # Setup fullscreen display
        screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.FULLSCREEN | pygame.NOFRAME
        )
        pygame.display.set_caption("TARS")
        pygame.mouse.set_visible(False)

        # Initialize modules
        self.eyes = RoboEyes(self.width, self.height)
        self.spectrum = SpectrumVisualizer(self.width, self.height)

        clock = pygame.time.Clock()
        last_time = time.time()

        while self.running:
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_e:
                        self.set_mode("eyes")
                    elif event.key == pygame.K_s:
                        self.set_mode("spectrum")

            # Delta time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Clear
            screen.fill(self.bg_color)

            # Update and draw based on mode
            with self._lock:
                if self.state.mode == DisplayMode.EYES:
                    self.eyes.update(dt)
                    self.eyes.draw(screen)
                elif self.state.mode == DisplayMode.SPECTRUM:
                    self.spectrum.update(dt)
                    self.spectrum.draw(screen)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def get_status(self) -> dict:
        """Get current display status"""
        with self._lock:
            return {
                "mode": self.state.mode.value,
                "eye_state": self.state.eye_state,
                "emotion": self.state.emotion,
                "audio_level": self.state.audio_level,
                "audio_source": self.state.audio_source,
                "face_detected": self.state.face_detected
            }
