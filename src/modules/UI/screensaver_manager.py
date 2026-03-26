"""
Screensaver manager for TARS display.
Activates on idle timeout, cycles through available screensavers.
"""
import time
import random
from typing import Optional

from modules.UI.screensavers.module_screensaver_starfield import StarfieldAnimation
from modules.UI.screensavers.module_screensaver_hyperspace import HyperspaceAnimation
from modules.UI.screensavers.module_screensaver_defrag import DefragAnimation
from modules.UI.screensavers.module_screensaver_dream import DreamAnimation

AVAILABLE_ANIMATIONS = {
    "starfield":  StarfieldAnimation,
    "hyperspace": HyperspaceAnimation,
    "defrag":     DefragAnimation,
    "dream":      DreamAnimation,
}


class ScreensaverManager:
    def __init__(self, screen, width: int, height: int,
                 timeout: int = 300,
                 screensaver_list: list = None,
                 cycle_interval: int = 300,
                 show_time: bool = True):
        self.screen = screen
        self.width = width
        self.height = height
        self.timeout = timeout
        self.cycle_interval = cycle_interval
        self.show_time = show_time

        self._screensaver_list = screensaver_list or ["random"]
        self._active = False
        self._animation = None
        self._active_name: Optional[str] = None
        self._last_activity = time.time()
        self._last_cycle = time.time()

    # ── Public interface ──────────────────────────────────────────────────

    def reset_timer(self):
        """Reset idle timer. Call on any user/AI activity."""
        self._last_activity = time.time()
        if self._active:
            self.deactivate()

    def check_timeout(self):
        """Check if idle timeout has elapsed; activate if so."""
        if not self._active and self.timeout > 0:
            if time.time() - self._last_activity >= self.timeout:
                self.activate()

    def is_active(self) -> bool:
        return self._active

    def get_active_name(self) -> Optional[str]:
        return self._active_name

    def get_available(self) -> list:
        return list(AVAILABLE_ANIMATIONS.keys())

    def activate(self, name: str = None):
        """Force-activate a screensaver by name, or pick one randomly."""
        chosen = name or self._pick_name()
        cls = AVAILABLE_ANIMATIONS.get(chosen)
        if cls is None:
            chosen = random.choice(list(AVAILABLE_ANIMATIONS.keys()))
            cls = AVAILABLE_ANIMATIONS[chosen]

        self._animation = cls(self.screen, self.width, self.height, show_time=self.show_time)
        self._animation.reset()
        self._active_name = chosen
        self._active = True
        self._last_cycle = time.time()

    def deactivate(self):
        if self._animation and hasattr(self._animation, 'cleanup'):
            self._animation.cleanup()
        self._animation = None
        self._active_name = None
        self._active = False

    def render(self):
        """Update and render the active screensaver. Handles cycle switching."""
        if not self._active or self._animation is None:
            return

        if self.cycle_interval > 0 and time.time() - self._last_cycle >= self.cycle_interval:
            self.activate()
            return

        self._animation.update()
        self._animation.render()

    # ── Private ────────────────────────────────────────────────────────────

    def _pick_name(self) -> str:
        available = list(AVAILABLE_ANIMATIONS.keys())
        if self._screensaver_list == ["random"] or not self._screensaver_list:
            return random.choice(available)
        valid = [s for s in self._screensaver_list if s in AVAILABLE_ANIMATIONS]
        if not valid:
            return random.choice(available)
        if self._active_name and len(valid) > 1:
            choices = [s for s in valid if s != self._active_name]
            return random.choice(choices)
        return random.choice(valid)
