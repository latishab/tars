"""
TARS tactical status bar.
Bottom bar: active app name (left), wifi + battery (right).
Aesthetic: amber/cyan, monospace, angular brackets.
"""
import pygame
from pathlib import Path
from typing import Optional

_CYAN   = (0, 200, 220)
_AMBER  = (200, 140, 0)
_DIM    = (40, 60, 70)
_GREEN  = (60, 180, 80)
_YELLOW = (200, 180, 40)
_RED    = (200, 60, 60)

BAR_HEIGHT = 28


class StatusBar:
    def __init__(self, screen, width: int, height: int):
        self.screen = screen
        self.width = width
        self.height = height

        self._app_name: str = "eyes"
        self._battery_pct: Optional[float] = None
        self._battery_charging: bool = False
        self._wifi_mode: str = "unknown"

        self._font = None
        self._font_small = None
        self._initialized = False

    def _init_fonts(self):
        if self._initialized:
            return
        try:
            font_path = str(Path(__file__).parent / "mono.ttf")
            self._font = pygame.font.Font(font_path, 14)
            self._font_small = pygame.font.Font(font_path, 11)
        except Exception:
            self._font = pygame.font.SysFont("monospace", 14)
            self._font_small = pygame.font.SysFont("monospace", 11)
        self._initialized = True

    def set_app(self, name: str):
        self._app_name = name

    def set_battery(self, percentage: Optional[float], charging: bool = False):
        self._battery_pct = percentage
        self._battery_charging = charging

    def set_wifi(self, mode: str):
        self._wifi_mode = mode

    def draw(self, surface: pygame.Surface):
        self._init_fonts()

        y = self.height - BAR_HEIGHT
        w = self.width

        # Translucent background bar
        bar_surf = pygame.Surface((w, BAR_HEIGHT), pygame.SRCALPHA)
        bar_surf.fill((8, 14, 18, 210))
        surface.blit(bar_surf, (0, y))

        # Top border line
        pygame.draw.line(surface, _CYAN, (0, y), (w, y), 1)

        cy = y + BAR_HEIGHT // 2

        # Left: active app name
        label = f"[ {self._app_name.upper()} ]"
        app_surf = self._font.render(label, True, _CYAN)
        surface.blit(app_surf, (10, cy - app_surf.get_height() // 2))

        # Right side: wifi + battery, right-aligned
        rx = w - 8

        # Battery
        if self._battery_pct is not None:
            pct = max(0, min(100, int(self._battery_pct)))
            if self._battery_charging:
                bat_color = _GREEN
                bat_text = f"+{pct}%"
            elif pct > 50:
                bat_color = _GREEN
                bat_text = f"{pct}%"
            elif pct > 20:
                bat_color = _YELLOW
                bat_text = f"{pct}%"
            else:
                bat_color = _RED
                bat_text = f"{pct}%"

            bat_surf = self._font.render(bat_text, True, bat_color)
            rx -= bat_surf.get_width()
            surface.blit(bat_surf, (rx, cy - bat_surf.get_height() // 2))
            rx -= 4

            # Battery icon
            icon_w, icon_h = 18, 11
            bx = rx - icon_w - 2
            by = cy - icon_h // 2
            pygame.draw.rect(surface, (120, 130, 135), (bx, by, icon_w, icon_h), 1)
            pygame.draw.rect(surface, (120, 130, 135), (bx + icon_w, by + 3, 2, 5))
            fill = int((icon_w - 4) * pct / 100)
            if fill > 0:
                pygame.draw.rect(surface, bat_color, (bx + 2, by + 2, fill, icon_h - 4))
            rx = bx - 8

        # WiFi indicator
        if self._wifi_mode == "wlan":
            wifi_color = _CYAN
            wifi_text = "WLAN"
        elif self._wifi_mode == "hotspot":
            wifi_color = _AMBER
            wifi_text = "AP"
        else:
            wifi_color = _DIM
            wifi_text = "----"

        wifi_surf = self._font_small.render(wifi_text, True, wifi_color)
        rx -= wifi_surf.get_width()
        surface.blit(wifi_surf, (rx, cy - wifi_surf.get_height() // 2))
