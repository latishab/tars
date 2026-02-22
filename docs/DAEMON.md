# TARS Daemon

Single process managing gRPC API, WebRTC audio, display, and hardware.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate gRPC code
./scripts/generate_grpc.sh

# Run daemon
python tars_daemon.py

# With options
python tars_daemon.py --grpc-port 50051 --face-tracking
```

## Architecture

```
tars_daemon.py (single process)
│
├── gRPC Server (:50051)
│   ├── Health, GetStatus
│   ├── ExecuteMovement, ResetPosition
│   ├── SetEmotion, SetEyeState
│   ├── CaptureCamera
│   ├── SetMicMute, GetMicMute
│   └── StreamBattery, StreamMovementStatus
│
├── HTTP Server (:8000)
│   ├── POST /api/offer (WebRTC signaling)
│   └── GET /health
│
├── WebRTC Server (aiortc)
│   ├── Mic track (16kHz)
│   ├── Speaker track (24kHz)
│   └── DataChannel (state sync)
│
├── Display Manager (Pygame thread)
│   ├── Robot eyes (animated)
│   ├── Audio spectrum bars
│   └── Face tracking (optional)
│
└── Hardware Modules
    ├── Servos (PCA9685)
    ├── Camera (Pi/USB)
    ├── Audio (USB soundcard)
    └── Battery (INA260)
```

## Command Line Options

```bash
python tars_daemon.py [OPTIONS]

--port PORT         HTTP API port (default: 8000)
--grpc-port PORT    gRPC API port (default: 50051)
--no-display        Headless mode (no pygame window)
--no-webrtc         Disable WebRTC server
--face-tracking     Enable face tracking with eyes
--help              Show help
```

## Configuration

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

## Systemd Service

### Install

```bash
# Copy service file
sudo cp tars.service /etc/systemd/system/

# Edit paths if different
sudo nano /etc/systemd/system/tars.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable tars
sudo systemctl start tars
```

### Manage

```bash
sudo systemctl status tars      # Check status
sudo systemctl restart tars     # Restart
journalctl -u tars -f           # View logs
```

## API Access

### gRPC (Primary)

```python
from tars_sdk import TarsClient

client = TarsClient("localhost:50051")
client.move("wave_right")
client.set_emotion("happy")
jpeg = client.capture_camera()
status = client.get_status()
```

### HTTP (WebRTC + Health)

```bash
# Health check
curl http://localhost:8000/health

# WebRTC signaling (used by aiortc)
curl -X POST http://localhost:8000/api/offer \
  -H "Content-Type: application/json" \
  -d '{"sdp": "...", "type": "offer"}'
```

## Features

- gRPC API for hardware control (5-10ms latency)
- WebRTC audio streaming (real-time, low latency)
- Auto-reconnection on network failures
- Integrated display management
- Face tracking support
- Battery monitoring with auto-shutdown
- Single process architecture

## Troubleshooting

### Daemon won't start

```bash
# Check dependencies
pip install -r requirements.txt

# Check permissions
groups  # Should include i2c, gpio, audio

# Run manually to see errors
python tars_daemon.py
```

### gRPC connection failed

```bash
# Test gRPC
python -c "from tars_sdk import TarsClient; print(TarsClient().health())"

# Check port
nc -zv localhost 50051

# Check logs
journalctl -u tars -f | grep gRPC
```

### WebRTC connection failed

```bash
# Check HTTP server
curl http://localhost:8000/health

# Test connectivity - replace with your robot's IP
ping 100.115.193.41
tailscale status
```

### No audio

```bash
# List devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Test mic
arecord -d 3 test.wav && aplay test.wav

# Check permissions
groups  # Should include audio
```

### Display issues

```bash
# Check environment
echo $DISPLAY

# Run headless
python tars_daemon.py --no-display

# Test pygame
python -c "import pygame; pygame.init()"
```

### Battery not detected

```bash
# Check I2C device
i2cdetect -y 1  # Should show 0x41

# Check permissions
groups  # Should include i2c
```

## Development

```bash
# Run in foreground with logs
python tars_daemon.py

# Test gRPC API
python -c "from tars_sdk import TarsClient; print(TarsClient().health())"

# Test HTTP
curl http://localhost:8000/health

# Monitor logs
journalctl -u tars -f
```

## Next Steps

1. Test locally: Run daemon
2. Setup AI brain: Start tars-conversation-app on host computer
3. Connect: WebRTC and gRPC will establish automatically
4. Install service: Setup systemd for auto-start
5. Configure Tailscale: For remote access

See [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview.
