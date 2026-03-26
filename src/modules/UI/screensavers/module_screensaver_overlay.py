"""
Module: Screensaver Overlay (Time Display)
Author: Charles-Olivier Dion (AtomikSpace)
Contact: atomikspace.labs@gmail.com
Copyright (c) 2026 Charles-Olivier Dion

Non-Commercial License:
This file is licensed under Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC 4.0).
You may use, modify, and redistribute this file for NON-COMMERCIAL purposes only, with attribution.

Commercial License:
Commercial use requires a separate written license from Charles-Olivier Dion (AtomikSpace).
"""
import os
import pygame
from datetime import datetime

try:
    from modules.module_config import load_config
    _cfg = load_config()
    _ampm_format = _cfg.get('UI', {}).get('ampm_format', False)
except Exception:
    _ampm_format = False


class TimeOverlay:

    def __init__(self, width, height, rotation=0):
        self.width = width
        self.height = height
        self.ampm_format = _ampm_format
        pygame.font.init()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(os.path.dirname(script_dir), 'assets')
        font_path = os.path.join(assets_dir, 'astrolab.ttf')
        try:
            self.font = pygame.font.Font(font_path, 30)
        except Exception:
            self.font = pygame.font.SysFont('monospace', 30)

    def render(self, screen):
        current_time = datetime.now()
        if self.ampm_format:
            time_str = current_time.strftime("%I:%M:%S %p")
        else:
            time_str = current_time.strftime("%H:%M:%S")

        x_pos = 40
        y_pos = 40

        shadow_surface = self.font.render(time_str, True, (0, 0, 0))
        screen.blit(shadow_surface, (x_pos + 3, y_pos + 3))
        screen.blit(shadow_surface, (x_pos + 2, y_pos + 2))

        text_surface = self.font.render(time_str, True, (255, 255, 255))
        screen.blit(text_surface, (x_pos, y_pos))
