# TARS Daemon

Single process managing gRPC, WebRTC, display, and hardware.

## ▶️ Running

```bash
# PyPI install
tars-daemon

# From source
python tars_daemon.py
```

See [Installation](./INSTALLATION.md) for setup and systemd service.

## ⚙️ CLI Options

| Option | Default | Description |
|---|---|---|
| `--port` | 8000 | HTTP API port |
| `--grpc-port` | 50051 | gRPC port |
| `--no-display` | — | Headless mode (no pygame) |
| `--no-webrtc` | — | Disable WebRTC |
| `--face-tracking` | — | Enable face tracking |
| `--install-service` | — | Print systemd service file and exit |

## 🏗️ Architecture

```
tars_daemon.py
├── gRPC Server (:50051)     — hardware control, camera, battery
├── HTTP Server (:8000)      — dashboard, REST API, WebRTC signaling
├── WebRTC (aiortc)          — mic (16kHz), speaker (24kHz)
├── Display Manager (pygame) — robot eyes, audio spectrum
└── Hardware
    ├── PCA9685 (servos)
    ├── Camera (Pi/USB)
    ├── USB audio
    └── INA260 (battery)
```

## 🔧 Configuration

Environment variables:

```bash
DISPLAY_ENABLED=true
DISPLAY_WIDTH=800
DISPLAY_HEIGHT=480
AUDIO_INPUT_DEVICE=
AUDIO_OUTPUT_DEVICE=
AUDIO_SAMPLE_RATE_IN=16000
AUDIO_SAMPLE_RATE_OUT=24000
```

## 🔍 Troubleshooting

**Daemon won't start:**
```bash
groups          # Should include: i2c, gpio, audio
tars-daemon     # Run manually to see full error output
```

**gRPC connection refused:**
```bash
nc -zv localhost 50051
journalctl -u tars -f | grep gRPC
```

**WebRTC not connecting:**
```bash
curl http://localhost:8000/health
```

**No audio:**
```bash
arecord -d 3 test.wav && aplay test.wav
groups  # Should include audio
```

**Display issues:**
```bash
tars-daemon --no-display  # Confirm it's a display-specific issue
```

**Battery not detected:**
```bash
i2cdetect -y 1  # INA260 should appear at 0x41
```
