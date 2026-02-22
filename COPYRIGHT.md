# Copyright & Ownership

This project is a fork of [TARS-AI-Community/TARS-AI](https://github.com/TARS-AI-Community/TARS-AI) by Charles-Olivier Dion (AtomikSpace).

## Original Author: AtomikSpace (Charles-Olivier Dion)

**License**: Dual-licensed (CC-BY-NC 4.0 for non-commercial use, separate license required for commercial use)

The following modules and files are original work by AtomikSpace:

### Hardware Control Modules
- `module_movements.py` - Robot movement sequences and choreography
- `module_movement_registry.py` - Movement registration system
- `module_servoctl.py` - Servo motor control via PCA9685
- `module_battery.py` - Battery monitoring (INA219)
- `module_cputemp.py` - CPU temperature monitoring
- `module_btcontroller.py` - Bluetooth gamepad controller support

### 3D Design Files
- All STL files in `3d-files/` - Physical robot design and parts

### Test Applications
- `app_eyes_test.py`
- `app_movements_test.py`
- `app_servo_config_tool.py`
- `app_walk_demo.py`

**Commercial Use**: AtomikSpace's files require a separate commercial license. See [DUAL-LICENSE.md](DUAL-LICENSE.md) for details. Contact: charles.olivier.dion@gmail.com

---

## Fork Maintainer: Latisha B

**License**: CC-BY-NC 4.0 (non-commercial use only)

**Repository**: https://github.com/latishab/tars

The following components were added by Latisha B:

### Core Daemon Architecture
- `tars_daemon.py` - FastAPI-based daemon server (HTTP + gRPC + WebRTC)
- `daemon_config.py` - Daemon configuration management
- `module_hardware_controller.py` - Unified hardware interface layer

### Dashboard (Web UI)
- `dashboard/` - Full React-based web dashboard
  - Robot control interface (movements, emotions, eyes)
  - System monitoring (battery, CPU, camera)
  - App management system
  - WiFi configuration
  - Settings and OTA updates

### Communication Protocols
- `grpc_server/` - gRPC server for low-latency hardware control
  - Protocol buffers definitions
  - Streaming API for movements, emotions, eye states
- `webrtc/` - WebRTC audio streaming server
  - P2P audio connection for real-time voice I/O

### SDK & API
- `tars_sdk/` - Python SDK for TARS control
  - HTTP client
  - gRPC client
  - Unified API interface

### Display & Eyes System
- `module_display.py` - OLED display manager (SSD1306)
- `modules_roboeyes.py` - Animated eye expressions system

### Supporting Infrastructure
- `app_manager.py` - App installation, lifecycle management
- `wifi_manager.py` - WiFi/hotspot configuration
- `module_systeminfo.py` - System metrics aggregation
- Setup wizard, OTA update system, logging infrastructure

**Commercial Use**: Latisha's additions are also CC-BY-NC 4.0. For commercial licensing of these components, contact via GitHub.

---

## Summary

| Component | Original Author | License | Commercial Use |
|-----------|----------------|---------|----------------|
| Hardware modules (movements, servo, battery, BT) | AtomikSpace | CC-BY-NC 4.0 / Dual | Requires AtomikSpace commercial license |
| 3D design files | AtomikSpace | CC-BY-NC 4.0 / Dual | Requires AtomikSpace commercial license |
| Test apps | AtomikSpace | CC-BY-NC 4.0 / Dual | Requires AtomikSpace commercial license |
| Daemon, dashboard, gRPC, WebRTC, SDK | Latisha B | CC-BY-NC 4.0 | Requires Latisha B commercial license |
| Display, eyes, app manager, WiFi manager | Latisha B | CC-BY-NC 4.0 | Requires Latisha B commercial license |

**Attribution Requirements**: Both authors must be credited when using this project or derivative works.

**Non-Commercial License**: [Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)

See [DUAL-LICENSE.md](DUAL-LICENSE.md) for AtomikSpace's dual-license details.
