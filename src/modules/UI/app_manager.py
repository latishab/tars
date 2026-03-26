"""
App manager for TARS display.
Wraps hardware display modules as switchable display apps.
"""
from typing import Optional

from modules.modules_roboeyes import RoboEyes, Mood
from modules.modules_spectrum import SpectrumVisualizer
from modules.UI.apps.module_app_clock import ClockApp


class EyesApp:
    """Thin wrapper around RoboEyes for use as a display app."""

    def __init__(self, screen, width: int, height: int):
        self.screen = screen
        self.eyes = RoboEyes(width, height)

    def reset(self):
        pass

    def update(self, dt: float = 0.016):
        self.eyes.update(dt)

    def render(self):
        self.eyes.draw(self.screen)

    def cleanup(self):
        pass

    def set_emotion(self, emotion: str):
        try:
            self.eyes.set_mood(Mood[emotion.upper()])
        except (KeyError, AttributeError):
            pass

    def set_eye_state(self, state: str):
        self.eyes.set_state(state)

    def set_look(self, x: float, y: float):
        self.eyes.set_look(x, y)

    def set_audio_level(self, level: float, source: str):
        self.eyes.set_audio_level(level, source)

    def blink(self):
        self.eyes.blink()


class SpectrumApp:
    """Thin wrapper around SpectrumVisualizer for use as a display app."""

    def __init__(self, screen, width: int, height: int):
        self.screen = screen
        self.spectrum = SpectrumVisualizer(width, height)

    def reset(self):
        pass

    def update(self, dt: float = 0.016):
        self.spectrum.update(dt)

    def render(self):
        self.spectrum.draw(self.screen)

    def cleanup(self):
        pass

    def set_audio_level(self, level: float, source: str):
        self.spectrum.set_level(level, source)


AVAILABLE_APPS = {
    "eyes":     {"class": EyesApp,    "label": "Eyes"},
    "spectrum": {"class": SpectrumApp, "label": "Spectrum"},
    "clock":    {"class": ClockApp,   "label": "Clock"},
}


class AppManager:
    def __init__(self, screen, width: int, height: int):
        self.screen = screen
        self.width = width
        self.height = height
        self._active_name: Optional[str] = None
        self._active_app = None

    def launch(self, name: str) -> bool:
        cls_info = AVAILABLE_APPS.get(name)
        if cls_info is None:
            return False

        if self._active_app and hasattr(self._active_app, 'cleanup'):
            self._active_app.cleanup()

        cls = cls_info["class"]
        self._active_app = cls(self.screen, self.width, self.height)
        self._active_app.reset()
        self._active_name = name
        return True

    def deactivate(self):
        if self._active_app and hasattr(self._active_app, 'cleanup'):
            self._active_app.cleanup()
        self._active_app = None
        self._active_name = None

    def is_active(self) -> bool:
        return self._active_app is not None

    def get_active_name(self) -> Optional[str]:
        return self._active_name

    def get_active_app(self):
        return self._active_app

    def get_available(self) -> list:
        return [{"name": k, "label": v["label"]} for k, v in AVAILABLE_APPS.items()]

    def render(self, dt: float = 0.016):
        if self._active_app is None:
            return
        self._active_app.update(dt)
        self._active_app.render()

    def handle_event(self, event):
        pass
