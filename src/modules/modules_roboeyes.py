"""Enhanced RoboEyes - Expressive animated eyes for conversational AI"""
import math
import random
import pygame
from enum import Enum, auto
from dataclasses import dataclass
from typing import Tuple, Optional


class Mood(Enum):
    """Emotional states for the eyes"""
    NEUTRAL = auto()
    HAPPY = auto()
    SAD = auto()
    ANGRY = auto()
    EXCITED = auto()
    AFRAID = auto()
    SIDEEYE_LEFT = auto()
    SIDEEYE_RIGHT = auto()
    SLEEPY = auto()
    CURIOUS = auto()
    SKEPTICAL = auto()
    SMUG = auto()
    SURPRISED = auto()


class EyeState(Enum):
    """Eye states for different activities"""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


# Emotion transition speeds (higher = faster)
EMOTION_TRANSITION_SPEEDS = {
    Mood.EXCITED: 8.0,
    
    # Mood.SURPRISED (removed): 15.0,
    Mood.ANGRY: 6.0,
    Mood.HAPPY: 5.0,
    Mood.NEUTRAL: 4.0,
    Mood.SAD: 2.0,
    Mood.SLEEPY: 1.5,
    
    Mood.AFRAID: 7.0,
    Mood.SIDEEYE_LEFT: 4.0,
    Mood.SIDEEYE_RIGHT: 4.0,
    Mood.CURIOUS: 5.0,
    Mood.SKEPTICAL: 3.0,
    Mood.SMUG: 3.5,
    Mood.SURPRISED: 12.0,
}

# Blink intervals per mood (min, max in seconds)
BLINK_INTERVALS = {
    Mood.NEUTRAL: (3.0, 5.0),
    Mood.EXCITED: (1.5, 3.0),
    
    Mood.HAPPY: (2.5, 4.5),
    Mood.SAD: (4.0, 7.0),
    Mood.SLEEPY: (5.0, 10.0),
    
    Mood.ANGRY: (2.0, 4.0),
    
    Mood.AFRAID: (2.0, 3.5),
    Mood.SIDEEYE_LEFT: (3.0, 5.0),
    Mood.SIDEEYE_RIGHT: (3.0, 5.0),
    Mood.CURIOUS: (2.5, 4.0),
    Mood.SKEPTICAL: (4.0, 6.0),
    Mood.SMUG: (3.5, 5.5),
    Mood.SURPRISED: (1.0, 2.0),
}

# Glow colors per mood (R, G, B)
GLOW_COLORS = {
    Mood.NEUTRAL: (0, 206, 209),
    Mood.HAPPY: (0, 206, 209),
    Mood.SAD: (0, 206, 209),
    Mood.ANGRY: (255, 69, 0),
    Mood.EXCITED: (0, 206, 209),
    Mood.AFRAID: (0, 206, 209),
    Mood.SLEEPY: (0, 206, 209),
    Mood.SIDEEYE_LEFT: (0, 206, 209),
    Mood.SIDEEYE_RIGHT: (0, 206, 209),
    Mood.CURIOUS: (0, 206, 209),
    Mood.SKEPTICAL: (0, 206, 209),
    Mood.SMUG: (0, 206, 209),
    Mood.SURPRISED: (255, 255, 255),
}


@dataclass
class EyeConfig:
    """Eye visual configuration"""
    width: int = 120
    height: int = 160
    border_radius: int = 30
    space_between: int = 80
    bg_color: Tuple[int, int, int] = (13, 17, 23)
    eye_color: Tuple[int, int, int] = (0, 206, 209)
    glow_color: Tuple[int, int, int] = (0, 206, 209)
    glow_alpha: int = 50


def smooth_lerp(current: float, target: float, speed: float, dt: float) -> float:
    """Frame-rate independent exponential smoothing"""
    return current + (target - current) * (1.0 - math.exp(-speed * dt))


class RoboEyes:
    """Expressive animated robot eyes for conversational AI"""
    
    def __init__(self, screen_width: int = 480, screen_height: int = 800):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Scale config to screen
        scale = min(screen_width, screen_height) / 480
        self.config = EyeConfig(
            width=int(100 * scale),
            height=int(140 * scale),
            border_radius=int(25 * scale),
            space_between=int(150 * scale)
        )
        
        # State
        self._state = EyeState.IDLE
        self._mood = Mood.NEUTRAL
        self._mood_intensity = 1.0
        self._prev_mood = Mood.NEUTRAL
        self._mood_transition_progress = 1.0  # 0.0 to 1.0
        
        # Look direction
        self._look_x = 0.0
        self._look_y = 0.0
        self._target_look_x = 0.0
        self._target_look_y = 0.0
        
        # Eyelid positions (0 = fully open, 1 = fully closed)
        self._lid_top_left = 0.0
        self._lid_top_right = 0.0
        self._lid_bottom_left = 0.0
        self._lid_bottom_right = 0.0
        self._lid_angle_left = 0.0
        self._lid_angle_right = 0.0
        
        # Curved eyelid state
        self._curved_bottom_left = False
        self._curved_bottom_right = False
        self._curved_amount_left = 0.0
        self._curved_amount_right = 0.0
        
        # Eye openness (0.0 to 1.5 - can be > 1.0 for wide eyes)
        self._left_open = 1.0
        self._right_open = 1.0
        self._left_open_target = 1.0
        self._right_open_target = 1.0
        
        # New expressive features
        self._pupil_scale = 1.0
        self._pupil_scale_target = 1.0
        self._squint_intensity = 0.0
        self._squint_target = 0.0
        self._eye_offset_y_left = 0.0
        self._eye_offset_y_right = 0.0
        
        # Glow
        self._glow_intensity = 1.0
        self._glow_target = 1.0
        self._current_glow_color = self.config.glow_color
        self._target_glow_color = self.config.glow_color
        
        # Blinking
        self._auto_blink = True
        self._is_blinking = False
        self._blink_phase = 0.0
        self._blink_timer = 0.0
        self._next_blink = self._random_blink_time()
        self._blink_left = True
        self._blink_right = True
        
        # Audio reactivity
        self._audio_level = 0.0
        self._audio_source = "none"
        self._speaking_pulse = 1.0
        self._listening_focus = 1.0
        
        # Idle behaviors
        self._idle_timer = 0.0
        self._next_idle = self._random_idle_time()
        self._breathing_enabled = True
        self._breathing_timer = 0.0
        self._breathing_phase = 0.0
        self._breathing_amplitude = 0.15
        self._breathing_speed = 0.8
        self._idle_threshold = 3.0
        
        # Micro-saccades
        self._saccade_timer = 0.0
        self._next_saccade = random.uniform(0.5, 2.0)
        
        # State-specific behaviors
        self._thinking_timer = 0.0
        self._thinking_phase = 0
        self._speaking_look_timer = 0.0
        self._speaking_look_away = False
        
        # Mood shake offsets
        self._anim_offset_x = 0.0
        self._anim_offset_y = 0.0
        
    # ========== Blink System ==========
    
    def _random_blink_time(self) -> float:
        """Get random blink interval based on current mood"""
        interval = BLINK_INTERVALS.get(self._mood, (3.0, 5.0))
        return random.uniform(interval[0], interval[1])
    
    def _random_idle_time(self) -> float:
        """Random time until next idle glance"""
        return random.uniform(2.0, 5.0)
    
    def blink(self, both: bool = True, left: bool = True, right: bool = True):
        """Trigger a blink"""
        if both:
            self._blink_left = True
            self._blink_right = True
        else:
            self._blink_left = left
            self._blink_right = right
        self._is_blinking = True
        self._blink_phase = 0.0
    
    # ========== State Control ==========
    
    def set_state(self, state: str):
        """Set eye state: idle, listening, thinking, speaking"""
        try:
            new_state = EyeState(state)
        except ValueError:
            new_state = EyeState.IDLE
        # Reset thinking overrides on exit
        if self._state == EyeState.THINKING and new_state != EyeState.THINKING:
            self._squint_target = 0.0
            self._thinking_timer = 0.0
        self._state = new_state
    
    def set_mood(self, mood: Mood, intensity: float = 1.0):
        """Set emotional mood with intensity (0.0 to 1.0)"""
        if self._mood != mood:
            self._prev_mood = self._mood
            self._mood_transition_progress = 0.0
            if self._mood in (Mood.SIDEEYE_LEFT, Mood.SIDEEYE_RIGHT):
                self._target_look_x = 0.0
                self._target_look_y = 0.0
                self._left_open_target = 1.0
                self._right_open_target = 1.0
        self._mood = mood
        self._mood_intensity = max(0.0, min(1.0, intensity))
        self._next_blink = self._random_blink_time()
        
        # Update glow color for this mood
        self._target_glow_color = GLOW_COLORS.get(mood, (0, 206, 209))
    
    def set_look(self, x: float, y: float):
        """Set look direction (-1 to 1)"""
        self._target_look_x = max(-1.0, min(1.0, x))
        self._target_look_y = max(-1.0, min(1.0, y))
    
    def set_pupil_scale(self, scale: float):
        """Set pupil dilation (0.5 = constricted, 1.5 = dilated)"""
        self._pupil_scale_target = max(0.5, min(1.5, scale))
    
    def set_squint(self, intensity: float):
        """Set squint intensity (0.0 = normal, 1.0 = fully squinted)"""
        self._squint_target = max(0.0, min(1.0, intensity))
    
    def set_audio_level(self, level: float, source: str):
        """Set audio level for reactive animations"""
        self._audio_level = level
        self._audio_source = source
    
    def set_breathing(self, enabled: bool, amplitude: float = 0.15, speed: float = 0.8):
        """Configure breathing animation"""
        self._breathing_enabled = enabled
        self._breathing_amplitude = max(0.0, min(0.5, amplitude))
        self._breathing_speed = max(0.5, min(3.0, speed))
    
    # ========== Query State ==========
    
    def get_current_mood(self) -> Tuple[Mood, float]:
        """Get current mood and intensity"""
        return (self._mood, self._mood_intensity)
    
    # ========== Update ==========
    
    def update(self, dt: float):
        """Update all animations and behaviors"""
        
        # Auto-blink
        if self._auto_blink and self._state != EyeState.SPEAKING:
            self._blink_timer += dt
            if self._blink_timer >= self._next_blink:
                self.blink()
                self._blink_timer = 0
                self._next_blink = self._random_blink_time()
        
        # Blink animation
        if self._is_blinking:
            self._blink_phase += dt * 12
            
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
                self._blink_left = True
                self._blink_right = True
        
        # Idle glances
        if self._state == EyeState.IDLE:
            self._idle_timer += dt
            if self._idle_timer >= self._next_idle:
                # Random glance
                self._target_look_x = random.uniform(-0.5, 0.5)
                self._target_look_y = random.uniform(-0.3, 0.2)
                self._idle_timer = 0
                self._next_idle = self._random_idle_time()
        
        # Micro-saccades (tiny quick movements)
        self._saccade_timer += dt
        if self._saccade_timer >= self._next_saccade:
            offset = random.uniform(-0.05, 0.05)
            self._target_look_x += offset
            self._target_look_x = max(-1.0, min(1.0, self._target_look_x))
            self._saccade_timer = 0
            self._next_saccade = random.uniform(0.5, 2.0)
        
        # Listening behavior
        if self._state == EyeState.LISTENING:
            self._target_look_x = 0
            self._target_look_y = 0
            base_focus = 1.25
            audio_boost = self._audio_level * 0.3 if self._audio_level > 0.1 else 0
            self._listening_focus = base_focus + audio_boost
        else:
            self._listening_focus = 1.0

        # Speaking behavior
        if self._state == EyeState.SPEAKING:
            self._speaking_look_timer += dt
            if not self._speaking_look_away:
                self._target_look_x = 0
                self._target_look_y = 0.15
            if self._speaking_look_timer > 1.8 and not self._speaking_look_away:
                if random.random() < 0.4:
                    self._target_look_x = (random.random() - 0.5) * 0.7
                    self._target_look_y = random.random() * 0.3 - 0.1
                    self._speaking_look_away = True
                self._speaking_look_timer = 0
            elif self._speaking_look_timer > 0.6 and self._speaking_look_away:
                self._target_look_x = 0
                self._target_look_y = 0.15
                self._speaking_look_away = False
                self._speaking_look_timer = 0
            if self._audio_level > 0.1:
                self._speaking_pulse = 0.85 + self._audio_level * 0.3
            else:
                self._speaking_pulse = 1.0
        
        # Thinking behavior
        if self._state == EyeState.THINKING:
            self._thinking_timer += dt
            if self._thinking_timer > 0.4 + random.random() * 0.5:
                self._thinking_timer = 0
                self._target_look_x = (random.random() - 0.5) * 2.0
                self._target_look_y = -0.5 - random.random() * 0.5
        
        # Breathing glow when idle
        if self._breathing_enabled and self._state == EyeState.IDLE:
            self._breathing_timer += dt
            if self._breathing_timer >= self._idle_threshold:
                self._breathing_phase += dt * self._breathing_speed * 3.14159 * 2
                breathing_factor = 1.0 + math.sin(self._breathing_phase) * self._breathing_amplitude
                self._glow_target = breathing_factor
        else:
            self._breathing_timer = 0.0
            self._breathing_phase = 0.0
            if self._state != EyeState.SPEAKING:
                self._glow_target = 1.0
        
        # Update mood eyelids
        self._update_mood(dt)
        
        # Smooth all values
        speed = EMOTION_TRANSITION_SPEEDS.get(self._mood, 6.0)
        
        # Smooth mood transition progress
        if self._mood_transition_progress < 1.0:
            self._mood_transition_progress += dt * 2.0  # 0.5 second transition
            self._mood_transition_progress = min(1.0, self._mood_transition_progress)
        
        self._look_x = smooth_lerp(self._look_x, self._target_look_x, 8.0, dt)
        self._look_y = smooth_lerp(self._look_y, self._target_look_y, 8.0, dt)
        self._left_open = smooth_lerp(self._left_open, self._left_open_target, speed, dt)
        self._right_open = smooth_lerp(self._right_open, self._right_open_target, speed, dt)
        self._glow_intensity = smooth_lerp(self._glow_intensity, self._glow_target, 8.0, dt)
        self._pupil_scale = smooth_lerp(self._pupil_scale, self._pupil_scale_target, 10.0, dt)
        self._squint_intensity = smooth_lerp(self._squint_intensity, self._squint_target, 6.0, dt)
        
        # Smooth glow color transition
        self._current_glow_color = tuple(
            int(smooth_lerp(self._current_glow_color[i], self._target_glow_color[i], 3.0, dt))
            for i in range(3)
        )
    
    def _update_mood(self, dt: float):
        """Update eyelid positions based on mood"""
        target_top_l = 0.0
        target_top_r = 0.0
        target_bot_l = 0.0
        target_bot_r = 0.0
        target_angle_l = 0.0
        target_angle_r = 0.0
        target_curve_l = 0.0
        target_curve_r = 0.0
        use_curved_bottom = False
        
        
        h = self.config.height * 0.5
        intensity = self._mood_intensity
        
        if self._mood == Mood.HAPPY:
            # Happy: curved bottom lids (smile eyes ^_^)
            use_curved_bottom = True
            target_curve_l = 0.48
            target_curve_r = 0.48
            self._left_open_target = 0.85
            self._right_open_target = 0.85
        
        elif self._mood == Mood.EXCITED:
            # Like happy (curved smile) but with vertical shake
            use_curved_bottom = True
            target_curve_l = 0.48
            target_curve_r = 0.48
            self._left_open_target = 1.0
            self._right_open_target = 1.0
            # Vertical shake animation
            import math
            shake = math.sin(pygame.time.get_ticks() * 0.02) * 8
            self._anim_offset_y = shake
        
        
        elif self._mood == Mood.SAD:
            # Droopy outer corners
            target_top_l = h * 0.5 * intensity
            target_top_r = h * 0.5 * intensity
            target_angle_l = 15 * intensity
            target_angle_r = -15 * intensity
            self._left_open_target = 0.8
            self._right_open_target = 0.8
        
        elif self._mood == Mood.AFRAID:
            # Like sad but with horizontal shake
            target_top_l = h * 0.5 * intensity
            target_top_r = h * 0.5 * intensity
            target_angle_l = 15 * intensity
            target_angle_r = -15 * intensity
            self._left_open_target = 0.8
            self._right_open_target = 0.8
            # Horizontal shake
            import math
            shake = math.sin(pygame.time.get_ticks() * 0.03) * 6
            self._anim_offset_x = shake
        
        elif self._mood == Mood.SIDEEYE_LEFT:
            # Looking left
            self._left_open_target = 1.3
            self._right_open_target = 0.8
            self._target_look_x = -0.9
        
        elif self._mood == Mood.SIDEEYE_RIGHT:
            # Looking right
            self._left_open_target = 0.8
            self._right_open_target = 1.3
            self._target_look_x = 0.9
        
        elif self._mood == Mood.ANGRY:
            # Slanted inner corners down
            target_top_l = h * 0.5 * intensity
            target_top_r = h * 0.5 * intensity
            target_angle_l = -30 * intensity
            target_angle_r = 30 * intensity
            self._left_open_target = 1.0
            self._right_open_target = 1.0
        
        elif self._mood == Mood.SLEEPY:
            # Narrow horizontal slits
            self._left_open_target = 0.1
            self._right_open_target = 0.1

        elif self._mood == Mood.CURIOUS:
            self._left_open_target = 1.2
            self._right_open_target = 0.85
            target_top_r = h * 0.15 * intensity
            self._target_look_x = -0.2
            self._target_look_y = -0.15

        elif self._mood == Mood.SKEPTICAL:
            self._left_open_target = 0.6
            self._right_open_target = 0.6
            self._squint_target = 0.5 * intensity
            target_top_l = h * 0.3 * intensity
            target_top_r = h * 0.3 * intensity
            self._target_look_x = 0.0
            self._target_look_y = 0.0

        elif self._mood == Mood.SMUG:
            use_curved_bottom = True
            target_curve_l = 0.25
            target_curve_r = 0.25
            self._left_open_target = 0.7
            self._right_open_target = 0.7
            target_top_l = h * 0.15 * intensity
            target_top_r = h * 0.15 * intensity
            self._target_look_y = 0.1

        elif self._mood == Mood.SURPRISED:
            self._left_open_target = 1.35
            self._right_open_target = 1.35
            target_top_l = 0.0
            target_top_r = 0.0
            target_bot_l = 0.0
            target_bot_r = 0.0
            self._pupil_scale_target = 1.3

        # Smooth transitions
        # Update curved bottom state
        self._curved_bottom_left = use_curved_bottom
        self._curved_bottom_right = use_curved_bottom
        
        speed = EMOTION_TRANSITION_SPEEDS.get(self._mood, 4.0)
        self._lid_top_left = smooth_lerp(self._lid_top_left, target_top_l, speed, dt)
        self._lid_top_right = smooth_lerp(self._lid_top_right, target_top_r, speed, dt)
        self._lid_bottom_left = smooth_lerp(self._lid_bottom_left, target_bot_l, speed, dt)
        self._lid_bottom_right = smooth_lerp(self._lid_bottom_right, target_bot_r, speed, dt)
        self._lid_angle_left = smooth_lerp(self._lid_angle_left, target_angle_l, speed, dt)
        self._lid_angle_right = smooth_lerp(self._lid_angle_right, target_angle_r, speed, dt)
        self._curved_amount_left = smooth_lerp(self._curved_amount_left, target_curve_l, speed, dt)
        self._curved_amount_right = smooth_lerp(self._curved_amount_right, target_curve_r, speed, dt)
    def draw(self, surface: pygame.Surface):
        """Draw eyes onto the surface"""
        center_y = self.screen_height // 2
        left_x = (self.screen_width - self.config.space_between) // 2 - self.config.width // 2
        right_x = (self.screen_width + self.config.space_between) // 2 - self.config.width // 2
        
        self._draw_eye(surface, left_x, center_y, True, 
                       curved_bottom=self._curved_bottom_left,
                       curve_amount=self._curved_amount_left)
        self._draw_eye(surface, right_x, center_y, False,
                        curved_bottom=self._curved_bottom_right,
                        curve_amount=self._curved_amount_right)
    
    def _draw_curved_bottom_lid(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, curve_amount: float):
        """Draw curved bottom eyelid for happy/smiling expression"""
        if curve_amount < 0.01:
            return
            
        cfg = self.config
        points = []
        num_points = 20
        curve_height = h * 0.5 * curve_amount
        
        for i in range(num_points + 1):
            t = i / num_points
            px = x + t * w
            curve = math.sin(t * math.pi)
            py = y + h * 0.75 - (curve * curve_height)
            points.append((px, py))
        
        points.append((x + w + 5, y + h + 20))
        points.append((x - 5, y + h + 20))
        pygame.draw.polygon(surface, cfg.bg_color, points)
    
    def _draw_eye(self, surface: pygame.Surface, x: int, y: int, is_left: bool, curved_bottom: bool = False, curve_amount: float = 0.0):
        """Draw a single eye"""
        # Calculate positions with look direction
        look_offset_x = int(self._look_x * self.config.width * 0.3)
        look_offset_y = int(self._look_y * self.config.height * 0.3)
        
        # Add animation offsets
        anim_x = int(self._anim_offset_x)
        anim_y = int(self._anim_offset_y)
        
        # Asymmetric offsets
        offset_y = int(self._eye_offset_y_left if is_left else self._eye_offset_y_right)
        
        total_x = x + look_offset_x + anim_x
        total_y = y + look_offset_y + anim_y + offset_y
        
        # Eye openness
        openness = (self._left_open if is_left else self._right_open) * self._speaking_pulse * self._listening_focus
        
        
        # Main eye
        eye_height = int(self.config.height * openness)
        eye_rect = pygame.Rect(
            total_x,
            total_y - eye_height // 2,
            self.config.width,
            eye_height
        )
        border_radius = min(self.config.border_radius, self.config.width // 2, eye_height // 2)
        pygame.draw.rect(surface, self._current_glow_color, eye_rect, border_radius=border_radius)
        
        # Pupil - removed per user request
        # pupil_size = int(self.config.width * 0.3 * self._pupil_scale)
        # pupil_rect = pygame.Rect(
        #     total_x + self.config.width // 2 - pupil_size // 2,
        #     total_y - pupil_size // 2,
        #     pupil_size,
        #     pupil_size
        # )
        # pygame.draw.ellipse(surface, (0, 0, 0), pupil_rect)
        
        # Eyelids
        lid_color = self.config.bg_color
        
        # Top lid
        lid_top = self._lid_top_left if is_left else self._lid_top_right
        lid_angle = self._lid_angle_left if is_left else self._lid_angle_right
        
        if lid_top > 1:
            top_y = total_y - eye_height // 2
            
            if abs(lid_angle) > 1:
                # Draw angled triangular lid for ANGRY/SAD
                if is_left:
                    if lid_angle < 0:
                        # ANGRY left: slant down from right
                        points = [
                            (total_x, top_y - 1),
                            (total_x + self.config.width, top_y - 1),
                            (total_x + self.config.width, top_y + int(lid_top))
                        ]
                    else:
                        # SAD left: droop from left
                        points = [
                            (total_x, top_y - 1),
                            (total_x + self.config.width, top_y - 1),
                            (total_x, top_y + int(lid_top))
                        ]
                else:
                    if lid_angle > 0:
                        # ANGRY right: slant down from left
                        points = [
                            (total_x, top_y - 1),
                            (total_x + self.config.width, top_y - 1),
                            (total_x, top_y + int(lid_top))
                        ]
                    else:
                        # SAD right: droop from right
                        points = [
                            (total_x, top_y - 1),
                            (total_x + self.config.width, top_y - 1),
                            (total_x + self.config.width, top_y + int(lid_top))
                        ]
                pygame.draw.polygon(surface, lid_color, points)
            else:
                # Draw straight rectangle lid
                pygame.draw.rect(surface, lid_color, 
                               (total_x - 2, top_y - 2, self.config.width + 4, int(lid_top) + 2))
        
        # Bottom eyelid overlay
        lid_bottom = self._lid_bottom_left if is_left else self._lid_bottom_right
        if curved_bottom and curve_amount > 0.01:
            # Use curved lid for happy expression
            self._draw_curved_bottom_lid(surface, total_x, total_y - eye_height // 2, self.config.width, eye_height, curve_amount)
        elif lid_bottom > 1:
            # Straight bottom lid (default)
            lid_h = int(lid_bottom)
            lid_rect = pygame.Rect(total_x - 2, total_y + eye_height - int(lid_bottom), self.config.width + 4, lid_h + 10)
            pygame.draw.rect(surface, lid_color, lid_rect)
