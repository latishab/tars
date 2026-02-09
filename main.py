"""
TARS Hardware Service
FastAPI server for servo control, camera capture, and audio I/O
All hardware interaction happens here on RPi 5
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import asyncio
import base64
import io
import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modules.module_movements import (
    step_forward, step_backward,
    walk_forward, walk_backward,
    turn_left_slow, turn_right_slow,
)
from modules.module_servoctl import (
    reset_positions,
    disable_all_servos,
    move_legs,
    servo_positions,
    MOVING,
)
from modules.module_camera import CameraModule
from modules.module_audio import AudioModule
from display_manager import DisplayManager

app = FastAPI(title="TARS Hardware Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize hardware modules
camera: Optional[CameraModule] = None
audio: Optional[AudioModule] = None
display: Optional[DisplayManager] = None

@app.on_event("startup")
async def startup():
    global camera, audio, display

    # Initialize camera
    try:
        camera = CameraModule(1280, 720)
        print("Camera initialized")
    except Exception as e:
        print(f"Camera not available: {e}")

    # Initialize audio
    try:
        audio = AudioModule()
        print(f"Audio initialized: {audio.get_device_info()}")
    except Exception as e:
        print(f"Audio not available: {e}")

    # Initialize display
    try:
        display = DisplayManager(width=800, height=480)
        display.start()
        print("Display initialized")
    except Exception as e:
        print(f"Display not available: {e}")

@app.on_event("shutdown")
async def shutdown():
    global camera, audio, display
    if camera:
        camera.close()
    if audio:
        audio.close()
    if display:
        display.stop()


# ============== Status Endpoints ==============

@app.get("/")
def root():
    return {
        "service": "TARS Hardware Service",
        "version": "1.0.0",
        "status": "running",
        "hardware": {
            "servos": True,
            "camera": camera is not None,
            "audio": audio is not None,
            "display": display is not None,
            "moving": MOVING
        }
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "moving": MOVING,
        "camera": camera is not None,
        "audio": audio is not None,
        "display": display is not None
    }


# ============== Movement Endpoints ==============

class MoveRequest(BaseModel):
    movements: list[str]

class LegsRequest(BaseModel):
    left_height: int = 50
    right_height: int = 50
    left_leg: int = 50
    right_leg: int = 50
    speed: float = 0.8

MOVEMENT_MAP = {
    "forward": step_forward,
    "backward": step_backward,
    "walk_forward": walk_forward,
    "walk_backward": walk_backward,
    "left": turn_left_slow,
    "right": turn_right_slow,
}

@app.get("/state")
def get_state():
    return {"positions": dict(servo_positions), "moving": MOVING}

@app.post("/move")
def execute_move(request: MoveRequest):
    if MOVING:
        raise HTTPException(409, "Already moving")

    results = []
    for movement in request.movements:
        if movement not in MOVEMENT_MAP:
            raise HTTPException(400, f"Unknown movement: {movement}. Valid: {list(MOVEMENT_MAP.keys())}")
        MOVEMENT_MAP[movement]()
        results.append({"movement": movement, "status": "completed"})

    return {"status": "ok", "results": results}

@app.post("/move/legs")
def move_legs_direct(request: LegsRequest):
    if MOVING:
        raise HTTPException(409, "Already moving")
    move_legs(request.left_height, request.right_height,
              request.left_leg, request.right_leg, request.speed)
    return {"status": "ok"}

@app.post("/reset")
def reset():
    reset_positions()
    return {"status": "ok", "message": "Reset to neutral"}

@app.post("/disable")
def disable():
    disable_all_servos()
    return {"status": "ok", "message": "Servos disabled"}


# ============== Camera Endpoints ==============

@app.get("/camera/capture")
def capture_frame():
    """Capture current camera frame and return as base64 JPEG"""
    if camera is None:
        raise HTTPException(503, "Camera not available")

    try:
        frame = camera.capture_frame()

        from PIL import Image
        img = Image.fromarray(frame)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return {
            "status": "ok",
            "image": img_base64,
            "format": "jpeg",
            "width": img.width,
            "height": img.height
        }
    except Exception as e:
        raise HTTPException(500, f"Capture failed: {str(e)}")

@app.get("/camera/status")
def camera_status():
    return {
        "available": camera is not None and camera.is_available() if camera else False,
        "running": camera is not None and camera.is_available() if camera else False,
        "camera_type": camera.get_camera_type() if camera else None
    }


# ============== Audio Endpoints ==============

@app.websocket("/audio/stream")
async def audio_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming microphone audio to client.
    Sends raw PCM audio chunks (16-bit, 16kHz, mono).
    """
    if audio is None:
        await websocket.close(code=1003, reason="Audio not available")
        return

    await websocket.accept()
    print("Audio stream client connected")

    try:
        audio.start_recording()

        while True:
            # Get audio chunk from microphone
            chunk = audio.get_audio_chunk()
            if chunk is not None:
                # Send as binary
                await websocket.send_bytes(chunk.tobytes())
            await asyncio.sleep(0.01)  # ~100 chunks/sec

    except WebSocketDisconnect:
        print("Audio stream client disconnected")
    except Exception as e:
        print(f"Audio stream error: {e}")
    finally:
        audio.stop_recording()


@app.post("/audio/play")
async def play_audio(request: dict):
    """
    Play audio through the speaker.
    Expects: {"audio": "<base64 encoded PCM/WAV>", "format": "pcm"|"wav", "sample_rate": 24000}
    """
    if audio is None:
        raise HTTPException(503, "Audio not available")

    try:
        audio_b64 = request.get("audio")
        audio_format = request.get("format", "pcm")
        sample_rate = request.get("sample_rate", 24000)

        if not audio_b64:
            raise HTTPException(400, "Missing 'audio' field")

        audio_bytes = base64.b64decode(audio_b64)

        if audio_format == "wav":
            audio.play_wav(audio_bytes)
        else:
            audio.play_pcm(audio_bytes, sample_rate=sample_rate)

        return {"status": "ok", "message": "Audio queued for playback"}

    except Exception as e:
        raise HTTPException(500, f"Playback failed: {str(e)}")


@app.post("/audio/stop")
def stop_audio():
    """Stop any currently playing audio"""
    if audio is None:
        raise HTTPException(503, "Audio not available")
    audio.stop_playback()
    return {"status": "ok"}


@app.get("/audio/status")
def audio_status():
    if audio is None:
        return {"available": False}
    return {
        "available": True,
        "recording": audio.is_recording,
        "playing": audio.is_playing,
        "device": audio.get_device_info()
    }


# ============== Display Endpoints ==============

@app.post("/display/mode")
def set_display_mode(request: dict):
    if display is None:
        raise HTTPException(503, "Display not available")
    mode = request.get("mode", "eyes")
    display.set_mode(mode)
    return {"status": "ok", "mode": mode}


@app.post("/eyes/state")
def set_eye_state(request: dict):
    if display is None:
        raise HTTPException(503, "Display not available")
    state = request.get("state", "idle")
    display.set_eye_state(state)
    return {"status": "ok", "state": state}


@app.post("/eyes/emotion")
def set_emotion(request: dict):
    if display is None:
        raise HTTPException(503, "Display not available")
    emotion = request.get("emotion", "default")
    display.set_emotion(emotion)
    return {"status": "ok", "emotion": emotion}


@app.post("/eyes/look")
def set_look(request: dict):
    if display is None:
        raise HTTPException(503, "Display not available")
    x = request.get("x", 0)
    y = request.get("y", 0)
    display.set_look(x, y)
    return {"status": "ok"}


@app.post("/eyes/blink")
def trigger_blink():
    if display is None:
        raise HTTPException(503, "Display not available")
    display.blink()
    return {"status": "ok"}


@app.post("/eyes/animation")
def play_animation(request: dict):
    if display is None:
        raise HTTPException(503, "Display not available")
    animation = request.get("animation", "")
    display.play_animation(animation)
    return {"status": "ok"}


@app.post("/display/audio")
def set_audio_level(request: dict):
    if display is None:
        raise HTTPException(503, "Display not available")
    level = request.get("level", 0)
    source = request.get("source", "none")
    display.set_audio_level(level, source)
    return {"status": "ok"}


@app.post("/eyes/face")
def set_face_position(request: dict):
    if display is None:
        raise HTTPException(503, "Display not available")

    detected = request.get("detected", False)
    if detected:
        x = request.get("x", 0)
        y = request.get("y", 0)
        w = request.get("width", 640)
        h = request.get("height", 480)
        display.set_face_position(x, y, w, h, True)
    else:
        display.set_face_position(0, 0, 1, 1, False)

    return {"status": "ok"}


@app.get("/display/status")
def get_display_status():
    if display is None:
        return {"available": False}
    return {"available": True, **display.get_status()}


if __name__ == "__main__":
    print("=" * 50)
    print("TARS Hardware Service")
    print("=" * 50)
    print("Starting on http://0.0.0.0:8001")
    print("API docs: http://0.0.0.0:8001/docs")
    print("=" * 50)

    uvicorn.run(app, host="0.0.0.0", port=8001)
