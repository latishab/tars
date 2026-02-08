# Movement Control API

Servo control system for TARS robot on Raspberry Pi 5. Provides 19 pre-programmed movements via HTTP API with V3 dual-leg independent control.

## Features

- **Servo Control V3**: Dual-leg independent control with improved servo management
- **19 Pre-programmed Movements**: From basic locomotion to complex choreography
- **Movement Registry**: Organized library of all available movements
- **HTTP API**: RESTful endpoints with OpenAPI documentation
- **Real-time Calibration**: Servo Tester GUI for fine-tuning

## Quick Start

### Start the Service

```bash
# Option 1: Using startup script
./start_movement_service.sh

# Option 2: Manual start
source venv/bin/activate
python main.py
```

The service will start on `http://0.0.0.0:8001`

### Test Movement

```bash
# Get available movements
curl http://localhost:8001/movements

# Execute a movement
curl -X POST http://localhost:8001/move \
  -H "Content-Type: application/json" \
  -d '{"movements": ["step_forward"]}'
```

## Installation

### 1. Install System Dependencies (Raspberry Pi 5)

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv i2c-tools
```

### 2. Enable I2C

```bash
sudo raspi-config
# Navigate to: Interface Options > I2C > Enable
sudo reboot
```

### 3. Install Python Dependencies

```bash
cd ~/tars
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Servos (V3 Format)

**⚠️ IMPORTANT**: Use the **Servo Tester GUI** for calibration - do NOT manually edit config.ini!

#### Using Servo Tester GUI

```bash
cd ~/tars/src
source ../venv/bin/activate
python app-servotester.py
```

The Servo Tester GUI provides:
- **Individual Servo Testing**: Test each servo (0-15) independently
- **Movement Testing**: Test all 19 pre-programmed movements
- **Calibration Adjustment**: Fine-tune offsets with real-time visual feedback
- **Safe Limits**: Prevents setting values that could damage servos
- **Auto-save**: Saves calibration values directly to config.ini

**Calibration Steps:**
1. Run `app-servotester.py`
2. Select "Servo Testing" tab
3. Test each leg servo individually (channels 0-3)
   - Servo 0: Left leg height
   - Servo 1: Right leg height
   - Servo 2: Left leg position
   - Servo 3: Right leg position
4. Use "Offset Adjustment" sliders to fine-tune neutral positions
5. Test movements in "Movement Testing" tab
6. Verify all movements execute smoothly
7. Calibration saves automatically to config.ini

## Movement API Endpoints

### `GET /movements`
List all available movements

**Response:**
```json
{
  "movements": {
    "step_forward": {
      "display_name": "Step Forward"
    },
    "turn_left": {
      "display_name": "Turn Left"
    }
  },
  "total": 19,
  "available": ["step_forward", "walk_forward", "turn_left", "bow", "pose", ...]
}
```

### `POST /move`
Execute a sequence of movements

**Request:**
```json
{
  "movements": ["step_forward", "turn_left", "step_forward"]
}
```

**Available Movements:**
- **Locomotion**: `step_forward`, `walk_forward`, `step_backward`, `walk_backward`
- **Turning**: `turn_left`, `turn_right`, `turn_left_slow`, `turn_right_slow`
- **Tilting**: `tilt_left`, `tilt_right`, `side_side`
- **Expressions**: `bow`, `pose`, `laugh`, `excited`, `swing_legs`
- **Waves**: `wave_left`, `wave_right`
- **Utility**: `neutral_legs`

**Response:**
```json
{
  "status": "ok",
  "results": [
    {"movement": "step_forward", "status": "completed"},
    {"movement": "turn_left", "status": "completed"}
  ]
}
```

**Example:**
```bash
# Single movement
curl -X POST http://localhost:8001/move \
  -H "Content-Type: application/json" \
  -d '{"movements": ["bow"]}'

# Sequence of movements
curl -X POST http://localhost:8001/move \
  -H "Content-Type: application/json" \
  -d '{"movements": ["step_forward", "step_forward", "bow"]}'
```

### `POST /move/legs`
Manual leg control (advanced - for custom choreography)

**Request:**
```json
{
  "left_height": 50,
  "right_height": 50,
  "left_leg": 50,
  "right_leg": 50,
  "speed": 0.8
}
```

**Parameters (all optional, 1-100 range):**
- `left_height`: Left leg height (1=up, 100=down)
- `right_height`: Right leg height (1=up, 100=down)
- `left_leg`: Left leg forward/back (1=forward, 50=neutral, 100=backward)
- `right_leg`: Right leg forward/back (1=forward, 50=neutral, 100=backward)
- `speed`: Movement speed (0.0-1.0, default 0.8)

**Example:**
```bash
# Raise both legs up
curl -X POST http://localhost:8001/move/legs \
  -H "Content-Type: application/json" \
  -d '{"left_height": 20, "right_height": 20, "speed": 0.6}'

# Neutral position
curl -X POST http://localhost:8001/move/legs \
  -H "Content-Type: application/json" \
  -d '{"left_height": 50, "right_height": 50, "left_leg": 50, "right_leg": 50, "speed": 0.8}'
```

### `POST /reset`
Reset all servos to neutral position

```bash
curl -X POST http://localhost:8001/reset
```

### `POST /disable`
Disable all servos (power off)

```bash
curl -X POST http://localhost:8001/disable
```

## Configuration

### Servo Calibration V3 (`src/config.ini`)

The `[SERVO]` section uses the V3 format with separate left/right controls:

**Key parameters:**
- Left/right leg heights: `leftUpHeight`, `leftDownHeight`, `rightUpHeight`, `rightDownHeight`
- Left/right leg positions: `forwardLeftLeg`, `backLeftLeg`, `forwardRightLeg`, `backRightLeg`
- Calibration offsets: `perfectLeftHeightOffset`, `perfectRightHeightOffset`, etc.

**Example V3 config:**
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

**⚠️ WARNING**: Do NOT manually edit these values. Use the Servo Tester GUI (`app-servotester.py`) for calibration.

## Essential Tools

### 1. Servo Tester GUI (app-servotester.py)
Interactive servo calibration and movement testing tool - **CRITICAL for setup**

```bash
python src/app-servotester.py
```

**Features:**
- Individual servo testing (channels 0-15)
- Test all 19 pre-programmed movements
- Real-time calibration offset adjustment
- Visual feedback for safe testing
- Auto-saves calibration to config.ini

**Use this for:**
- Initial servo calibration after assembly
- Testing movements before deploying API
- Debugging servo issues
- Fine-tuning movement performance

### 2. Configuration Manager (app-cms.py) - Optional
Synchronizes config.ini with config.ini.template

```bash
python src/app-cms.py
```

**Features:**
- Compares config.ini with template
- Adds new sections/fields from template updates
- Preserves existing values (especially servo calibration!)
- Creates backup before making changes
- Shows preview of changes before applying

**Use this when:**
- Updating TARS software (git pull)
- New configuration options are added to template
- Need to restore missing config sections while preserving calibration

**⚠️ IMPORTANT**: This tool preserves servo values - it does NOT recalibrate servos. Use app-servotester.py for calibration.

## Hardware Requirements

- **Raspberry Pi 5** (4GB+ RAM recommended)
- **PCA9685 PWM Driver** (I2C address 0x40)
- **Servos**: 4x servos (2 leg heights + 2 leg positions)
- **Power**: 12V battery with INA260 sensor (optional but recommended)
- **Bluetooth Gamepad** (optional, for manual control)

## Testing

### Servo Calibration Testing

Use the Servo Tester GUI for comprehensive testing:

```bash
cd ~/tars/src
source ../venv/bin/activate
python app-servotester.py
```

**Features:**
- Test individual servos (channels 0-15)
- Test all 19 pre-programmed movements
- Adjust calibration offsets in real-time
- View servo positions and PWM values
- Safe testing with visual feedback

### API Testing

```bash
# List all movements
curl http://localhost:8001/movements

# Execute movement
curl -X POST http://localhost:8001/move \
  -H "Content-Type: application/json" \
  -d '{"movements": ["step_forward"]}'

# Test manual control
curl -X POST http://localhost:8001/move/legs \
  -H "Content-Type: application/json" \
  -d '{"left_height": 50, "right_height": 50, "speed": 0.8}'

# Reset to neutral
curl -X POST http://localhost:8001/reset
```

## Troubleshooting

### I2C Errors

```bash
# Check I2C devices
sudo i2cdetect -y 1

# Should show device at 0x40 (PCA9685)
```

**If PCA9685 not detected:**
1. Check I2C is enabled: `sudo raspi-config` → Interface Options → I2C → Enable
2. Check wiring: SDA to GPIO 2, SCL to GPIO 3, VCC to 3.3V, GND to GND
3. Reboot: `sudo reboot`

### Servo Not Moving

1. **Use Servo Tester GUI**: `python src/app-servotester.py`
2. Test individual servos in "Servo Testing" tab
3. Verify power supply is connected and charged
4. Check servo wiring to PCA9685 channels:
   - Channel 0: Left leg height
   - Channel 1: Right leg height
   - Channel 2: Left leg position
   - Channel 3: Right leg position
5. Verify calibration values in config.ini (via GUI)
6. Test with manual commands: `curl -X POST http://localhost:8001/reset`

**Common issues:**
- **Servo jittering**: Adjust calibration offsets in Servo Tester GUI
- **Limited range**: Check servo min/max values in config.ini
- **No movement**: Verify power supply voltage (should be 12V)
- **Erratic movement**: Check for loose wiring or weak battery

### Movement Not Working

1. Check if movement is available:
   ```bash
   curl http://localhost:8001/movements
   ```
2. Test movement in Servo Tester GUI first
3. Check logs for error messages
4. Ensure robot is not already in motion (only one movement at a time)

### Calibration Issues

**Servos not centering properly:**
1. Use Servo Tester GUI offset adjustment sliders
2. Test each servo individually
3. Fine-tune until neutral position is correct
4. Save and verify changes persist

**Movements look wrong:**
1. Re-calibrate all servos from scratch
2. Verify servo channels are connected correctly
3. Check for mechanical binding or obstruction
4. Test with slower speeds first

## Safety Notes

- **Always test movements in a safe area with clearance**
- Keep emergency stop accessible (Bluetooth controller or `POST /disable`)
- Monitor battery voltage to prevent over-discharge
- Calibrate servos carefully to avoid mechanical strain
- Start with slow speeds when testing new movements
- Never manually move servos while powered
- Disconnect power before changing wiring

## API Documentation

FastAPI automatically generates interactive documentation:

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Dependencies

Movement control dependencies (from `requirements.txt`):

- **Servo Control**: adafruit-circuitpython-pca9685, lgpio
- **API**: fastapi, uvicorn
- **Input**: evdev (for Bluetooth gamepad)

## License

See main repository LICENSE file.
