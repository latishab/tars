"""
TARS Robot Eyes
FluxGarage-style animated robot eyes for Pygame
"""

import pygame
import math
import random
import time
from enum import Enum, auto
from typing import Tuple, Optional
from dataclasses import dataclass


class Mood(Enum):
    DEFAULT = auto()
    HAPPY = auto()
    ANGRY = auto()
    TIRED = auto()
    SURPRISED = auto()
    CONFUSED = auto()


class EyeState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


@dataclass
class EyeConfig:
    # Dimensions
    width: int = 120
    height: int = 160
    border_radius: int = 30
    space_between: int = 80

    # Colors
    bg_color: Tuple[int, int, int] = (13, 17, 23)
    eye_color: Tuple[int, int, int] = (0, 206, 209)  # Cyan #00CED1
    glow_color: Tuple[int, int, int] = (0, 206, 209)
    glow_alpha: int = 50


class RoboEyes:
    """Animated robot eyes with expressions and tracking"""

    def __init__(self, screen_width: int = 800, screen_height: int = 480):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Scale config to screen
        scale = min(screen_width, screen_height) / 480
        self.config = EyeConfig(
            width=int(100 * scale),
            height=int(140 * scale),
            border_radius=int(25 * scale),
            space_between=int(60 * scale)
        )

        # State
        self._state = EyeState.IDLE
        self._mood = Mood.DEFAULT
        self._audio_level = 0.0
        self._audio_source = "none"

        # Position
        self._look_x = 0.0
        self._look_y = 0.0
        self._target_look_x = 0.0
        self._target_look_y = 0.0

        # Eye openness (0=closed, 1=open)
        self._left_open = 1.0
        self._right_open = 1.0
        self._left_open_target = 1.0
        self._right_open_target = 1.0

        # Eyelid overlays
        self._lid_top_left = 0.0
        self._lid_top_right = 0.0
        self._lid_bottom_left = 0.0
        self._lid_bottom_right = 0.0
        self._lid_angle_left = 0.0
        self._lid_angle_right = 0.0

        # Glow intensity (for speaking)
        self._glow_intensity = 1.0
        self._glow_target = 1.0

        # Blink state
        self._is_blinking = False
        self._blink_phase = 0.0
        self._blink_left = True
        self._blink_right = True

        # Auto-blink timer
        self._auto_blink = True
        self._blink_interval = 4.0
        self._blink_variation = 2.0
        self._blink_timer = 0.0
        self._next_blink = self._random_blink_time()

        # Idle mode (random looks)
        self._idle_mode = True
        self._idle_timer = 0.0
        self._idle_interval = 3.0
        self._idle_variation = 2.0
        self._next_idle = self._random_idle_time()

        # Speaking animation
        self._speaking_look_timer = 0.0
        self._speaking_look_away = False

        # Animations
        self._anim_laugh = False
        self._anim_laugh_timer = 0.0
        self._anim_confused = False
        self._anim_confused_timer = 0.0
        self._anim_offset_x = 0.0
        self._anim_offset_y = 0.0

        # Calculate base positions
        self._calc_base_positions()

    def _calc_base_positions(self):
        """Calculate centered eye positions"""
        total_w = self.config.width * 2 + self.config.space_between
        self._base_x = (self.screen_width - total_w) // 2
        self._base_y = (self.screen_height - self.config.height) // 2

    def _random_blink_time(self) -> float:
        return self._blink_interval + random.random() * self._blink_variation

    def _random_idle_time(self) -> float:
        return self._idle_interval + random.random() * self._idle_variation

    # ========== Public API ==========

    def set_state(self, state: str):
        """Set eye state: idle, listening, thinking, speaking"""
        self._state = EyeState(state)

        if self._state == EyeState.LISTENING:
            # Widen eyes slightly
            self._left_open_target = 1.1
            self._right_open_target = 1.1
            self._idle_mode = False  # Focus on user

        elif self._state == EyeState.THINKING:
            # Look up-left
            self._target_look_x = -0.3
            self._target_look_y = -0.4
            self._idle_mode = False

        elif self._state == EyeState.SPEAKING:
            # Normal, will pulse with audio
            self._left_open_target = 1.0
            self._right_open_target = 1.0
            self._idle_mode = False
            self._speaking_look_timer = 0

        else:  # IDLE
            self._left_open_target = 1.0
            self._right_open_target = 1.0
            self._idle_mode = True
            self._target_look_x = 0
            self._target_look_y = 0

    def set_mood(self, mood: Mood):
        """Set mood expression"""
        self._mood = mood

    def set_look(self, x: float, y: float):
        """Set look direction (-1 to 1)"""
        self._target_look_x = max(-1, min(1, x))
        self._target_look_y = max(-1, min(1, y))
        # Reset idle timer when manually positioned
        self._idle_timer = 0

    def set_audio_level(self, level: float, source: str):
        """Update audio level for animations"""
        self._audio_level = max(0, min(1, level))
        self._audio_source = source

        # Glow pulses with audio when speaking
        if self._state == EyeState.SPEAKING:
            self._glow_target = 1.0 + level * 0.5

    def blink(self, left: bool = True, right: bool = True):
        """Trigger a blink"""
        if not self._is_blinking:
            self._is_blinking = True
            self._blink_phase = 0.0
            self._blink_left = left
            self._blink_right = right

    def anim_laugh(self, duration: float = 0.5):
        """Trigger laugh animation"""
        self._anim_laugh = True
        self._anim_laugh_timer = duration

    def anim_confused(self, duration: float = 0.5):
        """Trigger confused animation"""
        self._anim_confused = True
        self._anim_confused_timer = duration

    def set_autoblinker(self, enabled: bool, interval: float = 4.0, variation: float = 2.0):
        """Enable/disable auto blinking"""
        self._auto_blink = enabled
        self._blink_interval = interval
        self._blink_variation = variation

    def set_idle_mode(self, enabled: bool, interval: float = 3.0, variation: float = 2.0):
        """Enable/disable idle random movement"""
        self._idle_mode = enabled
        self._idle_interval = interval
        self._idle_variation = variation

    # ========== Update ==========

    def update(self, dt: float):
        """Update all animations"""

        # Auto-blink
        if self._auto_blink and self._state != EyeState.SPEAKING:
            self._blink_timer += dt
            if self._blink_timer >= self._next_blink:
                self.blink()
                self._blink_timer = 0
                self._next_blink = self._random_blink_time()

        # Blink animation
        if self._is_blinking:
            self._blink_phase += dt * 12  # Speed

            if self._blink_phase < 0.5:
                # Closing
                if self._blink_left:
                    self._left_open_target = 0.0
                if self._blink_right:
                    self._right_open_target = 0.0
            else:
                # Opening
                state_open = 1.1 if self._state == EyeState.LISTENING else 1.0
                if self._blink_left:
                    self._left_open_target = state_open
                if self._blink_right:
                    self._right_open_target = state_open

            if self._blink_phase >= 1.0:
                self._is_blinking = False

        # Idle mode - random looks
        if self._idle_mode and self._state == EyeState.IDLE:
            self._idle_timer += dt
            if self._idle_timer >= self._next_idle:
                # Random look direction
                self._target_look_x = random.uniform(-0.6, 0.6)
                self._target_look_y = random.uniform(-0.3, 0.3)
                self._idle_timer = 0
                self._next_idle = self._random_idle_time()

        # Speaking behavior - occasional look away
        if self._state == EyeState.SPEAKING:
            self._speaking_look_timer += dt
            if self._speaking_look_timer > 2.0 and not self._speaking_look_away:
                # Occasionally look slightly away
                if random.random() < 0.3:
                    self._target_look_x = random.uniform(-0.3, 0.3)
                    self._target_look_y = random.uniform(-0.2, 0.1)
                    self._speaking_look_away = True
            elif self._speaking_look_timer > 2.5 and self._speaking_look_away:
                # Look back
                self._target_look_x = 0
                self._target_look_y = 0
                self._speaking_look_away = False
                self._speaking_look_timer = 0

        # Laugh animation
        if self._anim_laugh:
            self._anim_laugh_timer -= dt
            self._anim_offset_y = math.sin(self._anim_laugh_timer * 50) * 5
            if self._anim_laugh_timer <= 0:
                self._anim_laugh = False
                self._anim_offset_y = 0

        # Confused animation
        if self._anim_confused:
            self._anim_confused_timer -= dt
            self._anim_offset_x = math.sin(self._anim_confused_timer * 50) * 5
            if self._anim_confused_timer <= 0:
                self._anim_confused = False
                self._anim_offset_x = 0

        # Smooth interpolation
        lerp = 8.0 * dt
        self._look_x += (self._target_look_x - self._look_x) * lerp
        self._look_y += (self._target_look_y - self._look_y) * lerp
        self._left_open += (self._left_open_target - self._left_open) * lerp * 2
        self._right_open += (self._right_open_target - self._right_open) * lerp * 2
        self._glow_intensity += (self._glow_target - self._glow_intensity) * lerp

        # Reset glow when not speaking
        if self._state != EyeState.SPEAKING:
            self._glow_target = 1.0

        # Update mood eyelids
        self._update_mood(dt)

    def _update_mood(self, dt: float):
        """Update eyelid positions based on mood"""
        target_top_l = 0.0
        target_top_r = 0.0
        target_bot_l = 0.0
        target_bot_r = 0.0
        target_angle_l = 0.0
        target_angle_r = 0.0

        h = self.config.height * 0.35

        if self._mood == Mood.HAPPY:
            target_bot_l = h * 0.5
            target_bot_r = h * 0.5
        elif self._mood == Mood.ANGRY:
            target_top_l = h * 0.4
            target_top_r = h * 0.4
            target_angle_l = -20
            target_angle_r = 20
        elif self._mood == Mood.TIRED:
            target_top_l = h * 0.5
            target_top_r = h * 0.5
        elif self._mood == Mood.SURPRISED:
            # Eyes wide (handled by openness)
            self._left_open_target = 1.2
            self._right_open_target = 1.2
        elif self._mood == Mood.CONFUSED:
            target_top_l = h * 0.2
            target_angle_l = 10

        lerp = 6.0 * dt
        self._lid_top_left += (target_top_l - self._lid_top_left) * lerp
        self._lid_top_right += (target_top_r - self._lid_top_right) * lerp
        self._lid_bottom_left += (target_bot_l - self._lid_bottom_left) * lerp
        self._lid_bottom_right += (target_bot_r - self._lid_bottom_right) * lerp
        self._lid_angle_left += (target_angle_l - self._lid_angle_left) * lerp
        self._lid_angle_right += (target_angle_r - self._lid_angle_right) * lerp

    # ========== Draw ==========

    def draw(self, surface: pygame.Surface):
        """Draw eyes on surface"""
        cfg = self.config

        # Calculate look offset
        max_move = cfg.width * 0.25
        look_offset_x = self._look_x * max_move
        look_offset_y = self._look_y * max_move * 0.6

        # Animation offsets
        offset_x = look_offset_x + self._anim_offset_x
        offset_y = look_offset_y + self._anim_offset_y

        # Left eye position
        left_x = self._base_x + int(offset_x)
        left_y = self._base_y + int(offset_y)
        left_h = int(cfg.height * self._left_open)
        left_y_adj = left_y + (cfg.height - left_h) // 2

        # Right eye position
        right_x = self._base_x + cfg.width + cfg.space_between + int(offset_x)
        right_y = self._base_y + int(offset_y)
        right_h = int(cfg.height * self._right_open)
        right_y_adj = right_y + (cfg.height - right_h) // 2

        # Draw glow (if speaking)
        if self._glow_intensity > 1.01:
            self._draw_glow(surface, left_x, left_y_adj, cfg.width, left_h)
            self._draw_glow(surface, right_x, right_y_adj, cfg.width, right_h)

        # Draw eyes
        if left_h > 2:
            self._draw_eye(surface, left_x, left_y_adj, cfg.width, left_h,
                          self._lid_top_left, self._lid_bottom_left, self._lid_angle_left)

        if right_h > 2:
            self._draw_eye(surface, right_x, right_y_adj, cfg.width, right_h,
                          self._lid_top_right, self._lid_bottom_right, self._lid_angle_right)

    def _draw_glow(self, surface: pygame.Surface, x: int, y: int, w: int, h: int):
        """Draw glow effect around eye"""
        glow_size = int(10 * self._glow_intensity)
        glow_rect = pygame.Rect(x - glow_size, y - glow_size,
                                w + glow_size * 2, h + glow_size * 2)

        # Create glow surface
        glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        glow_color = (*self.config.glow_color, int(self.config.glow_alpha * (self._glow_intensity - 1) * 2))
        pygame.draw.rect(glow_surf, glow_color,
                        pygame.Rect(0, 0, glow_rect.width, glow_rect.height),
                        border_radius=self.config.border_radius + glow_size)
        surface.blit(glow_surf, glow_rect.topleft)

    def _draw_eye(self, surface: pygame.Surface, x: int, y: int, w: int, h: int,
                  lid_top: float, lid_bot: float, lid_angle: float):
        """Draw single eye with eyelid overlays"""
        if h < 2:
            return

        cfg = self.config
        br = min(cfg.border_radius, w // 2, h // 2)

        # Main eye
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, cfg.eye_color, rect, border_radius=br)

        # Top eyelid overlay
        if lid_top > 1:
            lid_h = int(lid_top) + br
            lid_rect = pygame.Rect(x - 2, y - br, w + 4, lid_h)

            if abs(lid_angle) > 0.5:
                # Angled (for angry)
                lid_surf = pygame.Surface((w + 20, lid_h + 20), pygame.SRCALPHA)
                pygame.draw.rect(lid_surf, cfg.bg_color,
                               pygame.Rect(10, 10, w + 4, lid_h))
                rotated = pygame.transform.rotate(lid_surf, lid_angle)
                rot_rect = rotated.get_rect(center=(x + w//2, y + lid_h//2 - br//2))
                surface.blit(rotated, rot_rect)
            else:
                pygame.draw.rect(surface, cfg.bg_color, lid_rect)

        # Bottom eyelid overlay
        if lid_bot > 1:
            lid_h = int(lid_bot) + br
            lid_rect = pygame.Rect(x - 2, y + h - int(lid_bot), w + 4, lid_h)
            pygame.draw.rect(surface, cfg.bg_color, lid_rect)
