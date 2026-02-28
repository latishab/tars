"""
Module: Movements
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
import time
import modules.module_servoctl as servoctl

move_legs = servoctl.move_legs
disable_all_servos = servoctl.disable_all_servos

_swap_directions = False

def set_swap_turn_directions(swap: bool):
    """Set whether to swap left/right turn directions"""
    global _swap_directions
    _swap_directions = swap

def get_swap_turn_directions() -> bool:
    """Get current direction swap setting"""
    return _swap_directions


def step_forward():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.9)
            move_legs(42, 42, 40, 40, 0.9)
            move_legs(70, 70, 23, 23, 0.9)
            move_legs(30, 30, 30, 30, 0.8)
            move_legs(70, 70, 35, 35, 0.9)
            move_legs(60, 60, 50, 50, 0.9)
            move_legs(50, 50, 50, 50, 0.9)

            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def walk_forward():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.8)
            sequence = [
                (40, 70, 50, 50),
                (40, 70, 35, 50),
                (50, 50, 35, 50),
                (70, 40, 50, 50),
                (70, 40, 50, 35),
                (50, 50, 50, 35),
            ]
            for _ in range(2):
                for a, b, c, d in sequence:
                    move_legs(a, b, c, d, 0.5)
            for a, b, c, d in sequence[:3]:
                move_legs(a, b, c, d, 0.5)
            move_legs(70, 40, 35, 50, 0.5)
            move_legs(70, 40, 50, 50, 0.5)
            move_legs(50, 50, 50, 50, 0.8)

            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def step_backward():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.9)
            move_legs(30, 30, 55, 55, 0.8)
            move_legs(68, 68, 82, 82, 0.8)
            move_legs(30, 30, 70, 70, 0.8)
            move_legs(50, 50, 62, 62, 0.9)
            move_legs(65, 65, 50, 50, 0.9)
            move_legs(50, 50, 50, 50, 0.9)

            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def walk_backward():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.8)
            sequence = [
                (50, 65, 50, 50),
                (50, 65, 50, 75),
                (50, 50, 50, 75),
                (65, 50, 50, 50),
                (65, 50, 75, 50),
                (50, 50, 75, 50),
            ]
            for _ in range(2):
                for a, b, c, d in sequence:
                    move_legs(a, b, c, d, 0.5)
            for a, b, c, d in sequence[:3]:
                move_legs(a, b, c, d, 0.5)
            move_legs(65, 50, 50, 75, 0.5)
            move_legs(65, 50, 50, 50, 0.5)
            move_legs(50, 50, 50, 50, 0.8)

            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def _turn_right_impl():
    """Internal implementation of turn right"""
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.9)
            move_legs(70, 70, 50, 50, 0.9)
            move_legs(70, 70, 65, 35, 0.9)
            move_legs(45, 45, 65, 35, 0.9)
            move_legs(52, 52, 50, 50, 0.8)
            move_legs(50, 50, 50, 50, 0.8)
            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def _turn_right_slow_impl():
    """Internal implementation of turn right slow"""
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.9)
            move_legs(40, 70, 50, 50, 0.7)
            move_legs(40, 70, 40, 50, 0.7)
            move_legs(70, 50, 40, 50, 0.7)
            move_legs(70, 50, 50, 50, 0.7)
            move_legs(50, 50, 50, 50, 0.9)
            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def _turn_left_impl():
    """Internal implementation of turn left"""
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.9)
            move_legs(70, 70, 50, 50, 0.9)
            move_legs(70, 70, 35, 65, 0.9)
            move_legs(45, 45, 35, 65, 0.9)
            move_legs(52, 52, 50, 50, 0.8)
            move_legs(50, 50, 50, 50, 0.8)
            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def _turn_left_slow_impl():
    """Internal implementation of turn left slow"""
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.9)
            move_legs(70, 40, 50, 50, 0.7)
            move_legs(70, 40, 50, 40, 0.7)
            move_legs(50, 70, 50, 40, 0.7)
            move_legs(50, 70, 50, 50, 0.7)
            move_legs(50, 50, 50, 50, 0.9)
            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def turn_right():
    """Turn right (or left if swap_turn_directions is enabled)"""
    if _swap_directions:
        _turn_left_impl()
    else:
        _turn_right_impl()


def turn_right_slow():
    """Turn right slowly (or left if swap_turn_directions is enabled)"""
    if _swap_directions:
        _turn_left_slow_impl()
    else:
        _turn_right_slow_impl()


def turn_left():
    """Turn left (or right if swap_turn_directions is enabled)"""
    if _swap_directions:
        _turn_right_impl()
    else:
        _turn_left_impl()


def turn_left_slow():
    """Turn left slowly (or right if swap_turn_directions is enabled)"""
    if _swap_directions:
        _turn_right_slow_impl()
    else:
        _turn_left_slow_impl()


def laugh():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            for _ in range(5):
                move_legs(50, 50, 50, 50, 1)
                time.sleep(0.1)
                move_legs(1, 1, 50, 50, 1)
                time.sleep(0.1)
            move_legs(50, 50, 50, 50, 1)
            time.sleep(0.2)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()

def swing_legs():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 1)
            time.sleep(0.1)
            move_legs(100, 100, 50, 50, 1)
            time.sleep(0.1)
            for _ in range(3):
                move_legs(0, 0, 20, 80, 0.6)
                time.sleep(0.1)
                move_legs(0, 0, 80, 20, 0.6)
                time.sleep(0.1)
            move_legs(0, 0, 50, 50, 0.6)
            time.sleep(0.1)
            move_legs(50, 50, 50, 50, 0.7)
            time.sleep(0.2)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def pose():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.6)
            move_legs(30, 30, 40, 40, 0.6)
            move_legs(90, 90, 30, 30, 0.6)
            time.sleep(3)
            move_legs(90, 90, 30, 30, 0.8)
            move_legs(30, 30, 30, 30, 0.8)
            move_legs(30, 30, 40, 40, 0.6)
            move_legs(50, 50, 50, 50, 0.6)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()



def tilt_quick_right():
    """Quick tilt right and hold. Curiosity, 'hmm?'."""
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.85)
            move_legs(35, 65, 50, 50, 0.85)   # tilt right
            time.sleep(0.4)
            move_legs(50, 50, 50, 50, 0.8)    # return
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def tilt_quick_left():
    """Quick tilt left and hold. Thinking, considering."""
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.85)
            move_legs(65, 35, 50, 50, 0.85)   # tilt left
            time.sleep(0.4)
            move_legs(50, 50, 50, 50, 0.8)    # return
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def wiggle():
    """Quick side-to-side wiggle. Amusement, playful."""
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.85)
            for _ in range(2):
                move_legs(42, 58, 50, 50, 0.9)   # small range, can be faster
                move_legs(58, 42, 50, 50, 0.9)
            move_legs(50, 50, 50, 50, 0.8)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def wave_short():
    """Quick 2-cycle wave. Short greeting."""
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.8)
            move_legs(50, 80, 50, 50, 0.8)    # raise right side (planted left supports)
            move_legs(30, 80, 50, 85, 0.85)   # wave out
            move_legs(30, 80, 50, 60, 0.85)   # wave in
            move_legs(30, 80, 50, 85, 0.85)   # wave out
            move_legs(30, 80, 50, 60, 0.85)   # wave in
            move_legs(50, 50, 50, 50, 0.7)    # return (slow, rebalancing)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def bow():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.4)
            move_legs(15, 15, 50, 50, 0.7)
            move_legs(15, 15, 70, 70, 0.7)
            move_legs(60, 60, 70, 70, 0.7)
            move_legs(95, 95, 65, 65, 0.7)
            time.sleep(3)
            move_legs(15, 15, 65, 65, 0.7)
            move_legs(50, 50, 50, 50, 0.4)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def tilt_right():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.9)
            move_legs(20, 80, 50, 50, 0.9)
            time.sleep(3)
            move_legs(50, 50, 50, 50, 0.9)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def tilt_left():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.9)
            move_legs(80, 20, 50, 50, 0.9)
            time.sleep(3)
            move_legs(50, 50, 50, 50, 0.9)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def side_side():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.8)
            move_legs(10, 90, 50, 50, 0.9)
            move_legs(90, 10, 50, 50, 0.9)
            move_legs(10, 90, 50, 50, 0.9)
            move_legs(90, 10, 50, 50, 0.9)
            move_legs(10, 90, 50, 50, 0.9)
            move_legs(90, 10, 50, 50, 0.9)
            move_legs(50, 50, 50, 50, 0.9)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def wave_right():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.8)
            move_legs(50, 90, 50, 50, 0.9)
            move_legs(20, 90, 50, 100, 0.9)
            move_legs(20, 90, 50, 70, 0.9)
            move_legs(20, 90, 50, 100, 0.9)
            move_legs(20, 90, 50, 70, 0.9)
            move_legs(50, 90, 50, 100, 0.9)
            move_legs(50, 90, 50, 70, 0.9)
            move_legs(50, 90, 50, 100, 0.9)
            move_legs(50, 90, 50, 70, 0.9)
            move_legs(20, 90, 50, 100, 0.9)
            move_legs(20, 90, 50, 70, 0.9)
            move_legs(20, 90, 50, 100, 0.9)
            move_legs(20, 90, 50, 70, 0.9)
            move_legs(50, 50, 50, 50, 0.8)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def wave_left():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(50, 50, 50, 50, 0.8)
            move_legs(90, 50, 50, 50, 0.9)
            move_legs(90, 20, 100, 50, 0.9)
            move_legs(90, 20, 70, 50, 0.9)
            move_legs(90, 20, 100, 50, 0.9)
            move_legs(90, 20, 70, 50, 0.9)
            move_legs(90, 50, 100, 50, 0.9)
            move_legs(90, 50, 70, 50, 0.9)
            move_legs(90, 50, 100, 50, 0.9)
            move_legs(90, 50, 70, 50, 0.9)
            move_legs(90, 20, 100, 50, 0.9)
            move_legs(90, 20, 70, 50, 0.9)
            move_legs(90, 20, 100, 50, 0.9)
            move_legs(90, 20, 70, 50, 0.9)
            move_legs(50, 50, 50, 50, 0.8)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def neutral_legs():
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._notify_movement_start()
        try:
            move_legs(90, 90, None, None, 0.8)
            move_legs(90, 90, 50, 50, 0.8)
            move_legs(50, 50, 50, 50, 0.8)
            disable_all_servos()
        finally:
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def ventilate_on():
    """
    Position tars for better airflow
    """
    if not servoctl.MOVING:
        servoctl.MOVING = True
        servoctl._is_ventilate_operation = True
        
        servoctl._notify_movement_start()
        try:
            from modules.module_cputemp import set_ventilating
            
            move_legs(50, 50, 50, 50, 0.8)
            move_legs(25, 25, 50, 50, 0.75)
            move_legs(25, 25, 42, 42, 0.75)
            move_legs(55, 55, 30, 30, 0.75)

            set_ventilating(True)
            
            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl._is_ventilate_operation = False
            servoctl.MOVING = False
            servoctl._notify_movement_end()


def ventilate_off():
    from modules.module_cputemp import is_ventilating, set_ventilating
    
    if is_ventilating():
        was_moving = servoctl.MOVING

        servoctl.MOVING = True
        servoctl._is_ventilate_operation = True
        
        if not was_moving:
            servoctl._notify_movement_start()
        
        try:
            move_legs(55, 55, 30, 30, 0.75)
            move_legs(25, 25, 30, 30, 0.75)
            move_legs(25, 25, 50, 50, 0.75)
            move_legs(50, 50, 50, 50, 0.75)
            
            set_ventilating(False)
            
            time.sleep(0.1)
            disable_all_servos()
        finally:
            servoctl._is_ventilate_operation = False
            servoctl.MOVING = was_moving
            if not was_moving:
                servoctl._notify_movement_end()