#!/bin/bash

# ================================================
# TARS Movement Service Startup Script
# ================================================
# This script starts the FastAPI movement service
# for servo control and camera capture on Raspberry Pi 5

echo "================================================"
echo "🤖 Starting TARS Control System V3"
echo "================================================"

# Navigate to project directory
cd ~/tars

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found at ./venv"
    echo "   Please create one with: python3 -m venv venv"
    echo "   Then install dependencies: pip install -r requirements-minimal.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found in current directory"
    exit 1
fi

# Start the FastAPI service
echo "Starting FastAPI service on http://0.0.0.0:8001"
echo "API Documentation: http://localhost:8001/docs"
echo "================================================"
python main.py
