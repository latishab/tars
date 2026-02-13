#!/bin/bash
set -e

echo "Building TARS package for PyPI..."

# Check version consistency
SDK_VERSION=$(grep '__version__' tars_sdk/__init__.py | cut -d'"' -f2)
TOML_VERSION=$(grep 'version =' pyproject.toml | head -1 | cut -d'"' -f2)

if [ "$SDK_VERSION" != "$TOML_VERSION" ]; then
    echo "Version mismatch: SDK=$SDK_VERSION, pyproject.toml=$TOML_VERSION"
    exit 1
fi

echo "Version: $SDK_VERSION"

# Build dashboard frontend
echo "Building dashboard frontend..."
cd dashboard/frontend
npm install
npm run build
cd ../..

# Generate gRPC code
echo "Generating gRPC code..."
./scripts/generate_grpc.sh

# Clean old builds
echo "Cleaning old builds..."
rm -rf dist/ build/ *.egg-info

# Build package
echo "Building package..."
python -m build

# List contents
echo ""
echo "Package contents (key files):"
unzip -l dist/tars_robot-*.whl | grep -E "(tars_sdk|grpc_server|webrtc|dashboard|tars_daemon|__init__|proto)" | head -30

echo ""
echo "Build complete!"
ls -lh dist/

echo ""
echo "To test locally:"
echo "  pip install dist/tars_robot-$SDK_VERSION-py3-none-any.whl"
echo ""
echo "To publish to PyPI:"
echo "  python -m twine upload dist/*"
