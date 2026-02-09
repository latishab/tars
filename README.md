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

```
Host Computer (tars-omni)                       RPi 5 (tars)
┌──────────────────────┐                  ┌──────────────────────┐
│ AI PROCESSING ONLY   │                  │ ALL HARDWARE I/O     │
│                      │                  │                      │
│ pipecat_service.py   │    Tailscale     │ main.py (FastAPI)    │
│                      │ ◄──────────────► │                      │
│ Receives from RPi:   │   WebSocket +    │ Hardware:            │
│ - Audio stream (mic) │   HTTP REST      │ - USB Soundcard      │
│ - Camera frames      │                  │   - Microphone in    │
│                      │                  │   - Speaker out      │
│ Processes:           │                  │ - Camera (CSI/USB)   │
│ - Deepgram STT       │                  │ - PCA9685 + Servos   │
│ - GPT-OSS LLM        │                  │                      │
│ - Moondream Vision   │                  │ Endpoints:           │
│ - ElevenLabs TTS     │                  │ - /audio/stream (WS) │
│                      │                  │ - /audio/play (POST) │
│ Sends to RPi:        │                  │ - /camera/capture    │
│ - TTS audio bytes    │                  │ - /move              │
│ - Movement commands  │                  │ - /reset             │
└──────────────────────┘                  └──────────────────────┘
                                           │
                                           │ I2C + USB + CSI
                                           ▼
                                          ┌──────────────────┐
                                          │ Hardware         │
                                          │ - Servos         │
                                          │ - USB Soundcard  │
                                          │ - Camera         │
                                          └──────────────────┘
```

---

## What This Repo Contains

- **FastAPI-based control system** for Raspberry Pi 5
- **19 pre-programmed movements** for servo control
- **Camera capture endpoints** (Pi Camera or USB webcam)
- **Audio I/O endpoints** (USB soundcard)

## Quick Start

Run the unified daemon:

```bash
python tars_daemon.py --host http://100.64.0.1:7860
```

See **[docs/DAEMON.md](./docs/DAEMON.md)** for full setup guide

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

