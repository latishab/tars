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

## Architecture Overview (v6)

**New Architecture:** RPi is self-contained and runs a WebRTC server. The host computer connects to it as a client.

```
RPi 5 (tars) - Standalone Robot            Host Computer (tars-omni) - AI Brain
┌──────────────────────────────┐        ┌─────────────────────────────┐
│ WEBRTC SERVER + HARDWARE     │        │ WEBRTC CLIENT + AI          │
│                              │        │                             │
│ tars_daemon.py               │        │ pipecat_service.py          │
│                              │        │                             │
│ On boot:                     │        │ Connects to RPi:            │
│ - Starts WebRTC server       │ WebRTC │ - aiortc client             │
│ - Waits for AI brain         │◄───────┤ - POST /api/offer           │
│ - POST /api/offer endpoint   │  P2P   │                             │
│                              │        │ Audio Pipeline:             │
│ Audio Routing:               │        │ ┌─────────────────────┐     │
│ - Mic → WebRTC track ────────┼────────┼►│ VAD → STT → LLM     │     │
│ - WebRTC track → Speaker ◄───┼────────┼─┤ → TTS → Audio Out   │     │
│                              │        │ └─────────────────────┘     │
│ DataChannel State Sync:      │        │                             │
│ - Receives eye states        │        │ Services:                   │
│ - Sends battery status       │        │ - Deepgram STT              │
│                              │        │ - Claude LLM + Tools        │
│ HTTP REST API:               │        │ - ElevenLabs TTS            │
│ - /move (movements)          │◄───────┤ - Vision (tool calls)       │
│ - /camera/capture            │  HTTP  │                             │
│ - /eyes/emotion              │        │ Tools call RPi via HTTP     │
│ - /reset                     │        │                             │
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

- **FastAPI-based control system** for Raspberry Pi 5
- **19 pre-programmed movements** for servo control
- **Camera capture endpoints** (Pi Camera or USB webcam)
- **Audio I/O endpoints** (USB soundcard)

## Quick Start

Start the RPi daemon (waits for AI brain to connect):

```bash
# With WebRTC server (default)
python tars_daemon.py

# Or using start script
./start.sh

# REST API only (no WebRTC)
python tars_daemon.py --no-webrtc
```

The RPi will:
1. Start the WebRTC server and REST API on port 8001
2. Wait for the host computer to connect via POST /api/offer
3. Once connected, audio flows bidirectionally

See **[TARS_ARCHITECTURE_PLAN_V6.md](./TARS_ARCHITECTURE_PLAN_V6.md)** for full architecture details

## Documentation

**User Guides:**
- **[DAEMON.md](./docs/DAEMON.md)** - Getting started with unified daemon

**API Reference:**
- **[MOVEMENTS.md](./docs/MOVEMENTS.md)** - Servo control and movement API
- **[HARDWARE_IO.md](./docs/HARDWARE_IO.md)** - Camera and audio API

**Architecture & Design:**
- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - System architecture (v5)

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

