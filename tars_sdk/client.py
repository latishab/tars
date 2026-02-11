"""TARS gRPC Client for remote robot control."""

import os
from typing import Optional, Iterator, Dict, Any

import grpc
from loguru import logger

from .proto import tars_pb2, tars_pb2_grpc


class TarsClient:
    """
    Client for controlling TARS robot via gRPC.

    Example:
        # Remote mode (from MacBook) - replace with your robot's IP
        client = TarsClient("100.115.193.41:50051")

        # Local mode (on Pi)
        client = TarsClient("localhost:50051")

        # Auto-detect
        client = TarsClient()

        # Use it
        client.move("wave")
        client.set_emotion("happy")
        frame = client.capture_camera()
        status = client.get_status()
    """

    def __init__(self, address: Optional[str] = None, timeout: int = 10):
        """
        Initialize TarsClient.

        Args:
            address: gRPC server address (host:port).
                     If None, tries localhost:50051, then TARS_GRPC_ADDRESS env var.
            timeout: Default timeout for RPC calls in seconds.
        """
        if address is None:
            address = os.environ.get("TARS_GRPC_ADDRESS", "localhost:50051")

        self.address = address
        self.timeout = timeout
        self.channel = grpc.insecure_channel(address)
        self.stub = tars_pb2_grpc.TarsServiceStub(self.channel)

        logger.info(f"TarsClient connected to {address}")

    def move(self, movement: str, speed: float = 1.0) -> Dict[str, Any]:
        """
        Execute a movement.

        Args:
            movement: Movement name (e.g., "wave", "nod", "shake_head")
            speed: Movement speed (0.0-1.0), default 1.0

        Returns:
            Dictionary with success status, duration, and optional error message

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        try:
            request = tars_pb2.MoveRequest(movement=movement, speed=speed)
            response = self.stub.Move(request, timeout=self.timeout)

            result = {
                "success": response.success,
                "duration": response.duration,
                "error": response.error if response.error else None
            }

            if not response.success:
                logger.error(f"Movement '{movement}' failed: {response.error}")
            else:
                logger.debug(f"Movement '{movement}' completed in {response.duration:.2f}s")

            return result

        except grpc.RpcError as e:
            logger.error(f"gRPC error during move: {e}")
            raise

    def set_emotion(self, emotion: str) -> None:
        """
        Set facial emotion on display.

        Args:
            emotion: Emotion name ("happy", "sad", "angry", "surprised", "neutral")

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        try:
            request = tars_pb2.EmotionRequest(emotion=emotion)
            self.stub.SetEmotion(request, timeout=self.timeout)
            logger.debug(f"Emotion set to '{emotion}'")

        except grpc.RpcError as e:
            logger.error(f"gRPC error during set_emotion: {e}")
            raise

    def set_eye_state(self, state: str) -> None:
        """
        Set eye state.

        Args:
            state: Eye state ("idle", "listening", "thinking", "speaking")

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        try:
            request = tars_pb2.EyeStateRequest(state=state)
            self.stub.SetEyeState(request, timeout=self.timeout)
            logger.debug(f"Eye state set to '{state}'")

        except grpc.RpcError as e:
            logger.error(f"gRPC error during set_eye_state: {e}")
            raise

    def capture_camera(
        self,
        width: int = 640,
        height: int = 480,
        quality: int = 80
    ) -> bytes:
        """
        Capture a frame from the camera.

        Args:
            width: Image width, default 640
            height: Image height, default 480
            quality: JPEG quality (1-100), default 80

        Returns:
            JPEG image as bytes

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        try:
            request = tars_pb2.CaptureRequest(
                width=width,
                height=height,
                quality=quality
            )
            response = self.stub.CaptureCamera(request, timeout=self.timeout)

            logger.debug(
                f"Captured camera frame: {response.width}x{response.height}, "
                f"{len(response.image)} bytes"
            )

            return response.image

        except grpc.RpcError as e:
            logger.error(f"gRPC error during capture_camera: {e}")
            raise

    def health(self) -> Dict[str, Any]:
        """
        Get health status (gRPC Health RPC).

        Returns:
            Dictionary with health status including hardware, battery, WebRTC status

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        try:
            response = self.stub.Health(tars_pb2.Empty(), timeout=self.timeout)

            return {
                "status": response.status,
                "version": response.version,
                "grpc_available": response.grpc_available,
                "webrtc": {
                    "available": response.webrtc_available,
                    "connected": response.webrtc_connected,
                },
                "hardware": {
                    "servos": response.hardware.servos,
                    "camera": response.hardware.camera,
                    "audio": response.hardware.audio,
                    "display": response.hardware.display,
                    "battery": response.hardware.battery,
                    "moving": response.hardware.moving,
                },
                "battery": {
                    "level": response.battery.level,
                    "charging": response.battery.charging,
                    "voltage": response.battery.voltage,
                    "current": response.battery.current,
                },
            }

        except grpc.RpcError as e:
            logger.error(f"gRPC error during health: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """
        Get current robot status.

        Returns:
            Dictionary with robot status including battery, emotion, eye state, movement

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        try:
            response = self.stub.GetStatus(tars_pb2.Empty(), timeout=self.timeout)

            return {
                "connected": response.connected,
                "battery": {
                    "level": response.battery.level,
                    "charging": response.battery.charging,
                    "voltage": response.battery.voltage,
                    "current": response.battery.current,
                },
                "emotion": response.current_emotion,
                "eye_state": response.current_eye_state,
                "is_moving": response.is_moving,
                "movement": response.current_movement,
            }

        except grpc.RpcError as e:
            logger.error(f"gRPC error during get_status: {e}")
            raise

    def reset(self) -> None:
        """
        Reset robot to neutral position.

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        try:
            self.stub.Reset(tars_pb2.Empty(), timeout=self.timeout)
            logger.debug("Robot reset to neutral position")

        except grpc.RpcError as e:
            logger.error(f"gRPC error during reset: {e}")
            raise

    def stream_battery(self) -> Iterator[Dict[str, Any]]:
        """
        Stream battery status updates.

        Yields:
            Dictionary with battery level, charging status, voltage, current

        Raises:
            grpc.RpcError: If the streaming fails
        """
        try:
            for status in self.stub.StreamBattery(tars_pb2.Empty()):
                yield {
                    "level": status.level,
                    "charging": status.charging,
                    "voltage": status.voltage,
                    "current": status.current,
                }

        except grpc.RpcError as e:
            logger.error(f"gRPC error during stream_battery: {e}")
            raise

    def stream_movement_status(self) -> Iterator[Dict[str, Any]]:
        """
        Stream movement status updates.

        Yields:
            Dictionary with moving status, movement name, and progress

        Raises:
            grpc.RpcError: If the streaming fails
        """
        try:
            for status in self.stub.StreamMovementStatus(tars_pb2.Empty()):
                yield {
                    "moving": status.moving,
                    "movement": status.movement,
                    "progress": status.progress,
                }

        except grpc.RpcError as e:
            logger.error(f"gRPC error during stream_movement_status: {e}")
            raise

    def close(self) -> None:
        """Close the gRPC channel."""
        self.channel.close()
        logger.info(f"TarsClient connection to {self.address} closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        return f"TarsClient(address='{self.address}')"
