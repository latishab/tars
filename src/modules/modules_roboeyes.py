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
    SKEPTICAL = auto()
    SHY = auto()
    LOVE = auto()
    FEAR = auto()
    BORED = auto()
    DISGUST = auto()
    WORRIED = auto()
    CURIOUS = auto()
    SLEEPY = auto()
    FOCUSED = auto()
    PLAYFUL = auto()


class EyeState(Enum):
    """Eye states for different activities"""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


# Emotion transition speeds (higher = faster)
EMOTION_TRANSITION_SPEEDS = {
    Mood.EXCITED: 15.0,
    Mood.FEAR: 18.0,
    # Mood.SURPRISED (removed): 15.0,
    Mood.ANGRY: 10.0,
    Mood.HAPPY: 8.0,
    Mood.NEUTRAL: 6.0,
    Mood.SAD: 3.0,
    Mood.SLEEPY: 2.0,
    Mood.BORED: 4.0,
    Mood.WORRIED: 7.0,
    Mood.CURIOUS: 9.0,
    Mood.FOCUSED: 8.0,
    Mood.PLAYFUL: 10.0,
    Mood.SKEPTICAL: 7.0,
    Mood.SHY: 5.0,
    Mood.LOVE: 6.0,
    Mood.DISGUST: 8.0,
}

# Blink intervals per mood (min, max in seconds)
BLINK_INTERVALS = {
    Mood.NEUTRAL: (3.0, 5.0),
    Mood.EXCITED: (1.5, 3.0),
    Mood.FEAR: (0.5, 1.5),
    Mood.HAPPY: (2.5, 4.5),
    Mood.SAD: (4.0, 7.0),
    Mood.SLEEPY: (5.0, 10.0),
    Mood.BORED: (5.0, 10.0),
    Mood.ANGRY: (2.0, 4.0),
    Mood.WORRIED: (2.0, 3.5),
    Mood.CURIOUS: (2.5, 4.0),
    Mood.FOCUSED: (4.0, 6.0),
    Mood.PLAYFUL: (2.0, 4.0),
    Mood.SKEPTICAL: (3.0, 5.0),
    Mood.SHY: (4.0, 6.0),
    Mood.LOVE: (3.0, 5.0),
    Mood.DISGUST: (3.0, 5.0),
}

# Glow colors per mood (R, G, B)
GLOW_COLORS = {
    Mood.NEUTRAL: (0, 206, 209),      # Cyan
    Mood.HAPPY: (255, 223, 0),        # Gold
    Mood.SAD: (100, 149, 237),        # Cornflower blue
    Mood.ANGRY: (255, 69, 0),         # Red-orange
    Mood.EXCITED: (255, 165, 0),      # Orange
    Mood.LOVE: (255, 105, 180),       # Hot pink
    Mood.FEAR: (255, 255, 255),       # White
    Mood.BORED: (128, 128, 128),      # Gray
    Mood.SLEEPY: (147, 112, 219),     # Purple
    Mood.WORRIED: (255, 215, 0),      # Gold
    Mood.CURIOUS: (0, 255, 255),      # Cyan bright
    Mood.FOCUSED: (0, 191, 255),      # Deep sky blue
    Mood.PLAYFUL: (255, 192, 203),    # Pink
    Mood.SKEPTICAL: (255, 255, 0),    # Yellow
    Mood.SHY: (255, 182, 193),        # Light pink
    Mood.DISGUST: (173, 255, 47),     # Green yellow
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
            space_between=int(60 * scale)
        )
        
        # State
        self._state = EyeState.IDLE
        self._mood = Mood.NEUTRAL
        self._mood_intensity = 1.0
        
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
        
        # Animation system
        self._current_animation = None
        self._anim_timer = 0.0
        self._anim_duration = 0.0
        self._anim_phase = 0.0
        
        # Legacy animations (for compatibility)
        self._anim_laugh = False
        self._anim_laugh_timer = 0.0
        self._anim_confused = False
        self._anim_confused_timer = 0.0
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
            self._state = EyeState(state)
        except ValueError:
            self._state = EyeState.IDLE
    
    def set_mood(self, mood: Mood, intensity: float = 1.0):
        """Set emotional mood with intensity (0.0 to 1.0)"""
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
        
        if source == "bot" and level > 0.1:
            # Speaking - add subtle pulse
            self._speaking_pulse = 1.0 + level * 0.05
            self._glow_target = 1.0 + level * 0.5
        elif source == "user" and level > 0.1:
            # Listening - widen eyes slightly, focus
            self._listening_focus = min(1.15, 1.0 + level * 0.1)
            self._pupil_scale_target = 1.1  # Dilate when listening
        else:
            self._speaking_pulse = 1.0
            self._listening_focus = 1.0
    
    def set_breathing(self, enabled: bool, amplitude: float = 0.15, speed: float = 0.8):
        """Configure breathing animation"""
        self._breathing_enabled = enabled
        self._breathing_amplitude = max(0.0, min(0.5, amplitude))
        self._breathing_speed = max(0.5, min(3.0, speed))
    
    # ========== Animation Sequences ==========
    
    def is_animating(self) -> bool:
        """Check if an animation is currently playing"""
        return self._current_animation is not None
    
    def anim_wink(self, eye: str = 'right'):
        """Single eye closes briefly"""
        self._current_animation = 'wink'
        self._anim_timer = 0.0
        self._anim_duration = 0.3
        self._blink_left = (eye == 'left')
        self._blink_right = (eye == 'right')
    
    def anim_double_take(self):
        """Look away, then snap back with surprised expression"""
        self._current_animation = 'double_take'
        self._anim_timer = 0.0
        self._anim_duration = 1.5
        self._anim_phase = 0
    
    def anim_eye_roll(self):
        """Eyes roll up and around"""
        self._current_animation = 'eye_roll'
        self._anim_timer = 0.0
        self._anim_duration = 2.0
    
    def anim_excited(self):
        """Quick bounce up and down, eyes wide"""
        self._current_animation = 'excited'
        self._anim_timer = 0.0
        self._anim_duration = 0.8
    
    def anim_sleepy(self):
        """Slow droop closed, then snap back open"""
        self._current_animation = 'sleepy'
        self._anim_timer = 0.0
        self._anim_duration = 2.0
    
    def anim_thinking(self):
        """Eyes look up-left, then up-right, squint slightly"""
        self._current_animation = 'thinking'
        self._anim_timer = 0.0
        self._anim_duration = 2.5
        self._anim_phase = 0
    
    def anim_blink_fast(self):
        """Rapid double blink"""
        self._current_animation = 'blink_fast'
        self._anim_timer = 0.0
        self._anim_duration = 0.4
        self._anim_phase = 0
    
    def anim_squint_suspicious(self):
        """Slowly squint while looking at user"""
        self._current_animation = 'squint_suspicious'
        self._anim_timer = 0.0
        self._anim_duration = 1.5
    
    # Legacy animations for compatibility
    def anim_laugh(self):
        """Bouncy laugh animation"""
        self._anim_laugh = True
        self._anim_laugh_timer = 0.5
    
    def anim_confused(self):
        """Side-to-side confused shake"""
        self._anim_confused = True
        self._anim_confused_timer = 0.5
    
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
        
        # Speaking behavior
        if self._state == EyeState.SPEAKING:
            self._speaking_look_timer += dt
            if self._speaking_look_timer > 2.0 and not self._speaking_look_away:
                if random.random() < 0.3:
                    self._target_look_x = random.uniform(-0.3, 0.3)
                    self._target_look_y = random.uniform(-0.2, 0.1)
                    self._speaking_look_away = True
            elif self._speaking_look_timer > 2.5 and self._speaking_look_away:
                self._target_look_x = 0
                self._target_look_y = 0
                self._speaking_look_away = False
                self._speaking_look_timer = 0
        
        # Thinking behavior
        if self._state == EyeState.THINKING:
            self._thinking_timer += dt
            if self._thinking_timer > 1.5:
                self._thinking_timer = 0
                self._thinking_phase = (self._thinking_phase + 1) % 2
                
                if self._thinking_phase == 0:
                    self._target_look_x = -0.4
                    self._target_look_y = -0.5
                else:
                    self._target_look_x = 0.4
                    self._target_look_y = -0.5
        
        # Update animations
        self._update_animations(dt)
        
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
        
        self._look_x = smooth_lerp(self._look_x, self._target_look_x, 8.0, dt)
        self._look_y = smooth_lerp(self._look_y, self._target_look_y, 8.0, dt)
        self._left_open = smooth_lerp(self._left_open, self._left_open_target, speed * 2, dt)
        self._right_open = smooth_lerp(self._right_open, self._right_open_target, speed * 2, dt)
        self._glow_intensity = smooth_lerp(self._glow_intensity, self._glow_target, 8.0, dt)
        self._pupil_scale = smooth_lerp(self._pupil_scale, self._pupil_scale_target, 10.0, dt)
        self._squint_intensity = smooth_lerp(self._squint_intensity, self._squint_target, 6.0, dt)
        
        # Smooth glow color transition
        self._current_glow_color = tuple(
            int(smooth_lerp(self._current_glow_color[i], self._target_glow_color[i], 3.0, dt))
            for i in range(3)
        )
    
    def _update_animations(self, dt: float):
        """Update current animation sequence"""
        if self._current_animation is None:
            # Legacy animations
            if self._anim_laugh:
                self._anim_laugh_timer -= dt
                self._anim_offset_y = math.sin(self._anim_laugh_timer * 50) * 5
                if self._anim_laugh_timer <= 0:
                    self._anim_laugh = False
                    self._anim_offset_y = 0
            
            if self._anim_confused:
                self._anim_confused_timer -= dt
                self._anim_offset_x = math.sin(self._anim_confused_timer * 50) * 5
                if self._anim_confused_timer <= 0:
                    self._anim_confused = False
                    self._anim_offset_x = 0
            return
        
        self._anim_timer += dt
        progress = min(1.0, self._anim_timer / self._anim_duration)
        
        if self._current_animation == 'wink':
            if progress < 0.5:
                self._is_blinking = True
                self._blink_phase = progress * 2
            else:
                self._is_blinking = False
        
        elif self._current_animation == 'double_take':
            if progress < 0.3:
                # Look away
                self._target_look_x = 0.8
                self._target_look_y = 0.0
            elif progress < 0.35:
                # Snap back
                self._target_look_x = 0.0
                self._target_look_y = 0.0
            elif progress < 0.6:
                # Surprised
                self._left_open_target = 1.3
                self._right_open_target = 1.3
            else:
                # Return to normal
                self._left_open_target = 1.0
                self._right_open_target = 1.0
        
        elif self._current_animation == 'eye_roll':
            angle = progress * 3.14159 * 2
            self._target_look_x = math.sin(angle) * 0.6
            self._target_look_y = -math.cos(angle) * 0.6 - 0.3
        
        elif self._current_animation == 'excited':
            bounce = math.sin(progress * 3.14159 * 4) * 0.3
            self._anim_offset_y = -abs(bounce) * 10
            self._left_open_target = 1.3
            self._right_open_target = 1.3
        
        elif self._current_animation == 'sleepy':
            if progress < 0.7:
                # Droop
                self._left_open_target = 1.0 - progress / 0.7
                self._right_open_target = 1.0 - progress / 0.7
            else:
                # Snap open
                self._left_open_target = 1.0
                self._right_open_target = 1.0
        
        elif self._current_animation == 'thinking':
            cycle = int(progress * 3)
            if cycle == 0:
                self._target_look_x = -0.4
                self._target_look_y = -0.6
            elif cycle == 1:
                self._target_look_x = 0.4
                self._target_look_y = -0.6
            else:
                self._target_look_x = 0.0
                self._target_look_y = 0.0
            self._squint_target = 0.2
        
        elif self._current_animation == 'blink_fast':
            blink_cycle = int(progress * 4) % 2
            if blink_cycle == 0:
                self._left_open_target = 0.0
                self._right_open_target = 0.0
            else:
                self._left_open_target = 1.0
                self._right_open_target = 1.0
        
        elif self._current_animation == 'squint_suspicious':
            self._squint_target = progress * 0.7
            self._target_look_x = math.sin(progress * 3.14159) * 0.3
        
        # End animation
        if progress >= 1.0:
            self._current_animation = None
            self._anim_timer = 0.0
            self._anim_offset_x = 0.0
            self._anim_offset_y = 0.0
            self._squint_target = 0.0
    
    def _update_mood(self, dt: float):
        """Update eyelid positions based on mood and intensity"""
        target_top_l = 0.0
        target_top_r = 0.0
        target_bot_l = 0.0
        target_bot_r = 0.0
        target_angle_l = 0.0
        target_angle_r = 0.0
        
        h = self.config.height * 0.35
        intensity = self._mood_intensity
        
        if self._mood == Mood.HAPPY:
            target_bot_l = h * 0.5 * intensity
            target_bot_r = h * 0.5 * intensity
            self._left_open_target = max(0.7, 1.0 - 0.3 * intensity)
            self._right_open_target = max(0.7, 1.0 - 0.3 * intensity)
        
        elif self._mood == Mood.SAD:
            target_top_l = h * 0.6 * intensity
            target_top_r = h * 0.6 * intensity
            target_angle_l = 15 * intensity
            target_angle_r = -15 * intensity
            self._left_open_target = max(0.5, 1.0 - 0.5 * intensity)
            self._right_open_target = max(0.5, 1.0 - 0.5 * intensity)
        
        elif self._mood == Mood.ANGRY:
            target_top_l = h * 0.45 * intensity
            target_top_r = h * 0.45 * intensity
            target_angle_l = -25 * intensity
            target_angle_r = 25 * intensity
        
        elif self._mood == Mood.EXCITED:
            target_top_l = h * 0.15 * intensity
            target_top_r = h * 0.15 * intensity
            self._left_open_target = min(1.5, 1.0 + 0.5 * intensity)
            self._right_open_target = min(1.5, 1.0 + 0.5 * intensity)
            self._pupil_scale_target = min(1.5, 1.0 + 0.3 * intensity)
        
        elif self._mood == Mood.SKEPTICAL:
            target_top_l = h * 0.2 * intensity
            target_top_r = h * 0.5 * intensity
            target_angle_l = 20 * intensity
        
        elif self._mood == Mood.SHY:
            self._target_look_y = 0.4 * intensity
            target_top_l = h * 0.3 * intensity
            target_top_r = h * 0.3 * intensity
            self._left_open_target = max(0.7, 1.0 - 0.3 * intensity)
            self._right_open_target = max(0.7, 1.0 - 0.3 * intensity)
        
        elif self._mood == Mood.LOVE:
            target_bot_l = h * 0.3 * intensity
            target_bot_r = h * 0.3 * intensity
            self._left_open_target = min(1.3, 1.0 + 0.3 * intensity)
            self._right_open_target = min(1.3, 1.0 + 0.3 * intensity)
        
        elif self._mood == Mood.FEAR:
            self._left_open_target = min(1.5, 1.0 + 0.5 * intensity)
            self._right_open_target = min(1.5, 1.0 + 0.5 * intensity)
            self._pupil_scale_target = max(0.5, 1.0 - 0.5 * intensity)
        
        elif self._mood == Mood.BORED:
            target_top_l = h * 0.5 * intensity
            target_top_r = h * 0.5 * intensity
            self._left_open_target = max(0.5, 1.0 - 0.5 * intensity)
            self._right_open_target = max(0.5, 1.0 - 0.5 * intensity)
        
        elif self._mood == Mood.DISGUST:
            target_top_l = h * 0.4 * intensity
            target_top_r = h * 0.5 * intensity
            target_bot_l = h * 0.2 * intensity
            target_angle_l = -15 * intensity
            target_angle_r = 10 * intensity
        
        elif self._mood == Mood.WORRIED:
            target_top_l = h * 0.25 * intensity
            target_top_r = h * 0.35 * intensity
            target_angle_l = 10 * intensity
            self._left_open_target = min(1.2, 1.0 + 0.2 * intensity)
            self._right_open_target = min(1.2, 1.0 + 0.2 * intensity)
        
        elif self._mood == Mood.CURIOUS:
            target_top_l = h * 0.2 * intensity
            target_top_r = h * 0.4 * intensity
            target_angle_l = 15 * intensity
            self._left_open_target = min(1.2, 1.0 + 0.2 * intensity)
        
        elif self._mood == Mood.SLEEPY:
            target_top_l = h * 0.6 * intensity
            target_top_r = h * 0.6 * intensity
            self._left_open_target = max(0.3, 1.0 - 0.7 * intensity)
            self._right_open_target = max(0.3, 1.0 - 0.7 * intensity)
        
        elif self._mood == Mood.FOCUSED:
            target_top_l = h * 0.3 * intensity
            target_top_r = h * 0.3 * intensity
            self._left_open_target = max(0.8, 1.0 - 0.2 * intensity)
            self._right_open_target = max(0.8, 1.0 - 0.2 * intensity)
        
        elif self._mood == Mood.PLAYFUL:
            target_bot_l = h * 0.3 * intensity
            target_angle_l = -10 * intensity
            target_angle_r = 10 * intensity
            self._left_open_target = 1.0
            self._right_open_target = max(0.6, 1.0 - 0.4 * intensity)
        
        # Smooth transitions
        speed = EMOTION_TRANSITION_SPEEDS.get(self._mood, 6.0)
        self._lid_top_left = smooth_lerp(self._lid_top_left, target_top_l, speed, dt)
        self._lid_top_right = smooth_lerp(self._lid_top_right, target_top_r, speed, dt)
        self._lid_bottom_left = smooth_lerp(self._lid_bottom_left, target_bot_l, speed, dt)
        self._lid_bottom_right = smooth_lerp(self._lid_bottom_right, target_bot_r, speed, dt)
        self._lid_angle_left = smooth_lerp(self._lid_angle_left, target_angle_l, speed, dt)
        self._lid_angle_right = smooth_lerp(self._lid_angle_right, target_angle_r, speed, dt)
    
    # ========== Draw ==========
    
    def draw(self, surface: pygame.Surface):
        """Draw eyes onto the surface"""
        center_y = self.screen_height // 2
        left_x = (self.screen_width - self.config.space_between) // 2 - self.config.width // 2
        right_x = (self.screen_width + self.config.space_between) // 2 - self.config.width // 2
        
        self._draw_eye(surface, left_x, center_y, True)
        self._draw_eye(surface, right_x, center_y, False)
    
    def _draw_eye(self, surface: pygame.Surface, x: int, y: int, is_left: bool):
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
        
        # Glow layer
        if self._glow_intensity > 0.1:
            glow_surface = pygame.Surface(
                (self.config.width + 40, int(self.config.height * openness) + 40),
                pygame.SRCALPHA
            )
            glow_alpha = int(self.config.glow_alpha * self._glow_intensity)
            glow_color = self._current_glow_color + (glow_alpha,)
            pygame.draw.ellipse(
                glow_surface,
                glow_color,
                (0, 0, self.config.width + 40, int(self.config.height * openness) + 40),
                border_radius=self.config.border_radius + 20
            )
            surface.blit(glow_surface, (total_x - 20, total_y - int(self.config.height * openness / 2) - 20))
        
        # Main eye
        eye_height = int(self.config.height * openness)
        eye_rect = pygame.Rect(
            total_x,
            total_y - eye_height // 2,
            self.config.width,
            eye_height
        )
        pygame.draw.ellipse(surface, self.config.eye_color, eye_rect, border_radius=self.config.border_radius)
        
        # Pupil
        pupil_size = int(self.config.width * 0.3 * self._pupil_scale)
        pupil_rect = pygame.Rect(
            total_x + self.config.width // 2 - pupil_size // 2,
            total_y - pupil_size // 2,
            pupil_size,
            pupil_size
        )
        pygame.draw.ellipse(surface, (0, 0, 0), pupil_rect)
        
        # Eyelids
        lid_color = self.config.bg_color
        
        # Top lid
        lid_top = self._lid_top_left if is_left else self._lid_top_right
        lid_angle = self._lid_angle_left if is_left else self._lid_angle_right
        
        if lid_top > 0:
            top_surface = pygame.Surface((self.config.width + 10, int(lid_top) + 10), pygame.SRCALPHA)
            top_surface.fill((0, 0, 0, 0))
            pygame.draw.rect(top_surface, lid_color, (0, 0, self.config.width + 10, int(lid_top) + 10))
            
            if lid_angle != 0:
                top_surface = pygame.transform.rotate(top_surface, lid_angle)
            
            surface.blit(top_surface, (total_x - 5, total_y - eye_height // 2 - 5))
        
        # Bottom lid
        lid_bottom = self._lid_bottom_left if is_left else self._lid_bottom_right
        if lid_bottom > 0:
            pygame.draw.rect(
                surface,
                lid_color,
                (total_x, total_y + eye_height // 2, self.config.width, int(lid_bottom))
            )
