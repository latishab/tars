#!/bin/bash
# Generate gRPC Python code from proto files

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Generating gRPC code from tars.proto..."

python -m grpc_tools.protoc \
  --proto_path=tars_sdk/proto \
  --python_out=tars_sdk/proto \
  --grpc_python_out=tars_sdk/proto \
  --pyi_out=tars_sdk/proto \
  tars.proto

echo "Fixing imports in generated files..."

# Fix imports to use relative imports
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  sed -i '' 's/^import tars_pb2/from . import tars_pb2/' tars_sdk/proto/tars_pb2_grpc.py
else
  # Linux
  sed -i 's/^import tars_pb2/from . import tars_pb2/' tars_sdk/proto/tars_pb2_grpc.py
fi

echo "✓ gRPC code generated successfully"
echo "  - tars_sdk/proto/tars_pb2.py"
echo "  - tars_sdk/proto/tars_pb2_grpc.py"
echo "  - tars_sdk/proto/tars_pb2.pyi"
