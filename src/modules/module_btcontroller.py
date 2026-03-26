"""
Module: BT Controller
Author: Charles-Olivier Dion (Atomikspace)
Contact: atomikspace.labs@gmail.com
Copyright (c) 2026

This module was originally redesigned by Charles-Olivier Dion (Atomikspace).

Permission is granted to use, copy, modify, and redistribute this module,
in whole or in part, provided that:

- This notice is retained in the source file(s)
- The original author (Charles-Olivier Dion / Atomikspace) is clearly credited
- Any modifications are clearly identified as such

This notice applies only to this module and does not extend to the
entire project or repository in which it may be included.
"""


import evdev
import json
import time
from evdev import InputDevice, list_devices
from pathlib import Path

from modules.module_config import load_config
from modules.module_messageQue import queue_message
import modules.module_movement_registry as registry

config = load_config()
controller_name = config["CONTROLS"]["controller_name"]
invert_y = config["CONTROLS"].get("invert_y", False)
gamepad_path = None

_SETTINGS_FILE = Path(__file__).parent.parent / "state" / "settings.json"

DEFAULT_MAPPINGS = {
    "BTN_SOUTH": "pose",
    "BTN_SOUTH+R1": "wave_right",
    "BTN_EAST": "bow",
    "BTN_EAST+R1": "wave_left",
    "BTN_EAST+R2": "side_side",
    "BTN_NORTH": "laugh",
    "BTN_NORTH+R1": "tilt_right",
    "BTN_WEST": "wiggle",
    "BTN_WEST+R1": "tilt_left",
    "DPAD_UP": "walk_forward",
    "DPAD_UP+L2": "step_forward",
    "DPAD_DOWN": "walk_backward",
    "DPAD_DOWN+L2": "step_backward",
    "DPAD_LEFT": "turn_left_slow",
    "DPAD_LEFT+L2": "turn_left",
    "DPAD_RIGHT": "turn_right_slow",
    "DPAD_RIGHT+L2": "turn_right",
}

BUTTON_NAMES = {
    evdev.ecodes.BTN_SOUTH: "BTN_SOUTH",
    evdev.ecodes.BTN_EAST: "BTN_EAST",
    evdev.ecodes.BTN_NORTH: "BTN_NORTH",
    evdev.ecodes.BTN_WEST: "BTN_WEST",
}

_mappings_cache = None
_mappings_mtime = None


def _load_mappings():
    global _mappings_cache, _mappings_mtime
    try:
        mtime = _SETTINGS_FILE.stat().st_mtime
        if mtime != _mappings_mtime:
            with open(_SETTINGS_FILE) as f:
                data = json.load(f)
            _mappings_cache = data.get("controller", {}).get("mappings", DEFAULT_MAPPINGS)
            _mappings_mtime = mtime
    except Exception:
        _mappings_cache = DEFAULT_MAPPINGS
    return _mappings_cache or DEFAULT_MAPPINGS


def _resolve_face_button(btn_name, mappings):
    """Check R2 > R1 > bare for face button, return movement name or None."""
    if r2_held and (v := mappings.get(f"{btn_name}+R2")):
        return v
    if r1_held and (v := mappings.get(f"{btn_name}+R1")):
        return v
    return mappings.get(btn_name)


def _resolve_dpad(direction, mappings):
    """Check L2 > bare for dpad direction, return movement name or None."""
    if l2_held and (v := mappings.get(f"{direction}+L2")):
        return v
    return mappings.get(direction)

l2_held = False
r1_held = False
r2_held = False

dpad_state = {"y": 0, "x": 0}
last_dpad_time = 0
DEBOUNCE_TIME = 0.1

controller_search_notified = False


def find_controller(controller_name):
    global gamepad_path, controller_search_notified
    devices = [InputDevice(path) for path in list_devices()]
    matching_devices = []
    for device in devices:
        if controller_name.lower() in device.name.lower():
            matching_devices.append(device)
    if matching_devices:
        queue_message(f"LOAD: Found {len(matching_devices)} matching device(s):")
        for device in matching_devices:
            caps = device.capabilities(verbose=True)
            has_buttons = ('EV_KEY', evdev.ecodes.EV_KEY) in caps
            queue_message(f"      - {device.name} at {device.path} (buttons: {has_buttons})")
        excluded_keywords = ["imu", "motion", "sensor"]
        for device in matching_devices:
            if any(keyword in device.name.lower() for keyword in excluded_keywords):
                continue
            caps = device.capabilities(verbose=True)
            if ('EV_KEY', evdev.ecodes.EV_KEY) in caps:
                queue_message(f"LOAD: Using: {device.name} at {device.path}")
                gamepad_path = device.path
                controller_search_notified = False
                return device
        queue_message("LOAD: No suitable controller found (no device with button support)")
        return None
    if not controller_search_notified:
        queue_message(f"LOAD: {controller_name} not found, waiting for connection...")
        controller_search_notified = True
    return None

def execute_movement(name):
    info = registry.MOVEMENTS.get(name) or registry.get_custom().get(name)
    label = info["name"] if info and "name" in info else name
    queue_message(f"CTRL: {label}")
    try:
        registry.execute(name)
    except (ValueError, RuntimeError) as e:
        queue_message(f"CTRL: {e}")

def start_controls():
    global gamepad_path, l2_held, r1_held, r2_held, dpad_state, last_dpad_time
    
    DEADZONE = 16000
    
    while gamepad_path is None:
        find_controller(controller_name)
        if gamepad_path is None:
            time.sleep(5)
    
    gamepad = None
    while gamepad is None:
        try:
            gamepad = evdev.InputDevice(gamepad_path)
            queue_message(f"LOAD: {gamepad.name} connected")
        except FileNotFoundError:
            gamepad_path = None
            time.sleep(5)
            return

    queue_message("LOAD: Controls listening...")
    try:
        for event in gamepad.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                if event.value < -DEADZONE or event.value > DEADZONE:
                    pass
                    #queue_message(f"DEBUG ABS: code={event.code} value={event.value}")
            
            if event.type == evdev.ecodes.EV_KEY:
                #queue_message(f"DEBUG KEY: code={event.code} value={event.value}")
                
                if event.code in (312, 310):
                    l2_held = (event.value == 1)
                elif event.code == 311:
                    r1_held = (event.value == 1)
                elif event.code in (313, 314):
                    r2_held = (event.value == 1)
                
                if event.value == 1:
                    btn_name = BUTTON_NAMES.get(event.code)
                    if btn_name:
                        mappings = _load_mappings()
                        movement = _resolve_face_button(btn_name, mappings)
                        if movement:
                            execute_movement(movement)

            elif event.type == evdev.ecodes.EV_ABS:
                current_time = time.time()
                
                if event.code in [evdev.ecodes.ABS_HAT0Y, evdev.ecodes.ABS_HAT0X]:
                    new_state = event.value
                else:
                    if event.value < -DEADZONE:
                        new_state = -1
                    elif event.value > DEADZONE:
                        new_state = 1
                    else:
                        new_state = 0
                
                if event.code in [evdev.ecodes.ABS_HAT0Y, evdev.ecodes.ABS_Y]:
                    if invert_y:
                        new_state = -new_state
                    if new_state != dpad_state["y"]:
                        dpad_state["y"] = new_state
                        last_dpad_time = current_time
                        mappings = _load_mappings()
                        if new_state < 0:
                            movement = _resolve_dpad("DPAD_UP", mappings)
                        elif new_state > 0:
                            movement = _resolve_dpad("DPAD_DOWN", mappings)
                        else:
                            movement = None
                        if movement:
                            execute_movement(movement)

                elif event.code in [evdev.ecodes.ABS_HAT0X, evdev.ecodes.ABS_X]:
                    if dpad_state["y"] != 0:
                        continue
                    if (current_time - last_dpad_time) < DEBOUNCE_TIME:
                        continue
                    if new_state != dpad_state["x"]:
                        dpad_state["x"] = new_state
                        last_dpad_time = current_time
                        mappings = _load_mappings()
                        if new_state < 0:
                            movement = _resolve_dpad("DPAD_LEFT", mappings)
                        elif new_state > 0:
                            movement = _resolve_dpad("DPAD_RIGHT", mappings)
                        else:
                            movement = None
                        if movement:
                            execute_movement(movement)

    except (OSError, IOError) as e:
        queue_message(f"Controller disconnected: {e}")
        gamepad_path = None
    except KeyboardInterrupt:
        pass
    finally:
        gamepad.close()

find_controller(controller_name)

if __name__ == "__main__":
    while True:
        try:
            start_controls()
        except Exception as e:
            queue_message(f"ERROR: {e}")
            time.sleep(1)