#!/bin/bash
set -e

echo "Syncing versions..."
python3 scripts/sync_version.py

echo "Cleaning old builds..."
rm -rf dist/ build/ *.egg-info tars_robot.egg-info

echo "Building package..."
python -m build

echo "Build complete!"
ls -lh dist/
