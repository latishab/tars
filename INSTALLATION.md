# Installation Guide

## PyPI Package

The TARS robot software is available on PyPI as **tars-robot**.

### Installation Options

#### Default (Full Installation)

Install complete package with daemon, dashboard, and SDK:

```bash
pip install tars-robot
```

Includes everything:
- gRPC SDK (client library)
- Daemon server (WebRTC, gRPC)
- Web dashboard (FastAPI + React)
- Hardware control (servos, camera, display, battery)

#### Daemon + Dashboard (Raspberry Pi)

Same as default installation:

```bash
pip install tars-robot
# or explicitly
pip install tars-robot[daemon]
```

Use this on Raspberry Pi for running the robot.

#### SDK Only (App Development)

For lightweight SDK-only install (app development, remote control):

```bash
# Install without dependencies, then add minimal SDK deps
pip install --no-deps tars-robot
pip install grpcio>=1.60.0 protobuf>=4.25.0 loguru>=0.7.0
```

Perfect for:
- Developing apps that control TARS
- Remote control scripts  
- Lightweight client applications
- Host computer controlling a Pi

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

## Raspberry Pi Setup

### Quick Install

For running the robot daemon on Raspberry Pi:

```bash
# Install everything
pip install tars-robot

# Start daemon
python -m tars_daemon

# Or clone repo for development
git clone https://github.com/latishab/tars.git
cd tars
pip install -e .
python tars_daemon.py
```

### Development Install

For modifying the daemon code:

```bash
# Clone repository
git clone https://github.com/latishab/tars.git
cd tars

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in editable mode
pip install -e .

# Run daemon
python tars_daemon.py
```

### Starting the Daemon

```bash
# Start WebRTC + gRPC servers + dashboard
python tars_daemon.py

# With options
python tars_daemon.py --grpc-port 50051 --face-tracking

# Or using start script
./start.sh
```

The daemon will:
1. Start gRPC server on port 50051
2. Start WebRTC server on port 8001
3. Start web dashboard on port 8080
4. Initialize hardware (servos, camera, display)
5. Wait for AI brain or SDK client to connect

### Access Dashboard

```bash
# In browser
http://tars-pi.local:8080
# or
http://<pi-ip-address>:8080
```

Dashboard features:
- **Status**: Real-time system metrics (CPU, memory, battery, network)
- **Control**: Movement controls with virtual joystick
- **Apps**: Install and manage TARS apps from App Store
- **Settings**: WiFi configuration, system updates

---

## Developing Apps with SDK

### Setup

```bash
# Minimal SDK install
pip install --no-deps tars-robot
pip install grpcio>=1.60.0 protobuf>=4.25.0 loguru>=0.7.0

# Or install from source
git clone https://github.com/latishab/tars.git
cd tars
pip install --no-deps -e .
pip install grpcio protobuf loguru
```

### Example App

```python
#!/usr/bin/env python3
"""Simple TARS control app."""

from tars_sdk import TARSClient
import time

def main():
    # Connect to robot
    client = TARSClient(host="tars-pi.local", port=50051)
    
    # Check health
    health = client.health()
    print(f"Battery: {health['battery']['level']}%")
    
    # Execute movements
    client.set_emotion("happy")
    client.move("wave_right")
    time.sleep(2)
    
    client.set_emotion("excited")
    client.move("nod")
    time.sleep(2)
    
    # Capture photo
    photo = client.capture_camera(width=1280, height=720)
    with open("tars_view.jpg", "wb") as f:
        f.write(photo)
    print("Photo saved!")
    
    client.close()

if __name__ == "__main__":
    main()
```

### App Structure

For apps to be installable via dashboard App Store:

```
my-tars-app/
├── app.json          # App manifest
├── main.py           # Entry point
├── install.sh        # Installation script
├── uninstall.sh      # Cleanup script
└── requirements.txt  # Dependencies
```

`app.json` example:
```json
{
  "name": "my-tars-app",
  "version": "1.0.0",
  "description": "My TARS application",
  "author": "username",
  "repository": "https://github.com/username/my-app.git",
  "main": "main.py",
  "install_script": "install.sh",
  "uninstall_script": "uninstall.sh"
}
```

---

## System Requirements

### For SDK Development
- Python 3.9+
- Any OS (Windows, macOS, Linux)
- Dependencies: grpcio, protobuf, loguru

### For Daemon (Raspberry Pi)
- Raspberry Pi 5 (or 4 with 4GB+ RAM)
- Raspberry Pi OS (64-bit recommended)
- Python 3.9+
- I2C enabled
- Camera enabled (Pi Camera or USB webcam)

---

## Environment Variables

Optional configuration:

```bash
# SDK connection settings
export TARS_HOST="100.84.133.74"  # Robot IP
export TARS_PORT="50051"

# Daemon settings (on Pi)
export DISPLAY_ENABLED="true"
export DISPLAY_WIDTH="800"
export DISPLAY_HEIGHT="480"
```

---

## Troubleshooting

### SDK Connection Issues

```bash
# Test connection
python -c "from tars_sdk import TARSClient; print(TARSClient('tars-pi.local', 50051).health())"

# Check gRPC port
nc -zv tars-pi.local 50051

# Verify network
ping tars-pi.local
```

### Daemon Issues

```bash
# Check daemon is running
ps aux | grep tars_daemon

# Check I2C
sudo raspi-config  # Interface Options > I2C

# Verify camera
libcamera-hello

# Check permissions
sudo usermod -a -G i2c,gpio,video $USER

# View logs
journalctl -u tars -f
```

### Dashboard Issues

```bash
# Check dashboard is running
ps aux | grep start_dashboard

# Check port
lsof -i:8080

# Restart
pkill -f start_dashboard
python start_dashboard.py
```

---

## Next Steps

- [Dashboard Guide](./docs/DASHBOARD.md) - Web interface usage
- [API Documentation](./docs/MOVEMENTS.md) - Available movements
- [Hardware Setup](./docs/HARDWARE_IO.md) - Camera and audio
- [Architecture](./docs/ARCHITECTURE.md) - System overview
