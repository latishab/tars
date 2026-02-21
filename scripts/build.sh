#!/bin/bash
set -e

# Detect Python (prefer conda if available)
if [ -f "/Users/mac/miniconda3/bin/python" ]; then
    PYTHON="/Users/mac/miniconda3/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
else
    PYTHON="python"
fi

echo "Using Python: $PYTHON"
$PYTHON --version

echo ""
echo "Syncing versions..."
$PYTHON scripts/sync_version.py

echo ""
echo "Cleaning old builds..."
rm -rf dist/ build/ *.egg-info tars_robot.egg-info

echo ""
echo "Building package..."
$PYTHON -m build

echo ""
echo "Build complete!"
ls -lh dist/
