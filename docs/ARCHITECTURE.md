# TARS Architecture 

Distributed voice assistant with RPi 5 as standalone robot hardware. MacBook or other computers connect as AI brain clients.

The robot boots independently and waits for connections.

## System Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                      NETWORK (LAN / Tailscale)                               │
│                                                                              │
│   ┌────────────────────────────┐         ┌──────────────────────────┐       │
│   │   RPi 5                    │         │   Computer (tars-omni)   │       │
│   │   Standalone Robot         │         │   AI Brain               │       │
│   │                            │         │                          │       │
│   │   tars_daemon.py           │         │   tars_bot.py            │       │
│   │                            │         │                          │       │
│   │   ┌────────────────────┐   │ WebRTC  │   ┌──────────────────┐   │       │
│   │   │ WebRTC SERVER      │   │         │   │ WebRTC CLIENT    │   │       │
│   │   │ :8001              │   │         │   │ aiortc connects  │   │       │
│   │   │ POST /api/offer    │◄──┼─────────┼───│ to RPi           │   │       │
│   │   │ (waits for brain)  │   │  P2P    │   │                  │   │       │
│   │   │                    │   │  Audio  │   │                  │   │       │
│   │   │ Mic ──────────────►│───┼────────►│──►│ Pipecat Pipeline │   │       │
│   │   │ Speaker ◄──────────│◄──┼─────────┼◄──│ VAD → STT → LLM  │   │       │
│   │   │                    │   │         │   │ → TTS            │   │       │
│   │   └────────────────────┘   │         │   └──────────────────┘   │       │
│   │                            │         │           │              │       │
│   │   ┌────────────────────┐   │  gRPC   │           │              │       │
│   │   │ gRPC SERVER        │◄──┼─────────┼───────────┘              │       │
│   │   │ :50051             │   │ 5-10ms  │   tars_sdk.TarsClient    │       │
│   │   │                    │   │         │                          │       │
│   │   │ • Health()         │   │         │   LLM Tools:             │       │
│   │   │ • Move()           │   │         │   • execute_movement()   │       │
│   │   │ • SetEmotion()     │   │         │   • capture_camera()     │       │
│   │   │ • SetEyeState()    │   │         │   • set_emotion()        │       │
│   │   │ • CaptureCamera()  │   │         │   • get_status()         │       │
│   │   │ • GetStatus()      │   │         │                          │       │
│   │   │ • Reset()          │   │         │   Services:              │       │
│   │   │ • StreamBattery()  │   │         │   - Deepgram STT         │       │
│   │   │ • StreamMovement() │   │         │   - DeepInfra LLM        │       │
│   │   └────────────────────┘   │         │   - ElevenLabs TTS       │       │
│   │                            │         │                          │       │
│   │   ┌────────────────────┐   │  HTTP   │   ┌──────────────────┐   │       │
│   │   │ DASHBOARD          │◄──┼─────────┼───│ Web Browser      │   │       │
│   │   │ :8080              │   │ WebSoc  │   │ Control Panel    │   │       │
│   │   │                    │   │         │   │                  │   │       │
│   │   │ • Movement control │   │         │   │ • Movements      │   │       │
│   │   │ • WiFi setup       │   │         │   │ • Status         │   │       │
│   │   │ • Status monitor   │   │         │   │ • Settings       │   │       │
│   │   │ • Settings         │   │         │   │ • WiFi setup     │   │       │
│   │   │ • Chat interface   │   │         │   │ • Chat           │   │       │
│   │   └────────────────────┘   │         │   └──────────────────┘   │       │
│   │                            │         │                          │       │
│   │   ┌────────────────────┐   │         │                          │       │
│   │   │ WiFi Manager       │   │         │                          │       │
│   │   │ • Auto hotspot     │   │         │                          │       │
│   │   │ • Network scan     │   │         │                          │       │
│   │   │ • Connection setup │   │         │                          │       │
│   │   └────────────────────┘   │         │                          │       │
│   │                            │         │                          │       │
│   │   Hardware:                │         │                          │       │
│   │   • Servos (PCA9685)       │         │                          │       │
│   │   • Camera (Pi/USB)        │         │                          │       │
│   │   • Display (5" 800x480)   │         │                          │       │
│   │   • Battery (INA260)       │         │                          │       │
│   └────────────────────────────┘         └──────────────────────────┘       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Communication Channels

Four channels with different purposes:

| Channel | Transport | Direction | Purpose | Latency |
|---------|-----------|-----------|---------|---------|
| **Audio** | WebRTC (aiortc) | Bidirectional | Voice conversation | ~20ms |
| **Commands** | gRPC | Bidirectional | Hardware control | ~5-10ms |
| **Signaling** | HTTP | One-time | WebRTC setup | N/A |
| **Dashboard** | HTTP + WebSocket | Bidirectional | Web UI control | ~10-50ms |

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
rpc StreamAudioLevels() → bidirectional stream AudioLevel
```

### Signaling Channel (HTTP)

WebRTC Endpoints:
- `POST /api/offer` - WebRTC signaling (accepts SDP offer, returns answer)
- `GET /health` - Convenience health check (also available via gRPC)
- `GET /camera` - JPEG snapshot from camera

### Dashboard Channel (HTTP + WebSocket)

Dashboard runs on port 8080 with:
- React/Vite frontend
- FastAPI backend
- WebSocket for real-time updates

Endpoints:
- `GET /api/status` - Robot status
- `POST /api/movements/{name}` - Execute movement
- `GET /api/movements` - List available movements
- `GET /api/wifi/networks` - Scan WiFi networks
- `POST /api/wifi/connect` - Connect to WiFi
- `POST /api/wifi/hotspot` - Start/stop hotspot
- `GET /api/settings` - Get display settings
- `POST /api/settings` - Update display settings
- `WS /ws` - WebSocket for status updates

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
│   ├── Reset() - return to neutral position
│   ├── StreamBattery() - real-time battery
│   ├── StreamMovementStatus() - movement progress
│   └── StreamAudioLevels() - bidirectional audio levels
│
├── HTTP Server (:8001) - Minimal
│   ├── POST /api/offer (WebRTC signaling only)
│   ├── GET /health (convenience - also in gRPC)
│   └── GET /camera (JPEG snapshot)
│
├── WebRTC Server (aiortc)
│   ├── Waits for AI brain connections
│   ├── MicrophoneTrack → sends to host computer
│   ├── SpeakerOutput ← receives from host computer
│   └── DataChannel for state sync (eye states, battery, etc.)
│
├── Dashboard Server (:8080) - Web UI
│   ├── FastAPI backend with WebSocket
│   ├── React/Vite frontend (SPA)
│   ├── Movement controls
│   ├── Status monitoring
│   ├── Display settings
│   ├── WiFi setup interface
│   ├── Chat interface
│   └── Firmware updates
│
├── WiFi Manager
│   ├── Automatic hotspot on boot (if no connection)
│   ├── Network scanning
│   ├── Connection management
│   └── Hotspot control (start/stop)
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
│   └── Face tracking (OpenCV/MediaPipe) [optional]
│
└── Modules (src/modules/)
    ├── module_movements.py (19 pre-programmed movements)
    ├── module_servoctl.py (servo control + calibration)
    ├── module_camera.py (image capture)
    ├── module_audio.py (sounddevice wrapper)
    ├── module_battery.py (INA260 monitoring)
    ├── module_display.py (display compositor)
    ├── module_facetracking.py (face detection)
    ├── modules_roboeyes.py (eye animations)
    └── modules_spectrum.py (audio visualizer)
```

### Host computer (tars-omni) - AI Brain

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
    ├── services/robot.py (gRPC-based hardware control)
    ├── services/memory_chromadb.py (semantic memory)
    └── services/factories/ (STT/TTS provider factories)
```

## Configuration

### RPi (`.env`)
```bash
# Server configuration
API_PORT=8001              # HTTP (WebRTC signaling)
WEBRTC_ENABLED=true        # Enable WebRTC server

# Display
DISPLAY_ENABLED=true       # Enable display/eyes
DISPLAY_WIDTH=800
DISPLAY_HEIGHT=480

# Features
FACE_TRACKING_ENABLED=false  # Enable face tracking

# Audio devices (optional - auto-detected if not specified)
AUDIO_INPUT_DEVICE=
AUDIO_OUTPUT_DEVICE=
AUDIO_SAMPLE_RATE_IN=16000
AUDIO_SAMPLE_RATE_OUT=24000
```

Note: gRPC port (default 50051) and dashboard port (default 8080) are configured via command-line arguments, not .env:
```bash
python tars_daemon.py --grpc-port 50051 --dashboard-port 8080
```

### Host computer - `tars-omni/config.ini`
```ini
[Connection]
# Replace 100.115.193.41 with your robot's IP address
rpi_url = http://100.115.193.41:8001    # For WebRTC signaling
rpi_grpc = 100.115.193.41:50051         # For hardware control
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

# Run daemon (all services enabled by default)
python tars_daemon.py

# Or using start script
./start.sh

# With custom options
python tars_daemon.py --port 8001 --grpc-port 50051 --dashboard-port 8080

# Disable specific components
python tars_daemon.py --no-webrtc      # Disable WebRTC
python tars_daemon.py --no-dashboard   # Disable web dashboard
python tars_daemon.py --no-display     # Headless mode

# Enable optional features
python tars_daemon.py --face-tracking  # Enable face tracking

# Or as systemd service
sudo systemctl start tars
```

**On boot, RPi will:**
1. Start gRPC server on :50051
2. Start HTTP server on :8001 (WebRTC signaling)
3. Start dashboard on :8080 (web UI)
4. Initialize hardware (servos, camera, display)
5. Check WiFi connection, start hotspot if needed
6. Wait for AI brain connection
7. Display shows animated eyes or status

### Host computer (connects to RPi)
```bash
cd tars-omni
pip install -e ../tars  # Install tars_sdk
python tars_bot.py
```

**Host Computer will:**
1. Connect gRPC client to RPi :50051
2. Create WebRTC client
3. POST SDP offer to RPi :8001/api/offer
4. Establish P2P audio connection
5. Start Pipecat pipeline with STT/LLM/TTS
6. Use gRPC for all hardware control (fast!)

## Performance

Latency measurements on LAN:

| Operation | gRPC | Dashboard (HTTP) |
|-----------|------|------------------|
| Move command | 5-10ms | 15-30ms |
| Set emotion | 5-8ms | 15-25ms |
| Camera capture | 25-35ms | 50-100ms |
| Get status | 5-8ms | 10-20ms |
| Battery stream | 5-10ms/update | N/A |

## API Usage Examples

### Using the SDK (Python)

```python
from tars_sdk import TarsClient

# Connect to robot (replace with your robot's IP)
client = TarsClient("100.115.193.41:50051")

# Health check (gRPC)
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

# Context manager (replace with your robot's IP)
with TarsClient("100.115.193.41:50051") as client:
    client.move("wave_right")
```

### From tars-omni (LLM Tools)

```python
# In tars_bot.py
from services import robot as robot_service

# Initialize client (replace with your robot's IP)
robot_client = robot_service.get_robot_client("100.115.193.41:50051")

# LLM tool functions (already integrated)
async def execute_movement(movements: list[str]) -> str:
    # Uses gRPC client.move()
    result = robot_client.move(movements[0])
    return f"Completed in {result['duration']:.2f}s"

async def capture_camera_view() -> dict:
    # Uses gRPC client.capture_camera()
    jpeg_bytes = robot_client.capture_camera()
    return {"image": base64.b64encode(jpeg_bytes).decode()}
```

## Troubleshooting

### gRPC Connection Issues

```bash
# Test gRPC health (from Mac) - replace IP with your robot's IP
python -c "from tars_sdk import TarsClient; print(TarsClient('100.115.193.41:50051').health())"

# Check if gRPC port is open - replace IP with your robot's IP
nc -zv 100.115.193.41 50051

# Check daemon logs
journalctl -u tars -f | grep gRPC
```

### WebRTC Connection Issues

```bash
# Check if RPi is reachable - replace IP with your robot's IP
curl http://100.115.193.41:8001/health

# Test WebRTC signaling endpoint - replace IP with your robot's IP
curl -X POST http://100.115.193.41:8001/api/offer \
  -H "Content-Type: application/json" \
  -d '{"sdp": "test", "type": "offer"}'
```

### Dashboard Access Issues

```bash
# Check if dashboard is running - replace IP with your robot's IP
curl http://100.115.193.41:8080/

# Check WiFi hotspot status
# Connect to TARS_SETUP network, then visit http://10.42.0.1:8080

# View dashboard logs
journalctl -u tars -f | grep Dashboard
```

### Performance Testing

```python
import time
from tars_sdk import TarsClient

# Replace with your robot's IP
client = TarsClient("100.115.193.41:50051")

# Measure latency
start = time.time()
client.move("wave_right")
latency = (time.time() - start) * 1000
print(f"gRPC latency: {latency:.1f}ms")

# Should be 5-10ms on LAN
```

## See Also

- [DAEMON.md](./DAEMON.md) - Daemon setup and usage
- [MOVEMENTS.md](./MOVEMENTS.md) - Available movements
- [HARDWARE_IO.md](./HARDWARE_IO.md) - Hardware specifications
- [TARS_ARCHITECTURE_PLAN_V7.md](../TARS_ARCHITECTURE_PLAN_V7.md) - Full architecture plan
