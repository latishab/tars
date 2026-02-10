# TARS Architecture v6

**Distributed voice assistant**: RPi 5 is a self-contained robot that waits for AI brain connections. MacBook (or other computers) connect to it as clients.

**Key principle:** The robot is standalone. It boots up and waits for an AI brain to connect, not the other way around.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      NETWORK (LAN / Tailscale)                       │
│                                                                      │
│   ┌──────────────────────────┐         ┌──────────────────────────┐ │
│   │   RPi 5 (:8001)          │         │   MacBook (tars-omni)    │ │
│   │   Standalone Robot       │         │   AI Brain               │ │
│   │                          │         │                          │ │
│   │   tars_daemon.py         │         │   pipecat_service.py     │ │
│   │                          │         │                          │ │
│   │   WebRTC SERVER          │ WebRTC  │   WebRTC CLIENT          │ │
│   │   POST /api/offer ◄──────┼─────────┤   aiortc connects to RPi │ │
│   │   (waits for brain)      │  P2P    │                          │ │
│   │                          │  Audio  │                          │ │
│   │   Mic ──────────────────►┼────────►│──► Pipecat Pipeline      │ │
│   │   Speaker ◄──────────────┼◄────────┤◄── │  VAD → STT → LLM  │ │
│   │   Eye display            │  State  │    │  → TTS            │ │
│   │   Servos                 │ Channel │    └──► Audio Out       │ │
│   │   Camera ────────────────┼────────►│  HTTP  │                │ │
│   │   Battery                │  REST  │  Tools │  - Deepgram    │ │
│   │                          │ ◄──────┤ ◄──────┤  - DeepInfra   │ │
│   └──────────────────────────┘         │        - ElevenLabs    │ │
│                                        │        - Vision        │ │
│                                        └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Conversation Flow

```
User speaks → RPi USB Mic
                │
                ▼
         WebRTC Audio Track (16kHz)
                │
                ▼
         MacBook Pipecat Pipeline
                │
                ├─► VAD (Silero) - detects speech
                ├─► STT (Deepgram) - transcribes
                ├─► LLM (Qwen/Llama via DeepInfra) - generates response
                │       │
                │       └─► Tools (via HTTP to RPi)
                │           - move(), look(), set_emotion()
                │
                └─► TTS (ElevenLabs) - synthesizes
                        │
                        ▼
                 WebRTC Audio Track (24kHz)
                        │
                        ▼
                 RPi USB Speaker
                        │
                        ▼
                 User hears TARS

DataChannel (parallel to audio):
  MacBook → RPi: eye_state, emotion, audio_level
  RPi → MacBook: battery, movement_status, face_detected
```

## Communication Channels

Three distinct channels for different purposes:

| Channel | Transport | Direction | Purpose | Latency |
|---------|-----------|-----------|---------|---------|
| **Audio** | WebRTC (aiortc) | Bidirectional | Voice conversation | ~20ms |
| **State** | WebRTC DataChannel | Bidirectional | Real-time sync | ~10ms |
| **Commands** | HTTP REST | MacBook → RPi | Robot actions | ~50ms |

### Audio Channel (WebRTC)
- **RPi → MacBook**: Mic audio (16kHz mono PCM, Opus codec)
- **MacBook → RPi**: TTS audio (24kHz mono PCM, Opus codec)
- Latency: ~20ms one-way on LAN

### State Channel (WebRTC DataChannel)
Real-time state synchronization. No polling needed.

**MacBook → RPi:**
```json
{"type": "eye_state", "state": "listening"}
{"type": "emotion", "value": "happy"}
{"type": "transcript", "role": "user", "text": "Hello TARS"}
{"type": "audio_level", "level": 0.75}
{"type": "tts_state", "speaking": true}
```

**RPi → MacBook:**
```json
{"type": "battery", "level": 85, "charging": false}
{"type": "connected", "client": "macbook"}
{"type": "movement_status", "moving": true, "movement": "wave"}
{"type": "face_detected", "x": 320, "y": 240}
```

### Command Channel (HTTP REST)
For actions that need acknowledgment:
- `POST /api/offer` - WebRTC signaling
- `POST /move` - Execute movement
- `GET /camera/capture` - Capture frame (returns base64 JPEG)
- `POST /eyes/emotion` - Set emotion
- `GET /status` - Full robot status

## Components

### RPi 5 (tars) - Standalone Robot

```
tars_daemon.py (single process)
├── WebRTC Server (aiortc)
│   ├── Waits for AI brain connections
│   ├── Handles POST /api/offer (signaling)
│   ├── MicrophoneTrack (sounddevice) → sends to MacBook
│   ├── SpeakerOutput (sounddevice) ← receives from MacBook
│   └── DataChannel (bidirectional state sync)
│
├── REST API (FastAPI :8001)
│   ├── POST /api/offer (WebRTC signaling)
│   ├── /health, /state
│   ├── /move, /reset, /disable
│   ├── /camera/capture, /camera/status
│   ├── /display/*, /eyes/*, /audio/*
│   └── /battery/status, /battery/percentage
│
├── State Management
│   └── state/data_channel.py (DataChannel handler)
│       ├── Receives: eye_state, emotion, audio_level
│       └── Sends: battery, movement_status, face_detected
│
├── Hardware Drivers
│   ├── PCA9685 (16 servos via I2C)
│   ├── USB Soundcard (mic 16kHz + speaker 24kHz)
│   ├── Camera (Pi Camera v2 or USB webcam)
│   └── INA260 (battery monitor via I2C)
│
├── Display Manager (Pygame 800x480)
│   ├── RoboEyes (animated eyes with emotions)
│   ├── SpectrumVisualizer (audio bars)
│   ├── Battery indicator (top-right corner)
│   └── Face tracking (OpenCV/MediaPipe)
│
└── Modules (src/modules/)
    ├── module_movements.py (19 pre-programmed movements)
    ├── module_servoctl.py (servo control + calibration)
    ├── module_camera.py (image capture)
    ├── module_audio.py (sounddevice wrapper)
    ├── module_battery.py (INA260 monitoring)
    ├── module_display.py (display compositor)
    ├── modules_roboeyes.py (eye animations)
    ├── modules_spectrum.py (audio visualizer)
    └── module_facetracking.py (face detection)
```

### MacBook (tars-omni) - AI Brain

```
pipecat_service.py (FastAPI entry point)
├── Pipecat Pipeline
│   ├── WebRTC Client (aiortc)
│   │   └── Connects to RPi POST /api/offer
│   ├── Audio Bridge
│   │   ├── aiortc AudioFrame ↔ Pipecat AudioRawFrame
│   │   └── Handles sample rate conversion
│   ├── VAD (Silero)
│   ├── STT (Deepgram/Speechmatics)
│   ├── LLM (Qwen/Llama via DeepInfra API)
│   │   └── Tools: move(), look(), set_emotion(), dance()
│   ├── TTS (ElevenLabs/Qwen3)
│   └── Vision (Moondream/GPT-4V)
│
├── Transport Layer
│   ├── transport/aiortc_client.py (WebRTC client)
│   ├── transport/audio_bridge.py (audio conversion)
│   └── transport/state_sync.py (DataChannel manager)
│
├── Services
│   ├── services/tars_client.py (HTTP client to RPi)
│   ├── services/memory_chromadb.py (semantic memory)
│   └── services/factories/ (STT/TTS provider factories)
│
└── Observers
    └── observers/state_observer.py (pipeline events → DataChannel)
```

## Configuration

### RPi (`.env`)
```bash
# Server configuration
API_PORT=8001
WEBRTC_ENABLED=true

# Display
DISPLAY_ENABLED=true
DISPLAY_WIDTH=800
DISPLAY_HEIGHT=480

# Features
FACE_TRACKING_ENABLED=false

# Audio devices (optional - uses default if not specified)
AUDIO_INPUT_DEVICE=
AUDIO_OUTPUT_DEVICE=
AUDIO_SAMPLE_RATE_IN=16000
AUDIO_SAMPLE_RATE_OUT=24000
```

### MacBook - `tars-omni/.env.local`
```bash
# Robot connection (Tailscale IP or LAN)
TARS_RPI_IP=100.64.0.2
TARS_RPI_PORT=8001

# AI Services
DEEPGRAM_API_KEY=xxx
DEEPINFRA_API_KEY=xxx
ELEVENLABS_API_KEY=xxx
ELEVENLABS_VOICE_ID=xxx
```

## Quick Start

### RPi (boots and waits for AI brain)
```bash
# Run manually (with WebRTC server)
python tars_daemon.py

# Or with start script
./start.sh

# With options
python tars_daemon.py --port 8001 --face-tracking

# REST API only (no WebRTC)
python tars_daemon.py --no-webrtc

# Headless mode (no display)
python tars_daemon.py --no-display

# Or as systemd service
sudo systemctl start tars
```

**On boot, RPi will:**
1. Start WebRTC server on :8001
2. Initialize hardware (servos, camera, display)
3. Wait for AI brain connection at `POST /api/offer`
4. Display shows "Waiting for brain..."

### MacBook (connects to RPi)
```bash
cd tars-omni
source .venv/bin/activate
python pipecat_service.py
```

**MacBook will:**
1. Create WebRTC client
2. POST SDP offer to `http://<rpi-ip>:8001/api/offer`
3. Establish P2P audio connection
4. Start Pipecat pipeline with STT/LLM/TTS
5. Send state updates via DataChannel
6. Call RPi HTTP endpoints for movements/vision

## Connection Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                       CONNECTION LIFECYCLE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RPi BOOT                                                       │
│  ════════                                                       │
│  1. systemd starts tars_daemon.py                               │
│  2. Hardware initialization (servos, display, camera, audio)    │
│  3. FastAPI server starts on :8001                              │
│  4. WebRTC server ready, waiting for offers                     │
│  5. Display shows "Waiting for brain..." + idle eyes            │
│                                                                 │
│  MACBOOK CONNECTS                                               │
│  ═══════════════                                                │
│  1. pipecat_service.py starts                                   │
│  2. aiortc client creates SDP offer                             │
│  3. POST offer to http://<rpi-ip>:8001/api/offer               │
│  4. RPi returns SDP answer                                      │
│  5. ICE candidates exchanged                                    │
│  6. P2P connection established                                  │
│  7. Audio tracks flowing (RPi mic → MacBook, MacBook TTS → RPi) │
│  8. DataChannel open                                            │
│  9. RPi display → "Connected" + happy eyes                      │
│  10. Ready for conversation                                     │
│                                                                 │
│  CONVERSATION                                                   │
│  ════════════                                                   │
│  User speaks → RPi mic → WebRTC → VAD → STT → LLM → TTS →     │
│  WebRTC → RPi speaker                                          │
│                              │                                  │
│                              └─► Tools → HTTP → RPi movements  │
│                                                                 │
│  DISCONNECT                                                     │
│  ══════════                                                     │
│  1. MacBook closes connection (or network fails)                │
│  2. RPi detects disconnect                                      │
│  3. Display → "Waiting for brain..." + idle eyes                │
│  4. Robot returns to idle state                                 │
│  5. Ready to accept new connection                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## API Reference

See detailed docs:
- [DAEMON.md](./DAEMON.md) - Setup and usage
- [MOVEMENTS.md](./MOVEMENTS.md) - Servo API
- [HARDWARE_IO.md](./HARDWARE_IO.md) - Camera/audio API
- [TARS_ARCHITECTURE_PLAN_V6.md](../TARS_ARCHITECTURE_PLAN_V6.md) - Full architecture details

## Troubleshooting

### Check RPi Status
```bash
# Check daemon status
sudo systemctl status tars

# View logs
journalctl -u tars -f

# Test health endpoint
curl http://localhost:8001/health

# Check if WebRTC server is ready
curl http://localhost:8001/health | jq '.webrtc'
```

### Test WebRTC Connection
```bash
# From MacBook, test if RPi is reachable
curl http://100.64.0.2:8001/health

# Test WebRTC signaling endpoint
curl -X POST http://100.64.0.2:8001/api/offer \
  -H "Content-Type: application/json" \
  -d '{"sdp": "test", "type": "offer"}'
# Should return error (invalid SDP) but confirms endpoint works
```

### Audio Devices
```bash
# List available audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Test microphone
python -c "import sounddevice as sd; import time; print('Recording...'); sd.rec(16000, samplerate=16000, channels=1); time.sleep(3); print('Done')"

# Test speaker
python -c "import sounddevice as sd; import numpy as np; sd.play(np.sin(2*np.pi*440*np.linspace(0,1,16000)), 16000); sd.wait()"
```

### Network Diagnostics
```bash
# Check if Tailscale is running
sudo tailscale status

# Test latency
ping 100.64.0.2

# Check open ports
sudo netstat -tlnp | grep 8001
```
