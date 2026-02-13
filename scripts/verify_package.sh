#!/bin/bash
# Verify package structure before publishing

set -e

echo "Verifying TARS package structure..."
echo ""

# Check version consistency
echo "1. Checking version consistency..."
SDK_VERSION=$(grep '__version__' tars_sdk/__init__.py | cut -d'"' -f2)
TOML_VERSION=$(grep 'version =' pyproject.toml | head -1 | cut -d'"' -f2)
DASHBOARD_VERSION=$(grep '"version"' dashboard/frontend/package.json | head -1 | cut -d'"' -f4)

echo "   SDK version: $SDK_VERSION"
echo "   pyproject.toml version: $TOML_VERSION"
echo "   Dashboard version: $DASHBOARD_VERSION"

if [ "$SDK_VERSION" != "$TOML_VERSION" ]; then
    echo "   ERROR: Version mismatch between SDK and pyproject.toml"
    exit 1
fi
echo "   OK"
echo ""

# Check required files exist
echo "2. Checking required files..."
REQUIRED_FILES=(
    "pyproject.toml"
    "README.md"
    "LICENSE"
    ".env.example"
    "MANIFEST.in"
    "tars_daemon.py"
    "app_servotester.py"
    "src/app-servotester.py"
    "tars_sdk/__init__.py"
    "tars_sdk/client.py"
    "tars_sdk/async_client.py"
    "grpc_server/__init__.py"
    "grpc_server/server.py"
    "grpc_server/servicer.py"
    "webrtc/__init__.py"
    "webrtc/server.py"
    "state/__init__.py"
    "dashboard/__init__.py"
    "dashboard/backend/__init__.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "   ERROR: Missing file: $file"
        exit 1
    fi
done
echo "   All required files present"
echo ""

# Check __init__.py in all packages
echo "3. Checking package __init__.py files..."
PACKAGES=(
    "tars_sdk"
    "tars_sdk/proto"
    "grpc_server"
    "webrtc"
    "state"
    "dashboard"
    "dashboard/backend"
    "dashboard/backend/routes"
)

for pkg in "${PACKAGES[@]}"; do
    if [ ! -f "$pkg/__init__.py" ]; then
        echo "   ERROR: Missing $pkg/__init__.py"
        exit 1
    fi
done
echo "   All packages have __init__.py"
echo ""

# Check gRPC generated files
echo "4. Checking gRPC generated files..."
GRPC_FILES=(
    "tars_sdk/proto/tars_pb2.py"
    "tars_sdk/proto/tars_pb2_grpc.py"
    "tars_sdk/proto/tars_pb2.pyi"
)

for file in "${GRPC_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "   ERROR: Missing generated file: $file"
        echo "   Run: ./scripts/generate_grpc.sh"
        exit 1
    fi
done
echo "   gRPC files generated"
echo ""

# Check dashboard build
echo "5. Checking dashboard frontend build..."
if [ ! -d "dashboard/frontend/dist" ]; then
    echo "   ERROR: Dashboard not built"
    echo "   Run: cd dashboard/frontend && npm run build"
    exit 1
fi

DIST_FILES=$(ls -1 dashboard/frontend/dist/ 2>/dev/null | wc -l)
if [ "$DIST_FILES" -lt 2 ]; then
    echo "   ERROR: Dashboard build appears empty"
    exit 1
fi
echo "   Dashboard built ($DIST_FILES files in dist/)"
echo ""

# Check imports work
echo "6. Testing Python imports..."
python3 -c "import tars_sdk; print('   tars_sdk: OK')" || exit 1
python3 -c "from tars_sdk import TarsClient; print('   TarsClient: OK')" || exit 1
python3 -c "from tars_sdk import AsyncTarsClient; print('   AsyncTarsClient: OK')" || exit 1
python3 -c "import grpc_server; print('   grpc_server: OK')" || exit 1
python3 -c "import webrtc; print('   webrtc: OK')" || exit 1
python3 -c "import state; print('   state: OK')" || exit 1
python3 -c "import dashboard; print('   dashboard: OK')" || exit 1
python3 -c "import tars_daemon; print('   tars_daemon: OK')" || exit 1
echo ""

# Check entry points
echo "7. Checking entry points..."
if ! grep -q "tars-daemon = \"tars_daemon:main\"" pyproject.toml; then
    echo "   ERROR: tars-daemon console script not configured"
    exit 1
fi
if ! grep -q "tars-servo-tester = \"app_servotester:main\"" pyproject.toml; then
    echo "   ERROR: tars-servo-tester console script not configured"
    exit 1
fi
echo "   Console scripts configured (tars-daemon, tars-servo-tester)"
echo ""

# Summary
echo "========================================="
echo "Package verification PASSED"
echo "========================================="
echo ""
echo "Ready to build with:"
echo "  ./scripts/build_package.sh"
echo ""
echo "Or manually:"
echo "  python -m build"
echo ""
