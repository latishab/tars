# TARS Control System V3

FastAPI-based control system for servo control and camera capture on Raspberry Pi 5. Provides HTTP endpoints for controlling TARS robot movements (57+ pre-programmed movements) and capturing camera frames, with AI processing handled by a separate MacBook via tars-omni.

## Architecture

```
┌─────────────────────────────────────────┐
│     MacBook (tars-omni)                 │
│  ┌───────────────────────────────────┐  │
│  │  - Speech-to-Text (Whisper)       │  │
│  │  - Text-to-Speech (ElevenLabs)    │  │
│  │  - LLM (GPT-4o)                   │  │
│  │  - Vision Processing (GPT-4V)     │  │
│  └───────────────┬───────────────────┘  │
└──────────────────┼──────────────────────┘
                   │ HTTP API
                   │
┌──────────────────▼──────────────────────┐
│  Raspberry Pi 5 (TARS Control System)   │
│  ┌───────────────────────────────────┐  │
│  │  FastAPI Server (port 8001)       │  │
│  │  ├── Servo Control (PCA9685)      │  │
│  │  ├── Camera Capture (Picamera2)   │  │
│  │  ├── Movement Registry (57+)      │  │
│  │  └── Movement Endpoints           │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Features

- **Servo Control V3**: Dual-leg independent control with improved servo management
- **57+ Pre-programmed Movements**: From basic locomotion to complex choreography
- **Movement Registry**: Organized library of all available movements
- **Camera Capture**: Real-time frame capture from Raspberry Pi Camera Module v2 (1280x720 JPEG)
- **HTTP API**: RESTful endpoints with OpenAPI documentation
- **CORS Enabled**: Cross-origin requests supported for MacBook integration
- **Minimal Footprint**: ~250MB dependencies (vs. 1.3GB with AI components)

## Essential Tools

### 1. TARS Control API (main.py)
FastAPI HTTP server for robot control and camera capture
```bash
python main.py
# Access: http://localhost:8001
# Docs: http://localhost:8001/docs
```

### 2. Servo Tester GUI (app-servotester.py)
Interactive servo calibration and movement testing tool - **CRITICAL for setup**
```bash
python src/app-servotester.py
```

**Features:**
- Individual servo testing (channels 0-15)
- Test all 57+ pre-programmed movements
- Real-time calibration offset adjustment
- Visual feedback for safe testing
- Auto-saves calibration to config.ini

**Use this for:**
- Initial servo calibration after assembly
- Testing movements before deploying API
- Debugging servo issues
- Fine-tuning movement performance

### 3. Configuration Manager (app-cms.py) - Optional
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
- **Movement Testing**: Test all 57+ pre-programmed movements
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

## Usage

### Start the Service

#### Option 1: Using Startup Script

```bash
./start_movement_service.sh
```

#### Option 2: Manual Start

```bash
source venv/bin/activate
python main.py
```

The service will start on `http://0.0.0.0:8001`

### Test the Service

```bash
# Health check
curl http://localhost:8001/health

# Get available movements
curl http://localhost:8001/movements

# Execute a movement
curl -X POST http://localhost:8001/move \
  -H "Content-Type: application/json" \
  -d '{"movements": ["step_forward"]}'
```

## API Endpoints

### Service Endpoints

#### `GET /`
Root endpoint - service info

**Response:**
```json
{
  "service": "TARS Control System",
  "version": "3.0.0",
  "servo_controller": "V3",
  "status": "running",
  "camera_available": true,
  "moving": false,
  "arms_present": false,
  "available_movements": 20
}
```

#### `GET /health`
Health check

**Response:**
```json
{
  "status": "ok",
  "moving": false,
  "camera": true,
  "arms_present": false
}
```

#### `GET /state`
Get current servo positions and movement state

**Response:**
```json
{
  "positions": {
    "0": 350,
    "1": 350,
    "2": 300,
    "3": 300
  },
  "moving": false,
  "camera_running": true,
  "arms_present": false
}
```

#### `GET /movements`
List all available movements

**Response:**
```json
{
  "movements": {
    "step_forward": {
      "display_name": "Step Forward",
      "type": "legs_only",
      "available": true
    },
    "right_hi": {
      "display_name": "Right Hi",
      "type": "has_arms",
      "available": false
    }
  },
  "total": 57,
  "legs_only": ["step_forward", "walk_forward", "turn_left", ...],
  "requires_arms": ["right_hi", "left_hi", "monster", ...]
}
```

### Movement Endpoints

#### `POST /move`
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

#### `POST /move/legs`
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

#### `POST /reset`
Reset all servos to neutral position

```bash
curl -X POST http://localhost:8001/reset
```

#### `POST /disable`
Disable all servos (power off)

```bash
curl -X POST http://localhost:8001/disable
```

### Camera Endpoints

#### `GET /camera/status`
Get camera status

**Response:**
```json
{
  "available": true,
  "running": true,
  "first_frame_captured": true
}
```

#### `GET /camera/capture`
Capture current camera frame as base64-encoded JPEG

**Response:**
```json
{
  "status": "ok",
  "image": "base64-encoded-jpeg-data...",
  "format": "jpeg",
  "width": 1280,
  "height": 720
}
```

**Example (save to file):**
```bash
curl http://localhost:8001/camera/capture | jq -r '.image' | base64 -d > frame.jpg
```

**Example (from MacBook):**
```bash
curl http://raspberrypi.local:8001/camera/capture | jq -r '.image' | base64 -d > frame.jpg
```

## Configuration

### Servo Calibration V3 (`src/config.ini`)

The `[SERVO]` section uses the V3 format with separate left/right controls:

**Key parameters:**
- `arms_present`: Boolean - whether arms are installed
- Left/right leg heights: `leftUpHeight`, `leftDownHeight`, `rightUpHeight`, `rightDownHeight`
- Left/right leg positions: `forwardLeftLeg`, `backLeftLeg`, `forwardRightLeg`, `backRightLeg`
- Calibration offsets: `perfectLeftHeightOffset`, `perfectRightHeightOffset`, etc.
- Arm ranges (if arms_present): `leftMainMin`, `leftMainMax`, etc.

### Camera Configuration (`src/config.ini`)

The `[UI]` section controls camera settings:

```ini
[UI]
use_camera_module = True  # Enable/disable camera
rotation = 270            # Camera rotation (0, 90, 180, 270)
target_fps = 30           # Frame rate
```

## Hardware Requirements

- **Raspberry Pi 5** (4GB+ RAM recommended)
- **PCA9685 PWM Driver** (I2C address 0x40)
- **Servos**: 4x servos minimum (2 leg heights + 2 leg positions)
  - Optional: 6x additional servos for arms (when arms_present=True)
- **Camera**: Raspberry Pi Camera Module v2 or compatible
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
- Test all 57+ pre-programmed movements
- Adjust calibration offsets in real-time
- View servo positions and PWM values
- Safe testing with visual feedback

### API Testing

```bash
# Health check
curl http://localhost:8001/health

# List all movements
curl http://localhost:8001/movements

# Execute movement
curl -X POST http://localhost:8001/move \
  -H "Content-Type: application/json" \
  -d '{"movements": ["step_forward"]}'

# Capture camera frame
curl http://localhost:8001/camera/capture | jq -r '.image' | base64 -d > frame.jpg
```

## Troubleshooting

### I2C Errors

```bash
# Check I2C devices
sudo i2cdetect -y 1

# Should show device at 0x40 (PCA9685)
```

### Servo Not Moving

1. **Use Servo Tester GUI**: `python src/app-servotester.py`
2. Test individual servos in "Servo Testing" tab
3. Verify power supply is connected and charged
4. Check servo wiring to PCA9685 channels
5. Verify calibration values in config.ini (via GUI)
6. Test with manual commands: `curl -X POST http://localhost:8001/reset`

### Camera Not Available

```bash
# Check camera detection
libcamera-hello --list-cameras

# Test camera
libcamera-hello -t 5000
```

## Development

### API Documentation

FastAPI automatically generates interactive documentation:

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Dependencies

See `requirements-minimal.txt` for the complete list. Key dependencies:

- **Servo Control**: adafruit-circuitpython-pca9685, lgpio
- **Camera**: picamera2, opencv-python
- **API**: fastapi, uvicorn
- **Audio**: pygame (for basic beeps/sounds)
- **Input**: evdev (for Bluetooth gamepad)

**Total size**: ~250MB (vs. 1.3GB with AI dependencies)

## Rollback to Full AI Version

If you need to restore the original AI-enabled version:

```bash
# Restore files from git
git checkout HEAD -- src/modules/
git checkout HEAD -- src/config.ini

# Reinstall full dependencies
pip install -r requirements.txt

# Start original app
python src/app.py
```

All removed AI modules are preserved in git history.

## Safety Notes

- Always test movements in a safe area with clearance
- Keep emergency stop accessible (Bluetooth controller or `POST /disable`)
- Monitor battery voltage to prevent over-discharge
- Calibrate servos carefully to avoid mechanical strain
- Start with slow speeds when testing new movements

## License

See main repository LICENSE file.
