# TARS

> **⚠️ Note to Visitors**
>
> This repository is a **personal fork** for experimenting with a new distributed architecture.
> If you're looking for the **main TARS-AI project**, please visit:
>
> 👉 **https://github.com/TARS-AI-Community/TARS-AI**
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
│ - Move(movement, speed)      │◄───────┤ - Vision (tool calls)       │
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


## 📦 Installation

### SDK Only (App Development)

For controlling TARS from your computer (Mac/Windows/Linux):

```bash
pip install tars-robot
```

This installs only the lightweight SDK (~3 dependencies) needed to connect to the robot via gRPC.

### Full Daemon (Raspberry Pi)

For running the robot daemon on the Pi:

```bash
pip install tars-robot[daemon]
```

This installs all dependencies including FastAPI, pygame, Adafruit libraries, etc.

📖 **[Full Installation Guide](./INSTALLATION.md)** - Detailed instructions, usage examples, and troubleshooting

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

📖 **[WiFi Setup Guide](./docs/WIFI_SETUP.md)** - Complete WiFi configuration instructions

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

## 🤝 Contributing

- Join the community on Discord:  
  👉 https://discord.gg/AmE2Gv9EUt

---

## 📜 License & Copyright

This project is a fork of [TARS-AI-Community/TARS-AI](https://github.com/TARS-AI-Community/TARS-AI) with contributions from multiple authors.

**License**: Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC 4.0)

**Copyright Holders**:
- **Charles-Olivier Dion (AtomikSpace)** - Original hardware modules, movements, 3D design files
- **Latisha B** - Daemon architecture, dashboard, gRPC/WebRTC servers, SDK

See [COPYRIGHT.md](./COPYRIGHT.md) for detailed ownership breakdown.

### Non-Commercial Use

You may:
- Build and modify your own TARS robot
- Share improvements and derivatives
- Use the project for personal, educational, and research purposes

### Commercial Use

Commercial use is **not permitted** under CC-BY-NC 4.0 without explicit written permission from **both copyright holders**.

Commercial use includes:
- Selling 3D printed parts, kits, or complete robots  
- Selling or distributing STL/CAD files for money  
- Offering paid assembly, customization, or installation services  
- Monetized content that distributes project files or derivatives  
- Using this project in paid products, commercial research, or corporate projects  
- Integrating into commercial software or hardware products  

**AtomikSpace files** (hardware modules, movements, 3D files) are subject to a dual-license model. See [DUAL-LICENSE.md](./DUAL-LICENSE.md) and contact atomikspace.labs@gmail.com for commercial licensing.

**Latisha B additions** (daemon, dashboard, gRPC, WebRTC, SDK) also require separate commercial licensing. Contact via GitHub for inquiries.

See [LICENSE](./LICENSE) for full CC-BY-NC 4.0 terms.


---

## 🧾 Attribution

Please follow the attribution guidelines when sharing or publishing derivative work:

👉 [ATTRIBUTION.md](./ATTRIBUTION.md)

---

