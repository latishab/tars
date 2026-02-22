# Copyright & Attribution Notice

This project builds on work from the TARS-AI community and multiple contributors.

## Attribution Chain

Based on the mechanical puppet designs by Christopher Nolan, Nathan Crowley, and the production team who originally brought TARS to life—miniaturized CAD by Charlie Diaz, with additional modifications by the TARS-AI Community, AtomikSpace, and Latisha B.

---

## Christopher Nolan / Production Team

**Scope:** Original TARS character design from the film *Interstellar*.

TARS was created by Christopher Nolan, Nathan Crowley, and the production team for the 2014 film *Interstellar*. This project is a fan-made initiative inspired by that design.

**Rights:** All intellectual property rights for the original TARS character remain with Warner Bros. Entertainment Inc. and the production team.

---

## Charlie Diaz - Original Creator

**Scope:** Original miniaturized CAD files and code for TARS.

Charlie Diaz created the original miniaturized CAD designs and scripts that made it possible to build a functional TARS replica.

**Available at:** [Hackster.io](https://www.hackster.io/charlesdiaz/how-to-build-your-own-replica-of-tars-from-interstellar-224833)

**License:** See upstream [ATTRIBUTION.md](https://github.com/TARS-AI-Community/TARS-AI/blob/V2/ATTRIBUTION.md) for full attribution requirements.

---

## TARS-AI Community

**Scope:** Community project building on Charlie Diaz's work.

- **Upstream repository:** https://github.com/TARS-AI-Community/TARS-AI
- Includes AME code by "exploding cat" (MIT License) for module engine and memory functions
- Community contributions and improvements

**License:** CC-BY-NC 4.0

---

## Charles-Olivier Dion (AtomikSpace) - Hardware Developer

Copyright (c) 2026 Charles-Olivier Dion (AtomikSpace)

**Scope:** TARS V2 hardware, modified CAD files, and hardware software.

**Includes:**
- TARS V2 hardware design and modifications
- Modified 3D CAD files
- Hardware control modules:
  - `src/modules/module_movements.py` - Servo movement control
  - `src/modules/module_movement_registry.py` - Movement registry
  - `src/modules/module_cputemp.py` - CPU temperature monitoring
  - `src/app-cms.py` - Configuration management system
  - `src/ina260_Battery_Sensor_Test.py` - Battery sensor testing
  - `src/app-servotester.py` - Servo testing utility

**License:** Dual-licensed (see [DUAL-LICENSE.md](DUAL-LICENSE.md))
- **Non-commercial:** CC-BY-NC 4.0
- **Commercial:** Requires separate written license from AtomikSpace

**Contact:** atomikspace.labs@gmail.com

**How to identify:** Files with header `Author: Charles-Olivier Dion (AtomikSpace)`

---

## Latisha B - Fork Maintainer

Copyright (c) 2026 Latisha B

**Scope:** All additions and modifications made after forking from TARS-AI Community.

**Includes:**
- **Daemon Architecture:** Unified daemon system (`tars_daemon.py`, `daemon_config.py`)
- **Hardware Interface:** `module_hardware_controller.py` - Unified hardware abstraction layer
- **Communication Protocols:**
  - gRPC server for low-latency hardware control (`grpc_server/`)
  - WebRTC audio streaming server (`webrtc/`)
- **Dashboard:** Full React-based web UI (`dashboard/`)
  - Robot control interface
  - System monitoring
  - App management system
  - WiFi configuration
  - Settings and OTA updates
- **SDK & API:** Python SDK for TARS control (`tars_sdk/`)
- **Display & Eyes:**
  - `module_display.py` - OLED display manager
  - `modules_roboeyes.py` - Animated eye expressions system
- **Supporting Infrastructure:**
  - `app_manager.py` - App lifecycle management
  - `wifi_manager.py` - WiFi/hotspot configuration
  - `module_systeminfo.py` - System metrics
  - Setup wizard, OTA update system, logging infrastructure
- **Documentation:** All guides and documentation

**License:** CC-BY-NC 4.0 (see [LICENSE](LICENSE))

Non-commercial use is freely permitted with attribution. Commercial use is not permitted under this license.

**Repository:** https://github.com/latishab/tars

---

## How to Identify Ownership

- **Christopher Nolan / Production Team:** Original TARS character design (Interstellar film)
- **Charlie Diaz:** Original miniaturized CAD files and scripts (see upstream repo)
- **TARS-AI Community:** Base project structure, community contributions
- **AME by "exploding cat":** Module engine and memory functions (MIT License)
- **AtomikSpace:** Files with header `Author: Charles-Olivier Dion (AtomikSpace)`
- **Latisha B:** Files added/modified after fork (check git history)

---

## License Summary

| Component | Copyright Holder | License |
|-----------|------------------|---------|
| Original TARS design | Warner Bros. / Production Team | All rights reserved (fan project) |
| Original CAD files | Charlie Diaz | See upstream ATTRIBUTION.md |
| AME code | exploding cat | MIT |
| TARS-AI Community code | TARS-AI Community | CC-BY-NC 4.0 |
| AtomikSpace contributions | Charles-Olivier Dion | CC-BY-NC 4.0 / Dual (commercial requires separate license) |
| Latisha B additions | Latisha B | CC-BY-NC 4.0 |

---

## Attribution Requirements

When using or distributing this project or derivatives:

1. **Film Attribution:** State that this project is based on the character TARS from *Interstellar*
2. **Charlie Diaz Attribution:** Credit Charlie Diaz for the original miniaturized CAD designs
3. **TARS-AI Community Attribution:** Credit the TARS-AI Community for the base project
4. **AtomikSpace Attribution:** Include: "Contains contributions by Charles-Olivier Dion (AtomikSpace)"
5. **Latisha B Attribution:** Credit Latisha B for daemon architecture and additions
6. **AME Attribution:** Include MIT license notice for AME code

See [ATTRIBUTION.md](ATTRIBUTION.md) for detailed attribution guidelines.

---

## Commercial Use

**All components listed above are licensed under CC-BY-NC 4.0 or more restrictive terms.**

Commercial use includes:
- Selling 3D printed parts, kits, or complete robots
- Selling or distributing CAD files for money
- Offering paid assembly, customization, or installation services
- Monetized content that distributes project files or derivatives
- Using this project in paid products, commercial research, or corporate projects
- Integrating into commercial software or hardware products

**For commercial use, you must obtain separate licenses from ALL applicable copyright holders:**

- **AtomikSpace contributions:** Contact atomikspace.labs@gmail.com (required for hardware modules, CAD modifications)
- **Latisha B additions:** Contact via GitHub (required for daemon, dashboard, SDK, display system)
- **Upstream components:** Contact TARS-AI Community and Charlie Diaz as applicable

**Failure to obtain all required commercial licenses constitutes copyright infringement.**

---

## Non-Commercial License

Non-commercial use is permitted under [CC-BY-NC 4.0](LICENSE) with proper attribution to all contributors listed above.

See [LICENSE](LICENSE) for full CC-BY-NC 4.0 terms.
