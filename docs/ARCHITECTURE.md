# TARS Architecture v5

**Distributed voice assistant**: RPi 5 handles hardware, host computer (macOS/Windows/Linux) handles AI processing.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          NETWORK (Tailscale)                         │
│                                                                      │
│   ┌─────────────────────────┐         ┌──────────────────────────┐  │
│   │   RPi 5 (:8001)         │ WebRTC  │   Host Computer (:7860)        │  │
│   │   tars_daemon.py        │◄───────►│   pipecat_service.py     │  │
│   │                         │  Audio  │                          │  │
│   │   - Mic capture ────────┼────────►│   - Deepgram STT        │  │
│   │   - Speaker ◄───────────┼─────────┤   - DeepInfra LLM       │  │
│   │   - Eye display         │  State  │   - ElevenLabs TTS      │  │
│   │   - Servos              │         │   - Moondream Vision    │  │
│   │   - Camera ─────────────┼────────►│   - ChromaDB Memory     │  │
│   │   - Battery             │  HTTP   │                          │  │
│   │                         │  REST   │                          │  │
│   └─────────────────────────┘         └──────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Conversation Flow

```
User speaks
    │
    ▼
RPi USB Mic ──► WebRTC Audio ──► Host Computer Pipecat
                                      │
                                      ├─► STT (Deepgram)
                                      ├─► LLM (Qwen/GPT)
                                      └─► TTS (ElevenLabs)
                                            │
RPi USB Speaker ◄── WebRTC Audio ◄─────────┘
    │
    ▼
User hears TARS
```

## Data Channels

### WebRTC (Real-time Audio)
- RPi → Host Computer: Mic audio (16kHz mono PCM)
- Host Computer → RPi: TTS audio (24kHz mono PCM)
- Data channel: Eye states, emotions, transcripts

### HTTP REST (Commands)
- Host Computer → RPi: Movement commands, vision requests
- RPi → Host Computer: Image captures, status updates

## Components

### RPi 5 (tars)

```
tars_daemon.py (single process)
├── WebRTC Client (aiortc)
│   ├── MicrophoneTrack (sounddevice)
│   ├── SpeakerOutput (sounddevice)
│   └── DataChannel (state sync)
│
├── REST API (FastAPI :8001)
│   ├── /health, /state
│   ├── /move, /reset
│   ├── /camera/capture
│   ├── /display/*, /eyes/*
│   └── /battery/status
│
├── Hardware Drivers
│   ├── PCA9685 (16 servos)
│   ├── USB Soundcard (mic + speaker)
│   ├── Camera (Pi Camera or USB)
│   └── INA260 (battery monitor)
│
├── Display Manager (Pygame 800x480)
│   ├── RoboEyes (animated eyes)
│   ├── SpectrumVisualizer (audio bars)
│   └── Face tracking (OpenCV/MediaPipe)
│
└── Modules (src/modules/)
    ├── module_movements.py (19 movements)
    ├── module_servoctl.py (servo control)
    ├── module_camera.py (image capture)
    ├── module_audio.py (sounddevice)
    ├── module_battery.py (INA260)
    └── module_facetracking.py (face detection)
```

### Host Computer (macOS/Windows/Linux) - tars-omni

```
pipecat_service.py
├── POST /api/offer (WebRTC signaling)
└── bot.py (Pipecat pipeline)
    ├── SmallWebRTCTransport
    ├── STT (Speechmatics/Deepgram)
    ├── LLM (Qwen via DeepInfra)
    ├── TTS (Qwen3/ElevenLabs)
    ├── Vision (Moondream)
    ├── Memory (ChromaDB)
    └── TarsClient (REST calls to RPi)
```

## Configuration

### RPi (`.env`)
```bash
HOST_URL=http://100.64.0.1:7860
API_PORT=8001
DISPLAY_ENABLED=true
```

### Host Computer (macOS/Windows/Linux) - `tars-omni/.env.local`
```bash
TARS_RPI_URL=http://100.64.0.2:8001
DEEPGRAM_API_KEY=xxx
DEEPINFRA_API_KEY=xxx
ELEVENLABS_API_KEY=xxx
```

## Quick Start

### RPi
```bash
# Run manually
python tars_daemon.py --host http://100.64.0.1:7860

# Or with start.sh
./start.sh --host http://100.64.0.1:7860

# Or as service
sudo systemctl start tars
```

### Host Computer (macOS/Windows/Linux)
```bash
cd tars-omni
npm run dev:backend  # Starts on :7860
```

## API Reference

See detailed docs:
- [DAEMON.md](./DAEMON.md) - Setup and usage
- [MOVEMENTS.md](./MOVEMENTS.md) - Servo API
- [HARDWARE_IO.md](./HARDWARE_IO.md) - Camera/audio API

## Troubleshooting

```bash
# Check daemon status
sudo systemctl status tars

# View logs
journalctl -u tars -f

# Test connectivity
curl http://100.64.0.2:8001/health

# Test WebRTC signaling
curl http://100.64.0.1:7860/api/status

# List audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"
```
