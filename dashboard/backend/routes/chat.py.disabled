"""Chat API routes for text-based interaction with TARS."""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

# Chat handler (set by integration with Mac-side agent)
_chat_handler = None

# Simple in-memory chat history for dashboard
_chat_history: List[dict] = []
MAX_HISTORY = 100


class ChatMessage(BaseModel):
    text: str
    user_id: Optional[str] = "dashboard"


class ChatResponse(BaseModel):
    response: str
    timestamp: str
    actions: List[str] = []  # Actions that were triggered


def set_chat_handler(handler):
    """Set the chat handler function."""
    global _chat_handler
    _chat_handler = handler


@router.post("/chat", response_model=ChatResponse)
async def send_message(message: ChatMessage):
    """Send a text message to TARS and get a response."""
    timestamp = datetime.now().isoformat()

    # Store user message
    _chat_history.append({
        "role": "user",
        "text": message.text,
        "timestamp": timestamp,
        "user_id": message.user_id,
    })

    # Trim history
    while len(_chat_history) > MAX_HISTORY:
        _chat_history.pop(0)

    # If no handler is set, return a placeholder
    if not _chat_handler:
        response_text = (
            "Chat is not connected to the AI backend. "
            "Make sure tars-omni is running and connected."
        )
        actions = []
    else:
        try:
            result = await _chat_handler(
                text=message.text,
                user_id=message.user_id,
            )
            response_text = result.get("response", "No response")
            actions = result.get("actions", [])
        except Exception as e:
            logger.error(f"Chat handler error: {e}")
            response_text = f"Error processing message: {str(e)}"
            actions = []

    # Store assistant response
    _chat_history.append({
        "role": "assistant",
        "text": response_text,
        "timestamp": datetime.now().isoformat(),
        "actions": actions,
    })

    return ChatResponse(
        response=response_text,
        timestamp=timestamp,
        actions=actions,
    )


@router.get("/chat/history")
async def get_history(limit: int = 50):
    """Get recent chat history."""
    return {
        "messages": _chat_history[-limit:],
        "total": len(_chat_history),
    }


@router.delete("/chat/history")
async def clear_history():
    """Clear chat history."""
    global _chat_history
    _chat_history = []
    return {"success": True}
