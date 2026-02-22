# Movement Control API

Servo control system for TARS robot on Raspberry Pi 5. Provides 19 pre-programmed movements via gRPC API with V3 dual-leg independent control.

## Features

- **Servo Control V3**: Dual-leg independent control with improved servo management
- **19 Pre-programmed Movements**: From basic locomotion to complex choreography
- **Movement Registry**: Organized library of all available movements
- **gRPC API**: Low-latency hardware control (5-10ms response time)
- **Real-time Calibration**: Servo Tester GUI for fine-tuning

## Quick Start

### Start the Service

```bash
# Using startup script
./start.sh

# Or manually
python tars_daemon.py
```

The service will start:
- gRPC server on port 50051 (hardware control)
- WebRTC server on port 8000 (audio streaming)

### Test Movement

Using the Python SDK:

```python
from tars_sdk import TarsClient

# Connect to TARS
client = TarsClient("localhost:50051")

# Execute a movement
result = client.move("step_forward")
print(result)  # {'success': True, 'duration': 1.2, 'error': None}

# Get available movements
status = client.get_status()
print(status)
```

Or install the SDK:

```bash
pip install git+https://github.com/latishab/tars.git
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

## Movement gRPC API

### `ExecuteMovement(movement)`
Execute a single movement

**Python Example:**
```python
from tars_sdk import TarsClient

client = TarsClient("localhost:50051")

# Execute movement with default speed
result = client.move("step_forward")
print(result)
# {'success': True, 'duration': 1.2, 'error': None}

# Execute with custom speed
result = client.move("wave_right", speed=0.5)
```

**Available Movements:**
- **Locomotion**: `step_forward`, `walk_forward`, `step_backward`, `walk_backward`
- **Turning**: `turn_left`, `turn_right`, `turn_left_slow`, `turn_right_slow`
- **Tilting**: `tilt_left`, `tilt_right`, `side_side`
- **Expressions**: `bow`, `pose`, `laugh`, `excited`, `swing_legs`
- **Waves**: `wave_left`, `wave_right`
- **Utility**: `neutral_legs`

**Parameters:**
- `movement` (string): Movement name
- `speed` (float): Speed multiplier (0.1-1.0, default 1.0)

**Returns:**
- `success` (bool): Whether movement completed
- `duration` (float): Time taken in seconds
- `error` (string): Error message if failed

### `GetStatus()`
Get current robot status

**Python Example:**
```python
status = client.get_status()
print(status)
# {
#   'connected': True,
#   'battery': {'level': 87, 'charging': False, 'voltage': 11.8, 'current': 0.5},
#   'emotion': 'neutral',
#   'eye_state': 'idle',
#   'is_moving': False,
#   'movement': ''
# }
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

```python
from tars_sdk import TarsClient

client = TarsClient("localhost:50051")

# Execute movement
result = client.move("step_forward")
print(f"Success: {result.success}, duration: {result.duration:.2f}s")

# Reset to neutral
client.reset()

# Check status
status = client.get_status()
print(f"Moving: {status['is_moving']}")
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
6. Test with SDK: `python -c "from tars_sdk import TarsClient; TarsClient().reset()"`

**Common issues:**
- **Servo jittering**: Adjust calibration offsets in Servo Tester GUI
- **Limited range**: Check servo min/max values in config.ini
- **No movement**: Verify power supply voltage (should be 12V)
- **Erratic movement**: Check for loose wiring or weak battery

### Movement Not Working

1. Check if movement is available:
   ```python
   from tars_sdk import TarsClient; TarsClient().get_status()
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
- Keep emergency stop accessible (Bluetooth controller or `client.reset()`)
- Monitor battery voltage to prevent over-discharge
- Calibrate servos carefully to avoid mechanical strain
- Start with slow speeds when testing new movements
- Never manually move servos while powered
- Disconnect power before changing wiring

## API Documentation

FastAPI automatically generates interactive documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Dependencies

Movement control dependencies (from `requirements.txt`):

- **Servo Control**: adafruit-circuitpython-pca9685, lgpio
- **API**: fastapi, uvicorn
- **Input**: evdev (for Bluetooth gamepad)

## License

See main repository LICENSE file.
