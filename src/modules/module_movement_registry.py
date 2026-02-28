"""
Module : Movement Registry
Author: Charles-Olivier Dion (AtomikSpace)
Contact: atomikspace.labs@gmail.com
Copyright (c) 2026 Charles-Olivier Dion

This file is authored by Charles-Olivier Dion and is dual-licensed.

Non-Commercial License:
This file is licensed under Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC 4.0).
You may use, modify, and redistribute this file for NON-COMMERCIAL purposes only, with attribution.

Commercial License:
Commercial use (including selling products, paid services, SaaS, subscriptions, Patreon rewards, or derivatives)
requires a separate written license from Charles-Olivier Dion (AtomikSpace).

This license applies only to this file and does not override licenses of other files in the repository.
"""

MOVEMENTS = {
    "step_forward": {"name": "Step Forward"},
    "walk_forward": {"name": "Walk Forward"},
    "step_backward": {"name": "Step Backward"},
    "walk_backward": {"name": "Walk Backward"},
    "turn_right": {"name": "Turn Right"},
    "turn_right_slow": {"name": "Turn Right Slow"},
    "turn_left": {"name": "Turn Left"},
    "turn_left_slow": {"name": "Turn Left Slow"},
    "pose": {"name": "Pose"},
    "bow": {"name": "Bow"},
    "tilt_right": {"name": "Tilt Right"},
    "tilt_left": {"name": "Tilt Left"},
    "side_side": {"name": "Side Side"},
    "wave_right": {"name": "Wave Right"},
    "wave_left": {"name": "Wave Left"},
    "neutral_legs": {"name": "Neutral Legs"},
    "laugh": {"name": "Laugh"},
    "swing_legs": {"name": "Swing Legs"},
    "tilt_quick_right": {"name": "Tilt Quick Right"},
    "tilt_quick_left": {"name": "Tilt Quick Left"},
    "wiggle": {"name": "Wiggle"},
    "wave_short": {"name": "Wave Short"},
}

def get_all():
    return MOVEMENTS

def get_names():
    return [(v["name"], k) for k, v in MOVEMENTS.items()]