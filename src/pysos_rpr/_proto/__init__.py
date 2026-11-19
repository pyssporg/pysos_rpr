"""Generated protobuf bindings for the ``rpr.v2`` vocabulary.

The modules under ``rpr/v2/`` are produced by ``protoc`` (via
``grpcio-tools``) from ``proto/rpr/v2/``. Do not edit them by hand.

Regenerate from the repository root with::

    python -m grpc_tools.protoc \\
        --proto_path=proto \\
        --python_out=src/pysos_rpr/_proto \\
        proto/rpr/v2/entity.proto proto/rpr/v2/spatial.proto \\
        proto/rpr/v2/platform.proto

``protoc`` emits absolute imports (``from rpr.v2 import spatial_pb2``), so this
package publishes its own ``rpr`` namespace under the top-level name ``rpr``
before importing the generated modules. That keeps the generated files
untouched while letting ``pysos_rpr._proto`` be the only import a consumer
needs.
"""

from __future__ import annotations

import sys as _sys

from . import rpr as _rpr

_sys.modules.setdefault("rpr", _rpr)

from .rpr.v2 import entity_pb2, platform_pb2, spatial_pb2  # noqa: E402

__all__ = ["entity_pb2", "platform_pb2", "spatial_pb2"]
