"""Generate, build, package and decode the RPR entity adapter end to end."""

from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("pyfmi_interop")
pytest.importorskip("pycps_sysml2")
pytest.importorskip("pyfmi_sysml")

from pyfmi_interop.builder import resolve_runtime_include  # noqa: E402
from pyfmi_interop.packaging import platform_binary_dir  # noqa: E402
from pyfmi_interop.serialization.naming import float_literal, identifier  # noqa: E402
from pyfmi_interop.wire import decode as decode_frame  # noqa: E402

from pysos_rpr import messages  # noqa: E402
from pysos_rpr.projection import generate_entity_adapter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SYSML = ROOT / "sysml" / "rpr_entity.sysml"

_CMAKE = shutil.which("cmake")
_CXX = shutil.which("g++") or shutil.which("c++")
_PROTOC = shutil.which("protoc")

pytestmark = [
    pytest.mark.skipif(_CMAKE is None, reason="cmake is not available"),
    pytest.mark.skipif(_CXX is None, reason="no C++ compiler is available"),
    pytest.mark.skipif(_PROTOC is None, reason="protoc is not available"),
]

VALUES = {
    "entity_identifier_site": 7,
    "entity_identifier_application": 3,
    "entity_identifier_entity": 42,
    "entity_type_kind": 1,
    "entity_type_domain": 2,
    "entity_type_country": 752,
    "entity_type_category": 3,
    "entity_type_subcategory": 4,
    "entity_type_specific": 5,
    "entity_type_extra": 6,
    "marking_character_set": 1,
    "marking_characters": "ALPHA",
    "force": 1,
    "spatial_world_location_x": 1000.5,
    "spatial_world_location_y": 2000.25,
    "spatial_world_location_z": 3000.125,
    "spatial_orientation_psi": 0.5,
    "spatial_orientation_theta": 0.25,
    "spatial_orientation_phi": 0.125,
    "spatial_velocity_x": 10.0,
    "spatial_velocity_y": 20.0,
    "spatial_velocity_z": 30.0,
    "spatial_acceleration_x": 1.0,
    "spatial_acceleration_y": 2.0,
    "spatial_acceleration_z": 3.0,
    "spatial_angular_velocity_x": 0.1,
    "spatial_angular_velocity_y": 0.2,
    "spatial_angular_velocity_z": 0.3,
    "spatial_dead_reckoning_algorithm": 2,
    "spatial_is_frozen": True,
}


def _probe_source(model: dict) -> str:
    assignments = []
    for signal in model["signals"]:
        flat = signal["name"].rsplit(".", 1)[-1]
        member = f"m_vr{signal['value_reference']}_{identifier(signal['name'])}"
        value = VALUES[flat]
        if signal["data_type"] == "integer":
            expression = str(value)
        elif signal["data_type"] == "real":
            expression = float_literal(float(value))
        elif signal["data_type"] == "boolean":
            expression = "true" if value else "false"
        else:
            expression = f'"{value}"'
        if signal["data_type"] == "string":
            assignments.append(
                f"    copy_bounded(model.{member}.data(), model.{member}.size(), "
                f"{expression});"
            )
        else:
            assignments.append(f"    model.{member} = {expression};")
    body = "\n".join(assignments)
    return f"""#include "model_runtime.hpp"
#include <cstdio>
#include <string>
#include <vector>
int main() {{
    GeneratedModelRuntime model;
{body}
    std::string error;
    const std::vector<std::uint8_t> frame = model.encode_wire_frame(1u, 1u, 0u, error);
    if (!error.empty() || frame.empty()) {{
        std::fprintf(stderr, "%s\\n", error.c_str());
        return 1;
    }}
    for (const std::uint8_t byte : frame) {{
        std::printf("%02x", byte);
    }}
    std::printf("\\n");
    return 0;
}}
"""


def test_identity_projection_end_to_end(tmp_path):
    fmu = generate_entity_adapter(SYSML, tmp_path)

    assert fmu.is_file()
    assert fmu.suffix == ".fmu"
    assert fmu.stat().st_size > 0

    model_dir = tmp_path / "model"
    build_dir = tmp_path / "build"
    model = json.loads((model_dir / "model.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(fmu) as archive:
        projection = json.loads(archive.read("resources/rpr_projection.json"))
        wire = json.loads(archive.read(f"binaries/{platform_binary_dir()}/wire.json"))
        names = set(archive.namelist())

    assert projection == {
        "frame_mode": "identity",
        "entity_message": "rpr.v2.PhysicalEntity",
        "omitted_bytes": ["spatial.dead_reckoning.parameters"],
        "note": "identity mode is an interop stand-in, not RPR conformance",
    }
    assert wire["payload_message"] == "PhysicalEntity"
    assert wire["proto_package"] == "rpr.v2"
    assert wire["format_id"] == 1
    for proto in ("entity.proto", "platform.proto", "spatial.proto"):
        assert f"binaries/{platform_binary_dir()}/proto/rpr/v2/{proto}" in names

    probe = tmp_path / "probe.cpp"
    probe.write_text(_probe_source(model), encoding="utf-8")
    binary = tmp_path / "probe"
    subprocess.run(
        [
            _CXX,
            "-std=c++17",
            str(probe),
            "-I",
            str(model_dir),
            "-I",
            str(resolve_runtime_include()),
            "-L",
            str(build_dir),
            f"-l{model['name']}",
            f"-Wl,-rpath,{build_dir}",
            "-lprotobuf",
            "-o",
            str(binary),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    frame = bytes.fromhex(
        subprocess.run(
            [str(binary)], check=True, capture_output=True, text=True
        ).stdout.strip()
    )

    decoded = decode_frame(frame)
    assert decoded.header.payload_format == 1
    entity = messages.decode(messages.PhysicalEntity, decoded.payload)
    assert messages.validate(entity) == []

    assert entity.base.entity_identifier.site == 7
    assert entity.base.entity_identifier.application == 3
    assert entity.base.entity_identifier.entity == 42
    assert entity.base.entity_type.country == 752
    assert entity.base.marking.characters == "ALPHA"
    assert entity.base.force == messages.Force.FORCE_FRIENDLY

    assert entity.spatial.world_location.x == pytest.approx(1000.5)
    assert entity.spatial.world_location.y == pytest.approx(2000.25)
    assert entity.spatial.world_location.z == pytest.approx(3000.125)

    # Identity mode is a pure reorder over the vocabulary's psi/theta/phi
    # fields: no frame maths, and distinct inputs stay distinct outputs.
    assert entity.spatial.orientation.psi == pytest.approx(0.5)
    assert entity.spatial.orientation.theta == pytest.approx(0.25)
    assert entity.spatial.orientation.phi == pytest.approx(0.125)

    assert entity.spatial.velocity.x == pytest.approx(10.0)
    assert entity.spatial.velocity.y == pytest.approx(20.0)
    assert entity.spatial.velocity.z == pytest.approx(30.0)
    assert entity.spatial.acceleration.x == pytest.approx(1.0)
    assert entity.spatial.angular_velocity.z == pytest.approx(0.3)
    assert entity.spatial.dead_reckoning.algorithm == (
        messages.DeadReckoningAlgorithm.DR_ALGORITHM_FPW
    )
    assert entity.spatial.dead_reckoning.parameters == b""
    assert entity.spatial.is_frozen is True
