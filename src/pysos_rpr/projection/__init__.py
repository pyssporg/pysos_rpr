"""Projections of the ``rpr.v2`` vocabulary.

Importing this package pulls the FMI artifact implementer (``pyfmi_interop``),
so it is not part of the dependency-free vocabulary surface.
:mod:`pysos_rpr` and :mod:`pysos_rpr.messages` never import it. Composition
(ingestion and lowering) lives in :mod:`pysos_rpr.composition`; the entry
point below is a lazy re-export and does not import it until called.
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
