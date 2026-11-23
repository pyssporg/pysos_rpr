#!/usr/bin/env python3
"""Generate the flat schema table for ``rpr.v2``.

One schema, many projections: the proto definitions under ``proto/rpr/v2/`` are
the single source and the table is generated from the descriptors of the
committed bindings, never from ``protoc`` or from hand-written field lists::

    python tools/generate_schema_paths.py

Output:

* ``src/pysos_rpr/schema_paths.py`` -- the flat name -> dotted proto path and
  proto type table the FMI projection consumes.

The flat attribute name is the dotted path with ``.`` replaced by ``_``.  It is
not reversible (``world_location`` already contains an underscore), so the
schema table is the authority.

The SysML port built from this table is an implementation asset of
``pyfmi_rpr`` (``src/pyfmi_rpr/sysml/rpr_entity.sysml``, exposed as
``pyfmi_rpr.rpr_entity()``); this package owns the protobuf contract and the
table, not the port shape.

``bytes`` fields have no dialect representation and are omitted from the port;
the FMI codec defaults them to empty.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pysos_rpr._proto.rpr.v2 import entity_pb2, spatial_pb2  # noqa: E402

DEFAULT_SCHEMA_PATHS = SRC / "pysos_rpr" / "schema_paths.py"

ROOT_MESSAGE = "rpr.v2.PhysicalEntity"
BASE_MESSAGE = "rpr.v2.BaseEntity"

# descriptor.FieldDescriptor.type values (stable protobuf wire constants).
TYPE_DOUBLE = 1
TYPE_FLOAT = 2
TYPE_INT64 = 3
TYPE_UINT64 = 4
TYPE_INT32 = 5
TYPE_FIXED64 = 6
TYPE_FIXED32 = 7
TYPE_BOOL = 8
TYPE_STRING = 9
TYPE_GROUP = 10
TYPE_MESSAGE = 11
TYPE_BYTES = 12
TYPE_UINT32 = 13
TYPE_ENUM = 14
TYPE_SFIXED32 = 15
TYPE_SFIXED64 = 16
TYPE_SINT32 = 17
TYPE_SINT64 = 18

LABEL_REPEATED = 3

_PROTO_NAMES = {
    TYPE_DOUBLE: "double",
    TYPE_FLOAT: "float",
    TYPE_INT64: "int64",
    TYPE_UINT64: "uint64",
    TYPE_INT32: "int32",
    TYPE_FIXED64: "fixed64",
    TYPE_FIXED32: "fixed32",
    TYPE_BOOL: "bool",
    TYPE_STRING: "string",
    TYPE_BYTES: "bytes",
    TYPE_UINT32: "uint32",
    TYPE_SFIXED32: "sfixed32",
    TYPE_SFIXED64: "sfixed64",
    TYPE_SINT32: "sint32",
    TYPE_SINT64: "sint64",
}


@dataclass(frozen=True)
class Leaf:
    """One representable leaf field of the entity-state shape."""

    path: str
    proto_type: str

    @property
    def flat(self) -> str:
        """Flat SysML attribute name: the dotted path with ``.`` -> ``_``."""
        return self.path.replace(".", "_")


def _proto_type_name(field: object) -> str:
    if field.type == TYPE_ENUM:
        return field.enum_type.full_name
    return _PROTO_NAMES[field.type]


def _walk_field(field: object, prefix: str) -> tuple[list[Leaf], list[str]]:
    path = f"{prefix}.{field.name}" if prefix else field.name
    if field.label == LABEL_REPEATED:
        raise ValueError(
            f"{path}: repeated fields have no fixed length and cannot be projected"
        )
    if field.type == TYPE_GROUP:
        raise ValueError(f"{path}: proto groups are not part of this vocabulary")
    if field.type == TYPE_MESSAGE:
        return _walk(field.message_type, path)
    if field.type == TYPE_BYTES:
        return [], [path]
    leaf = Leaf(path, _proto_type_name(field))
    return [leaf], []


def _walk(message: object, prefix: str) -> tuple[list[Leaf], list[str]]:
    """Walk a message in declaration order, nested messages before own leaves.

    Message-typed fields are emitted depth-first in field-number order, then the
    message's own scalar/enum leaves in field-number order.  That is the
    entity-state shape: vectors group together and ``is_frozen`` follows them.
    """
    nested: list[Leaf] = []
    leaves: list[Leaf] = []
    omitted: list[str] = []
    for field in message.fields:
        child_leaves, child_omitted = _walk_field(field, prefix)
        if field.type == TYPE_MESSAGE:
            nested.extend(child_leaves)
        else:
            leaves.extend(child_leaves)
        omitted.extend(child_omitted)
    return nested + leaves, omitted


def _message(full_name: str) -> object:
    """Look a message descriptor up across the rpr.v2 binding modules."""
    package, name = full_name.rsplit(".", 1)
    for descriptor in (entity_pb2.DESCRIPTOR, spatial_pb2.DESCRIPTOR):
        if descriptor.package == package and name in descriptor.message_types_by_name:
            return descriptor.message_types_by_name[name]
    raise KeyError(f"unknown message {full_name}")


def projection() -> tuple[list[Leaf], list[str]]:
    """Projected leaves in declaration order plus the omitted ``bytes`` paths."""
    root = _message(ROOT_MESSAGE)
    leaves: list[Leaf] = []
    omitted: list[str] = []
    for field in root.fields:
        if field.type == TYPE_MESSAGE and field.message_type.full_name == BASE_MESSAGE:
            # The inherited BaseEntity wrapper is flattened into the state.
            child_leaves, child_omitted = _walk(field.message_type, "")
        else:
            child_leaves, child_omitted = _walk_field(field, "")
        leaves.extend(child_leaves)
        omitted.extend(child_omitted)

    flat_names = [leaf.flat for leaf in leaves]
    duplicates = {name for name in flat_names if flat_names.count(name) > 1}
    if duplicates:
        raise ValueError(f"flat attribute names collide: {sorted(duplicates)}")
    return leaves, omitted


def render_schema_paths() -> str:
    """Render ``schema_paths.py`` with ``\\n`` and one trailing newline."""
    leaves, omitted = projection()
    lines = [
        '"""Flat RPR entity-state attribute names and the proto paths they project from.',
        "",
        "Generated by tools/generate_schema_paths.py from the ``rpr.v2`` proto descriptors.",
        "Reproduce with ``python tools/generate_schema_paths.py``; do not edit by hand.",
        "",
        "``SCHEMA_PATHS`` maps the flat SysML port attribute name (dots replaced by",
        "underscores) to the dotted entity-state path it represents.  The mapping is",
        "not reversible -- ``world_location`` already contains an underscore -- so",
        "this table is the authority.  ``PROTO_TYPES`` carries the protobuf leaf type",
        "so the FMI projection does not have to re-read the descriptors.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        f'ENTITY_MESSAGE = "{ROOT_MESSAGE}"',
        "",
        "SCHEMA_PATHS: dict[str, str] = {",
    ]
    lines.extend(f'    "{leaf.flat}": "{leaf.path}",' for leaf in leaves)
    lines.extend(["}", "", "PROTO_TYPES: dict[str, str] = {"])
    lines.extend(f'    "{leaf.flat}": "{leaf.proto_type}",' for leaf in leaves)
    lines.extend(["}", "", "OMITTED_BYTES: tuple[str, ...] = ("])
    lines.extend(f'    "{path}",' for path in omitted)
    lines.extend([")", ""])
    return "\n".join(lines)


def write(schema_paths_path: Path = DEFAULT_SCHEMA_PATHS) -> Path:
    """Write the generated schema table deterministically."""
    schema_paths_path = Path(schema_paths_path)
    schema_paths_path.parent.mkdir(parents=True, exist_ok=True)
    schema_paths_path.write_text(render_schema_paths(), encoding="utf-8", newline="\n")
    return schema_paths_path


def main() -> int:
    """Script entry point; writes the schema table in the repository."""
    path = write()
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
