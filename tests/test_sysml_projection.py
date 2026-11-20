"""The SysML port library and schema table are generated from the proto."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

from pysos_rpr import schema_paths as table

ROOT = Path(__file__).resolve().parents[1]
SYSML = ROOT / "sysml" / "rpr_entity.sysml"
SCHEMA_PATHS = ROOT / "src" / "pysos_rpr" / "schema_paths.py"
GENERATOR = ROOT / "tools" / "generate_sysml.py"

# Independent of the generator: a proto leaf type names one bare SysML
# primitive.  Enums collapse to Integer.
_PRIMITIVES = {
    "double": "Real",
    "float": "Real",
    "int32": "Integer",
    "int64": "Integer",
    "uint32": "Integer",
    "uint64": "Integer",
    "sint32": "Integer",
    "sint64": "Integer",
    "fixed32": "Integer",
    "fixed64": "Integer",
    "sfixed32": "Integer",
    "sfixed64": "Integer",
    "bool": "Boolean",
    "string": "String",
}


def _generator() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("generate_sysml_rpr", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses can resolve the module's own types.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _primitive(proto_type: str) -> str:
    if proto_type.startswith("rpr.v2."):
        return "Integer"
    return _PRIMITIVES[proto_type]


def test_sysml_is_fresh():
    assert _generator().render_sysml().encode("utf-8") == SYSML.read_bytes()


def test_schema_paths_is_fresh():
    assert _generator().render_schema_paths().encode("utf-8") == SCHEMA_PATHS.read_bytes()


def test_port_definition_matches_schema_paths():
    sysml2 = pytest.importorskip("pycps_sysml2")
    try:
        architecture = sysml2.load(SYSML)
    except Exception as exc:  # report the parser's verdict, do not hide it
        pytest.fail(f"pycps_sysml2 rejected {SYSML.relative_to(ROOT)}: {exc}")

    assert "EntityState" in architecture.port_definitions
    port = architecture.port_definitions["EntityState"]

    assert list(port.attributes) == list(table.SCHEMA_PATHS)
    assert set(table.PROTO_TYPES) == set(table.SCHEMA_PATHS)
    for flat, path in table.SCHEMA_PATHS.items():
        attribute = port.attributes[flat]
        assert attribute.type_name == _primitive(table.PROTO_TYPES[flat]), flat
        assert attribute.multiplicity is None, flat
        if table.PROTO_TYPES[flat].startswith("rpr.v2."):
            assert attribute.value == 0, flat
        assert path.replace(".", "_") == flat

    omitted = {path.replace(".", "_") for path in table.OMITTED_BYTES}
    assert not omitted & set(port.attributes)
    assert table.OMITTED_BYTES == ("spatial.dead_reckoning.parameters",)

    state = architecture.part_definitions["RprEntity"].ports["entityState"]
    assert state.direction == "out"
    assert state.type_name == "EntityState"
