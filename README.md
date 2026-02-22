# TARS

> **Note to Visitors**
>
> This repository is a **personal fork** for experimenting with a new distributed architecture.
> If you're looking for the **main TARS-AI project**, please visit:
>
> **https://github.com/TARS-AI-Community/TARS-AI**
>
> This fork splits TARS into a dual-machine setup:
> - **Host Computer (macOS/Windows/Linux)**: Handles all AI processing (STT, TTS, LLM, Vision)
> - **Raspberry Pi 5**: Handles all hardware I/O (servos, camera, audio)

---

## Architecture Overview

**New Architecture:** RPi is self-contained and runs a WebRTC server + gRPC server. The host computer connects to it as a client.

```
RPi 5 (tars) - Standalone Robot            Host Computer (tars-conversation-app) - AI Brain
┌──────────────────────────────┐        ┌─────────────────────────────┐
│ WEBRTC + gRPC SERVERS        │        │ WEBRTC CLIENT + AI          │
│                              │        │                             │
│ tars_daemon.py               │        │ tars_bot.py                 │
│                              │        │                             │
│ On boot:                     │        │ Connects to RPi:            │
│ - Starts WebRTC server       │ WebRTC │ - aiortc client             │
│ - Starts gRPC server         │◄───────┤ - POST /api/offer           │
│ - POST /api/offer endpoint   │  P2P   │                             │
│                              │        │ Audio Pipeline:             │
│ Audio Routing:               │        │ ┌─────────────────────┐     │
│ - Mic → WebRTC track ────────┼────────┼►│ VAD → STT → LLM     │     │
│ - WebRTC track → Speaker ◄───┼────────┼─┤ → TTS → Audio Out   │     │
│                              │        │ └─────────────────────┘     │
│ DataChannel State Sync:      │        │                             │
│ - Receives eye states        │        │ Services:                   │
│ - Sends battery status       │        │ - Deepgram STT              │
│                              │        │ - GPT LLM + Tools           │
│ gRPC API (port 50051):       │        │ - ElevenLabs TTS            │
│ - ExecuteMovement(movement)      │◄───────┤ - Vision (tool calls)       │
│ - CaptureCamera(w, h, q)     │  gRPC  │                             │
│ - SetEmotion(emotion)        │        │ Tools call RPi via gRPC     │
│ - SetEyeState(state)         │        │                             │
│ - GetStatus()                │        │                             │
└──────────────────────────────┘        └─────────────────────────────┘
          │
          │ I2C + USB + CSI
          ▼
┌──────────────────┐
│ Hardware         │
│ - Servos         │
│ - USB Soundcard  │
│ - Pi Camera      │
│ - Display        │
│ - Battery        │
└──────────────────┘
```

**Key Principle:** The robot is self-contained. It boots up and waits for an AI brain to connect, not the other way around.

---


## Installation

### SDK (Mac / Windows / Linux)

For controlling TARS from your computer:

```bash
pip install tars-robot
```

Installs the gRPC client SDK only (~3 deps). Connect to a running Pi daemon and control hardware, run LLM tools, stream camera.

### Daemon on Raspberry Pi

Two options — choose based on your use case:

**Option A: PyPI (recommended for most users)**

```bash
pip install tars-robot[daemon]
./start.sh
```

Installs all daemon dependencies (FastAPI, WebRTC, pygame, Adafruit libs). Includes `tars-daemon` and `tars-servo-tester` CLI commands.

**Option B: Git clone (for development)**

```bash
git clone https://github.com/latishab/tars.git
cd tars
python -m venv venv && source venv/bin/activate
pip install -e .[daemon]
./start.sh
```

Use this if you want to modify the daemon, contribute code, or run dev tools directly from source (`src/app-servotester.py`, `src/app-cms.py`).

| | PyPI | Git clone |
|---|---|---|
| Install time | Fast | Moderate |
| Dashboard updates | One-click from UI | `git pull` |
| Modify daemon code | No | Yes |
| Servo tester / dev tools | `tars-servo-tester` CLI | CLI + direct source access |

**[Full Installation Guide](./docs/INSTALLATION.md)** — detailed setup, systemd service, troubleshooting

---



## What This Repo Contains

- **gRPC-based control system** for Raspberry Pi 5 (low-latency hardware control)
- **WebRTC server** for bidirectional audio streaming
- **19 pre-programmed movements** for servo control
- **Camera capture via gRPC** (Pi Camera or USB webcam)
- **Real-time state synchronization** via WebRTC DataChannel

## Quick Start

### Web Dashboard

**First Boot WiFi Setup:**

On first boot, TARS starts a WiFi hotspot:
```
SSID: TARS-Setup
Password: tars1234
Setup URL: http://tars.local:8000/setup (or http://10.42.0.1:8000/setup)
```

After WiFi is configured, access the dashboard at:
```
# Local network (home WiFi)
http://tars.local:8000

# Tailscale (dorm/corporate networks)
http://tars:8000
```

**[WiFi Setup Guide](./docs/WIFI_SETUP.md)** - Complete WiFi configuration instructions

**Dashboard Features:**
- Monitor robot status (battery, CPU, network)
- Control movements via joystick
- Install and manage apps from the App Store
- Configure WiFi and system settings

**Tabs:**
- **Status**: System metrics, battery, connections
- **Control**: Movement controls with joystick interface
- **Apps**: Official and community apps marketplace
- **Settings**: WiFi management, enterprise WiFi support, updates

### Command Line

Start the RPi daemon (waits for AI brain to connect):

```bash
# Start WebRTC + gRPC servers (default)
python tars_daemon.py

# Or using start script
./start.sh

# WebRTC only (no gRPC)
python tars_daemon.py --no-grpc

# Specify custom gRPC port
python tars_daemon.py --grpc-port 50052
```

The RPi will (unified daemon on port 8000):
1. Start unified HTTP server on port 8000 (WebRTC + REST API + Dashboard)
2. Start the gRPC server on port 50051 (default)
3. Wait for host computer to connect via POST /api/offer
4. Once connected, audio flows bidirectionally and gRPC handles hardware control


## Documentation

**User Guides:**
- **[DAEMON.md](./docs/DAEMON.md)** - Getting started with unified daemon
- **[DASHBOARD.md](./docs/DASHBOARD.md)** - Web dashboard guide
- **[WIFI_SETUP.md](./docs/WIFI_SETUP.md)** - WiFi configuration and troubleshooting

**API Reference:**
- **[MOVEMENTS.md](./docs/MOVEMENTS.md)** - Servo control and movement API
- **[HARDWARE_IO.md](./docs/HARDWARE_IO.md)** - Camera and audio API

**Architecture & Design:**
- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - System architecture

---

## Contributing

- Join the community on Discord:  
  https://discord.gg/AmE2Gv9EUt

---

## License & Attribution

This project is licensed under [CC-BY-NC 4.0](LICENSE) for non-commercial use.

### Attribution Chain

Based on the mechanical puppet designs by Christopher Nolan, Nathan Crowley, and the production team who originally brought TARS to life—miniaturized CAD by Charlie Diaz, with additional modifications by the TARS-AI Community, AtomikSpace, and Latisha B.

**Contributors:**
- **Christopher Nolan / Production Team** - Original TARS character from *Interstellar*
- **Charlie Diaz** - Original miniaturized CAD files and code ([Hackster.io](https://www.hackster.io/charlesdiaz/how-to-build-your-own-replica-of-tars-from-interstellar-224833))
- **TARS-AI Community** - Community project ([repo](https://github.com/TARS-AI-Community/TARS-AI))
- **Charles-Olivier Dion (AtomikSpace)** - V2 hardware, modified CAD, hardware modules
- **Latisha B** - Daemon architecture, display system, conversation pipeline

See [LEGAL.md](LEGAL.md) for detailed ownership and licensing information.

### Commercial Use

Commercial use is **not permitted** under CC-BY-NC 4.0 without explicit written permission from **all applicable copyright holders**.

Commercial use includes:
- Selling 3D printed parts, kits, or complete robots
- Selling or distributing CAD files for money
- Offering paid assembly, customization, or installation services
- Monetized content that distributes project files or derivatives
- Using this project in paid products, commercial research, or corporate projects

**For commercial use, you must obtain separate licenses from:**
- **AtomikSpace** (hardware modules, CAD modifications): atomikspace.labs@gmail.com
- **Latisha B** (daemon, dashboard, SDK, display): Contact via GitHub
- **Upstream contributors** (Charlie Diaz, TARS-AI Community): As applicable

See [LEGAL.md](LEGAL.md) for AtomikSpace's dual-license model.


---

## 🧾 Attribution

Please follow the attribution guidelines when sharing or publishing derivative work:

See [LEGAL.md](./LEGAL.md) for attribution requirements.

---

