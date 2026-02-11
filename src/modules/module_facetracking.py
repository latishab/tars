"""
Face tracking module for TARS
Detects faces using BlazeFace (MediaPipe's face detection model) via TFLite
"""

import cv2
import numpy as np
import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass
from pathlib import Path
from loguru import logger


@dataclass
class FacePosition:
    """Face position data"""
    x: int  # Center X
    y: int  # Center Y
    width: int
    height: int
    confidence: float


class BlazeFaceDetector:
    """Runs BlazeFace short-range model directly via TFLite runtime."""

    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        from ai_edge_litert.interpreter import Interpreter

        self.interpreter = Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.confidence_threshold = confidence_threshold

        self._input_details = self.interpreter.get_input_details()
        self._output_details = self.interpreter.get_output_details()
        self._input_shape = self._input_details[0]['shape']  # [1, 128, 128, 3]
        self._input_size = self._input_shape[1]  # 128

        # Pre-compute anchors
        self._anchors = self._generate_anchors()

    def _generate_anchors(self) -> np.ndarray:
        """Generate SSD anchors for BlazeFace short-range (128x128 input)."""
        strides = [8, 16, 16, 16]
        anchors = []
        for stride in strides:
            grid_size = self._input_size // stride
            for y in range(grid_size):
                for x in range(grid_size):
                    cx = (x + 0.5) / grid_size
                    cy = (y + 0.5) / grid_size
                    anchors.append([cx, cy])
                    anchors.append([cx, cy])
        return np.array(anchors, dtype=np.float32)

    def detect(self, frame: np.ndarray):
        """
        Detect faces in an RGB frame.

        Returns list of (center_x, center_y, w, h, confidence) in pixel coords,
        or empty list if no faces found.
        """
        frame_h, frame_w = frame.shape[:2]

        # Preprocess: resize to 128x128, normalize to [0, 1]
        input_img = cv2.resize(frame, (self._input_size, self._input_size))
        input_data = input_img.astype(np.float32) / 255.0
        input_data = np.expand_dims(input_data, axis=0)

        # Run inference
        self.interpreter.set_tensor(self._input_details[0]['index'], input_data)
        self.interpreter.invoke()

        # Get outputs
        regressors = self.interpreter.get_tensor(self._output_details[0]['index'])[0]  # [896, 16]
        scores_raw = self.interpreter.get_tensor(self._output_details[1]['index'])[0]  # [896, 1]

        # Sigmoid on scores (clip to avoid overflow)
        scores_clipped = np.clip(scores_raw.flatten(), -50, 50)
        scores = 1.0 / (1.0 + np.exp(-scores_clipped))

        # Filter by confidence
        mask = scores > self.confidence_threshold
        if not np.any(mask):
            return []

        filtered_regressors = regressors[mask]
        filtered_scores = scores[mask]
        filtered_anchors = self._anchors[mask]

        # Decode boxes: offsets are in input_size scale
        cx = filtered_anchors[:, 0] + filtered_regressors[:, 1] / self._input_size
        cy = filtered_anchors[:, 1] + filtered_regressors[:, 0] / self._input_size
        w = filtered_regressors[:, 3] / self._input_size
        h = filtered_regressors[:, 2] / self._input_size

        # Convert to pixel coordinates
        detections = []
        for i in range(len(filtered_scores)):
            px = int(cx[i] * frame_w)
            py = int(cy[i] * frame_h)
            pw = int(w[i] * frame_w)
            ph = int(h[i] * frame_h)
            detections.append((px, py, pw, ph, float(filtered_scores[i])))

        # NMS: pick the highest confidence
        detections.sort(key=lambda d: d[4], reverse=True)
        return detections


class FaceTracker:
    """
    Face tracker using BlazeFace (TFLite).

    Detects faces and provides smoothed position updates via callbacks.
    """

    MODEL_PATH = str(Path(__file__).parent.parent.parent / "models" / "face_detection_short_range.tflite")

    def __init__(
        self,
        camera,
        on_face_detected: Optional[Callable[[FacePosition, int, int], None]] = None,
        on_face_lost: Optional[Callable[[], None]] = None,
        detection_interval: float = 0.1,
        smoothing: float = 0.3,
        confidence_threshold: float = 0.5,
    ):
        self.camera = camera
        self.on_face_detected = on_face_detected
        self.on_face_lost = on_face_lost
        self.detection_interval = detection_interval
        self.smoothing = smoothing

        # State
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._last_face: Optional[FacePosition] = None
        self._face_lost_time: Optional[float] = None
        self._smoothed_x: Optional[float] = None
        self._smoothed_y: Optional[float] = None
        self.face_timeout = 1.0

        # Initialize BlazeFace detector
        self._detector = BlazeFaceDetector(
            model_path=self.MODEL_PATH,
            confidence_threshold=confidence_threshold
        )
        logger.info("Face detector: BlazeFace (TFLite)")

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
                frame = self.camera.capture_frame()
                if frame is None:
                    time.sleep(self.detection_interval)
                    continue

                frame_h, frame_w = frame.shape[:2]

                # Detect faces
                detections = self._detector.detect(frame)

                if detections:
                    # Use highest confidence detection
                    center_x, center_y, w, h, conf = detections[0]

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

                    face_pos = FacePosition(
                        x=int(self._smoothed_x),
                        y=int(self._smoothed_y),
                        width=w,
                        height=h,
                        confidence=conf
                    )

                    self._last_face = face_pos
                    self._face_lost_time = None

                    if self.on_face_detected:
                        self.on_face_detected(face_pos, frame_w, frame_h)

                else:
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
