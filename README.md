# TARS

> **Note:** This is a fork of [TARS-AI-Community/TARS-AI](https://github.com/TARS-AI-Community/TARS-AI) with a distributed architecture. The original runs everything on the Pi. This fork separates the hardware daemon from the AI pipeline, exposing gRPC and WebRTC APIs so anyone can build apps that control the robot.

Raspberry Pi 5 robot daemon. Handles servo control, WebRTC audio streaming, display, camera, and battery monitoring. Apps connect via gRPC and WebRTC.

## 🛠️ What You Need

See the [TARS-AI wiki](https://github.com/TARS-AI-Community/TARS-AI/wiki) for the full bill of materials and build instructions. Come back here if you want to run this distributed architecture instead of the original monolithic setup.


**Hardware:**
- Raspberry Pi 5 (or Pi 4 4GB+)
- PCA9685 servo driver + servos
- USB audio adapter
- Speaker (8Ω 5W)
- Pi Camera or USB webcam
- INA260 battery monitor (optional)
- 12V battery pack

**Software:**
- Python 3.9+

---

## 🚀 Quick Start

### 1. Install on Pi

```bash
pip install tars-robot[daemon]
tars-daemon
```

Dashboard: `http://tars.local:8000` — see [WiFi Setup](./docs/WIFI_SETUP.md) for Tailscale access

### 2. Install an App

Browse and install apps from the dashboard's Apps tab.

**Featured:**
- **[tars-conversation-app](https://huggingface.co/spaces/latishab/tars-conversation-app)** — Voice AI pipeline (LLM, STT, TTS). Talk to your robot. ([source](https://github.com/latishab/tars-conversation-app))
---

## 📦 Installation

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

client = TarsClient("tars.local:50051")
client.move("wave_right")
client.set_emotion("happy")
client.close()
```

---

## 🏗️ Architecture

```
App (any machine)                     tars-daemon (Raspberry Pi)
─────────────────────────────────     ─────────────────────────────
tars-conversation-app                   ├── gRPC Server (:50051)
  ├── LLM (Claude)                      ├── HTTP + Dashboard (:8000)
  ├── STT (Deepgram)                    ├── WebRTC Audio
  ├── TTS (Kokoro)                      ├── Servo Control (PCA9685)
  └── TarsClient SDK ─────────────────►├── Display (pygame)
                        gRPC :50051     ├── Camera
                        WebRTC :8000    └── Battery (INA260)
```

Apps connect via gRPC (:50051) and WebRTC (:8000). They can run on a separate computer or on the Pi itself.

---

## 📱 Apps

TARS supports installable apps. Browse and install from the dashboard's Apps tab.

**Featured:**
- **[tars-conversation-app](https://huggingface.co/spaces/latishab/tars-conversation-app)** — Voice AI pipeline (LLM, STT, TTS). Talk to your robot. ([source](https://github.com/latishab/tars-conversation-app))

*More apps coming soon.*

---

## 📚 Documentation

- [Installation](./docs/INSTALLATION.md)
- [API Reference](./docs/API.md)
- [WiFi Setup](./docs/WIFI_SETUP.md)
- [Servo Calibration](./docs/CALIBRATION.md)
- [Daemon](./docs/DAEMON.md)
- [Dashboard](./docs/DASHBOARD.md)
- [Architecture](./docs/ARCHITECTURE.md)

---

## ⚖️ License

See [LEGAL.md](./LEGAL.md).
