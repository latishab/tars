# Installation Guide

## PyPI Package

The TARS robot software is available on PyPI as **tars-robot**.

### SDK Only (Client Library)

For controlling a TARS robot remotely via gRPC:

```bash
pip install tars-robot
```

This installs only the gRPC client SDK for communicating with the robot daemon.

### With Daemon Dependencies

For running the full robot daemon on Raspberry Pi:

```bash
pip install tars-robot[daemon]
```

This includes all dependencies needed to run the robot daemon:
- FastAPI & Uvicorn (HTTP API server)
- aiortc (WebRTC audio streaming)
- OpenCV (camera processing)
- pygame (display/roboeyes)
- pyserial (servo control)
- Adafruit libraries (PCA9685 servos, INA260 battery monitor)

### All Dependencies

To install everything:

```bash
pip install tars-robot[all]
```

---

## SDK Usage Example

```python
from tars_sdk import TARSClient

# Connect to robot
client = TARSClient(host="tars-pi.local", port=50051)

# Control the robot
client.move("wave_right")
client.set_emotion("happy")

# Capture camera frame
frame = client.capture_camera(width=640, height=480, quality=85)

# Get status
status = client.get_status()
print(f"Battery: {status.battery_percent}%")

# Close connection
client.close()
```

### Async SDK

```python
from tars_sdk import AsyncTARSClient
import asyncio

async def main():
    async with AsyncTARSClient(host="tars-pi.local") as client:
        await client.move("nod")
        await client.set_emotion("excited")
        frame = await client.capture_camera()

asyncio.run(main())
```

---

## Daemon Installation (Raspberry Pi)

For running the robot daemon on a Raspberry Pi:

### 1. Clone Repository

```bash
git clone https://github.com/latishab/tars.git
cd tars
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install daemon
pip install -e .[daemon]
```

### 3. Run Daemon

```bash
# Start WebRTC + gRPC servers
python tars_daemon.py

# Or using start script
./start.sh
```

The daemon will:
1. Start unified HTTP server on port 8000 (WebRTC + Dashboard + REST API)
2. Start gRPC server on port 50051
3. Wait for AI brain or SDK client to connect

---

## System Requirements

### For SDK (Client)
- Python 3.9+
- Any OS (Windows, macOS, Linux)

### For Daemon (Raspberry Pi)
- Raspberry Pi 5 (or 4 with 4GB+ RAM)
- Raspberry Pi OS (64-bit recommended)
- Python 3.9+
- I2C enabled
- Camera enabled (Pi Camera or USB webcam)

---

## Environment Variables

Optional configuration for the SDK:

```bash
# Default connection settings
export TARS_HOST="100.84.133.74"  # Tailscale IP
export TARS_PORT="50051"
```

---

## Troubleshooting

### SDK Connection Issues

If you cannot connect to the robot:

1. Check robot is running: `ssh tars-pi "ps aux | grep tars_daemon"`
2. Test gRPC port: `telnet tars-pi.local 50051`
3. Check firewall settings on Pi
4. Verify network connectivity (ping tars-pi.local)

### Daemon Issues

If daemon fails to start:

1. Check I2C is enabled: `sudo raspi-config` > Interface Options > I2C
2. Verify camera: `libcamera-hello`
3. Check permissions: `sudo usermod -a -G i2c,gpio,video mac`
4. Check logs: `tail -f /tmp/tars.log`

---

## Next Steps

- [API Documentation](./docs/MOVEMENTS.md) - Available movements and API
- [Hardware Setup](./docs/HARDWARE_IO.md) - Camera and audio configuration
- [Architecture](./docs/ARCHITECTURE.md) - System architecture overview

