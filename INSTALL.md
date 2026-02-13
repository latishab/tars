# TARS Installation Guide

## PyPI Installation

The `tars-robot` package is available on PyPI with multiple installation options depending on your use case.

### For Raspberry Pi 5 (Default - Full Installation)

The default installation includes everything needed to run TARS on Raspberry Pi 5:

```bash
pip install tars-robot
```

This includes:
- SDK (gRPC client)
- Daemon (gRPC server)
- Hardware control (servos, battery, camera)
- Display support (animated eyes)
- Web dashboard
- WiFi manager

Available commands after installation:
```bash
# Start the daemon
tars-daemon

# Run servo calibration GUI
tars-servo-tester

# Daemon with options
tars-daemon --port 8001 --grpc-port 50051 --dashboard-port 8080
tars-daemon --no-display --no-webrtc  # Headless mode
tars-daemon --face-tracking           # Enable face tracking
```

### For Host Computers (SDK Only)

If you only need to control a TARS robot from your computer (no hardware):

```bash
pip install tars-robot[sdk]
```

This installs only the minimal SDK with gRPC client support.

Usage:
```python
from tars_sdk import TarsClient

client = TarsClient("192.168.1.100:50051")
client.move("wave_right")
```

### Optional Features

Add optional features to the default installation:

```bash
# WebRTC support (for host computers with audio streaming)
pip install tars-robot[webrtc]

# Audio support (sounddevice for USB audio)
pip install tars-robot[audio]

# Face tracking (MediaPipe)
pip install tars-robot[facetracking]

# Everything including development tools
pip install tars-robot[all]
```

### Development Installation

For contributing to TARS:

```bash
git clone https://github.com/latishab/tars.git
cd tars
pip install -e .[dev]

# Generate gRPC code
./scripts/generate_grpc.sh
```

## System Dependencies

### Raspberry Pi OS

Some dependencies require system packages:

```bash
# Camera support (Pi Camera)
sudo apt install python3-picamera2

# GPIO and I2C (for servos)
sudo apt install python3-lgpio

# Audio (if using USB soundcard)
sudo apt install portaudio19-dev

# Display (if using pygame)
sudo apt install libsdl2-dev libsdl2-mixer-dev
```

### Ubuntu/Debian (Host Computer)

```bash
# Audio support
sudo apt install portaudio19-dev

# WebRTC dependencies
sudo apt install libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev
```

### macOS (Host Computer)

```bash
# Audio support
brew install portaudio

# WebRTC dependencies
brew install ffmpeg
```

## Dashboard Frontend

The dashboard frontend is pre-built and included in the PyPI package. If you need to rebuild it:

```bash
cd dashboard/frontend
npm install
npm run build
```

The built files go to `dashboard/frontend/dist/` and are automatically included in the package.

## Configuration

After installation, copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` to configure:
- `API_PORT` - WebRTC signaling port
- `WEBRTC_ENABLED` - Enable/disable WebRTC
- `DISPLAY_ENABLED` - Enable/disable display
- `DISPLAY_WIDTH`, `DISPLAY_HEIGHT` - Display resolution
- `FACE_TRACKING_ENABLED` - Enable/disable face tracking
- Audio device settings

## Package Structure

```
tars-robot/
├── tars_sdk/              # Python SDK (gRPC client)
│   ├── client.py          # Synchronous client
│   ├── async_client.py    # Async client
│   └── proto/             # Protocol buffers
├── grpc_server/           # gRPC server implementation
│   ├── server.py
│   └── servicer.py
├── webrtc/                # WebRTC server/client
│   ├── server.py
│   ├── client.py
│   ├── audio_track.py
│   └── audio_output.py
├── state/                 # State management
│   └── data_channel.py
├── dashboard/             # Web dashboard
│   ├── backend/           # FastAPI backend
│   └── frontend/          # React frontend (pre-built)
├── src/                   # Hardware modules
│   ├── modules/           # Hardware abstraction layer
│   ├── app-servotester.py # Servo calibration GUI
│   └── config.ini         # Default configuration
├── tars_daemon.py         # Main daemon entry point
└── app_servotester.py     # Servo tester wrapper
```

## Console Scripts

After installation, these commands are available:

```bash
tars-daemon          # Start the TARS daemon
tars-servo-tester    # Open servo calibration GUI
```

### First Time Setup Workflow

```bash
# 1. Install TARS on Raspberry Pi
pip install tars-robot

# 2. Calibrate servos (first time only)
tars-servo-tester
# Opens GUI, adjust servo positions, saves to ~/.tars/config.ini

# 3. Run daemon
tars-daemon
# Reads servo positions from ~/.tars/config.ini
```

No git clone needed - everything is installed via pip.

## Verification

Test your installation:

```bash
# Test SDK import
python -c "from tars_sdk import TarsClient; print('SDK OK')"

# Test daemon (RPi only)
python -c "import tars_daemon; print('Daemon OK')"

# Check version
python -c "import tars_sdk; print(tars_sdk.__version__)"
```

## Troubleshooting

### Import Errors

If you get import errors, ensure you're using Python 3.9+:
```bash
python --version
```

### gRPC Not Found

Regenerate gRPC code:
```bash
./scripts/generate_grpc.sh
```

### Dashboard Not Loading

Ensure dashboard frontend is built:
```bash
cd dashboard/frontend
npm run build
```

### Hardware Errors (RPi)

Check I2C is enabled:
```bash
sudo raspi-config
# Interface Options -> I2C -> Enable
```

Check devices:
```bash
i2cdetect -y 1
```

## See Also

- [README.md](./README.md) - Overview and quick start
- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) - System architecture
- [DAEMON.md](./docs/DAEMON.md) - Daemon configuration
- [MOVEMENTS.md](./docs/MOVEMENTS.md) - Movement API reference
