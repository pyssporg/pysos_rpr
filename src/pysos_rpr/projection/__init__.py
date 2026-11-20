"""Projections of the ``rpr.v2`` vocabulary.

Importing this package pulls the artifact implementer of the projection
(``pyfmi_interop`` and the SysML dialect), so it is not part of the
dependency-free vocabulary surface.  :mod:`pysos_rpr` and
:mod:`pysos_rpr.messages` never import it.
"""

from __future__ import annotations

from .fmi import (
    FRAME_MODE,
    RprSerialization,
    backend,
    generate_entity_adapter,
    register,
)

__all__ = [
    "FRAME_MODE",
    "RprSerialization",
    "backend",
    "generate_entity_adapter",
    "register",
]
