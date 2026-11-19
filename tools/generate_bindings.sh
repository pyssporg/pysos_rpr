#!/usr/bin/env bash
# Regenerate the committed Python bindings from proto/rpr/v2/.
# Usage: tools/generate_bindings.sh (set PYTHON to choose an interpreter).
set -euo pipefail

cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"

"$PYTHON" -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=src/pysos_rpr/_proto \
  proto/rpr/v2/entity.proto \
  proto/rpr/v2/spatial.proto \
  proto/rpr/v2/platform.proto
