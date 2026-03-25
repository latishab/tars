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
    # locomotion — robot displaces through space
    "step_forward":     {"name": "Step Forward",    "type": "locomotion"},
    "walk_forward":     {"name": "Walk Forward",    "type": "locomotion"},
    "step_backward":    {"name": "Step Backward",   "type": "locomotion"},
    "walk_backward":    {"name": "Walk Backward",   "type": "locomotion"},
    "turn_right":       {"name": "Turn Right",      "type": "locomotion"},
    "turn_right_slow":  {"name": "Turn Right Slow", "type": "locomotion"},
    "turn_left":        {"name": "Turn Left",       "type": "locomotion"},
    "turn_left_slow":   {"name": "Turn Left Slow",  "type": "locomotion"},
    # gesture — servo movement, no displacement
    "pose":             {"name": "Pose",            "type": "gesture"},
    "bow":              {"name": "Bow",             "type": "gesture"},
    "tilt_right":       {"name": "Tilt Right",      "type": "gesture"},
    "tilt_left":        {"name": "Tilt Left",       "type": "gesture"},
    "side_side":        {"name": "Side Side",       "type": "gesture"},
    "wave_right":       {"name": "Wave Right",      "type": "gesture"},
    "wave_left":        {"name": "Wave Left",       "type": "gesture"},
    "neutral_legs":     {"name": "Neutral Legs",    "type": "gesture"},
    "laugh":            {"name": "Laugh",           "type": "gesture"},
    "swing_legs":       {"name": "Swing Legs",      "type": "gesture"},
    "tilt_quick_right": {"name": "Tilt Quick Right","type": "gesture"},
    "tilt_quick_left":  {"name": "Tilt Quick Left", "type": "gesture"},
    "wiggle":           {"name": "Wiggle",          "type": "gesture"},
    "wave_short":       {"name": "Wave Short",      "type": "gesture"},
}

def get_all():
    return MOVEMENTS

def get_names():
    return [(v["name"], k) for k, v in MOVEMENTS.items()]