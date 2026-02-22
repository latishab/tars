# TARS

> **Note to Visitors:** This repository contains only the robot hardware daemon. The voice AI pipeline runs on a separate host computer. If you are looking for the full conversational AI system, see [tars-conversation-app](https://github.com/latishab/tars-conversation-app).

Raspberry Pi 5 robot daemon. Handles servo control, WebRTC audio streaming, display, camera, and battery monitoring. Connects to an AI brain running on a host computer.

## What You Need

**Hardware:**
- Raspberry Pi 5 (or Pi 4 4GB+)
- PCA9685 servo driver + servos
- USB audio adapter
- Pi Camera or USB webcam
- INA260 battery monitor (optional)
- 12V battery pack

**Software:**
- Python 3.9+

---

## Quick Start

### 1. Install on Pi

```bash
pip install tars-robot[daemon]
tars-daemon
```

Dashboard: `http://tars.local:8000`

### 2. Connect AI Brain

On your host computer, run [tars-conversation-app](https://github.com/latishab/tars-conversation-app). It connects to the daemon over WebRTC and gRPC.

---

## Installation

| | PyPI | Git clone |
|---|---|---|
| Install time | Fast | Moderate |
| Dashboard updates | One-click from UI | `git pull` |
| Modify daemon code | No | Yes |
| Servo tester / dev tools | `tars-servo-tester` CLI | `python src/app-servotester.py` |

### PyPI (Recommended)

```bash
pip install tars-robot[daemon]
tars-daemon
```

### Git Clone (Development)

```bash
git clone https://github.com/latishab/tars.git
cd tars && pip install -e .[daemon]
tars-daemon
```

### SDK Only (Remote Control)

```bash
pip install tars-robot
```

```python
from tars_sdk import TarsClient

client = TarsClient(tars.local:50051)
client.move(wave_right)
client.set_emotion(happy)
client.close()
```

---

## Architecture

```
Host Computer                         Raspberry Pi
─────────────────────────────────     ─────────────────────────────
tars-conversation-app                 tars-daemon
  ├── LLM (Claude)                      ├── gRPC Server (:50051)
  ├── STT (Deepgram)                    ├── HTTP + Dashboard (:8000)
  ├── TTS (Kokoro/Cartesia)             ├── WebRTC (aiortc)
  └── TarsClient SDK ──────────────────→ ├── Servo Control (PCA9685)
                        gRPC :50051      ├── Display (pygame)
                        WebRTC :8000     ├── Camera
                                         └── Battery (INA260)
```

---

## Documentation

- [Installation](./docs/INSTALLATION.md)
- [API Reference](./docs/API.md)
- [WiFi Setup](./docs/WIFI_SETUP.md)
- [Servo Calibration](./docs/CALIBRATION.md)
- [Daemon](./docs/DAEMON.md)
- [Dashboard](./docs/DASHBOARD.md)
- [Architecture](./docs/ARCHITECTURE.md)

---

## AI Brain

The voice AI pipeline (LLM, STT, TTS) runs separately from the daemon:

**[tars-conversation-app](https://github.com/latishab/tars-conversation-app)**

You can run it on:
- **Host computer** (Mac/Windows/Linux) — recommended for better performance
- **Raspberry Pi 5** — works, but may be slower depending on STT/TTS providers

---

## License

See [LEGAL.md](./LEGAL.md).
