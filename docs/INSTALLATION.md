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
from tars_sdk import TarsClient

# Connect to robot
client = TarsClient("tars-pi.local:50051")

# Control the robot
client.move("wave_right")
client.set_emotion("happy")

# Capture camera frame
frame = client.capture_camera(width=640, height=480, quality=85)

# Get status
status = client.get_status()
print(f"Battery: {status['battery']['level']}%")

# Close connection
client.close()
```

### Async SDK

```python
from tars_sdk import AsyncTarsClient
import asyncio

async def main():
    async with AsyncTarsClient("tars-pi.local:50051") as client:
        await client.move("nod")
        await client.set_emotion("excited")
        frame = await client.capture_camera()

asyncio.run(main())
```

---

## Daemon Installation (Raspberry Pi)

Two methods to install the robot daemon on a Raspberry Pi. **PyPI** is simpler; **Git clone** is for development.

---

### Method 1: PyPI (Recommended)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install daemon + all dependencies
pip install tars-robot[daemon]
```

After install, run the daemon:

```bash
# Download and run start script
curl -O https://raw.githubusercontent.com/latishab/tars/main/start.sh
chmod +x start.sh
./start.sh
```

Or run directly:

```bash
python -c "from tars_daemon import main; main()"
```

The daemon will:
1. Start unified HTTP server on port 8000 (dashboard + WebRTC signaling + REST API)
2. Start gRPC server on port 50051
3. Wait for AI brain or SDK client to connect

**Dashboard:** Open `http://tars.local:8000` in a browser.

---

### Method 2: Git Clone (Development)

```bash
git clone https://github.com/latishab/tars.git
cd tars

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in editable mode
pip install -e .[daemon]
```

Run the daemon:

```bash
./start.sh

# Or directly
python tars_daemon.py
```

**Servo Tester** (calibration tool, run separately on Pi with display):

```bash
python src/app-servotester.py
```

---

### Systemd Service (Auto-start on boot)

```bash
# Copy service file
sudo cp tars.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable tars
sudo systemctl start tars

# Check status
sudo systemctl status tars
journalctl -u tars -f
```

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

- [API Documentation](./MOVEMENTS.md) - Available movements and API
- [Hardware Setup](./HARDWARE_IO.md) - Camera and audio configuration
- [Architecture](./ARCHITECTURE.md) - System architecture overview

