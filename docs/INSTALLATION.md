# Installation

## SDK (Control robot remotely)

```bash
pip install tars-robot
```

```python
from tars_sdk import TarsClient

client = TarsClient("tars-pi.local:50051")
client.move("wave_right")
client.set_emotion("happy")
client.close()
```

---

## Daemon (Run on Raspberry Pi)

```bash
pip install tars-robot[daemon]
tars-daemon
```

Dashboard at `http://tars.local:8000`

### Auto-start on boot

```bash
sudo cp tars.service /etc/systemd/system/
sudo systemctl enable --now tars
```

### Development install

```bash
git clone https://github.com/latishab/tars.git
cd tars && pip install -e .[daemon]
tars-daemon

# Servo calibration tool (Pi with display only)
tars-servo-tester
```

---

## Troubleshooting

### SDK connection issues

1. Check daemon is running: `ssh tars-pi "sudo systemctl status tars"`
2. Test gRPC port: `telnet tars-pi.local 50051`
3. Verify network: `ping tars-pi.local`

### Daemon issues

1. Check I2C is enabled: `sudo raspi-config` → Interface Options → I2C
2. Verify camera: `libcamera-hello`
3. Check permissions: `sudo usermod -a -G i2c,gpio,video mac`
4. Check logs: `journalctl -u tars -f`

---

## See also

- [Movements & API](./MOVEMENTS.md)
- [Hardware I/O](./HARDWARE_IO.md)
- [Architecture](./ARCHITECTURE.md)
