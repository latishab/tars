# TARS Architecture 

Distributed voice assistant with RPi 5 as standalone robot hardware. MacBook or other computers connect as AI brain clients.

The robot boots independently and waits for connections.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      NETWORK (LAN / Tailscale)                          │
│                                                                         │
│   ┌──────────────────────────┐         ┌──────────────────────────┐    │
│   │   RPi 5                  │         │   Computer               │    │
│   │   Standalone Robot       │         │   AI Brain               │    │
│   │                          │         │                          │    │
│   │   tars_daemon.py         │         │   tars_bot.py            │    │
│   │                          │         │                          │    │
│   │   ┌──────────────────┐   │ WebRTC  │   ┌──────────────────┐   │    │
│   │   │ WebRTC SERVER    │   │         │   │ WebRTC CLIENT    │   │    │
│   │   │ POST /api/offer  │◄──┼─────────┼───│ aiortc connects  │   │    │
│   │   │ (waits for brain)│   │  P2P    │   │ to RPi           │   │    │
│   │   │                  │   │  Audio  │   │                  │   │    │
│   │   │ Mic ────────────►│───┼────────►│──►│ Pipecat Pipeline │   │    │
│   │   │ Speaker ◄────────│◄──┼─────────┼◄──│ VAD → STT → LLM  │   │    │
│   │   │                  │   │         │   │ → TTS            │   │    │
│   │   └──────────────────┘   │         │   └──────────────────┘   │    │
│   │                          │         │           │              │    │
│   │   ┌──────────────────┐   │  gRPC   │           │              │    │
│   │   │ gRPC SERVER      │◄──┼─────────┼───────────┘              │    │
│   │   │ :50051           │   │ 5-10ms  │   tars_sdk.TarsClient    │    │
│   │   │                  │   │         │                          │    │
│   │   │ • Health()       │   │         │   LLM Tools:             │    │
│   │   │ • Move()         │   │         │   • execute_movement()   │    │
│   │   │ • SetEmotion()   │   │         │   • capture_camera()     │    │
│   │   │ • SetEyeState()  │   │         │   • set_emotion()        │    │
│   │   │ • CaptureCamera()│   │         │   • get_status()         │    │
│   │   │ • GetStatus()    │   │         │                          │    │
│   │   │ • StreamBattery()│   │         │   Services:              │    │
│   │   └──────────────────┘   │         │   - Deepgram STT         │    │
│   │                          │         │   - DeepInfra LLM        │    │
│   │   ┌──────────────────┐   │         │   - ElevenLabs TTS       │    │
│   │   │ Web Dashboard    │   │         │                          │    │
│   │   │ :8000            │   │         │                          │    │
│   │   │                  │   │         │                          │    │
│   │   │ • Status         │   │         │                          │    │
│   │   │ • Control        │   │         │                          │    │
│   │   │ • Apps           │   │         │                          │    │
│   │   │ • Settings       │   │         │                          │    │
│   │   └──────────────────┘   │         │                          │    │
│   │                          │         │                          │    │
│   │   Hardware:              │         │                          │    │
│   │   • Servos (PCA9685)     │         │                          │    │
│   │   • Camera (Pi/USB)      │         │                          │    │
│   │   • Display (5" 800x480) │         │                          │    │
│   │   • Battery (INA260)     │         │                          │    │
│   └──────────────────────────┘         └──────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Communication Channels

Three channels with different purposes:

| Channel | Transport | Direction | Purpose | Latency |
|---------|-----------|-----------|---------|---------|
| **Audio** | WebRTC (aiortc) | Bidirectional | Voice conversation | ~20ms |
| **Commands** | gRPC | Bidirectional | Hardware control | ~5-10ms |
| **Signaling** | HTTP | One-time | WebRTC setup | N/A |

### Audio Channel (WebRTC)
- **RPi → Host Computer**: Mic audio (16kHz mono PCM, Opus codec)
- **Host Computer → RPi**: TTS audio (24kHz mono PCM, Opus codec)
- Latency: ~20ms one-way on LAN
- Uses aiortc P2P connection

### Command Channel (gRPC)

RPCs Available:
```protobuf
// Health & Status
rpc Health() → HealthResponse
rpc GetStatus() → StatusResponse

// Movement
rpc Move(movement, speed) → MoveResponse
rpc Reset() → Empty

// Display
rpc SetEmotion(emotion) → Empty
rpc SetEyeState(state) → Empty

// Camera
rpc CaptureCamera(width, height, quality) → CaptureResponse

// Streaming
rpc StreamBattery() → stream BatteryStatus
rpc StreamMovementStatus() → stream MovementStatus
```

### Signaling Channel (HTTP)

Endpoints:
- `POST /api/offer` - WebRTC signaling (accepts SDP offer, returns answer)
- `GET /health` - Convenience health check (also available via gRPC)

## Conversation Flow

```
User speaks → RPi USB Mic
                │
                ▼
         WebRTC Audio Track (16kHz)
                │
                ▼
         Host Computer Pipecat Pipeline
                │
                ├─► VAD (Silero) - detects speech
                ├─► STT (Deepgram) - transcribes
                ├─► LLM (via DeepInfra) - generates response
                │       │
                │       └─► Tools (via gRPC to RPi)
                │           - execute_movement()
                │           - capture_camera()
                │           - set_emotion()
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
```

## Components

### RPi 5 (tars) - Standalone Robot

```
tars_daemon.py (single process)
├── gRPC Server (:50051)
│   ├── Health() - comprehensive status
│   ├── Move() - execute movements
│   ├── SetEmotion() - display control
│   ├── SetEyeState() - eye animations
│   ├── CaptureCamera() - grab frames
│   ├── GetStatus() - robot status
│   ├── StreamBattery() - real-time battery
│   └── StreamMovementStatus() - movement progress
│
├── HTTP Server (:8000) - Minimal
│   ├── POST /api/offer (WebRTC signaling only)
│   └── GET /health (convenience - also in gRPC)
│
├── WebRTC Server (aiortc)
│   ├── Waits for AI brain connections
│   ├── MicrophoneTrack → sends to host computer
│   └── SpeakerOutput ← receives from host computer
│
├── Unified HTTP Server (:8000)
│   ├── Status - system metrics, battery, connections
│   ├── Control - movement controls with joystick
│   ├── Apps - app marketplace and management
│   └── Settings - WiFi, updates, configuration
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
    └── modules_spectrum.py (audio visualizer)
```

### Host Computer (tars-conversation-app) - AI Brain

```
tars_bot.py (robot mode)
├── gRPC Client (tars_sdk.TarsClient)
│   └── Connects to RPi :50051
│
├── Pipecat Pipeline
│   ├── WebRTC Client (aiortc)
│   │   └── Connects to RPi POST /api/offer
│   ├── Audio Bridge (aiortc ↔ Pipecat frames)
│   ├── VAD (Silero)
│   ├── STT (Deepgram/Speechmatics)
│   ├── LLM (via DeepInfra API)
│   │   └── Tools: execute_movement(), capture_camera()
│   ├── TTS (ElevenLabs/Qwen3)
│   └── Vision (Moondream/GPT-4V)
│
├── Transport Layer
│   ├── transport/aiortc_client.py (WebRTC client)
│   └── transport/audio_bridge.py (audio conversion)
│
└── Services
    ├── services/tars_robot.py (gRPC-based hardware control)
    ├── services/memory_chromadb.py (semantic memory)
    └── services/factories/ (STT/TTS provider factories)
```

## Configuration

### RPi (tars_daemon.py)
```bash
# Start daemon with options
python tars_daemon.py [OPTIONS]

Options:
  --port PORT         HTTP API port (default: 8000)
  --grpc-port PORT    gRPC API port (default: 50051)
  --no-display        Headless mode (no pygame window)
  --no-webrtc         Disable WebRTC server
  --face-tracking     Enable face tracking with eyes
```

Environment variables (optional):
```bash
# Display
DISPLAY_ENABLED=true
DISPLAY_WIDTH=800
DISPLAY_HEIGHT=480

# Audio devices
AUDIO_INPUT_DEVICE=
AUDIO_OUTPUT_DEVICE=
AUDIO_SAMPLE_RATE_IN=16000
AUDIO_SAMPLE_RATE_OUT=24000
```

### Host Computer (tars-conversation-app)

`config.ini`:
```ini
[Connection]
rpi_url = http://100.84.133.74:8000    # WebRTC signaling
rpi_grpc = 100.84.133.74:50051         # Hardware control
mode = robot

[LLM]
model = openai/gpt-oss-20b

[STT]
provider = deepgram

[TTS]
provider = elevenlabs
```

## Quick Start

### RPi (boots and waits for AI brain)
```bash
# Install dependencies
pip install -r requirements.txt

# Generate gRPC code
./scripts/generate_grpc.sh

# Run daemon
python tars_daemon.py

# With options
python tars_daemon.py --grpc-port 50051 --face-tracking

# Or as systemd service
sudo systemctl start tars
```

**On boot, RPi will:**
1. Start gRPC server on :50051
2. Start HTTP server on :8000 (WebRTC signaling)
3. Initialize hardware and wait for connections
4. Initialize hardware (servos, camera, display)
5. Wait for AI brain connection
6. Display shows "Waiting for brain..."

### Host Computer (connects to RPi)
```bash
cd tars-conversation-app
pip install -e ../tars  # Install tars_sdk
python tars_bot.py
```

**Host Computer will:**
1. Connect gRPC client to RPi :50051
2. Create WebRTC client
3. POST SDP offer to RPi :8000/api/offer
4. Establish P2P audio connection
5. Start Pipecat pipeline with STT/LLM/TTS
6. Use gRPC for all hardware control

## Performance

Latency measurements on LAN:

| Operation | gRPC |
|-----------|------|
| Move command | 5-10ms |
| Set emotion | 5-8ms |
| Camera capture | 25-35ms |
| Get status | 5-8ms |

## API Usage Examples

### Using the SDK (Python)

```python
from tars_sdk import TarsClient

# Connect to robot
client = TarsClient("100.84.133.74:50051")

# Health check
health = client.health()
print(f"Status: {health['status']}")
print(f"Battery: {health['battery']['level']}%")
print(f"WebRTC connected: {health['webrtc']['connected']}")

# Execute movement
result = client.move("wave_right")
if result['success']:
    print(f"Wave completed in {result['duration']:.2f}s")

# Display control
client.set_emotion("happy")
client.set_eye_state("idle")

# Camera capture
jpeg_bytes = client.capture_camera(width=640, height=480, quality=80)
with open("capture.jpg", "wb") as f:
    f.write(jpeg_bytes)

# Status check
status = client.get_status()
print(f"Moving: {status['is_moving']}")
print(f"Emotion: {status['emotion']}")

# Streaming battery updates
for battery in client.stream_battery():
    print(f"Battery: {battery['level']}% ({battery['voltage']:.2f}V)")
    if battery['level'] < 20:
        break

# Context manager
with TarsClient("100.84.133.74:50051") as client:
    client.move("wave_right")
```

### From tars-conversation-app (LLM Tools)

```python
# In tars_bot.py
from services import tars_robot

# Initialize client
robot_client = tars_robot.get_robot_client("100.84.133.74:50051")

# LLM tool functions
async def execute_movement(movements: list[str]) -> str:
    result = robot_client.move(movements[0])
    return f"Completed in {result['duration']:.2f}s"

async def capture_camera_view() -> dict:
    jpeg_bytes = robot_client.capture_camera()
    return {"image": base64.b64encode(jpeg_bytes).decode()}
```

## Troubleshooting

### gRPC Connection Issues

```bash
# Test gRPC health
python -c "from tars_sdk import TarsClient; print(TarsClient('100.84.133.74:50051').health())"

# Check if gRPC port is open
nc -zv 100.84.133.74 50051

# Check daemon logs
journalctl -u tars -f | grep gRPC
```

### WebRTC Connection Issues

```bash
# Check if RPi is reachable
curl http://100.84.133.74:8000/health

# Test WebRTC signaling endpoint
curl -X POST http://100.84.133.74:8000/api/offer \
  -H "Content-Type: application/json" \
  -d '{"sdp": "test", "type": "offer"}'
```

### Dashboard Not Accessible

```bash
# Check dashboard is running
ps aux | grep start_dashboard

# Check port 8080
lsof -i:8000  # Unified HTTP server

# Restart dashboard
pkill -f start_dashboard
python start_dashboard.py
```

### Performance Testing

```python
import time
from tars_sdk import TarsClient

client = TarsClient("100.84.133.74:50051")

# Measure latency
start = time.time()
client.move("wave_right")
latency = (time.time() - start) * 1000
print(f"gRPC latency: {latency:.1f}ms")

# Should be 5-10ms on LAN
```

## See Also

- [DAEMON.md](./DAEMON.md) - Daemon setup and usage
- [DASHBOARD.md](./DASHBOARD.md) - Web dashboard guide
- [MOVEMENTS.md](./MOVEMENTS.md) - Available movements
- [HARDWARE_IO.md](./HARDWARE_IO.md) - Hardware specifications
