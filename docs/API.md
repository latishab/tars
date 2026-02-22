# API Reference

## Python SDK

```bash
pip install tars-robot
```

### TarsClient (sync)

```python
from tars_sdk import TarsClient

client = TarsClient(tars.local:50051)

# Movement
client.move(wave_right)
client.move(step_forward, speed=0.5)
client.reset()

# Emotions & eyes
client.set_emotion(happy)
client.set_eye_state(listening)

# Camera
frame = client.capture_camera(width=640, height=480, quality=85)

# Status
status = client.get_status()
# {connected, battery: {level, charging, voltage}, emotion, eye_state, is_moving}

# Microphone
client.set_mic_mute(True)
muted = client.is_mic_muted

client.close()
```

### AsyncTarsClient

```python
from tars_sdk import AsyncTarsClient
import asyncio

async def main():
    async with AsyncTarsClient(tars.local:50051) as client:
        await client.move(nod)
        status = await client.get_status()

asyncio.run(main())
```

### Available Movements

| Category | Movements |
|---|---|
| Locomotion | `step_forward`, `walk_forward`, `step_backward`, `walk_backward` |
| Turning | `turn_left`, `turn_right`, `turn_left_slow`, `turn_right_slow` |
| Tilting | `tilt_left`, `tilt_right`, `side_side` |
| Expressions | `bow`, `pose`, `laugh`, `excited`, `swing_legs` |
| Waves | `wave_left`, `wave_right` |
| Utility | `neutral_legs` |

---

## REST API

Base URL: `http://tars.local:8000`

### Status

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/status` | System status (battery, CPU, memory) |
| GET | `/api/status/battery` | Battery info |
| GET | `/api/camera` | JPEG snapshot |

### Control

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/control/movements` | List available movements |
| POST | `/api/control/move` | Execute movement |
| POST | `/api/control/emotion` | Set emotion |
| POST | `/api/control/eye-state` | Set eye state |
| POST | `/api/control/reset` | Reset to neutral |

### WebRTC

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/webrtc/offer` | WebRTC signaling (SDP offer/answer) |

### WiFi

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/wifi/status` | Current connection status |
| GET | `/api/wifi/networks` | Scan available networks |
| POST | `/api/wifi/connect` | Connect to network |
| PUT | `/api/wifi/hotspot` | Enable/disable hotspot |

### Apps

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/apps` | List all apps |
| GET | `/api/apps/installed` | List installed apps |
| POST | `/api/apps/{app_id}/install` | Install app |
| POST | `/api/apps/{app_id}/start` | Start app |
| POST | `/api/apps/{app_id}/stop` | Stop app |
| DELETE | `/api/apps/{app_id}` | Uninstall app |

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/system/settings` | Get settings |
| PUT | `/api/system/settings` | Update settings |
| GET | `/api/updates/check` | Check for updates |
| POST | `/api/updates/install` | Install updates |
| POST | `/api/updates/restart` | Restart service |

---

## gRPC

Port: `50051`. The SDK wraps gRPC internally. For direct access, see proto in `tars_sdk/proto/`.

### RPCs

| RPC | Description |
|---|---|
| `Health()` | Health check |
| `GetStatus()` | Robot status |
| `ExecuteMovement(movement, speed)` | Run movement |
| `ResetPosition()` | Return to neutral |
| `SetEmotion(emotion)` | Set display emotion |
| `SetEyeState(state)` | Set eye state |
| `CaptureCamera(width, height, quality)` | Get JPEG frame |
| `SetMicMute(muted)` | Mute/unmute microphone |
| `GetMicMute()` | Get mute state |
| `StreamBattery()` | Battery updates stream |
| `StreamMovementStatus()` | Movement status stream |
