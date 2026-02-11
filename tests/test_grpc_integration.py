"""Integration tests for gRPC server with mocked hardware modules."""

import sys
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import grpc

# Add paths
repo_root = str(Path(__file__).parent.parent)
src_dir = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, repo_root)
sys.path.insert(0, src_dir)

from tars_sdk.proto import tars_pb2, tars_pb2_grpc
from tars_sdk import TarsClient


def _create_mock_modules():
    """Create mock versions of hardware modules to avoid real I2C/servo calls."""
    mock_servoctl = MagicMock()
    mock_servoctl.MOVING = False
    mock_servoctl.reset_positions = MagicMock()

    mock_movements = MagicMock()
    for name in [
        "step_forward", "walk_forward", "step_backward", "walk_backward",
        "turn_right", "turn_right_slow", "turn_left", "turn_left_slow",
        "pose", "bow", "tilt_right", "tilt_left", "side_side",
        "wave_right", "wave_left", "neutral_legs", "excited", "laugh", "swing_legs",
    ]:
        setattr(mock_movements, name, MagicMock())

    mock_registry = MagicMock()
    mock_registry.MOVEMENTS = {
        "step_forward": {"name": "Step Forward"},
        "walk_forward": {"name": "Walk Forward"},
        "laugh": {"name": "Laugh"},
        "wave_right": {"name": "Wave Right"},
    }

    return mock_servoctl, mock_movements, mock_registry


@pytest.fixture(scope="class")
def grpc_server():
    """Start a real gRPC server with mocked hardware, yield info dict, then tear down."""
    mock_servoctl, mock_movements, mock_registry = _create_mock_modules()

    with patch.dict(sys.modules, {
        'src.modules.module_servoctl': mock_servoctl,
        'src.modules.module_movements': mock_movements,
        'src.modules.module_movement_registry': mock_registry,
    }):
        import importlib
        for mod_name in ['grpc_server.servicer', 'grpc_server.server']:
            if mod_name in sys.modules:
                del sys.modules[mod_name]

        from grpc_server.server import TARSgRPCServer

        server = TARSgRPCServer(port=50099, max_workers=4)
        server.server.start()
        time.sleep(0.3)

        yield {
            'address': 'localhost:50099',
            'server': server,
            'mock_servoctl': mock_servoctl,
            'mock_movements': mock_movements,
        }

        server.server.stop(grace=1.0).wait()


class TestGRPCIntegration:
    """Test gRPC server with mocked hardware."""

    def test_health_check(self, grpc_server):
        """Health endpoint returns running status."""
        client = TarsClient(grpc_server['address'])
        health = client.health()
        assert health.status == "running"
        assert health.grpc_available is True
        assert health.hardware.servos is True
        assert health.hardware.camera is False
        client.close()

    def test_move_known_movement(self, grpc_server):
        """Move endpoint calls the correct movement function."""
        client = TarsClient(grpc_server['address'])
        result = client.move("walk_forward")
        assert result.success is True
        assert result.duration >= 0
        grpc_server['mock_movements'].walk_forward.assert_called()
        client.close()

    def test_move_unknown_movement(self, grpc_server):
        """Move endpoint returns error for unknown movement."""
        client = TarsClient(grpc_server['address'])
        result = client.move("backflip")
        assert result.success is False
        assert "Unknown movement" in result.error
        client.close()

    def test_move_multiple_movements(self, grpc_server):
        """Multiple movements execute in sequence."""
        client = TarsClient(grpc_server['address'])
        result1 = client.move("laugh")
        assert result1.success is True
        result2 = client.move("wave_right")
        assert result2.success is True
        client.close()

    def test_reset(self, grpc_server):
        """Reset endpoint calls servoctl.reset_positions."""
        client = TarsClient(grpc_server['address'])
        client.reset()
        grpc_server['mock_servoctl'].reset_positions.assert_called()
        client.close()

    def test_get_status(self, grpc_server):
        """GetStatus returns connected status."""
        client = TarsClient(grpc_server['address'])
        status = client.get_status()
        assert status.connected is True
        assert status.is_moving is False
        client.close()

    def test_set_emotion_no_display(self, grpc_server):
        """SetEmotion with no display returns UNAVAILABLE."""
        channel = grpc.insecure_channel(grpc_server['address'])
        stub = tars_pb2_grpc.TarsServiceStub(channel)
        with pytest.raises(grpc.RpcError) as exc_info:
            stub.SetEmotion(tars_pb2.EmotionRequest(emotion="happy"))
        assert exc_info.value.code() == grpc.StatusCode.UNAVAILABLE
        channel.close()

    def test_capture_camera_no_camera(self, grpc_server):
        """CaptureCamera with no camera returns UNAVAILABLE."""
        channel = grpc.insecure_channel(grpc_server['address'])
        stub = tars_pb2_grpc.TarsServiceStub(channel)
        with pytest.raises(grpc.RpcError) as exc_info:
            stub.CaptureCamera(tars_pb2.CaptureRequest())
        assert exc_info.value.code() == grpc.StatusCode.UNAVAILABLE
        channel.close()

    def test_client_context_manager(self, grpc_server):
        """Client works as context manager."""
        with TarsClient(grpc_server['address']) as client:
            health = client.health()
            assert health.status == "running"

    def test_stream_battery(self, grpc_server):
        """StreamBattery returns battery updates."""
        channel = grpc.insecure_channel(grpc_server['address'])
        stub = tars_pb2_grpc.TarsServiceStub(channel)
        stream = stub.StreamBattery(tars_pb2.Empty())
        status = next(stream)
        assert status.level == 0
        assert status.charging is False
        stream.cancel()
        channel.close()
