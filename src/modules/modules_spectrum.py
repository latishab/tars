"""
TARS Audio Spectrum Visualizer
"""

import pygame
import numpy as np
import math
import time
from typing import Tuple
from enum import Enum


class SpectrumStyle(Enum):
    BARS = "bars"
    MIRRORED = "mirrored"
    WAVE = "wave"


class SpectrumVisualizer:
    """Audio spectrum visualization"""

    def __init__(self, screen_width: int = 480, screen_height: int = 800):
        self.width = screen_width
        self.height = screen_height

        # Config
        self.num_bars = 32
        self.style = SpectrumStyle.BARS

        # State
        self.bar_values = np.zeros(self.num_bars)
        self.bar_targets = np.zeros(self.num_bars)
        self.level = 0.0
        self.source = "none"

        # Colors
        self.color_mic = (0, 255, 136)       # Green #00FF88
        self.color_speaker = (0, 212, 255)   # Cyan #00D4FF
        self.color_idle = (0, 80, 100)       # Dim
        self.bg_color = (13, 17, 23)

        # Layout
        self.margin = 40
        self.bar_spacing = 4

    def set_level(self, level: float, source: str):
        """Update audio level"""
        self.level = max(0, min(1, level))
        self.source = source

        # Generate bar targets with variation
        t = time.time()
        for i in range(self.num_bars):
            wave = 0.5 + 0.5 * math.sin(t * 8 + i * 0.4)
            noise = np.random.uniform(0.7, 1.3)
            self.bar_targets[i] = level * wave * noise

    def set_style(self, style: str):
        """Set visualization style"""
        self.style = SpectrumStyle(style)

    def update(self, dt: float):
        """Update animation"""
        # Smooth interpolation
        lerp = 12.0 * dt
        self.bar_values += (self.bar_targets - self.bar_values) * lerp

        # Decay when no audio
        if self.level < 0.01:
            self.bar_values *= (1.0 - 3.0 * dt)

    def draw(self, surface: pygame.Surface):
        """Draw spectrum"""
        if self.style == SpectrumStyle.BARS:
            self._draw_bars(surface)
        elif self.style == SpectrumStyle.MIRRORED:
            self._draw_mirrored(surface)
        elif self.style == SpectrumStyle.WAVE:
            self._draw_wave(surface)

        # Draw state label
        font = pygame.font.Font(None, 28)
        label = "LISTENING" if self.source == "mic" else "SPEAKING" if self.source == "speaker" else "IDLE"
        text = font.render(f"[ {label} ]", True, self._get_color())
        text_rect = text.get_rect(center=(self.width // 2, self.height - 30))
        surface.blit(text, text_rect)

    def _get_color(self) -> Tuple[int, int, int]:
        if self.source == "mic":
            return self.color_mic
        elif self.source == "speaker":
            return self.color_speaker
        return self.color_idle

    def _draw_bars(self, surface: pygame.Surface):
        """Draw classic bar spectrum"""
        color = self._get_color()

        total_w = self.width - 2 * self.margin
        bar_w = (total_w - (self.num_bars - 1) * self.bar_spacing) // self.num_bars
        max_h = self.height * 0.6
        base_y = self.height * 0.7

        for i, val in enumerate(self.bar_values):
            x = self.margin + i * (bar_w + self.bar_spacing)
            bar_h = int(val * max_h)
            y = int(base_y - bar_h)

            if bar_h > 0:
                rect = pygame.Rect(x, y, bar_w, bar_h)
                pygame.draw.rect(surface, color, rect, border_radius=2)

                # Reflection
                ref_h = bar_h // 4
                ref_color = tuple(c // 4 for c in color)
                ref_rect = pygame.Rect(x, int(base_y) + 5, bar_w, ref_h)
                pygame.draw.rect(surface, ref_color, ref_rect, border_radius=2)

    def _draw_mirrored(self, surface: pygame.Surface):
        """Draw mirrored spectrum"""
        color = self._get_color()

        total_w = self.width - 2 * self.margin
        bar_w = (total_w - (self.num_bars - 1) * self.bar_spacing) // self.num_bars
        max_h = self.height * 0.35
        center_y = self.height // 2

        for i, val in enumerate(self.bar_values):
            x = self.margin + i * (bar_w + self.bar_spacing)
            bar_h = int(val * max_h)

            if bar_h > 0:
                # Top
                pygame.draw.rect(surface, color,
                               pygame.Rect(x, center_y - bar_h, bar_w, bar_h),
                               border_radius=2)
                # Bottom
                pygame.draw.rect(surface, color,
                               pygame.Rect(x, center_y, bar_w, bar_h),
                               border_radius=2)

        # Center line
        pygame.draw.line(surface, tuple(c // 2 for c in color),
                        (self.margin, center_y), (self.width - self.margin, center_y), 2)

    def _draw_wave(self, surface: pygame.Surface):
        """Draw waveform"""
        color = self._get_color()
        center_y = self.height // 2
        max_amp = self.height * 0.35

        points_top = []
        points_bot = []

        for i in range(self.num_bars + 1):
            x = self.margin + i * (self.width - 2 * self.margin) // self.num_bars
            val = self.bar_values[min(i, self.num_bars - 1)]
            offset = int(val * max_amp)

            points_top.append((x, center_y - offset))
            points_bot.append((x, center_y + offset))

        if len(points_top) >= 2:
            pygame.draw.lines(surface, color, False, points_top, 3)
            pygame.draw.lines(surface, color, False, points_bot, 3)
