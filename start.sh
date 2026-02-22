#!/bin/bash
# TARS Daemon Startup Script
# Activates venv and starts the unified daemon

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "Starting TARS Daemon"
echo "========================================"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ -f ".env" ]; then
    echo "Loading environment from .env"
    export $(grep -v '^#' .env | xargs)
fi

# Default values
API_PORT=${API_PORT:-8000}
DISPLAY_ENABLED=${DISPLAY_ENABLED:-true}
WEBRTC_ENABLED=${WEBRTC_ENABLED:-true}
FACE_TRACKING=${FACE_TRACKING:-false}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port|-p)
            API_PORT="$2"
            shift 2
            ;;
        --no-display)
            DISPLAY_ENABLED=false
            shift
            ;;
        --no-webrtc)
            WEBRTC_ENABLED=false
            shift
            ;;
        --face-tracking)
            FACE_TRACKING=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port, -p PORT       REST API port (default: 8001)"
            echo "  --no-display          Disable display (headless mode)"
            echo "  --no-webrtc           Disable WebRTC server (REST API only)"
            echo "  --face-tracking       Enable face tracking with eyes"
            echo "  --help, -h            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
CMD="python tars_daemon.py --port $API_PORT"

if [ "$DISPLAY_ENABLED" = "false" ]; then
    CMD="$CMD --no-display"
    echo "Display: disabled"
else
    echo "Display: enabled"
fi

if [ "$WEBRTC_ENABLED" = "false" ]; then
    CMD="$CMD --no-webrtc"
    echo "WebRTC: disabled (REST API only)"
else
    echo "WebRTC: enabled (waiting for AI brain)"
fi

if [ "$FACE_TRACKING" = "true" ]; then
    CMD="$CMD --face-tracking"
    echo "Face Tracking: enabled"
fi

echo "API Port: $API_PORT"
echo "========================================"

# Run daemon
exec $CMD
