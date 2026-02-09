"""
Face tracking module for TARS
Detects faces using OpenCV and updates eye tracking
"""

import cv2
import numpy as np
import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass
from loguru import logger


@dataclass
class FacePosition:
    """Face position data"""
    x: int  # Center X
    y: int  # Center Y
    width: int
    height: int
    confidence: float


class FaceTracker:
    """
    Face tracker that detects faces and provides position updates.

    Uses OpenCV's Haar Cascade for lightweight face detection suitable for RPi.
    For better accuracy, MediaPipe can be used as an alternative.
    """

    def __init__(
        self,
        camera,
        on_face_detected: Optional[Callable[[FacePosition, int, int], None]] = None,
        on_face_lost: Optional[Callable[[], None]] = None,
        detection_interval: float = 0.1,  # 10Hz detection
        smoothing: float = 0.3,  # Smoothing factor (0-1)
    ):
        """
        Initialize face tracker.

        Args:
            camera: CameraModule instance
            on_face_detected: Callback when face is detected (face_pos, frame_w, frame_h)
            on_face_lost: Callback when face is lost
            detection_interval: Time between detections (seconds)
            smoothing: Position smoothing factor (0=no smooth, 1=max smooth)
        """
        self.camera = camera
        self.on_face_detected = on_face_detected
        self.on_face_lost = on_face_lost
        self.detection_interval = detection_interval
        self.smoothing = smoothing

        # Face detector (Haar Cascade)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            raise RuntimeError("Failed to load face cascade classifier")

        # State
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._last_face: Optional[FacePosition] = None
        self._face_lost_time: Optional[float] = None
        self._smoothed_x: Optional[float] = None
        self._smoothed_y: Optional[float] = None

        # Config
        self.face_timeout = 1.0  # Consider face lost after 1 second

    def start(self):
        """Start face tracking"""
        if self.running:
            return

        logger.info("Starting face tracker")
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop face tracking"""
        if not self.running:
            return

        logger.info("Stopping face tracker")
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run(self):
        """Main tracking loop"""
        while self.running:
            try:
                # Capture frame
                frame = self.camera.capture_frame()
                if frame is None:
                    time.sleep(self.detection_interval)
                    continue

                frame_h, frame_w = frame.shape[:2]

                # Convert to grayscale for detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Detect faces
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(80, 80),  # Minimum face size
                    flags=cv2.CASCADE_SCALE_IMAGE
                )

                if len(faces) > 0:
                    # Use the largest face
                    face = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = face

                    # Calculate center
                    center_x = x + w // 2
                    center_y = y + h // 2

                    # Smooth position
                    if self._smoothed_x is None:
                        self._smoothed_x = center_x
                        self._smoothed_y = center_y
                    else:
                        self._smoothed_x = (
                            self.smoothing * self._smoothed_x +
                            (1 - self.smoothing) * center_x
                        )
                        self._smoothed_y = (
                            self.smoothing * self._smoothed_y +
                            (1 - self.smoothing) * center_y
                        )

                    # Create face position
                    face_pos = FacePosition(
                        x=int(self._smoothed_x),
                        y=int(self._smoothed_y),
                        width=w,
                        height=h,
                        confidence=1.0
                    )

                    self._last_face = face_pos
                    self._face_lost_time = None

                    # Notify callback
                    if self.on_face_detected:
                        self.on_face_detected(face_pos, frame_w, frame_h)

                else:
                    # No face detected
                    if self._last_face is not None:
                        # Start face lost timer
                        if self._face_lost_time is None:
                            self._face_lost_time = time.time()

                        # Check if face has been lost for too long
                        if time.time() - self._face_lost_time > self.face_timeout:
                            self._last_face = None
                            self._smoothed_x = None
                            self._smoothed_y = None

                            if self.on_face_lost:
                                self.on_face_lost()

                # Wait before next detection
                time.sleep(self.detection_interval)

            except Exception as e:
                logger.error(f"Face tracking error: {e}")
                time.sleep(self.detection_interval)

    @property
    def has_face(self) -> bool:
        """Check if a face is currently detected"""
        return self._last_face is not None

    @property
    def face_position(self) -> Optional[FacePosition]:
        """Get current face position"""
        return self._last_face


# ========== MediaPipe Alternative (Optional) ==========

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


class MediaPipeFaceTracker(FaceTracker):
    """
    Alternative face tracker using MediaPipe for better accuracy.

    MediaPipe provides more accurate face detection and can also
    detect face landmarks (eyes, nose, mouth) for more advanced tracking.
    """

    def __init__(self, *args, **kwargs):
        if not MEDIAPIPE_AVAILABLE:
            raise RuntimeError("MediaPipe not installed")

        super().__init__(*args, **kwargs)

        # MediaPipe face detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=0,  # 0 for short-range (< 2m)
            min_detection_confidence=0.5
        )

    def _run(self):
        """Main tracking loop with MediaPipe"""
        while self.running:
            try:
                # Capture frame
                frame = self.camera.capture_frame()
                if frame is None:
                    time.sleep(self.detection_interval)
                    continue

                frame_h, frame_w = frame.shape[:2]

                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Detect faces
                results = self.face_detector.process(rgb_frame)

                if results.detections:
                    # Use first detection
                    detection = results.detections[0]
                    bbox = detection.location_data.relative_bounding_box

                    # Convert to pixel coordinates
                    x = int(bbox.xmin * frame_w)
                    y = int(bbox.ymin * frame_h)
                    w = int(bbox.width * frame_w)
                    h = int(bbox.height * frame_h)

                    # Calculate center
                    center_x = x + w // 2
                    center_y = y + h // 2

                    # Smooth position
                    if self._smoothed_x is None:
                        self._smoothed_x = center_x
                        self._smoothed_y = center_y
                    else:
                        self._smoothed_x = (
                            self.smoothing * self._smoothed_x +
                            (1 - self.smoothing) * center_x
                        )
                        self._smoothed_y = (
                            self.smoothing * self._smoothed_y +
                            (1 - self.smoothing) * center_y
                        )

                    # Create face position
                    face_pos = FacePosition(
                        x=int(self._smoothed_x),
                        y=int(self._smoothed_y),
                        width=w,
                        height=h,
                        confidence=detection.score[0]
                    )

                    self._last_face = face_pos
                    self._face_lost_time = None

                    # Notify callback
                    if self.on_face_detected:
                        self.on_face_detected(face_pos, frame_w, frame_h)

                else:
                    # No face detected
                    if self._last_face is not None:
                        if self._face_lost_time is None:
                            self._face_lost_time = time.time()

                        if time.time() - self._face_lost_time > self.face_timeout:
                            self._last_face = None
                            self._smoothed_x = None
                            self._smoothed_y = None

                            if self.on_face_lost:
                                self.on_face_lost()

                time.sleep(self.detection_interval)

            except Exception as e:
                logger.error(f"MediaPipe face tracking error: {e}")
                time.sleep(self.detection_interval)
