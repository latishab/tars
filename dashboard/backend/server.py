"""
TARS Dashboard Server

FastAPI backend serving the dashboard UI and API endpoints.
"""

import asyncio
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger

from .routes import status, movements, settings, updates, wifi, chat
from .ws import ConnectionManager


# WebSocket connection manager
ws_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Dashboard server starting...")

    # Start background task for status broadcasts
    broadcast_task = asyncio.create_task(status_broadcast_loop())

    yield

    # Cleanup
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass

    logger.info("Dashboard server stopped")


app = FastAPI(
    title="TARS Dashboard",
    description="Control interface for TARS robot",
    version="0.2.0",
    lifespan=lifespan,
)

# Include API routes
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(movements.router, prefix="/api", tags=["movements"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(updates.router, prefix="/api", tags=["updates"])
app.include_router(wifi.router, prefix="/api", tags=["wifi"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time status updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()
            # Echo or handle commands if needed
            logger.debug(f"WebSocket received: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


async def status_broadcast_loop():
    """Broadcast status updates to all connected WebSocket clients."""
    while True:
        try:
            if ws_manager.has_connections():
                status_data = await status.get_status_data()
                await ws_manager.broadcast(status_data)
        except Exception as e:
            logger.error(f"Status broadcast error: {e}")

        await asyncio.sleep(2)  # Update every 2 seconds


# Serve static frontend files
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend SPA - fallback to index.html for client-side routing."""
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    async def no_frontend():
        """Placeholder when frontend is not built."""
        return {
            "message": "TARS Dashboard API",
            "status": "Frontend not built",
            "hint": "Run: cd dashboard/frontend && npm install && npm run build"
        }


def get_app() -> FastAPI:
    """Get the FastAPI application instance."""
    return app
