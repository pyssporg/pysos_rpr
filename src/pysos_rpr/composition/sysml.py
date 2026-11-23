"""SysML composition: load an architecture and lower it to an FMI model.

This is the only package in :mod:`pysos_rpr` that loads a SysML architecture
and turns it into a :class:`~pyfmi_interop.ir.ModelDefinition` for the
parser-free ``rpr`` projection. The dependency points from this module to
:mod:`pysos_rpr.projection`, never the other way round.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pyfmi_interop import BuildConfig, build_model, generate_model, package_fmu
from pyfmi_interop.ir import (
    DataType,
    Direction,
    ModelDefinition,
    Signal,
    assign_value_references,
    deterministic_guid,
    model_from_dict,
)
from pyfmi_interop.packaging import platform_binary_dir
from pyfmi_interop.serialization.descriptor import WIRE_JSON_NAME

from ..projection.fmi import (
    _PROTO_ROOT,
    FRAME_MODE,
    _projection_json,
    _proto_files,
    backend,
    register,
    resolve_frame_mode,
)

__all__ = ["generate_entity_adapter"]

_DATA_TYPES = {
    "real": DataType.REAL,
    "integer": DataType.INTEGER,
    "boolean": DataType.BOOLEAN,
    "string": DataType.STRING,
}
_CAUSALITIES = {
    "input": Direction.INPUT,
    "output": Direction.OUTPUT,
    "parameter": Direction.PARAMETER,
}


def _identifier(text: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_]", "_", text)
    if not cleaned:
        return "model"
    if cleaned[0].isdigit():
        return f"_{cleaned}"
    return cleaned


def _select_part(architecture: Any, part: str | None) -> Any:
    if part is not None:
        return architecture.get_part_def(part)
    candidates = [
        definition
        for definition in architecture.part_definitions.values()
        if definition.ports and not definition.parts
    ]
    if len(candidates) != 1:
        names = ", ".join(sorted(definition.name for definition in candidates)) or "none"
        raise ValueError(
            "Cannot pick the entity part definition; "
            f"{len(candidates)} candidates ({names}). Pass part=."
        )
    return candidates[0]


def _model_from_architecture(
    architecture: Any,
    *,
    name: str | None,
    part: str | None,
    step_size_s: float | None,
) -> ModelDefinition:
    from pyfmi_sysml import DEFAULT_STRING_CAPACITY, component_interface

    definition = _select_part(architecture, part)
    component = component_interface(architecture, definition)
    signals = []
    for variable in component.variables:
        data_type = _DATA_TYPES[variable.type_name.strip().lower()]
        signals.append(
            Signal(
                name=variable.name,
                value_reference=1,
                data_type=data_type,
                direction=_CAUSALITIES[variable.causality],
                initial=variable.start,
                capacity=DEFAULT_STRING_CAPACITY if data_type is DataType.STRING else 0,
            )
        )
    model_name = _identifier(
        name or getattr(architecture, "package_name", None) or definition.name
    )
    return ModelDefinition(
        name=model_name,
        guid=deterministic_guid(model_name),
        step_size_s=step_size_s,
        realtime=False,
        signals=assign_value_references(signals),
        interface=definition.name,
    )


def generate_entity_adapter(
    architecture: Any,
    out_dir: str | Path,
    *,
    build: bool = True,
    package: bool = True,
    name: str | None = None,
    part: str | None = None,
    step_size_s: float | None = None,
    frame_mode: str = FRAME_MODE,
) -> Path:
    """Generate, build and package the RPR entity adapter FMU.

    ``architecture`` is a SysML path or a loaded ``pycps_sysml2.Architecture``.
    The payload backend is registered explicitly here, never as an import side
    effect.

    Returns the FMU path when ``package`` is true, else the built library, else
    the generated model directory.
    """

    from pyfmi_sysml import architecture as load_architecture

    register()
    frame_mode = resolve_frame_mode(frame_mode)
    loaded = load_architecture(architecture)
    model = _model_from_architecture(
        loaded, name=name, part=part, step_size_s=step_size_s
    )

    root = Path(out_dir)
    model_dir = root / "model"
    build_dir = root / "build"
    generate_model(
        model,
        model_dir,
        config=BuildConfig(serialization=backend.name),
    )
    if not build:
        return model_dir

    # A single cold build now works: the wire helper keeps the proto's
    # root-relative path and orders compilation after protoc.
    library = build_model(model_dir, build_dir=build_dir)
    if not package:
        return library

    effective = model_from_dict(
        json.loads((model_dir / "model.json").read_text(encoding="utf-8"))
    )
    platform = platform_binary_dir()
    extra: dict[str, bytes] = {
        "resources/rpr_projection.json": _projection_json(frame_mode),
        f"binaries/{platform}/wire.json": (model_dir / WIRE_JSON_NAME).read_bytes(),
    }
    for path in _proto_files():
        relative = path.relative_to(_PROTO_ROOT).as_posix()
        extra[f"binaries/{platform}/proto/{relative}"] = path.read_bytes()
    return package_fmu(
        model_dir,
        library,
        root / f"{effective.name}.fmu",
        model=effective,
        extra_entries=extra,
        include_schema=False,
    )
