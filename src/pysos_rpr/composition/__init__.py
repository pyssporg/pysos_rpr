"""Composition layer for the ``rpr`` projection.

This package owns ingestion of a SysML architecture and its lowering to a
:class:`~pyfmi_interop.ir.ModelDefinition`. The parser-free projection in
:mod:`pysos_rpr.projection` does not depend on it.
"""

from __future__ import annotations

from .sysml import generate_entity_adapter

__all__ = ["generate_entity_adapter"]
