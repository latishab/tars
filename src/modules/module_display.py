"""
TARS Display Manager
Coordinates between eyes and spectrum modes
"""

# Configure SDL for Wayland
import os
os.environ["SDL_VIDEODRIVER"] = "wayland"
os.environ.setdefault("WAYLAND_DISPLAY", "wayland-0")
os.environ.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")

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
    emotion: str = "neutral"
    audio_level: float = 0.0
    audio_source: str = "none"
    face_detected: bool = False
    face_x: float = 0.0
    face_y: float = 0.0
    battery_percentage: Optional[float] = None
    battery_charging: bool = False
    wifi_mode: str = "unknown"  # hotspot, wlan, disconnected
    wifi_ssid: Optional[str] = None
    battery_voltage: Optional[float] = None


class DisplayManager:
    """Manages TARS display - switches between eyes and spectrum"""

    def __init__(self, width: int = 480, height: int = 800):
        self.width = width
        self.height = height
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # State
        self.state = DisplayState()
        self._last_fps_print = 0.0

        # Modules (initialized in _run)
        self.eyes: Optional[RoboEyes] = None
        self.spectrum: Optional[SpectrumVisualizer] = None

        # Colors
        self.bg_color = (13, 17, 23)  # #0d1117

        # WiFi icons (loaded in _run to avoid pygame init issues)
        self.wifi_icons = {}

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
        """Set emotion: neutral, happy, sad, angry, excited, afraid, sideeye_left, sideeye_right, sleepy"""
        # Backward compatibility aliases
        emotion_map = {
            "default": "neutral",
            "tired": "sleepy",
            "surprised": "excited",
            "confused": "curious"
        }
        emotion = emotion_map.get(emotion.lower(), emotion.lower())
        
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
                # Convert face position to look direction with amplified range
                look_x = (x / frame_w - 0.5) * 4
                look_y = (y / frame_h - 0.5) * 3
                look_x = max(-1.0, min(1.0, look_x))
                look_y = max(-1.0, min(1.0, look_y))

                self.state.face_x = look_x
                self.state.face_y = look_y
                self.eyes.set_look(look_x, look_y)

    # ========== Battery ==========

    def set_battery_status(self, percentage: float, voltage: float, charging: bool = False):
        """Update battery status for display"""
        with self._lock:
            self.state.battery_percentage = percentage
            self.state.battery_voltage = voltage
            self.state.battery_charging = charging

    # ========== WiFi ==========

    def set_wifi_status(self, mode: str, ssid: str = None):
        """Update WiFi status for display"""
        with self._lock:
            self.state.wifi_mode = mode
            self.state.wifi_ssid = ssid
    # ========== Main Loop ==========

    def _run(self):
        """Main display loop - renders portrait content rotated onto landscape screen"""
        pygame.init()
        
        # Initialize video subsystem explicitly
        pygame.display.init()

        # Physical screen is 800x480 landscape (DSI panel mounted vertically)
        display_info = pygame.display.Info()
        screen_w = display_info.current_w
        screen_h = display_info.current_h

        screen = pygame.display.set_mode(
            (screen_w, screen_h),
            pygame.FULLSCREEN | pygame.NOFRAME
        )
        pygame.display.set_caption("TARS")
        pygame.mouse.set_visible(False)

        # Render to portrait surface (480x800), then rotate for landscape screen
        portrait_surface = pygame.Surface((self.width, self.height))

        # Initialize modules with portrait dimensions
        self.eyes = RoboEyes(self.width, self.height)
        self.spectrum = SpectrumVisualizer(self.width, self.height)

        # Load and scale WiFi icons
        icon_size = 26  # Scale down from 250x250 to 26x26
        assets_path = Path(__file__).parent.parent / "assets"
        try:
            self.wifi_icons["wlan"] = pygame.transform.scale(
                pygame.image.load(str(assets_path / "wifi-blue.png")), (icon_size, icon_size)
            )
            self.wifi_icons["hotspot"] = pygame.transform.scale(
                pygame.image.load(str(assets_path / "wifi-yellow.png")), (icon_size, icon_size)
            )
            self.wifi_icons["disconnected"] = pygame.transform.scale(
                pygame.image.load(str(assets_path / "wifi-gray.png")), (icon_size, icon_size)
            )
        except Exception as e:
            print(f"Warning: Failed to load WiFi icons: {e}")
            self.wifi_icons = {}

        clock = pygame.time.Clock()
        last_time = time.time()

        while self.running:
            # Events
            for event in pygame.event.get():
                # Only exit on ESC key or screen tap, ignore QUIT events
                if event.type == pygame.QUIT:
                    continue  # Ignore window close events from Wayland
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Tap screen to exit
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

            # Draw to portrait surface
            portrait_surface.fill(self.bg_color)

            with self._lock:
                if self.state.mode == DisplayMode.EYES:
                    self.eyes.update(dt)
                    self.eyes.draw(portrait_surface)
                elif self.state.mode == DisplayMode.SPECTRUM:
                    self.spectrum.update(dt)
                    self.spectrum.draw(portrait_surface)

                self._draw_wifi_indicator(portrait_surface)
                self._draw_battery_indicator(portrait_surface)

            # Rotate portrait (480x800) -> landscape (800x480) and blit to screen
            # Using rotozoom with scale=1.0 is faster than rotate()
            rotated = pygame.transform.rotozoom(portrait_surface, 270, 1.0)
            screen.blit(rotated, (0, 0))

            pygame.display.flip()
            clock.tick(60)
            
            # FPS monitoring (print every 5 seconds)
            now = time.time()
            if now - self._last_fps_print >= 5.0:
                fps = clock.get_fps()
                if fps < 55:  # Only print if below target
                    print(f"Display FPS: {fps:.1f} (target: 60)")
                self._last_fps_print = now

        pygame.quit()

    def _draw_battery_indicator(self, screen: pygame.Surface):
        """Draw battery status in top-right corner"""
        if self.state.battery_percentage is None:
            return

        # Position: top-right with margin
        margin = 15
        width = 60
        height = 25
        x = self.width - width - margin
        y = margin

        # Battery percentage
        percentage = max(0, min(100, self.state.battery_percentage))

        # Colors based on charge level
        if self.state.battery_charging:
            color = (100, 200, 100)  # Green when charging
        elif percentage > 50:
            color = (100, 200, 100)  # Green
        elif percentage > 20:
            color = (255, 200, 0)    # Yellow
        else:
            color = (255, 50, 50)    # Red

        # Draw battery outline
        pygame.draw.rect(screen, (200, 200, 200), (x, y, width, height), 2)

        # Draw battery terminal (little nub on right)
        pygame.draw.rect(screen, (200, 200, 200), (x + width, y + 7, 3, 11))

        # Draw fill level
        fill_width = int((width - 4) * (percentage / 100))
        if fill_width > 0:
            pygame.draw.rect(screen, color, (x + 2, y + 2, fill_width, height - 4))

        # Draw percentage text
        font = pygame.font.Font(None, 18)
        text = f"{int(percentage)}%"
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        screen.blit(text_surface, text_rect)

        # Draw charging indicator if charging
        if self.state.battery_charging:
            bolt_font = pygame.font.Font(None, 20)
            bolt = bolt_font.render("⚡", True, (255, 255, 100))
            screen.blit(bolt, (x - 15, y + 2))


    def _draw_wifi_indicator(self, screen: pygame.Surface):
        """Draw WiFi status indicator in top-left corner"""
        if not self.wifi_icons:
            return  # Icons not loaded yet

        # Position: top-left with margin
        margin = 15

        # Select icon based on WiFi mode
        if self.state.wifi_mode == "hotspot":
            icon = self.wifi_icons.get("hotspot")
        elif self.state.wifi_mode == "wlan":
            icon = self.wifi_icons.get("wlan")
        else:
            icon = self.wifi_icons.get("disconnected")

        # Draw icon if available
        if icon:
            screen.blit(icon, (margin, margin))
    def get_status(self) -> dict:
        """Get current display status"""
        with self._lock:
            return {
                "mode": self.state.mode.value,
                "eye_state": self.state.eye_state,
                "emotion": self.state.emotion,
                "audio_level": self.state.audio_level,
                "audio_source": self.state.audio_source,
                "face_detected": self.state.face_detected,
                "battery_percentage": self.state.battery_percentage,
                "wifi_mode": self.state.wifi_mode,
                "wifi_ssid": self.state.wifi_ssid,
                "battery_charging": self.state.battery_charging
            }
