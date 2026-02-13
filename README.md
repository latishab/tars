# TARS

> Note to Visitors
>
> This repository is a personal fork for experimenting with a new distributed architecture.
> If you're looking for the main TARS-AI project, please visit:
>
> https://github.com/TARS-AI-Community/TARS-AI
>
> This fork splits TARS into a dual-machine setup:
> - **Host Computer (macOS/Windows/Linux)**: Handles all AI processing (STT, TTS, LLM, Vision)
> - **Raspberry Pi 5**: Handles all hardware I/O (servos, camera, audio)

---

## Architecture Overview

RPi is self-contained and runs a WebRTC server + gRPC server. The host computer connects to it as a client.

```
RPi 5 (tars) - Standalone Robot            Host Computer (tars-omni) - AI Brain
┌──────────────────────────────┐        ┌─────────────────────────────┐
│ WEBRTC + gRPC + DASHBOARD    │        │ WEBRTC CLIENT + AI          │
│                              │        │                             │
│ tars_daemon.py               │        │ tars_bot.py                 │
│                              │        │                             │
│ On boot:                     │        │ Connects to RPi:            │
│ - WebRTC server :8001        │ WebRTC │ - aiortc client             │
│ - gRPC server :50051         │◄───────┤ - POST /api/offer           │
│ - Dashboard :8080            │  P2P   │                             │
│ - WiFi hotspot (if needed)   │        │                             │
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
│ - StreamBattery()            │        │                             │
│ - StreamMovementStatus()     │        │                             │
│                              │        │                             │
│ Dashboard (port 8080):       │        │ Web Browser                 │
│ - Web UI control panel       │◄───────┤ - Movement controls         │
│ - WiFi setup interface       │  HTTP  │ - Status monitoring         │
│ - Movement controls          │        │ - Settings management       │
│ - Settings & status          │        │                             │
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

## What This Repo Contains

- **gRPC-based control system** for Raspberry Pi 5 (low-latency hardware control)
- **WebRTC server** for bidirectional audio streaming
- **Web dashboard** for robot control and WiFi setup
- **19 pre-programmed movements** for servo control
- **Camera capture via gRPC** (Pi Camera or USB webcam)
- **Real-time state synchronization** via WebRTC DataChannel
- **WiFi manager** with automatic hotspot fallback

## Quick Start

Start the RPi daemon (waits for AI brain to connect):

```bash
# Start all services (WebRTC + gRPC + Dashboard)
python tars_daemon.py

# Or using start script
./start.sh

# With custom ports
python tars_daemon.py --port 8001 --grpc-port 50051 --dashboard-port 8080

# Disable specific components
python tars_daemon.py --no-webrtc    # Disable WebRTC
python tars_daemon.py --no-dashboard # Disable web dashboard
python tars_daemon.py --no-display   # Headless mode

# Enable face tracking
python tars_daemon.py --face-tracking
```

The RPi will:
1. Start the WebRTC server on port 8001 (signaling)
2. Start the gRPC server on port 50051 (hardware control)
3. Start the web dashboard on port 8080 (control panel)
4. Start WiFi hotspot if no network connection detected
5. Wait for the host computer to connect via POST /api/offer
6. Once connected, audio flows bidirectionally and gRPC handles hardware control

## PyPI Installation

Install from PyPI:

```bash
# Daemon and SDK (for Raspberry Pi 5)
pip install tars-robot

# SDK only (for host computers)
pip install tars-robot[sdk]

# Development
git clone https://github.com/latishab/tars.git
cd tars
pip install -e .[dev]
```

Commands available after installation:
```bash
tars-daemon          # Start the daemon
tars-servo-tester    # Calibrate servos
```

See [INSTALL.md](./INSTALL.md) for detailed installation options and troubleshooting.

## Pre-built OS Images

Pre-built Raspberry Pi OS images with TARS pre-installed:

**[TARS OS Repository](https://github.com/latishab/tars-os)**

Download ready-to-flash SD card images with:
- TARS daemon pre-installed
- Web dashboard for WiFi setup
- Automatic WiFi hotspot fallback
- Auto-start on boot
- mDNS (tars.local) configured

See the tars-os repository for flashing instructions and build documentation.

## Documentation

**User Guides:**
- **[DAEMON.md](./docs/DAEMON.md)** - Getting started with unified daemon

**API Reference:**
- **[MOVEMENTS.md](./docs/MOVEMENTS.md)** - Servo control and movement API
- **[HARDWARE_IO.md](./docs/HARDWARE_IO.md)** - Camera and audio API

**Architecture & Design:**
- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - System architecture (v5)

---

## Contributing

Join the community on Discord: https://discord.gg/AmE2Gv9EUt

---

## License

This project is licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC 4.0)**.

You may:
- Build and modify your own TARS robot
- Share improvements and derivatives
- Use the project for personal, educational, and research purposes

You may **not** use this project for commercial purposes without explicit permission from the authors.
Commercial use includes, but is not limited to:

- Selling 3D printed parts, kits, or complete robots  
- Selling or distributing STL / CAD files for money  
- Offering paid assembly, customization, or installation services  
- Monetized YouTube, Social Media, Patreon, or subscription content that distributes project files or derivatives  
- Using this project in paid products, commercial research, or corporate projects  
- Integrating this project into commercial software or hardware products  
- Selling derivatives or modified versions of the hardware or software  

If you are unsure whether your use case is commercial, assume it is and request permission from the authors.

See the [LICENSE](./LICENSE) file for details.

---

## Attribution

Please follow the attribution guidelines when sharing or publishing derivative work:

[ATTRIBUTION.md](./ATTRIBUTION.md)

---

