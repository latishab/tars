"""
gRPC Server wrapper for TARS robot.
"""

import asyncio
from concurrent import futures
from typing import Optional

import grpc
from loguru import logger

# Import proto files
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "tars_sdk" / "proto"))

from tars_sdk.proto import tars_pb2_grpc
from grpc_server.servicer import TarsServiceServicer


class TARSgRPCServer:
    """gRPC server for TARS robot control."""

    def __init__(
        self,
        port: int = 50051,
        max_workers: int = 10,
        hardware_controller=None,
        camera=None,
        display=None,
        battery=None,
        audio=None,
        webrtc=None
    ):
        """
        Initialize gRPC server.

        Args:
            port: Port to listen on (default 50051)
            max_workers: Maximum thread pool workers (default 10)
            camera: CameraModule instance
            display: DisplayManager instance
            battery: BatteryModule instance
            audio: AudioModule instance
            webrtc: WebRTCServer instance
        """
        self.port = port
        self.max_workers = max_workers

        # Create servicer with hardware controller
        self.servicer = TarsServiceServicer(
            hardware_controller=hardware_controller,
            camera=camera,
            display=display,
            battery=battery,
            audio=audio,
            webrtc=webrtc
        )

        # Create gRPC server
        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=max_workers),
            options=[
                ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
            ]
        )

        # Add servicer to server
        tars_pb2_grpc.add_TarsServiceServicer_to_server(
            self.servicer,
            self.server
        )

        # Bind to port
        self.server.add_insecure_port(f'[::]:{port}')

        logger.info(f"TARSgRPCServer created on port {port}")

    async def start(self):
        """Start the gRPC server."""
        self.server.start()
        logger.success(f"✓ gRPC server started on port {self.port}")

    async def stop(self, grace: Optional[float] = 5.0):
        """
        Stop the gRPC server.

        Args:
            grace: Grace period for shutdown in seconds (default 5.0)
        """
        logger.info("Stopping gRPC server...")
        event = self.server.stop(grace)
        event.wait()
        logger.info("gRPC server stopped")

    def wait_for_termination(self):
        """Block until server terminates."""
        self.server.wait_for_termination()
