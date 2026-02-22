# Hardware I/O API

gRPC and WebRTC endpoints for camera, audio, and system control on Raspberry Pi 5.

**Communication Protocols:**
- **gRPC** (port 50051): Low-latency hardware control (camera, movements, status)
- **WebRTC** (port 8000): Real-time bidirectional audio streaming

## ⚡ gRPC API

### `Health()`
Get system health and status

**Python Example:**
```python
from tars_sdk import TarsClient

client = TarsClient("localhost:50051")
health = client.health()
print(health)
# {
#   'status': 'healthy',
#   'version': '3.0.0',
#   'grpc_available': True,
#   'webrtc': {'available': True, 'connected': True},
#   'hardware': {
#     'servos': True, 'camera': True, 'audio': True,
#     'display': True, 'battery': True, 'moving': False
#   },
#   'battery': {'level': 87, 'charging': False, 'voltage': 11.8, 'current': 0.5}
# }
```

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

## 🔇 Audio Mute API

### `SetMicMute(muted)`
Mute or unmute the robot microphone.

**Python Example:**
```python
# Mute mic
client.set_mic_mute(True)

# Unmute mic
client.set_mic_mute(False)

# Check current state
is_muted = client.is_mic_muted
```

When muted, the WebRTC audio track stops forwarding frames from the mic. Queued frames are drained to prevent buffer fill. The mic hardware remains active.

---

## 📷 Camera API

### `CaptureCamera(width, height, quality)`
Capture camera frame as JPEG bytes

**Python Example:**
```python
from tars_sdk import TarsClient

client = TarsClient("localhost:50051")

# Capture with default settings (640x480, quality 80)
jpeg_bytes = client.capture_camera()
with open("frame.jpg", "wb") as f:
    f.write(jpeg_bytes)

# Capture with custom settings
jpeg_bytes = client.capture_camera(width=1280, height=720, quality=90)
```

**Parameters:**
- `width` (int): Image width (default 640)
- `height` (int): Image height (default 480)
- `quality` (int): JPEG quality 1-100 (default 80)

**Returns:** Raw JPEG image bytes

**Latency:** 5-10ms for 640x480 capture

## 🎙️ Audio API (WebRTC)

Audio streaming uses **WebRTC** for real-time bidirectional audio with minimal latency.

**Architecture:**
```
Host Computer                      Raspberry Pi
┌─────────────┐                   ┌──────────────┐
│ TTS Output  │──WebRTC Audio────►│ Speaker      │
│             │    (24kHz PCM)    │              │
│ STT Input   │◄──WebRTC Audio────│ Microphone   │
└─────────────┘    (16kHz PCM)    └──────────────┘
```

**Setup:**
1. Host connects to RPi WebRTC server via POST /api/offer
2. Audio tracks are established automatically
3. Mic audio flows: RPi → Host (for STT)
4. TTS audio flows: Host → RPi (for speaker output)

**Python Example (using tars-conversation-app):**
```python
from transport import AiortcRPiClient

# Connect to RPi
client = AiortcRPiClient(rpi_url="http://tars.local:8000")
await client.connect()

# Audio tracks are established automatically
# Use in Pipecat pipeline for STT/TTS
```

**See tars-conversation-app repository** for full audio pipeline implementation with:
- VAD (Voice Activity Detection)
- STT (Speech-to-Text via Deepgram)
- TTS (Text-to-Speech via ElevenLabs)
- Audio frame processing

## 🔧 Hardware Setup

### Camera

The camera module automatically detects and uses available cameras:

1. **Pi Camera Module v2** (preferred) - Uses picamera2
2. **USB Webcam** (fallback) - Uses OpenCV

**No manual configuration required** - just connect your camera and the system will detect it.

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

## 🧪 Testing

### gRPC Service Testing

```python
from tars_sdk import TarsClient

# Connect to TARS
client = TarsClient("localhost:50051")

# Test health
health = client.health()
print(f"Status: {health['status']}")
print(f"Camera available: {health['hardware']['camera']}")

# Test camera capture
jpeg_bytes = client.capture_camera()
with open("test_frame.jpg", "wb") as f:
    f.write(jpeg_bytes)
print(f"Captured {len(jpeg_bytes)} bytes")

# Test movement
result = client.move("wave_right")
print(f"Movement: {result}")
```

### WebRTC Audio Testing

Test audio streaming using the tars-conversation-app repository:

```bash
cd /path/to/tars-conversation-app
python tars_bot.py
```

This will:
1. Connect to RPi WebRTC server
2. Establish bidirectional audio
3. Test full STT → LLM → TTS pipeline

## 🔍 Troubleshooting

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

**gRPC connection issues:**
```python
# Test gRPC connection
from tars_sdk import TarsClient
try:
    client = TarsClient("localhost:50051")
    health = client.health()
    print(f"Connection successful: {health['status']}")
except Exception as e:
    print(f"Connection failed: {e}")
```

**WebRTC connection issues:**
- Check RPi is running: `python tars_daemon.py`
- Check port 8000 is accessible
- Test from tars-conversation-app with `python tars_bot.py`

## 📋 Hardware Requirements

- **Camera**: Pi Camera Module v2 (preferred) or USB webcam (fallback)
- **Audio**: USB soundcard with microphone input and speaker output
- **Raspberry Pi 5**: 4GB+ RAM recommended

## 📚 API Documentation

**gRPC Proto Definition:**
See `tars_sdk/proto/tars.proto` for complete API specification

**Python SDK:**
```bash
pip install tars-robot
```

**SDK Documentation:**
```python
from tars_sdk import TarsClient
help(TarsClient)
```

## 📦 Dependencies

Required dependencies (from `requirements.txt`):

- **gRPC**: grpcio, grpcio-tools, protobuf
- **Camera**: picamera2, opencv-python
- **Audio/WebRTC**: aiortc, aiohttp, av
- **Hardware**: adafruit-pca9685, smbus2

## License

See main repository LICENSE file.
