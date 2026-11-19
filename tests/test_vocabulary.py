"""Schema contract tests.

These tests pin the published contract, not just round-trip agreement:

* field numbers and enum values are frozen;
* every message and enum declares a reserved never-use block and names;
* reserved numbers and names are not reused;
* no message contains a protobuf ``map``;
* one representative ``Aircraft`` serializes to exact, deterministic bytes.

The golden hex changes whenever a field number changes, because protobuf wire
tags are derived from field numbers; it also changes if a value or type changes.
That is the point: the encoding is the contract.
"""

from __future__ import annotations

import json
from pathlib import Path

from google.protobuf import descriptor_pb2

from pysos_rpr._proto import entity_pb2, platform_pb2, spatial_pb2

FIXTURES = Path(__file__).parent / "fixtures"
MODULES = (entity_pb2, spatial_pb2, platform_pb2)

EXPECTED_FIELDS = {
    "rpr.v2.EntityIdentifier": {1: "site", 2: "application", 3: "entity"},
    "rpr.v2.EntityType": {
        1: "kind",
        2: "domain",
        3: "country",
        4: "category",
        5: "subcategory",
        6: "specific",
        7: "extra",
    },
    "rpr.v2.Marking": {1: "character_set", 2: "characters"},
    "rpr.v2.BaseEntity": {
        1: "entity_identifier",
        2: "entity_type",
        3: "marking",
        4: "force",
    },
    "rpr.v2.PhysicalEntity": {1: "base", 2: "spatial"},
    "rpr.v2.WorldLocation": {1: "x", 2: "y", 3: "z"},
    "rpr.v2.Orientation": {1: "psi", 2: "theta", 3: "phi"},
    "rpr.v2.Velocity": {1: "x", 2: "y", 3: "z"},
    "rpr.v2.Acceleration": {1: "x", 2: "y", 3: "z"},
    "rpr.v2.AngularVelocity": {1: "x", 2: "y", 3: "z"},
    "rpr.v2.DeadReckoningParameters": {1: "algorithm", 2: "parameters"},
    "rpr.v2.Spatial": {
        1: "world_location",
        2: "is_frozen",
        3: "orientation",
        4: "velocity",
        5: "acceleration",
        6: "angular_velocity",
        7: "dead_reckoning",
    },
    "rpr.v2.Platform": {1: "physical", 2: "kind"},
    "rpr.v2.Aircraft": {1: "platform"},
}

EXPECTED_ENUMS = {
    "rpr.v2.Force": {
        0: "FORCE_OTHER",
        1: "FORCE_FRIENDLY",
        2: "FORCE_OPPOSING",
        3: "FORCE_NEUTRAL",
    },
    "rpr.v2.DeadReckoningAlgorithm": {
        0: "DR_ALGORITHM_OTHER",
        1: "DR_ALGORITHM_STATIC",
        2: "DR_ALGORITHM_FPW",
        3: "DR_ALGORITHM_FVW",
        4: "DR_ALGORITHM_FPB",
        5: "DR_ALGORITHM_FVB",
        6: "DR_ALGORITHM_RPW",
        7: "DR_ALGORITHM_RVW",
        8: "DR_ALGORITHM_RPB",
        9: "DR_ALGORITHM_RVB",
    },
    "rpr.v2.PlatformKind": {
        0: "PLATFORM_KIND_UNKNOWN",
        1: "PLATFORM_FIXED_WING",
        2: "PLATFORM_ROTARY_WING",
        3: "PLATFORM_UNMANNED_AIRCRAFT",
        4: "PLATFORM_SPACECRAFT",
        5: "PLATFORM_SURFACE_VESSEL",
        6: "PLATFORM_SUBMERSIBLE",
        7: "PLATFORM_GROUND_VEHICLE",
    },
}

GOLDEN_HEX = (
    "0a9b010a96010a260a070801100218e907120b0801100218c806200128011a0c080112085649"
    "5045522d30312001126c0a1b0900000020f74a5141110000008044a7224119000000704919"
    "51411a0f0ddb0f493f15567756bd1d39fa8e3c220a0d00805c431d0000a0bf2a0a0d000000"
    "3f1d00001c41320f0d0ad7233c150ad7a3bc1d8fc2f53c3a130805120f0000000000000000"
    "000000000000001001"
)


def _file_descriptors():
    for module in MODULES:
        yield descriptor_pb2.FileDescriptorProto.FromString(
            module.DESCRIPTOR.serialized_pb
        )


def _messages(message):
    yield message
    for nested in message.nested_type:
        yield from _messages(nested)


def _full_name(package: str, message) -> str:
    return f"{package}.{message.name}"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _build_aircraft(data: dict) -> platform_pb2.Aircraft:
    spatial = data["spatial"]
    return platform_pb2.Aircraft(
        platform=platform_pb2.Platform(
            physical=entity_pb2.PhysicalEntity(
                base=entity_pb2.BaseEntity(
                    entity_identifier=entity_pb2.EntityIdentifier(
                        **data["entity_identifier"]
                    ),
                    entity_type=entity_pb2.EntityType(**data["entity_type"]),
                    marking=entity_pb2.Marking(**data["marking"]),
                    force=entity_pb2.Force.Value(data["force"]),
                ),
                spatial=spatial_pb2.Spatial(
                    world_location=spatial_pb2.WorldLocation(
                        **spatial["world_location"]
                    ),
                    is_frozen=spatial["is_frozen"],
                    orientation=spatial_pb2.Orientation(**spatial["orientation"]),
                    velocity=spatial_pb2.Velocity(**spatial["velocity"]),
                    acceleration=spatial_pb2.Acceleration(**spatial["acceleration"]),
                    angular_velocity=spatial_pb2.AngularVelocity(
                        **spatial["angular_velocity"]
                    ),
                    dead_reckoning=spatial_pb2.DeadReckoningParameters(
                        algorithm=spatial_pb2.DeadReckoningAlgorithm.Value(
                            spatial["dead_reckoning"]["algorithm"]
                        ),
                        parameters=bytes.fromhex(
                            spatial["dead_reckoning"]["parameters"]
                        ),
                    ),
                ),
            ),
            kind=platform_pb2.PlatformKind.Value(data["platform"]["kind"]),
        )
    )


def test_field_numbers_are_frozen():
    actual = {
        _full_name(fdp.package, message): {
            field.number: field.name for field in message.field
        }
        for fdp in _file_descriptors()
        for message in fdp.message_type
    }
    assert actual == EXPECTED_FIELDS


def test_enum_values_are_frozen():
    actual = {
        _full_name(fdp.package, enum): {value.number: value.name for value in enum.value}
        for fdp in _file_descriptors()
        for enum in fdp.enum_type
    }
    assert actual == EXPECTED_ENUMS


def test_no_map_fields():
    for fdp in _file_descriptors():
        for top in fdp.message_type:
            for message in _messages(top):
                # A map field is compiled into a nested message whose
                # map_entry option is set; checking every nested message
                # therefore rules out map fields anywhere in the file.
                assert not message.options.map_entry, message.name


def test_every_message_declares_reserved_ranges_and_names():
    for fdp in _file_descriptors():
        for message in fdp.message_type:
            assert message.reserved_range, message.name
            assert message.reserved_name, message.name


def test_reserved_numbers_and_names_are_unused():
    for fdp in _file_descriptors():
        for message in fdp.message_type:
            # DescriptorProto reserved ranges use an exclusive end.
            ranges = [(item.start, item.end) for item in message.reserved_range]
            for field in message.field:
                assert not any(
                    start <= field.number < end for start, end in ranges
                ), (message.name, field.name, field.number)
                assert field.name not in message.reserved_name


def test_every_enum_declares_reserved_ranges_and_names():
    for fdp in _file_descriptors():
        for enum in fdp.enum_type:
            assert enum.reserved_range, enum.name
            assert enum.reserved_name, enum.name


def test_enum_reserved_numbers_and_names_are_unused():
    for fdp in _file_descriptors():
        for enum in fdp.enum_type:
            # EnumReservedRange uses an inclusive end.
            ranges = [(item.start, item.end) for item in enum.reserved_range]
            for value in enum.value:
                assert not any(
                    start <= value.number <= end for start, end in ranges
                ), (enum.name, value.name, value.number)
                assert value.name not in enum.reserved_name


def test_golden_aircraft_encoding():
    aircraft = _build_aircraft(_load_fixture("aircraft.json"))
    assert aircraft.SerializeToString(deterministic=True).hex() == GOLDEN_HEX


def test_deterministic_encoding_is_stable():
    aircraft = _build_aircraft(_load_fixture("aircraft.json"))
    first = aircraft.SerializeToString(deterministic=True)
    assert first == aircraft.SerializeToString(deterministic=True)
    assert platform_pb2.Aircraft.FromString(first) == aircraft
