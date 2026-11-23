"""The flat schema table is generated from the proto."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

from pysos_rpr import schema_paths as table

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATHS = ROOT / "src" / "pysos_rpr" / "schema_paths.py"
GENERATOR = ROOT / "tools" / "generate_schema_paths.py"


def _generator() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("generate_schema_paths_rpr", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses can resolve the module's own types.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_schema_paths_is_fresh():
    assert _generator().render_schema_paths().encode("utf-8") == SCHEMA_PATHS.read_bytes()


def test_table_is_self_consistent():
    assert set(table.PROTO_TYPES) == set(table.SCHEMA_PATHS)
    omitted = {path.replace(".", "_") for path in table.OMITTED_BYTES}
    for flat, path in table.SCHEMA_PATHS.items():
        assert path.replace(".", "_") == flat
        assert flat not in omitted, flat
    assert table.OMITTED_BYTES == ("spatial.dead_reckoning.parameters",)
