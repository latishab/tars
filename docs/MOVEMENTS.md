# Movement API

Controls TARS servos via gRPC. 19 pre-programmed movements across locomotion, expression, and utility.

## Hardware Requirements

- Raspberry Pi 5 (4GB+ RAM recommended)
- PCA9685 PWM driver (I2C address 0x40)
- 4× servos (channels 0–3: left height, right height, left position, right position)
- 12V battery + INA260 sensor (optional)

## Available Movements

| Category | Movements |
|---|---|
| Locomotion | `step_forward`, `walk_forward`, `step_backward`, `walk_backward` |
| Turning | `turn_left`, `turn_right`, `turn_left_slow`, `turn_right_slow` |
| Tilting | `tilt_left`, `tilt_right`, `side_side` |
| Expressions | `bow`, `pose`, `laugh`, `excited`, `swing_legs` |
| Waves | `wave_left`, `wave_right` |
| Utility | `neutral_legs` |

## SDK Usage

```bash
pip install tars-robot
```

```python
from tars_sdk import TarsClient

client = TarsClient(tars-pi.local:50051)

result = client.move(wave_right)
# {'success': True, 'duration': 1.2, 'error': None}

client.reset()

status = client.get_status()
print(status['is_moving'])
```

## Calibration

Use `tars-servo-tester` to calibrate servo positions. Requires Pi with display attached.

```bash
tars-servo-tester
```

Saves automatically to `src/config.ini`. For direct editing (advanced):

```ini
[SERVO]
# Left leg
leftUpHeight = 250
leftDownHeight = 450
forwardLeftLeg = 200
backLeftLeg = 400
perfectLeftHeightOffset = 0
perfectLeftLegOffset = 0

# Right leg
rightUpHeight = 250
rightDownHeight = 450
forwardRightLeg = 200
backRightLeg = 400
perfectRightHeightOffset = 0
perfectRightLegOffset = 0
```

## Troubleshooting

### I2C errors

```bash
sudo i2cdetect -y 1  # PCA9685 should appear at 0x40
```

If not detected: check I2C is enabled (`sudo raspi-config` → Interface Options → I2C) and verify wiring (SDA→GPIO 2, SCL→GPIO 3).

### Servo not moving

1. Run `tars-servo-tester` and test individual channels
2. Verify 12V power supply is connected and charged
3. Check channel assignments: 0=left height, 1=right height, 2=left position, 3=right position
4. Common issues: jittering → adjust calibration offsets; no movement → check 12V supply

### Movement not working

1. Verify movement name is in the table above
2. Check daemon is running: `sudo systemctl status tars`
3. Check logs: `journalctl -u tars -f`
