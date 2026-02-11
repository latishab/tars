"""TARS gRPC Client for remote robot control."""

import os
from typing import Optional, Iterator

import grpc
from loguru import logger

from .proto import tars_pb2, tars_pb2_grpc


class TarsClient:
    """
    Client for controlling TARS robot via gRPC.

    Returns raw protobuf response objects for type safety and forward compatibility.

    Example:
        client = TarsClient("100.115.193.41:50051")

        result = client.move("wave")
        print(result.success, result.duration)

        health = client.health()
        print(health.status, health.hardware.servos)

        status = client.get_status()
        print(status.connected, status.battery.level)
    """

    def __init__(self, address: Optional[str] = None, timeout: int = 10):
        """
        Initialize TarsClient.

        Args:
            address: gRPC server address (host:port).
                     If None, tries TARS_GRPC_ADDRESS env var, then localhost:50051.
            timeout: Default timeout for RPC calls in seconds.
        """
        if address is None:
            address = os.environ.get("TARS_GRPC_ADDRESS", "localhost:50051")

        self.address = address
        self.timeout = timeout
        self.channel = grpc.insecure_channel(address)
        self.stub = tars_pb2_grpc.TarsServiceStub(self.channel)

        logger.info(f"TarsClient connected to {address}")

    def move(self, movement: str, speed: float = 1.0) -> tars_pb2.MoveResponse:
        """
        Execute a movement.

        Args:
            movement: Movement name (e.g., "wave", "walk_forward")
            speed: Movement speed (0.0-1.0), default 1.0

        Returns:
            MoveResponse with .success, .duration, .error fields
        """
        try:
            request = tars_pb2.MoveRequest(movement=movement, speed=speed)
            response = self.stub.Move(request, timeout=self.timeout)

            if not response.success:
                logger.error(f"Movement '{movement}' failed: {response.error}")
            else:
                logger.debug(f"Movement '{movement}' completed in {response.duration:.2f}s")

            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC error during move: {e}")
            raise

    def set_emotion(self, emotion: str) -> None:
        """
        Set facial emotion on display.

        Args:
            emotion: Emotion name ("happy", "sad", "angry", "surprised", "neutral")
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
    ) -> tars_pb2.CaptureResponse:
        """
        Capture a frame from the camera.

        Args:
            width: Image width, default 640
            height: Image height, default 480
            quality: JPEG quality (1-100), default 80

        Returns:
            CaptureResponse with .image (bytes), .width, .height, .format fields
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

            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC error during capture_camera: {e}")
            raise

    def health(self) -> tars_pb2.HealthResponse:
        """
        Get health status.

        Returns:
            HealthResponse with .status, .version, .grpc_available, .hardware, .battery fields
        """
        try:
            response = self.stub.Health(tars_pb2.Empty(), timeout=self.timeout)
            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC error during health: {e}")
            raise

    def get_status(self) -> tars_pb2.StatusResponse:
        """
        Get current robot status.

        Returns:
            StatusResponse with .connected, .battery, .current_emotion,
            .current_eye_state, .is_moving, .current_movement fields
        """
        try:
            response = self.stub.GetStatus(tars_pb2.Empty(), timeout=self.timeout)
            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC error during get_status: {e}")
            raise

    def reset(self) -> None:
        """Reset robot to neutral position."""
        try:
            self.stub.Reset(tars_pb2.Empty(), timeout=self.timeout)
            logger.debug("Robot reset to neutral position")

        except grpc.RpcError as e:
            logger.error(f"gRPC error during reset: {e}")
            raise

    def stream_battery(self) -> Iterator[tars_pb2.BatteryStatus]:
        """
        Stream battery status updates.

        Yields:
            BatteryStatus with .level, .charging, .voltage, .current fields
        """
        try:
            for status in self.stub.StreamBattery(tars_pb2.Empty()):
                yield status

        except grpc.RpcError as e:
            logger.error(f"gRPC error during stream_battery: {e}")
            raise

    def stream_movement_status(self) -> Iterator[tars_pb2.MovementStatus]:
        """
        Stream movement status updates.

        Yields:
            MovementStatus with .moving, .movement, .progress fields
        """
        try:
            for status in self.stub.StreamMovementStatus(tars_pb2.Empty()):
                yield status

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
