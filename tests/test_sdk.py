"""Unit tests for TARS SDK (TarsClient and AsyncTarsClient)."""

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from tars_sdk import TarsClient, AsyncTarsClient
from tars_sdk.proto import tars_pb2


class TestTarsClient:
    """Tests for synchronous TarsClient."""

    def test_init_with_address(self):
        """Test client initialization with explicit address."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            assert client.address == "localhost:50051"
            assert client.timeout == 10

    def test_init_with_custom_timeout(self):
        """Test client initialization with custom timeout."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051", timeout=30)
            assert client.timeout == 30

    def test_init_from_env(self):
        """Test client initialization from environment variable."""
        os.environ["TARS_GRPC_ADDRESS"] = "192.168.1.100:50051"
        with patch('grpc.insecure_channel'):
            client = TarsClient()
            assert client.address == "192.168.1.100:50051"
        del os.environ["TARS_GRPC_ADDRESS"]

    def test_init_default_address(self):
        """Test client initialization with default address."""
        if "TARS_GRPC_ADDRESS" in os.environ:
            del os.environ["TARS_GRPC_ADDRESS"]

        with patch('grpc.insecure_channel'):
            client = TarsClient()
            assert client.address == "localhost:50051"

    def test_move_success(self):
        """Test successful movement."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()
            client.stub.Move.return_value = tars_pb2.MoveResponse(
                success=True,
                duration=1.5,
                error=""
            )

            result = client.move("wave")

            assert result["success"] is True
            assert result["duration"] == 1.5
            assert result["error"] is None

            # Verify request
            call_args = client.stub.Move.call_args
            request = call_args[0][0]
            assert request.movement == "wave"
            assert request.speed == 1.0

    def test_move_with_speed(self):
        """Test movement with custom speed."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()
            client.stub.Move.return_value = tars_pb2.MoveResponse(
                success=True,
                duration=2.0,
                error=""
            )

            result = client.move("nod", speed=0.5)

            assert result["success"] is True
            assert result["duration"] == 2.0

            # Verify speed was passed
            call_args = client.stub.Move.call_args
            request = call_args[0][0]
            assert request.speed == 0.5

    def test_move_failure(self):
        """Test failed movement."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()
            client.stub.Move.return_value = tars_pb2.MoveResponse(
                success=False,
                duration=0.0,
                error="Unknown movement: invalid"
            )

            result = client.move("invalid")

            assert result["success"] is False
            assert result["error"] == "Unknown movement: invalid"

    def test_set_emotion(self):
        """Test setting emotion."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()
            client.stub.SetEmotion.return_value = tars_pb2.Empty()

            client.set_emotion("happy")

            client.stub.SetEmotion.assert_called_once()
            call_args = client.stub.SetEmotion.call_args
            request = call_args[0][0]
            assert request.emotion == "happy"

    def test_set_eye_state(self):
        """Test setting eye state."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()
            client.stub.SetEyeState.return_value = tars_pb2.Empty()

            client.set_eye_state("listening")

            client.stub.SetEyeState.assert_called_once()
            call_args = client.stub.SetEyeState.call_args
            request = call_args[0][0]
            assert request.state == "listening"

    def test_capture_camera(self):
        """Test camera capture."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()

            fake_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF...'
            client.stub.CaptureCamera.return_value = tars_pb2.CaptureResponse(
                image=fake_jpeg,
                width=640,
                height=480,
                format="jpeg"
            )

            result = client.capture_camera()

            assert result == fake_jpeg
            assert len(result) > 0

    def test_capture_camera_with_params(self):
        """Test camera capture with custom parameters."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()
            client.stub.CaptureCamera.return_value = tars_pb2.CaptureResponse(
                image=b'...',
                width=1280,
                height=720,
                format="jpeg"
            )

            client.capture_camera(width=1280, height=720, quality=90)

            call_args = client.stub.CaptureCamera.call_args
            request = call_args[0][0]
            assert request.width == 1280
            assert request.height == 720
            assert request.quality == 90

    def test_health(self):
        """Test health check."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()

            hardware = tars_pb2.HardwareStatus(
                servos=True,
                camera=True,
                audio=True,
                display=True,
                battery=True,
                moving=False
            )
            battery = tars_pb2.BatteryStatus(
                level=85,
                charging=False,
                voltage=12.4,
                current=0.5
            )

            client.stub.Health.return_value = tars_pb2.HealthResponse(
                status="running",
                version="2.0.0",
                grpc_available=True,
                webrtc_available=True,
                webrtc_connected=False,
                hardware=hardware,
                battery=battery
            )

            result = client.health()

            assert result["status"] == "running"
            assert result["version"] == "2.0.0"
            assert result["grpc_available"] is True
            assert result["webrtc"]["available"] is True
            assert result["webrtc"]["connected"] is False
            assert result["hardware"]["servos"] is True
            assert result["battery"]["level"] == 85

    def test_get_status(self):
        """Test getting robot status."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()

            battery = tars_pb2.BatteryStatus(
                level=90,
                charging=True,
                voltage=12.6,
                current=1.2
            )

            client.stub.GetStatus.return_value = tars_pb2.StatusResponse(
                connected=True,
                battery=battery,
                current_emotion="happy",
                current_eye_state="listening",
                is_moving=True,
                current_movement="wave"
            )

            result = client.get_status()

            assert result["connected"] is True
            assert result["battery"]["level"] == 90
            assert result["emotion"] == "happy"
            assert result["eye_state"] == "listening"
            assert result["is_moving"] is True
            assert result["movement"] == "wave"

    def test_reset(self):
        """Test robot reset."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()
            client.stub.Reset.return_value = tars_pb2.Empty()

            client.reset()

            client.stub.Reset.assert_called_once()

    def test_context_manager(self):
        """Test context manager usage."""
        mock_channel = MagicMock()
        with patch('grpc.insecure_channel', return_value=mock_channel):
            with TarsClient("localhost:50051") as client:
                assert client is not None

            mock_channel.close.assert_called_once()

    def test_stream_battery(self):
        """Test battery streaming."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()

            mock_stream = [
                tars_pb2.BatteryStatus(level=100, charging=False, voltage=12.6, current=0.5),
                tars_pb2.BatteryStatus(level=99, charging=False, voltage=12.5, current=0.5),
                tars_pb2.BatteryStatus(level=98, charging=False, voltage=12.4, current=0.5),
            ]
            client.stub.StreamBattery.return_value = iter(mock_stream)

            results = list(client.stream_battery())

            assert len(results) == 3
            assert results[0]["level"] == 100
            assert results[1]["level"] == 99
            assert results[2]["level"] == 98
            assert results[0]["charging"] is False

    def test_stream_movement_status(self):
        """Test movement status streaming."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("localhost:50051")
            client.stub = MagicMock()

            mock_stream = [
                tars_pb2.MovementStatus(moving=True, movement="wave", progress=0.0),
                tars_pb2.MovementStatus(moving=True, movement="wave", progress=0.5),
                tars_pb2.MovementStatus(moving=False, movement="", progress=1.0),
            ]
            client.stub.StreamMovementStatus.return_value = iter(mock_stream)

            results = list(client.stream_movement_status())

            assert len(results) == 3
            assert results[0]["moving"] is True
            assert results[0]["movement"] == "wave"
            assert results[1]["progress"] == 0.5
            assert results[2]["moving"] is False

    def test_repr(self):
        """Test string representation."""
        with patch('grpc.insecure_channel'):
            client = TarsClient("192.168.1.1:50051")
            assert repr(client) == "TarsClient(address='192.168.1.1:50051')"


@pytest.mark.asyncio
class TestAsyncTarsClient:
    """Tests for async TarsClient."""

    async def test_init_with_address(self):
        """Test async client initialization with explicit address."""
        client = AsyncTarsClient("localhost:50051")
        assert client.address == "localhost:50051"
        assert client.timeout == 10
        assert not client._initialized

    async def test_async_move(self):
        """Test async movement."""
        client = AsyncTarsClient("localhost:50051")

        with patch('grpc.aio.insecure_channel'):
            client.stub = MagicMock()
            client.stub.Move = AsyncMock(return_value=tars_pb2.MoveResponse(
                success=True,
                duration=1.5,
                error=""
            ))
            client._initialized = True

            result = await client.move("wave")

            assert result["success"] is True
            assert result["duration"] == 1.5
            assert result["error"] is None

    async def test_async_set_emotion(self):
        """Test async set emotion."""
        client = AsyncTarsClient("localhost:50051")

        with patch('grpc.aio.insecure_channel'):
            client.stub = MagicMock()
            client.stub.SetEmotion = AsyncMock(return_value=tars_pb2.Empty())
            client._initialized = True

            await client.set_emotion("happy")

            client.stub.SetEmotion.assert_called_once()

    async def test_async_capture_camera(self):
        """Test async camera capture."""
        client = AsyncTarsClient("localhost:50051")

        with patch('grpc.aio.insecure_channel'):
            fake_jpeg = b'\xff\xd8\xff\xe0...'
            client.stub = MagicMock()
            client.stub.CaptureCamera = AsyncMock(return_value=tars_pb2.CaptureResponse(
                image=fake_jpeg,
                width=640,
                height=480,
                format="jpeg"
            ))
            client._initialized = True

            result = await client.capture_camera()

            assert result == fake_jpeg

    async def test_async_health(self):
        """Test async health check."""
        client = AsyncTarsClient("localhost:50051")

        with patch('grpc.aio.insecure_channel'):
            hardware = tars_pb2.HardwareStatus(
                servos=True, camera=True, audio=True,
                display=True, battery=True, moving=False
            )
            battery = tars_pb2.BatteryStatus(
                level=85, charging=False, voltage=12.4, current=0.5
            )

            client.stub = MagicMock()
            client.stub.Health = AsyncMock(return_value=tars_pb2.HealthResponse(
                status="running",
                version="2.0.0",
                grpc_available=True,
                webrtc_available=True,
                webrtc_connected=False,
                hardware=hardware,
                battery=battery
            ))
            client._initialized = True

            result = await client.health()

            assert result["status"] == "running"
            assert result["grpc_available"] is True

    async def test_async_context_manager(self):
        """Test async context manager."""
        mock_channel = MagicMock()
        mock_channel.close = AsyncMock()

        with patch('grpc.aio.insecure_channel', return_value=mock_channel):
            async with AsyncTarsClient("localhost:50051") as client:
                assert client is not None
                assert client._initialized

            mock_channel.close.assert_called_once()

    async def test_async_stream_battery(self):
        """Test async battery streaming."""
        client = AsyncTarsClient("localhost:50051")

        async def mock_stream():
            for level in [100, 99, 98]:
                yield tars_pb2.BatteryStatus(
                    level=level,
                    charging=False,
                    voltage=12.5,
                    current=0.5
                )

        with patch('grpc.aio.insecure_channel'):
            client.stub = MagicMock()
            client.stub.StreamBattery = MagicMock(return_value=mock_stream())
            client._initialized = True

            results = []
            async for status in client.stream_battery():
                results.append(status)

            assert len(results) == 3
            assert results[0]["level"] == 100
            assert results[1]["level"] == 99

    async def test_repr(self):
        """Test string representation."""
        client = AsyncTarsClient("192.168.1.1:50051")
        assert repr(client) == "AsyncTarsClient(address='192.168.1.1:50051')"
