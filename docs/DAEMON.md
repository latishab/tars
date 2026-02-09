# TARS Unified Daemon

**Single process** managing WebRTC audio, REST API, display, and hardware.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Set MACBOOK_URL

# Run
python tars_daemon.py --macbook http://100.64.0.1:7860

# Or use start script
./start.sh --macbook http://100.64.0.1:7860
```

## Architecture

```
tars_daemon.py (single process)
│
├─► WebRTC Client (aiortc)
│   ├── Mic capture (16kHz)
│   ├── Speaker output (24kHz)
│   └── Data channel (state sync)
│
├─► REST API (FastAPI :8001)
│   ├── /move, /reset
│   ├── /camera/capture
│   ├── /display/*, /eyes/*
│   └── /battery/status
│
├─► Display Manager (Pygame thread)
│   ├── Robot eyes (animated)
│   ├── Audio spectrum bars
│   └── Face tracking (optional)
│
└─► Hardware Modules
    ├── Servos (PCA9685)
    ├── Camera (Pi/USB)
    ├── Audio (USB soundcard)
    └── Battery (INA260)
```

## Connection Flow

```
Start Daemon
    │
    ├─► Initialize Hardware
    │   ├─► Servos (PCA9685)
    │   ├─► Camera (if available)
    │   ├─► Audio (if available)
    │   └─► Display (if enabled)
    │
    ├─► Start REST API (:8001)
    │
    └─► Connect WebRTC (if --macbook specified)
        │
        ├─► POST /api/offer to MacBook
        ├─► Receive SDP answer
        ├─► Establish P2P connection
        │
        ├─► Start mic streaming ────────►
        ├─► Start speaker playback ◄──────
        └─► Open data channel ◄─────────►
```

## Command Line Options

```bash
python tars_daemon.py [OPTIONS]

--macbook URL       MacBook URL for WebRTC (http://100.64.0.1:7860)
--port PORT         REST API port (default: 8001)
--no-display        Headless mode (no pygame window)
--face-tracking     Enable face tracking with eyes
--help              Show help
```

## Configuration (`.env`)

```bash
# MacBook (Tailscale recommended)
MACBOOK_URL=http://100.64.0.1:7860

# API
API_PORT=8001

# Display
DISPLAY_ENABLED=true
DISPLAY_WIDTH=800
DISPLAY_HEIGHT=480

# Audio devices (optional)
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

## Features

### WebRTC Audio Streaming
- Mic → MacBook: 16kHz mono PCM
- MacBook → Speaker: 24kHz mono PCM
- Auto-reconnect on failure

### REST API
Full hardware control via HTTP:
- `/health` - Status check
- `/move` - Execute movements
- `/camera/capture` - Grab image
- `/display/*` - Control display
- `/eyes/*` - Control eye states
- `/battery/status` - Battery info

See [API docs](http://localhost:8001/docs) when running.

### Display Manager
- Animated robot eyes
- Audio spectrum visualizer
- Face tracking (with `--face-tracking`)
- Battery indicator (top-right corner)
- Modes: eyes, spectrum, off

### Hardware Integration
- PCA9685 servo control (19 movements)
- Camera capture (Pi Camera or USB)
- USB soundcard (mic + speaker)
- INA260 battery monitoring
- Automatic hardware detection

## Troubleshooting

### Daemon won't start
```bash
# Check dependencies
pip install -r requirements.txt

# Check permissions
groups  # Should include i2c, gpio

# Run manually to see errors
python tars_daemon.py
```

### WebRTC connection failed
```bash
# Check MacBook service
curl http://100.64.0.1:7860/health

# Test connectivity
ping 100.64.0.1
tailscale status

# Run without WebRTC
python tars_daemon.py  # REST API only
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

## API Endpoints

**Health & Status:**
- `GET /` - Service info
- `GET /health` - Health check
- `GET /state` - Servo positions

**Movement:**
- `POST /move` - Execute movements
- `POST /reset` - Reset to neutral
- `POST /disable` - Disable servos
- See [MOVEMENTS.md](./MOVEMENTS.md)

**Camera:**
- `GET /camera/capture` - Capture image (base64 JPEG)
- `GET /camera/status` - Camera availability

**Display:**
- `POST /display/mode` - Set mode (eyes/spectrum/off)
- `POST /eyes/state` - Set state (idle/listening/thinking/speaking)
- `POST /eyes/emotion` - Set emotion (happy/angry/tired/surprised)
- `POST /eyes/look` - Look direction (-1 to 1)
- `POST /eyes/blink` - Trigger blink
- `POST /eyes/face` - Update face tracking position
- `GET /display/status` - Display status

**Battery:**
- `GET /battery/status` - Full battery info
- `GET /battery/percentage` - Battery percentage

Full API docs: http://localhost:8001/docs

## Features

The unified daemon provides:
- ✅ WebRTC audio streaming (real-time, low latency)
- ✅ REST API for hardware control
- ✅ Auto-reconnection on network failures
- ✅ Integrated display management
- ✅ Face tracking support
- ✅ Battery monitoring with auto-shutdown
- ✅ Single process architecture

## Development

```bash
# Run in foreground with logs
python tars_daemon.py --macbook http://100.64.0.1:7860

# Test REST API
curl http://localhost:8001/health
curl http://localhost:8001/docs

# Test movement
curl -X POST http://localhost:8001/move \
  -H "Content-Type: application/json" \
  -d '{"movements": ["forward"]}'

# Monitor logs
journalctl -u tars -f
```

## Next Steps

1. **Test locally**: Run daemon without WebRTC
2. **Setup MacBook**: Start tars-omni pipecat service
3. **Connect**: Run with `--macbook` flag
4. **Install service**: Setup systemd for auto-start
5. **Configure Tailscale**: For remote access

See [ARCHITECTURE.md](./ARCHITECTURE.md) for system overview.
