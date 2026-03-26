"""
TARS Display Manager
App-based display: eyes / spectrum / clock as switchable apps.
Screensavers activate on idle timeout.
"""
import pygame
import threading
import time
from typing import Optional
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from modules.UI.app_manager import AppManager
from modules.UI.screensaver_manager import ScreensaverManager
from modules.UI.status_bar import StatusBar


@dataclass
class DisplayState:
    active_app: str = "eyes"
    screensaver_active: bool = False
    eye_state: str = "idle"
    emotion: str = "neutral"
    audio_level: float = 0.0
    audio_source: str = "none"
    face_detected: bool = False
    face_x: float = 0.0
    face_y: float = 0.0
    battery_percentage: Optional[float] = None
    battery_charging: bool = False
    wifi_mode: str = "unknown"
    wifi_ssid: Optional[str] = None
    battery_voltage: Optional[float] = None


class DisplayManager:
    """Manages TARS display — app-based with screensaver idle support."""

    def __init__(self, width: int = 480, height: int = 800):
        self.width = width
        self.height = height
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self.state = DisplayState()

        # Managers (init in _run after pygame is ready)
        self.app_mgr: Optional[AppManager] = None
        self.screensaver_mgr: Optional[ScreensaverManager] = None
        self.status_bar: Optional[StatusBar] = None

        self.bg_color = (13, 17, 23)
        self._last_fps_print = 0.0

        from collections import deque
        self._log_lines: deque = deque(maxlen=3)
        self._log_font = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    # ── Activity reset ─────────────────────────────────────────────────────

    def _reset_activity(self):
        if self.screensaver_mgr:
            self.screensaver_mgr.reset_timer()

    # ── App Control ────────────────────────────────────────────────────────

    def launch_app(self, name: str) -> bool:
        with self._lock:
            if self.screensaver_mgr and self.screensaver_mgr.is_active():
                self.screensaver_mgr.deactivate()
            if self.app_mgr:
                result = self.app_mgr.launch(name)
                if result:
                    self.state.active_app = name
                    if self.status_bar:
                        self.status_bar.set_app(name)
                return result
            return False

    def get_available_apps(self) -> list:
        if self.app_mgr:
            return self.app_mgr.get_available()
        from modules.UI.app_manager import AVAILABLE_APPS
        return [{"name": k, "label": v["label"]} for k, v in AVAILABLE_APPS.items()]

    # ── Screensaver Control ────────────────────────────────────────────────

    def activate_screensaver(self, name: str = None):
        with self._lock:
            if self.screensaver_mgr:
                self.screensaver_mgr.activate(name, manual=True)
                self.state.screensaver_active = True

    def deactivate_screensaver(self):
        with self._lock:
            if self.screensaver_mgr:
                self.screensaver_mgr.deactivate()
                self.state.screensaver_active = False

    def get_available_screensavers(self) -> list:
        if self.screensaver_mgr:
            return self.screensaver_mgr.get_available()
        from modules.UI.screensaver_manager import AVAILABLE_ANIMATIONS
        return list(AVAILABLE_ANIMATIONS.keys())

    # ── Eyes Control ───────────────────────────────────────────────────────

    def set_eye_state(self, state: str):
        with self._lock:
            self.state.eye_state = state
            self._reset_activity()
            if self.app_mgr:
                app = self.app_mgr.get_active_app()
                if hasattr(app, 'set_eye_state'):
                    app.set_eye_state(state)

    def set_emotion(self, emotion: str):
        emotion_map = {
            "default": "neutral",
            "tired": "sleepy",
            "surprised": "surprised",
            "confused": "curious",
            "side eye l": "sideeye_left",
            "side eye r": "sideeye_right",
            "thinking": "curious",
            "doubt": "skeptical",
            "doubtful": "skeptical",
            "suspicious": "skeptical",
            "satisfied": "smug",
            "proud": "smug",
            "shocked": "surprised",
            "startled": "surprised",
        }
        emotion = emotion_map.get(emotion.lower(), emotion.lower())

        with self._lock:
            self.state.emotion = emotion
            self._reset_activity()
            if self.app_mgr:
                app = self.app_mgr.get_active_app()
                if not hasattr(app, 'set_emotion'):
                    # Switch to eyes so the emotion is visible
                    if self.screensaver_mgr and self.screensaver_mgr.is_active():
                        self.screensaver_mgr.deactivate()
                    self.app_mgr.launch('eyes')
                    self.state.active_app = 'eyes'
                    if self.status_bar:
                        self.status_bar.set_app('eyes')
                    app = self.app_mgr.get_active_app()
                if hasattr(app, 'set_emotion'):
                    app.set_emotion(emotion)

    def set_look(self, x: float, y: float):
        with self._lock:
            if self.app_mgr:
                app = self.app_mgr.get_active_app()
                if hasattr(app, 'set_look'):
                    app.set_look(x, y)

    def blink(self):
        with self._lock:
            if self.app_mgr:
                app = self.app_mgr.get_active_app()
                if hasattr(app, 'blink'):
                    app.blink()

    # ── Audio ──────────────────────────────────────────────────────────────

    def set_audio_level(self, level: float, source: str):
        with self._lock:
            self.state.audio_level = level
            self.state.audio_source = source
            self._reset_activity()
            if self.app_mgr:
                app = self.app_mgr.get_active_app()
                if hasattr(app, 'set_audio_level'):
                    app.set_audio_level(level, source)

    # ── Face Tracking ──────────────────────────────────────────────────────

    def set_face_position(self, x: int, y: int, frame_w: int, frame_h: int, detected: bool):
        with self._lock:
            self.state.face_detected = detected
            if detected and self.app_mgr:
                look_x = max(-1.0, min(1.0, (x / frame_w - 0.5) * 4))
                look_y = max(-1.0, min(1.0, (y / frame_h - 0.5) * 3))
                self.state.face_x = look_x
                self.state.face_y = look_y
                app = self.app_mgr.get_active_app()
                if hasattr(app, 'set_look'):
                    app.set_look(look_x, look_y)

    # ── Battery / WiFi ─────────────────────────────────────────────────────

    def set_battery_status(self, percentage: float, voltage: float, charging: bool = False):
        with self._lock:
            self.state.battery_percentage = percentage
            self.state.battery_voltage = voltage
            self.state.battery_charging = charging
            if self.status_bar:
                self.status_bar.set_battery(percentage, charging)

    def set_wifi_status(self, mode: str, ssid: str = None):
        with self._lock:
            self.state.wifi_mode = mode
            self.state.wifi_ssid = ssid
            if self.status_bar:
                self.status_bar.set_wifi(mode)

    # ── Camera log ─────────────────────────────────────────────────────────

    def add_camera_log(self, text):
        self._log_lines.append(text)

    # ── Main Loop ──────────────────────────────────────────────────────────

    def _run(self):
        pygame.init()
        pygame.display.init()
        self._log_font = pygame.font.SysFont("monospace", 18)

        display_info = pygame.display.Info()
        screen_w = display_info.current_w
        screen_h = display_info.current_h

        screen = pygame.display.set_mode(
            (screen_w, screen_h),
            pygame.FULLSCREEN | pygame.NOFRAME
        )
        pygame.display.set_caption("TARS")
        pygame.mouse.set_visible(False)

        # Portrait surface (480x800), rotated 270 for landscape output
        portrait_surface = pygame.Surface((self.width, self.height))

        # Load UI config
        try:
            from modules.module_config import load_config
            ui_cfg = load_config().get('UI', {})
        except Exception:
            ui_cfg = {}

        default_app      = ui_cfg.get('default_app', 'eyes')
        screensaver_timer = ui_cfg.get('screensaver_timer', 300)
        screensaver_cycle = ui_cfg.get('screensaver_cycle_interval', 300)
        screensaver_list  = ui_cfg.get('screensaver_list', ['random'])
        show_time         = ui_cfg.get('show_time', True)
        target_fps        = ui_cfg.get('target_fps', 30)

        # Init managers
        self.app_mgr = AppManager(portrait_surface, self.width, self.height)
        self.app_mgr.launch(default_app)
        self.state.active_app = default_app

        self.screensaver_mgr = ScreensaverManager(
            portrait_surface, self.width, self.height,
            timeout=screensaver_timer,
            screensaver_list=screensaver_list,
            cycle_interval=screensaver_cycle,
            show_time=show_time,
        )

        self.status_bar = StatusBar(portrait_surface, self.width, self.height)
        self.status_bar.set_app(default_app)

        clock = pygame.time.Clock()
        last_time = time.time()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    continue
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_e:
                        self.launch_app("eyes")
                    elif event.key == pygame.K_s:
                        self.launch_app("spectrum")
                    elif event.key == pygame.K_c:
                        self.launch_app("clock")

            # Snapshot rendering state under lock, then draw outside it.
            # This prevents HTTP/gRPC threads from inflating dt by blocking here.
            with self._lock:
                screensaver_active = self.screensaver_mgr.is_active()
                self.state.screensaver_active = screensaver_active

            current_time = time.time()
            dt = min(current_time - last_time, 0.05)  # cap at 50 ms to prevent animation jumps
            last_time = current_time

            # OpenGL screensavers manage their own flip — skip the pygame blit pipeline
            active_anim = self.screensaver_mgr.get_active_animation() if screensaver_active else None
            opengl_mode = screensaver_active and active_anim and getattr(active_anim, "uses_opengl", False)

            if not opengl_mode:
                portrait_surface.fill(self.bg_color)

            if screensaver_active:
                self.screensaver_mgr.render()
            else:
                self.screensaver_mgr.check_timeout()
                self.app_mgr.render(dt)

            if not opengl_mode:
                self.status_bar.draw(portrait_surface)
                self._draw_log_overlay(portrait_surface)
                rotated = pygame.transform.rotozoom(portrait_surface, 270, 1.0)
                screen.blit(rotated, (0, 0))
                pygame.display.flip()
            clock.tick(60)

            now = time.time()
            if now - self._last_fps_print >= 5.0:
                self._last_fps_print = now

        pygame.quit()

    def _draw_log_overlay(self, surface):
        if not self._log_lines or not self._log_font:
            return
        import pygame as _pg
        line_h = 22
        pad = 6
        lines = list(self._log_lines)
        total_h = len(lines) * line_h + pad * 2
        y_start = self.height - total_h - 28  # above status bar
        bg = _pg.Surface((self.width, total_h), _pg.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        surface.blit(bg, (0, y_start))
        for i, line in enumerate(lines):
            text_surf = self._log_font.render(line[:52], True, (200, 200, 200))
            surface.blit(text_surf, (pad, y_start + pad + i * line_h))

    def get_status(self) -> dict:
        with self._lock:
            return {
                "active_app": self.state.active_app,
                "screensaver_active": self.state.screensaver_active,
                "active_screensaver": self.screensaver_mgr.get_active_name() if self.screensaver_mgr else None,
                "available_apps": self.get_available_apps(),
                "available_screensavers": self.get_available_screensavers(),
                "eye_state": self.state.eye_state,
                "emotion": self.state.emotion,
                "audio_level": self.state.audio_level,
                "audio_source": self.state.audio_source,
                "face_detected": self.state.face_detected,
                "battery_percentage": self.state.battery_percentage,
                "wifi_mode": self.state.wifi_mode,
                "wifi_ssid": self.state.wifi_ssid,
                "battery_charging": self.state.battery_charging,
            }
