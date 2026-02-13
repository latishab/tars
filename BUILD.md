# Building and Publishing TARS to PyPI

## Prerequisites

```bash
pip install build twine
```

## Pre-build Checklist

1. Update version in `pyproject.toml`
2. Update version in `tars_sdk/__init__.py`
3. Update version in `dashboard/frontend/package.json`
4. Build dashboard frontend
5. Run tests
6. Update CHANGELOG if applicable

## Build Dashboard Frontend

The dashboard frontend must be built before packaging:

```bash
cd dashboard/frontend
npm install
npm run build
cd ../..
```

This creates `dashboard/frontend/dist/` with production-ready assets.

## Generate gRPC Code

Ensure gRPC code is up to date:

```bash
./scripts/generate_grpc.sh
```

This generates:
- `tars_sdk/proto/tars_pb2.py`
- `tars_sdk/proto/tars_pb2_grpc.py`
- `tars_sdk/proto/tars_pb2.pyi`

## Build Package

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build wheel and source distribution
python -m build
```

This creates:
- `dist/tars_robot-X.Y.Z-py3-none-any.whl` (wheel)
- `dist/tars-robot-X.Y.Z.tar.gz` (source)

## Verify Package Contents

```bash
# List contents of wheel
unzip -l dist/tars_robot-*.whl

# Check what files will be included
python -m setuptools.command.sdist --list-only
```

Ensure the following are included:
- `tars_sdk/` with proto files
- `grpc_server/`
- `webrtc/`
- `state/`
- `dashboard/backend/`
- `dashboard/frontend/dist/`
- `tars_daemon.py`
- `README.md`
- `LICENSE`
- `.env.example`

## Test Package Locally

```bash
# Create test virtualenv
python -m venv test_env
source test_env/bin/activate

# Install from wheel
pip install dist/tars_robot-*.whl

# Test SDK import
python -c "from tars_sdk import TarsClient; print('OK')"

# Test daemon import
python -c "import tars_daemon; print('OK')"

# Test console script
which tars-daemon

deactivate
rm -rf test_env
```

## Test Different Installation Options

```bash
# Test minimal install
pip install dist/tars_robot-*.whl

# Test daemon install
pip install dist/tars_robot-*.whl[daemon]

# Test all extras
pip install dist/tars_robot-*.whl[all]
```

## Publish to TestPyPI (Optional)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ tars-robot
```

## Publish to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*
```

You'll be prompted for your PyPI credentials or API token.

## Post-publish Verification

```bash
# Install from PyPI
pip install tars-robot

# Verify version
python -c "import tars_sdk; print(tars_sdk.__version__)"
```

## Automated Build Script

Create `scripts/build_package.sh`:

```bash
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
echo "Package contents:"
unzip -l dist/tars_robot-*.whl | grep -E "tars_sdk|grpc_server|webrtc|dashboard|tars_daemon"

echo "Build complete! Files in dist/"
ls -lh dist/
```

Make executable:
```bash
chmod +x scripts/build_package.sh
```

## CI/CD with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install build twine
          pip install grpcio-tools

      - name: Build dashboard
        run: |
          cd dashboard/frontend
          npm install
          npm run build

      - name: Generate gRPC code
        run: ./scripts/generate_grpc.sh

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## Version Bumping

Update versions across all files:

```bash
# Update version (replace X.Y.Z with new version)
NEW_VERSION="0.3.0"

# pyproject.toml
sed -i '' "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# tars_sdk/__init__.py
sed -i '' "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" tars_sdk/__init__.py

# dashboard/frontend/package.json
sed -i '' "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" dashboard/frontend/package.json

# Verify
echo "pyproject.toml: $(grep 'version =' pyproject.toml | head -1)"
echo "tars_sdk: $(grep '__version__' tars_sdk/__init__.py)"
echo "dashboard: $(grep '\"version\"' dashboard/frontend/package.json | head -1)"
```

## Troubleshooting

### Dashboard not included

Ensure `dashboard/frontend/dist/` exists before building:
```bash
ls -la dashboard/frontend/dist/
```

### gRPC files missing

Regenerate:
```bash
./scripts/generate_grpc.sh
```

### Wrong files included

Check `MANIFEST.in` and `pyproject.toml` package configuration.

### Import errors after install

Check package structure:
```bash
unzip -l dist/tars_robot-*.whl | grep __init__.py
```

All packages need `__init__.py`.

## See Also

- [pyproject.toml](./pyproject.toml) - Package configuration
- [MANIFEST.in](./MANIFEST.in) - File inclusion rules
- [INSTALL.md](./INSTALL.md) - Installation guide
