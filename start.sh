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
HOST_URL=${HOST_URL:-""}
API_PORT=${API_PORT:-8001}
DISPLAY_ENABLED=${DISPLAY_ENABLED:-true}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host|-m)
            HOST_URL="$2"
            shift 2
            ;;
        --port|-p)
            API_PORT="$2"
            shift 2
            ;;
        --no-display)
            DISPLAY_ENABLED=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --host, -H URL        Host computer URL for WebRTC (e.g., http://100.64.0.1:7860)"
            echo "  --port, -p PORT       REST API port (default: 8001)"
            echo "  --no-display          Disable display (headless mode)"
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

if [ -n "$HOST_URL" ]; then
    CMD="$CMD --host $HOST_URL"
    echo "Host Computer: $HOST_URL"
fi

if [ "$DISPLAY_ENABLED" = "false" ]; then
    CMD="$CMD --no-display"
    echo "Display: disabled"
else
    echo "Display: enabled"
fi

echo "API Port: $API_PORT"
echo "========================================"

# Run daemon
exec $CMD
