# Hardware I/O API

FastAPI endpoints for camera, audio, and general system status on Raspberry Pi 5.

## Service Endpoints

### `GET /`
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
  "available_movements": 19
}
```

### `GET /health`
Health check

**Response:**
```json
{
  "status": "ok",
  "moving": false,
  "camera": true
}
```

### `GET /state`
Get current servo positions and system state

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
  "camera_running": true
}
```

## Camera Endpoints

### `GET /camera/status`
Get camera status

**Response:**
```json
{
  "available": true,
  "running": true,
  "camera_type": "picamera2"
}
```

**Note:** `camera_type` can be:
- `"picamera2"` - Pi Camera Module
- `"opencv"` - USB webcam
- `null` - No camera available

### `GET /camera/capture`
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

**Example (from MacBook via Tailscale):**
```bash
curl http://raspberrypi.local:8001/camera/capture | jq -r '.image' | base64 -d > frame.jpg
```

## Audio Endpoints

### `POST /audio/play`
Play audio bytes through USB soundcard speaker

**Request:**
```json
{
  "audio_data": "base64-encoded-audio-bytes",
  "format": "pcm",
  "sample_rate": 24000,
  "channels": 1
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "Audio played successfully"
}
```

### `WS /audio/stream`
WebSocket endpoint for bidirectional audio streaming

**Usage:**
- Connect to `ws://localhost:8001/audio/stream`
- Send audio bytes from MacBook (TTS output)
- Receive audio bytes from RPi (microphone input)

**Example (Python client):**
```python
import asyncio
import websockets

async def audio_stream():
    async with websockets.connect("ws://raspberrypi.local:8001/audio/stream") as ws:
        # Send TTS audio to RPi speaker
        await ws.send(tts_audio_bytes)

        # Receive mic audio from RPi
        mic_data = await ws.recv()
        print(f"Received {len(mic_data)} bytes from microphone")

asyncio.run(audio_stream())
```

## Hardware Setup

### Camera

The camera module automatically detects and uses available cameras:

1. **Pi Camera Module v2** (preferred) - Uses picamera2
2. **USB Webcam** (fallback) - Uses OpenCV

**No manual configuration required** - just connect your camera and the system will detect it.

**Configuration in `src/config.ini`:**
```ini
[UI]
use_camera_module = True  # Enable/disable camera in servo tester
```

**Hardware connection:**
- **Pi Camera**: Connect to CSI port on Raspberry Pi 5
- **USB Webcam**: Connect to any USB port

### Audio (USB Soundcard)

**Hardware connection:**
- USB soundcard with microphone input and speaker output
- Connect to USB port on Raspberry Pi 5

**Testing soundcard:**
```bash
# List audio devices
aplay -l
arecord -l

# Test speaker
speaker-test -t wav -c 2

# Test microphone
arecord -d 5 test.wav && aplay test.wav
```

**Configuration:**
The audio module automatically detects USB soundcard. Set default device in `~/.asoundrc` if needed:

```bash
defaults.pcm.card 1
defaults.ctl.card 1
```

## Testing

### Camera Testing

```bash
# Test with TARS camera module
python test_camera.py  # Captures test frames and saves as test_frame.jpg

# Check which camera is detected
curl http://localhost:8001/camera/status

# Capture a frame
curl http://localhost:8001/camera/capture | jq -r '.image' | base64 -d > frame.jpg
```

### Audio Testing

```bash
# Test speaker playback
curl -X POST http://localhost:8001/audio/play \
  -H "Content-Type: application/json" \
  -d '{"audio_data": "base64-audio-here", "format": "pcm", "sample_rate": 24000, "channels": 1}'

# Test WebSocket streaming
# (Use Python script or WebSocket client)
```

## Troubleshooting

### Camera Not Available

The camera module tries Pi Camera first, then USB webcam. Check which camera type you're using:

**For Pi Camera:**
```bash
# Check camera detection
libcamera-hello --list-cameras

# Test camera
libcamera-hello -t 5000

# Enable legacy camera (if needed)
sudo raspi-config
# Navigate to: Interface Options > Legacy Camera > Enable
sudo reboot
```

**For USB Webcam:**
```bash
# List video devices
ls -l /dev/video*

# Test with fswebcam
fswebcam test.jpg

# Check permissions
sudo usermod -a -G video $USER
```

**Test with TARS camera module:**
```bash
python test_camera.py  # Should show which camera type is detected
```

### Audio Issues

**No sound from speaker:**
```bash
# Check if USB soundcard is detected
aplay -l

# Test speaker
speaker-test -t wav -c 2

# Adjust volume
alsamixer

# Set default audio device
sudo nano ~/.asoundrc
# Add:
# defaults.pcm.card 1
# defaults.ctl.card 1
```

**Microphone not working:**
```bash
# Check if microphone is detected
arecord -l

# Test recording
arecord -d 5 -f cd test.wav && aplay test.wav

# Check microphone levels
alsamixer
# Press F4 for capture devices
# Adjust microphone gain
```

**WebSocket connection issues:**
```bash
# Check if service is running
curl http://localhost:8001/health

# Test WebSocket connection
# Use websocat or wscat
websocat ws://localhost:8001/audio/stream
```

## Hardware Requirements

- **Camera**: Pi Camera Module v2 (preferred) or USB webcam (fallback)
- **Audio**: USB soundcard with microphone input and speaker output
- **Raspberry Pi 5**: 4GB+ RAM recommended

## API Documentation

FastAPI automatically generates interactive documentation:

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Dependencies

Camera and audio dependencies (from `requirements.txt`):

- **Camera**: picamera2, opencv-python
- **Audio**: pygame, pyaudio, websockets
- **API**: fastapi, uvicorn

## License

See main repository LICENSE file.
