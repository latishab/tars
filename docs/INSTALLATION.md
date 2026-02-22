# Installation

## SDK (Control Robot Remotely)

```bash
pip install tars-robot
```

```python
from tars_sdk import TarsClient

client = TarsClient("tars.local:50051")
client.move("wave_right")
client.set_emotion("happy")
client.close()
```

Works on any OS. Python 3.9+ required.

---

## Daemon (Run on Raspberry Pi)

### Quick Install

```bash
pip install tars-robot[daemon]
tars-daemon
```

Dashboard: `http://tars.local:8000`

### Development Install

```bash
git clone https://github.com/latishab/tars.git
cd tars && pip install -e .[daemon]
tars-daemon
```

---

## Auto-Start on Boot

### PyPI users

```bash
tars-daemon --install-service | sudo tee /etc/systemd/system/tars.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now tars
```

### Git clone users

```bash
sudo cp tars.service /etc/systemd/system/
sudo systemctl enable --now tars
```

---

## Requirements

- **SDK**: Python 3.9+, Windows / macOS / Linux
- **Daemon**: Raspberry Pi 5 (or Pi 4 4GB+), Pi OS 64-bit, I2C enabled

---

## Next Steps

- [WiFi Setup](./WIFI_SETUP.md) — Connect to your network
- [API Reference](./API.md) — SDK methods and REST endpoints
- [Calibration](./CALIBRATION.md) — Servo setup
- [Daemon](./DAEMON.md) — CLI options and architecture
