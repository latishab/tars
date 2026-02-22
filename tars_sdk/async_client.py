"""TARS async gRPC Client for remote robot control."""

import os
from typing import Optional, AsyncIterator

import grpc.aio
from loguru import logger

from .proto import tars_pb2, tars_pb2_grpc


class AsyncTarsClient:
    """
    Async client for controlling TARS robot via gRPC.

    Returns raw protobuf response objects for type safety and forward compatibility.

    Example:
        async with AsyncTarsClient("100.115.193.41:50051") as client:
            result = await client.move("wave")
            print(result.success, result.duration)

            async for status in client.stream_battery():
                print(f"Battery: {status.level}%")
    """

    def __init__(self, address: Optional[str] = None, timeout: int = 10):
        """
        Initialize AsyncTarsClient.

        Args:
            address: gRPC server address (host:port).
                     If None, tries TARS_GRPC_ADDRESS env var, then localhost:50051.
            timeout: Default timeout for RPC calls in seconds.
        """
        if address is None:
            address = os.environ.get("TARS_GRPC_ADDRESS", "localhost:50051")

        self.address = address
        self.timeout = timeout
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[tars_pb2_grpc.TarsServiceStub] = None
        self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_connected()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_connected(self):
        """Ensure gRPC channel is connected."""
        if not self._initialized:
            self.channel = grpc.aio.insecure_channel(self.address)
            self.stub = tars_pb2_grpc.TarsServiceStub(self.channel)
            self._initialized = True
            logger.info(f"AsyncTarsClient connected to {self.address}")

    async def move(self, movement: str, speed: float = 1.0) -> tars_pb2.MoveResponse:
        """
        Execute a movement.

        Args:
            movement: Movement name (e.g., "wave", "walk_forward")
            speed: Movement speed (0.0-1.0), default 1.0

        Returns:
            MoveResponse with .success, .duration, .error fields
        """
        await self._ensure_connected()

        try:
            request = tars_pb2.MoveRequest(movement=movement, speed=speed)
            response = await self.stub.Move(request, timeout=self.timeout)

            if not response.success:
                logger.error(f"Movement '{movement}' failed: {response.error}")
            else:
                logger.debug(f"Movement '{movement}' completed in {response.duration:.2f}s")

            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC error during move: {e}")
            raise

    async def set_emotion(self, emotion: str) -> None:
        """
        Set facial emotion on display.

        Args:
            emotion: Emotion name ("happy", "sad", "angry", "surprised", "neutral")
        """
        await self._ensure_connected()

        try:
            request = tars_pb2.EmotionRequest(emotion=emotion)
            await self.stub.SetEmotion(request, timeout=self.timeout)
            logger.debug(f"Emotion set to '{emotion}'")

        except grpc.RpcError as e:
            logger.error(f"gRPC error during set_emotion: {e}")
            raise

    async def set_eye_state(self, state: str) -> None:
        """
        Set eye state.

        Args:
            state: Eye state ("idle", "listening", "thinking", "speaking")
        """
        await self._ensure_connected()

        try:
            request = tars_pb2.EyeStateRequest(state=state)
            await self.stub.SetEyeState(request, timeout=self.timeout)
            logger.debug(f"Eye state set to '{state}'")

        except grpc.RpcError as e:
            logger.error(f"gRPC error during set_eye_state: {e}")
            raise

    async def capture_camera(
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
        await self._ensure_connected()

        try:
            request = tars_pb2.CaptureRequest(
                width=width,
                height=height,
                quality=quality
            )
            response = await self.stub.CaptureCamera(request, timeout=self.timeout)

            logger.debug(
                f"Captured camera frame: {response.width}x{response.height}, "
                f"{len(response.image)} bytes"
            )

            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC error during capture_camera: {e}")
            raise

    async def health(self) -> tars_pb2.HealthResponse:
        """
        Get health status.

        Returns:
            HealthResponse with .status, .version, .grpc_available, .hardware, .battery fields
        """
        await self._ensure_connected()

        try:
            response = await self.stub.Health(tars_pb2.Empty(), timeout=self.timeout)
            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC error during health: {e}")
            raise

    async def get_status(self) -> tars_pb2.StatusResponse:
        """
        Get current robot status.

        Returns:
            StatusResponse with .connected, .battery, .current_emotion,
            .current_eye_state, .is_moving, .current_movement fields
        """
        await self._ensure_connected()

        try:
            response = await self.stub.GetStatus(tars_pb2.Empty(), timeout=self.timeout)
            return response

        except grpc.RpcError as e:
            logger.error(f"gRPC error during get_status: {e}")
            raise

    async def reset(self) -> None:
        """Reset robot to neutral position."""
        await self._ensure_connected()

        try:
            await self.stub.Reset(tars_pb2.Empty(), timeout=self.timeout)
            logger.debug("Robot reset to neutral position")

        except grpc.RpcError as e:
            logger.error(f"gRPC error during reset: {e}")
            raise

    async def stream_battery(self) -> AsyncIterator[tars_pb2.BatteryStatus]:
        """
        Stream battery status updates.

        Yields:
            BatteryStatus with .level, .charging, .voltage, .current fields
        """
        await self._ensure_connected()

        try:
            async for status in self.stub.StreamBattery(tars_pb2.Empty()):
                yield status

        except grpc.RpcError as e:
            logger.error(f"gRPC error during stream_battery: {e}")
            raise

    async def stream_movement_status(self) -> AsyncIterator[tars_pb2.MovementStatus]:
        """
        Stream movement status updates.

        Yields:
            MovementStatus with .moving, .movement, .progress fields
        """
        await self._ensure_connected()

        try:
            async for status in self.stub.StreamMovementStatus(tars_pb2.Empty()):
                yield status

        except grpc.RpcError as e:
            logger.error(f"gRPC error during stream_movement_status: {e}")
            raise


    async def set_mic_mute(self, muted: bool) -> None:
        await self._ensure_connected()
        request = tars_pb2.MicMuteRequest(muted=muted)
        await self.stub.SetMicMute(request, timeout=self.timeout)

    async def get_mic_mute(self) -> bool:
        await self._ensure_connected()
        response = await self.stub.GetMicMute(tars_pb2.Empty(), timeout=self.timeout)
        return response.muted

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self.channel:
            await self.channel.close()
            logger.info(f"AsyncTarsClient connection to {self.address} closed")
            self._initialized = False

    def __repr__(self) -> str:
        return f"AsyncTarsClient(address='{self.address}')"
