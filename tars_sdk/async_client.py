"""TARS async gRPC Client for remote robot control."""

import os
from typing import Optional, AsyncIterator, Dict, Any

import grpc.aio
from loguru import logger

from .proto import tars_pb2, tars_pb2_grpc


class AsyncTarsClient:
    """
    Async client for controlling TARS robot via gRPC.

    Example:
        async with AsyncTarsClient("100.64.0.2:50051") as client:
            await client.move("wave")
            await client.set_emotion("happy")
            frame = await client.capture_camera()

            async for battery in client.stream_battery():
                print(f"Battery: {battery['level']}%")
    """

    def __init__(self, address: Optional[str] = None, timeout: int = 10):
        """
        Initialize AsyncTarsClient.

        Args:
            address: gRPC server address (host:port).
                     If None, tries localhost:50051, then TARS_GRPC_ADDRESS env var.
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

    async def move(self, movement: str, speed: float = 1.0) -> Dict[str, Any]:
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
        await self._ensure_connected()

        try:
            request = tars_pb2.MoveRequest(movement=movement, speed=speed)
            response = await self.stub.Move(request, timeout=self.timeout)

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

    async def set_emotion(self, emotion: str) -> None:
        """
        Set facial emotion on display.

        Args:
            emotion: Emotion name ("happy", "sad", "angry", "surprised", "neutral")

        Raises:
            grpc.RpcError: If the RPC call fails
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

        Raises:
            grpc.RpcError: If the RPC call fails
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

            return response.image

        except grpc.RpcError as e:
            logger.error(f"gRPC error during capture_camera: {e}")
            raise

    async def health(self) -> Dict[str, Any]:
        """
        Get health status (gRPC Health RPC).

        Returns:
            Dictionary with health status including hardware, battery, WebRTC status

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        await self._ensure_connected()

        try:
            response = await self.stub.Health(tars_pb2.Empty(), timeout=self.timeout)

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

    async def get_status(self) -> Dict[str, Any]:
        """
        Get current robot status.

        Returns:
            Dictionary with robot status including battery, emotion, eye state, movement

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        await self._ensure_connected()

        try:
            response = await self.stub.GetStatus(tars_pb2.Empty(), timeout=self.timeout)

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

    async def reset(self) -> None:
        """
        Reset robot to neutral position.

        Raises:
            grpc.RpcError: If the RPC call fails
        """
        await self._ensure_connected()

        try:
            await self.stub.Reset(tars_pb2.Empty(), timeout=self.timeout)
            logger.debug("Robot reset to neutral position")

        except grpc.RpcError as e:
            logger.error(f"gRPC error during reset: {e}")
            raise

    async def stream_battery(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream battery status updates.

        Yields:
            Dictionary with battery level, charging status, voltage, current

        Raises:
            grpc.RpcError: If the streaming fails
        """
        await self._ensure_connected()

        try:
            async for status in self.stub.StreamBattery(tars_pb2.Empty()):
                yield {
                    "level": status.level,
                    "charging": status.charging,
                    "voltage": status.voltage,
                    "current": status.current,
                }

        except grpc.RpcError as e:
            logger.error(f"gRPC error during stream_battery: {e}")
            raise

    async def stream_movement_status(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream movement status updates.

        Yields:
            Dictionary with moving status, movement name, and progress

        Raises:
            grpc.RpcError: If the streaming fails
        """
        await self._ensure_connected()

        try:
            async for status in self.stub.StreamMovementStatus(tars_pb2.Empty()):
                yield {
                    "moving": status.moving,
                    "movement": status.movement,
                    "progress": status.progress,
                }

        except grpc.RpcError as e:
            logger.error(f"gRPC error during stream_movement_status: {e}")
            raise

    async def close(self) -> None:
        """Close the gRPC channel."""
        if self.channel:
            await self.channel.close()
            logger.info(f"AsyncTarsClient connection to {self.address} closed")
            self._initialized = False

    def __repr__(self) -> str:
        return f"AsyncTarsClient(address='{self.address}')"
