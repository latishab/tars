"""WebRTC signaling API routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

class OfferRequest(BaseModel):
    sdp: str
    type: str

@router.post("/offer")
async def handle_webrtc_offer(request: OfferRequest, req: Request):
    """Handle WebRTC SDP offer for P2P audio connection."""
    daemon = req.app.state.daemon
    if not daemon.webrtc:
        raise HTTPException(503, "WebRTC server not available")
    try:
        answer = await daemon.webrtc.handle_offer(request.sdp, request.type)
        return answer
    except Exception as e:
        logger.error(f"Failed to handle WebRTC offer: {e}")
        raise HTTPException(500, f"WebRTC offer failed: {str(e)}")
