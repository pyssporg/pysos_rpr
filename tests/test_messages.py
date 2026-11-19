"""Tests for the public reference codec and constructors.

The unknown-field tests pin the policy stated in the README: strict decoding
rejects unknown fields, non-strict decoding preserves them, and re-encoding a
message decoded non-strictly reproduces the original bytes for payloads
produced by ``encode``.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from google.protobuf.message import DecodeError

from pysos_rpr import messages as m

FIXTURES = Path(__file__).parent / "fixtures"
SRC = Path(__file__).resolve().parents[1] / "src"
AIRCRAFT_HASH = "6c54b39adb9bebf6223a09e459fcc2654f2500e5f4e37e3b533474124a884818"
# Field 50, wire type 0 (varint), value 1: a field the schema does not define.
UNKNOWN_FIELD = b"\x90\x03\x01"


def _identifier() -> m.EntityIdentifier:
    return m.entity_identifier(site=1, application=2, entity=1001)


def _entity_type() -> m.EntityType:
    return m.entity_type(kind=1, domain=2, country=840, category=1, subcategory=1)


def _base() -> m.BaseEntity:
    return m.base_entity(
        entity_identifier=_identifier(),
        entity_type=_entity_type(),
        force="FORCE_FRIENDLY",
        marking=m.marking("VIPER-01"),
    )


def _spatial() -> m.Spatial:
    return m.spatial_ecef(
        x=4533212.5,
        y=611234.25,
        z=4482341.75,
        psi=0.7853982,
        theta=-0.0523599,
        phi=0.0174533,
        vx=220.5,
        vz=-1.25,
        ax=0.5,
        az=9.75,
        wx=0.01,
        wy=-0.02,
        wz=0.03,
        algorithm="DR_ALGORITHM_FVB",
        parameters=b"\0" * 15,
    )


def _samples() -> dict[str, object]:
    base = _base()
    spatial = _spatial()
    physical = m.physical_entity(base=base, spatial=spatial)
    platform = m.platform(physical=physical, kind="PLATFORM_FIXED_WING")
    return {
        "EntityIdentifier": base.entity_identifier,
        "EntityType": base.entity_type,
        "Marking": base.marking,
        "BaseEntity": base,
        "PhysicalEntity": physical,
        "WorldLocation": spatial.world_location,
        "Orientation": spatial.orientation,
        "Velocity": spatial.velocity,
        "Acceleration": spatial.acceleration,
        "AngularVelocity": spatial.angular_velocity,
        "DeadReckoningParameters": spatial.dead_reckoning,
        "Spatial": spatial,
        "Platform": platform,
        "Aircraft": m.aircraft(platform=platform),
    }


SAMPLES = _samples()


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_message_registry_covers_every_subset_type():
    assert set(m.MESSAGE_TYPES) == set(SAMPLES)


def test_public_names_are_exported():
    for name in m.__all__:
        assert hasattr(m, name), name


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_encode_decode_round_trip(name):
    cls = m.MESSAGE_TYPES[name]
    message = SAMPLES[name]
    payload = m.encode(message)
    decoded = m.decode(cls, payload)
    assert decoded == message
    assert m.encode(decoded) == payload


def test_encode_is_deterministic_across_repeated_calls():
    message = SAMPLES["Aircraft"]
    first = m.encode(message)
    assert all(m.encode(message) == first for _ in range(5))


def test_encode_rejects_non_message():
    with pytest.raises(TypeError):
        m.encode(object())


def test_decode_rejects_malformed_payload_with_typed_error():
    with pytest.raises(m.RprMalformedPayloadError) as caught:
        m.decode(m.BaseEntity, b"\x08")
    assert isinstance(caught.value, m.RprDecodeError)
    assert not isinstance(caught.value, DecodeError)


def test_decode_rejects_non_message_class():
    with pytest.raises(TypeError):
        m.decode(dict, b"")


def test_strict_decode_rejects_unknown_fields():
    payload = m.encode(_base()) + UNKNOWN_FIELD
    with pytest.raises(m.RprUnknownFieldError):
        m.decode(m.BaseEntity, payload)


def test_non_strict_decode_preserves_unknown_fields_byte_for_byte():
    payload = m.encode(_base()) + UNKNOWN_FIELD
    decoded = m.decode(m.BaseEntity, payload, strict=False)
    assert m.encode(decoded) == payload
    assert m.validate(decoded) == []


def test_constructors_require_identity_and_force():
    with pytest.raises(TypeError):
        m.entity_identifier()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        m.entity_identifier(site=1, application=2)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        m.base_entity(entity_type=_entity_type(), force=1)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        m.base_entity(  # type: ignore[call-arg]
            entity_identifier=_identifier(), entity_type=_entity_type()
        )
    with pytest.raises(TypeError):
        m.aircraft_entity(  # type: ignore[call-arg]
            entity_identifier=_identifier(),
            entity_type=_entity_type(),
            spatial=_spatial(),
        )


def test_enum_arguments_accept_names_and_numbers():
    by_name = m.dead_reckoning(algorithm="DR_ALGORITHM_FVB")
    by_number = m.dead_reckoning(algorithm=m.DeadReckoningAlgorithm.Value("DR_ALGORITHM_FVB"))
    assert by_name == by_number
    fixed_wing = m.platform(
        physical=m.physical_entity(base=_base()), kind="PLATFORM_FIXED_WING"
    )
    assert fixed_wing.kind == 1
    assert m.platform(physical=m.physical_entity(base=_base()), kind=2).kind == 2
    with pytest.raises(ValueError):
        m.dead_reckoning(algorithm="DR_ALGORITHM_NOPE")


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_validate_accepts_valid_messages(name):
    assert m.validate(SAMPLES[name]) == []


def test_validate_rejects_identity_and_type_ranges():
    errors = m.validate(
        m.EntityIdentifier(site=70000, application=2, entity=3)
    )
    assert any("site" in error and "65535" in error for error in errors)

    errors = m.validate(
        m.EntityType(kind=256, domain=2, country=70000, category=1)
    )
    assert any("kind" in error and "255" in error for error in errors)
    assert any("country" in error and "65535" in error for error in errors)


def test_validate_rejects_bad_marking():
    assert m.validate(m.marking("ABCDEFGHIJKL")) != []
    assert m.validate(m.marking("BAD\nLABEL")) != []
    assert m.validate(m.marking("")) == []
    assert m.validate(m.marking("ABCDEFGHIJK")) == []


def test_validate_rejects_enum_values_outside_the_schema():
    base = m.BaseEntity(entity_identifier=_identifier(), force=4)
    assert any("force" in error for error in m.validate(base))

    dead_reckoning = m.DeadReckoningParameters(algorithm=10)
    assert any("algorithm" in error for error in m.validate(dead_reckoning))

    platform = m.Platform(physical=m.physical_entity(base=_base()), kind=8)
    assert any("kind" in error for error in m.validate(platform))


def test_validate_rejects_non_finite_spatial_values():
    location = m.WorldLocation(x=float("nan"), y=0.0, z=0.0)
    assert any("x" in error and "finite" in error for error in m.validate(location))

    velocity = m.Velocity(x=float("inf"))
    assert any("x" in error and "finite" in error for error in m.validate(velocity))


def test_validate_rejects_wrong_dead_reckoning_parameter_length():
    assert m.validate(m.dead_reckoning(algorithm=2, parameters=b"\0" * 15)) == []
    assert m.validate(m.dead_reckoning(algorithm=2, parameters=b"")) == []
    errors = m.validate(m.dead_reckoning(algorithm=2, parameters=b"\0" * 14))
    assert any("parameters" in error and "15" in error for error in errors)


def test_validate_rejects_missing_required_submessages():
    assert any("entity_identifier" in error for error in m.validate(m.BaseEntity()))
    assert any("base" in error for error in m.validate(m.PhysicalEntity()))
    assert any("world_location" in error for error in m.validate(m.Spatial()))
    assert any("physical" in error for error in m.validate(m.Platform()))
    assert any("platform" in error for error in m.validate(m.Aircraft()))


def test_validate_reports_nested_paths():
    bad_identifier = m.entity_identifier(site=70000, application=2, entity=3)
    aircraft = m.aircraft_entity(
        entity_identifier=bad_identifier,
        entity_type=_entity_type(),
        force=1,
        spatial=_spatial(),
    )
    errors = m.validate(aircraft)
    assert errors == [
        "platform.physical.base.entity_identifier.site: 70000 exceeds 65535"
    ]


@pytest.mark.parametrize(
    ("fixture", "cls"),
    [("aircraft.proto.json", m.Aircraft), ("base_entity.proto.json", m.BaseEntity)],
)
def test_json_round_trip_fixtures(fixture, cls):
    data = _load(fixture)
    message = m.from_dict(cls, data)
    assert m.to_dict(message) == data
    assert m.from_dict(cls, m.to_dict(message)) == message
    assert m.decode(cls, m.encode(message)) == message


def test_from_dict_wraps_parse_errors():
    with pytest.raises(m.RprMalformedPayloadError):
        m.from_dict(m.EntityIdentifier, {"site": "not-a-number"})


def test_aircraft_fixture_hash_is_process_independent():
    message = m.from_dict(m.Aircraft, _load("aircraft.proto.json"))
    assert hashlib.sha256(m.encode(message)).hexdigest() == AIRCRAFT_HASH

    script = (
        "import hashlib, json, pathlib\n"
        "from pysos_rpr import messages as m\n"
        f"data = json.loads(pathlib.Path({str(FIXTURES / 'aircraft.proto.json')!r})"
        ".read_text(encoding='utf-8'))\n"
        "message = m.from_dict(m.Aircraft, data)\n"
        "print(hashlib.sha256(m.encode(message)).hexdigest())\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.stdout.strip() == AIRCRAFT_HASH
