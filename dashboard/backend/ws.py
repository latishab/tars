"""WebSocket connection manager for real-time updates."""

import json
from typing import List, Any
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """Manages WebSocket connections for real-time status updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    def has_connections(self) -> bool:
        """Check if there are active connections."""
        return len(self.active_connections) > 0

    async def broadcast(self, data: Any):
        """Broadcast data to all connected clients."""
        if not self.active_connections:
            return

        message = json.dumps(data) if not isinstance(data, str) else data
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to(self, websocket: WebSocket, data: Any):
        """Send data to a specific client."""
        message = json.dumps(data) if not isinstance(data, str) else data
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send to WebSocket: {e}")
            self.disconnect(websocket)
