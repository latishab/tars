# Servo Calibration

## Servo Tester

```bash
tars-servo-tester
```

Interactive GUI for calibrating servos. Requires Pi with display attached.

Features:
- Individual servo testing (channels 0–15)
- Test all 19 pre-programmed movements
- Real-time offset adjustment
- Auto-save to `src/config.ini`

## Servo Channels

| Channel | Function |
|---|---|
| 0 | Left leg height |
| 1 | Right leg height |
| 2 | Left leg position |
| 3 | Right leg position |

## Calibration Steps

1. Run `tars-servo-tester`
2. Go to Servo Testing tab
3. Test each servo individually and adjust offsets
4. Go to Movement Testing tab and verify all movements
5. Values auto-save to `src/config.ini`

## Config Format

`src/config.ini` — edit manually only if you know the correct target values:

```ini
[SERVO]
leftUpHeight = 250
leftDownHeight = 450
forwardLeftLeg = 200
backLeftLeg = 400
perfectLeftHeightOffset = 0
perfectLeftLegOffset = 0

rightUpHeight = 250
rightDownHeight = 450
forwardRightLeg = 200
backRightLeg = 400
perfectRightHeightOffset = 0
perfectRightLegOffset = 0
```

## Troubleshooting

**Servo not moving:** Check 12V power supply and wiring to correct PCA9685 channel.

**Servo jittering:** Adjust calibration offsets in the GUI.

**I2C not detected:**
```bash
sudo i2cdetect -y 1  # PCA9685 should appear at 0x40
sudo raspi-config    # Interface Options → I2C → Enable
```
