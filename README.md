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

### Default (Everything)

Full installation with daemon, dashboard, and SDK:

```bash
pip install tars-robot
```

### SDK Only

For app development (minimal install):

```bash
pip install --no-deps tars-robot
pip install grpcio protobuf loguru
```

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

Access the dashboard at  to:
- Monitor robot status (battery, CPU, network)
- Control movements via joystick
- Install and manage apps from the App Store
- Configure WiFi and system settings

Tabs:
- **Status**: System metrics, battery, connections
- **Control**: Movement controls with joystick interface
- **Apps**: Official and community apps marketplace
- **Settings**: WiFi, updates, system configuration

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

The RPi will:
1. Start the WebRTC server on port 8001
2. Start the gRPC server on port 50051 (default)
3. Start the web dashboard on port 8080
4. Wait for the host computer to connect via POST /api/offer
5. Once connected, audio flows bidirectionally and gRPC handles hardware control


## Documentation

**User Guides:**
- **[DAEMON.md](./docs/DAEMON.md)** - Getting started with unified daemon
- **[DASHBOARD.md](./docs/DASHBOARD.md)** - Web dashboard guide

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

## 📜 License

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

## 🧾 Attribution

Please follow the attribution guidelines when sharing or publishing derivative work:

👉 [ATTRIBUTION.md](./ATTRIBUTION.md)

---

