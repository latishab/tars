"""
module_config.py

Configuration loader for the TARS daemon.
Reads hardware settings from config.ini.
"""

import os
import configparser

from modules.module_messageQue import queue_message


def load_config():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config = configparser.ConfigParser()
    config_path = os.path.join(base_dir, 'config.ini')
    config.read(config_path)

    required_sections = ['CONTROLS', 'SERVO', 'BATTERY', 'MISC']
    missing_sections = [s for s in required_sections if s not in config]

    if missing_sections:
        queue_message(f"ERROR: Missing sections in config.ini: {', '.join(missing_sections)}")
        raise SystemExit(1)

    return {
        "BASE_DIR": base_dir,
        "CONTROLS": {
            "controller_name": config.get('CONTROLS', 'controller_name', fallback='8BitDo'),
            "enabled": config.getboolean('CONTROLS', 'enabled', fallback=False),
            "voicemovement": config.getboolean('CONTROLS', 'voicemovement', fallback=False),
            "swap_turn_directions": config.getboolean('CONTROLS', 'swap_turn_directions', fallback=False),
            "invert_y": config.getboolean('CONTROLS', 'invert_y', fallback=False),
        },
        "SERVO": {
            "leftUpHeight": config['SERVO']['leftUpHeight'],
            "leftDownHeight": config['SERVO']['leftDownHeight'],
            "perfectLeftHeightOffset": config['SERVO']['perfectLeftHeightOffset'],
            "rightUpHeight": config['SERVO']['rightUpHeight'],
            "rightDownHeight": config['SERVO']['rightDownHeight'],
            "perfectRightHeightOffset": config['SERVO']['perfectRightHeightOffset'],
            "forwardLeftLeg": config['SERVO']['forwardLeftLeg'],
            "backLeftLeg": config['SERVO']['backLeftLeg'],
            "perfectLeftLegOffset": config['SERVO']['perfectLeftLegOffset'],
            "forwardRightLeg": config['SERVO']['forwardRightLeg'],
            "backRightLeg": config['SERVO']['backRightLeg'],
            "perfectRightLegOffset": config['SERVO']['perfectRightLegOffset'],
        },
        "BATTERY": {
            "battery_capacity_mAh": int(config['BATTERY']['battery_capacity_mAh']),
            "battery_initial_voltage": float(config['BATTERY']['battery_initial_voltage']),
            "battery_cutoff_voltage": float(config['BATTERY']['battery_cutoff_voltage']),
            "auto_shutdown": config.getboolean('BATTERY', 'auto_shutdown'),
        },
        "MISC": {
            "ventilate": config.getboolean('MISC', 'ventilate', fallback=False),
        },
        "UI": {
            "default_app": config.get('UI', 'default_app', fallback='eyes'),
            "screensaver_timer": config.getint('UI', 'screensaver_timer', fallback=300),
            "screensaver_cycle_interval": config.getint('UI', 'screensaver_cycle_interval', fallback=300),
            "screensaver_list": [s.strip() for s in config.get('UI', 'screensaver_list', fallback='random').split(',')],
            "show_time": config.getboolean('UI', 'show_time', fallback=True),
            "ampm_format": config.getboolean('UI', 'ampm_format', fallback=True),
            "target_fps": config.getint('UI', 'target_fps', fallback=30),
        },
    }
