"""The ``rpr`` serialization backend declares the rpr.v2 payload identity."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("pyfmi_interop")

from pyfmi_interop.codegen import generate_model  # noqa: E402
from pyfmi_interop.ir import (  # noqa: E402
    DataType,
    Direction,
    ModelDefinition,
    ProjectionError,
    Signal,
    deterministic_guid,
)

from pysos_rpr.projection import RprSerialization, register  # noqa: E402
from pysos_rpr.schema_paths import SCHEMA_PATHS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def make_model(*, frozen_type: DataType = DataType.BOOLEAN, extra: bool = False) -> ModelDefinition:
    signals = [
        Signal("entityState.entity_identifier_site", 1, DataType.INTEGER, Direction.INPUT),
        Signal("entityState.spatial_world_location_x", 2, DataType.REAL, Direction.INPUT),
        Signal(
            "entityState.marking_characters",
            3,
            DataType.STRING,
            Direction.INPUT,
            capacity=16,
        ),
        Signal("entityState.spatial_is_frozen", 4, frozen_type, Direction.INPUT),
    ]
    if extra:
        signals.append(Signal("entityState.not_in_the_schema", 5, DataType.REAL, Direction.INPUT))
    return ModelDefinition(
        name="RprEntityProbe",
        guid=deterministic_guid("RprEntityProbe"),
        step_size_s=None,
        realtime=False,
        signals=tuple(signals),
        interface="RprEntity",
    )


@pytest.fixture(autouse=True)
def registered():
    register()


def test_registered_name_is_accepted_by_generation(tmp_path):
    target = generate_model(make_model(), tmp_path / "gen", serialization="rpr")

    assert (target / "model_wire.cpp").is_file()
    cmake = (target / "CMakeLists.txt").read_text(encoding="utf-8")
    assert "target_sources(RprEntityProbe PRIVATE model_wire.cpp)" in cmake
    for proto in ("entity.proto", "platform.proto", "spatial.proto"):
        assert f"proto/rpr/v2/{proto}" in cmake
    assert "protobuf::libprotobuf" in cmake
    assert "IMPORT_ROOTS" in cmake


def test_wire_json_carries_the_entity_message(tmp_path):
    target = generate_model(make_model(), tmp_path / "gen", serialization="rpr")
    payload = json.loads((target / "wire.json").read_text(encoding="utf-8"))

    assert payload["format"] == "rpr"
    assert payload["format_id"] == 1
    assert payload["payload_message"] == "PhysicalEntity"
    assert payload["proto_package"] == "rpr.v2"
    assert payload["format_version"] == RprSerialization.format_version


def test_format_id_and_frame_mode_are_pinned():
    # The wire envelope's payload_format is a closed set (0, 1, 2); rpr is a
    # protobuf payload, so 1 is the only coherent tag.
    assert RprSerialization.format_id == 1
    assert RprSerialization.format_version == 1
    assert RprSerialization.frame_mode == "identity"


def test_a_signal_outside_the_schema_is_an_error(tmp_path):
    with pytest.raises(ProjectionError, match="not part of the rpr.v2.PhysicalEntity shape"):
        generate_model(make_model(extra=True), tmp_path / "gen", serialization="rpr")


def test_a_wrong_data_type_is_an_error(tmp_path):
    with pytest.raises(ProjectionError, match="declares integer"):
        generate_model(
            make_model(frozen_type=DataType.INTEGER), tmp_path / "gen", serialization="rpr"
        )


def test_importing_the_projection_does_not_register_as_a_side_effect():
    script = (
        "import pysos_rpr.projection\n"
        "from pyfmi_interop.serialization import names\n"
        "assert 'rpr' not in names(), names()\n"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_schema_paths_are_all_resolvable():
    # Every published leaf resolves against the proto, so the codec never has
    # to guess whether a base-entity path carries its ``base`` wrapper.
    from pysos_rpr.projection.fmi import _resolve_path

    for flat, path in SCHEMA_PATHS.items():
        chain = _resolve_path(path)
        assert chain, flat


def test_exact_frame_mode_refuses_instead_of_approximating():
    # The frame maths does not exist yet; the reserved mode must raise rather
    # than pass unconverted values under a truthy name.
    from pysos_rpr.projection.fmi import resolve_frame_mode

    assert resolve_frame_mode("identity") == "identity"
    with pytest.raises(NotImplementedError):
        resolve_frame_mode("exact")
    with pytest.raises(ValueError):
        resolve_frame_mode("angular")
