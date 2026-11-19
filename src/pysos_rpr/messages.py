"""Reference codec and constructors for the RPR-derived vocabulary.

This is the documented public module for consumers that want a stable Python
surface over the generated bindings in :mod:`pysos_rpr._proto`. It does not
redefine the schema: every constructor returns a generated protobuf message and
the wire format is owned by protobuf.

Unknown-field policy
--------------------
:func:`decode` rejects unknown fields by default (``strict=True``). Pass
``strict=False`` to preserve them: protobuf keeps the unknown bytes on the
message, so :func:`encode` emits them again. For payloads produced by
:func:`encode`, a non-strict decode followed by :func:`encode` is byte-identical.

The semantic rules implemented by :func:`validate` are listed in
``docs/rpr-mapping.md`` under "Semantic validation rules".
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, TypeVar

from google.protobuf import json_format
from google.protobuf.message import DecodeError, Message

from ._proto import entity_pb2, platform_pb2, spatial_pb2

# Re-export the generated schema so consumers have one import surface.
EntityIdentifier = entity_pb2.EntityIdentifier
EntityType = entity_pb2.EntityType
Marking = entity_pb2.Marking
BaseEntity = entity_pb2.BaseEntity
PhysicalEntity = entity_pb2.PhysicalEntity
Force = entity_pb2.Force

WorldLocation = spatial_pb2.WorldLocation
Orientation = spatial_pb2.Orientation
Velocity = spatial_pb2.Velocity
Acceleration = spatial_pb2.Acceleration
AngularVelocity = spatial_pb2.AngularVelocity
DeadReckoningParameters = spatial_pb2.DeadReckoningParameters
Spatial = spatial_pb2.Spatial
DeadReckoningAlgorithm = spatial_pb2.DeadReckoningAlgorithm

Platform = platform_pb2.Platform
Aircraft = platform_pb2.Aircraft
PlatformKind = platform_pb2.PlatformKind

MessageT = TypeVar("MessageT", bound=Message)


class RprDecodeError(ValueError):
    """Base class for payloads that cannot be decoded as a vocabulary message."""


class RprMalformedPayloadError(RprDecodeError):
    """The payload is not valid protobuf wire data for the requested type."""


class RprUnknownFieldError(RprDecodeError):
    """Strict decoding encountered fields absent from the schema."""


def encode(message: Message) -> bytes:
    """Serialize ``message`` deterministically.

    Field order is fixed by field number, so equal messages produce equal
    bytes across processes and across protobuf runs.
    """

    if not isinstance(message, Message):
        raise TypeError("encode() expects a protobuf message instance")
    try:
        return message.SerializeToString(deterministic=True)
    except TypeError:  # pragma: no cover - protobuf runtime without the keyword
        return message.SerializeToString()


def _has_unknown_fields(message: Message) -> bool:
    try:
        return bool(message.UnknownFields())
    except (AttributeError, NotImplementedError):
        # The upb backend does not implement UnknownFields(); removing the
        # unknown set and comparing encodings answers the same question.
        clone = type(message)()
        clone.CopyFrom(message)
        with_unknown = clone.SerializeToString(deterministic=True)
        clone.DiscardUnknownFields()
        return with_unknown != clone.SerializeToString(deterministic=True)


def decode(
    cls: type[MessageT],
    data: bytes | bytearray | memoryview,
    *,
    strict: bool = True,
) -> MessageT:
    """Decode ``data`` as ``cls``.

    ``strict=True`` rejects unknown fields with :class:`RprUnknownFieldError`.
    ``strict=False`` preserves them on the returned message, so re-encoding
    reproduces the original bytes. Malformed wire data raises
    :class:`RprMalformedPayloadError`; the protobuf ``DecodeError`` never
    escapes.
    """

    if not (isinstance(cls, type) and issubclass(cls, Message)):
        raise TypeError("decode() expects a generated protobuf message class")
    message = cls()
    try:
        message.ParseFromString(bytes(data))
    except DecodeError as exc:
        raise RprMalformedPayloadError(f"cannot decode {cls.__name__}: {exc}") from exc
    if strict and _has_unknown_fields(message):
        raise RprUnknownFieldError(
            f"{cls.__name__} contains unknown fields; pass strict=False to preserve them"
        )
    return message


def to_dict(message: Message) -> dict[str, Any]:
    """Render a message as protobuf JSON, keeping proto field names."""

    if not isinstance(message, Message):
        raise TypeError("to_dict() expects a protobuf message instance")
    return json_format.MessageToDict(message, preserving_proto_field_name=True)


def from_dict(cls: type[MessageT], data: Mapping[str, Any]) -> MessageT:
    """Build ``cls`` from protobuf JSON (the inverse of :func:`to_dict`)."""

    if not (isinstance(cls, type) and issubclass(cls, Message)):
        raise TypeError("from_dict() expects a generated protobuf message class")
    message = cls()
    try:
        json_format.ParseDict(dict(data), message)
    except (json_format.ParseError, TypeError, ValueError) as exc:
        raise RprMalformedPayloadError(f"cannot parse {cls.__name__} JSON: {exc}") from exc
    return message


# ---------------------------------------------------------------------------
# Constructors. Identity and force have no defaults: a caller cannot silently
# mint a message without them.
# ---------------------------------------------------------------------------


def entity_identifier(*, site: int, application: int, entity: int) -> EntityIdentifier:
    """Build the RPR/DIS ``(site, application, entity)`` identity triple."""

    return EntityIdentifier(site=site, application=application, entity=entity)


def entity_type(
    *,
    kind: int,
    domain: int,
    country: int,
    category: int = 0,
    subcategory: int = 0,
    specific: int = 0,
    extra: int = 0,
) -> EntityType:
    """Build a DIS entity-type record; the remaining octets default to zero."""

    return EntityType(
        kind=kind,
        domain=domain,
        country=country,
        category=category,
        subcategory=subcategory,
        specific=specific,
        extra=extra,
    )


def marking(characters: str, *, character_set: int = 1) -> Marking:
    """Build a human-readable marking (not identity)."""

    return Marking(character_set=character_set, characters=characters)


def base_entity(
    *,
    entity_identifier: EntityIdentifier,
    entity_type: EntityType,
    force: int | str,
    marking: Marking | None = None,
) -> BaseEntity:
    """Build the identity/type/marking/force attributes common to entities."""

    message = BaseEntity(
        entity_identifier=entity_identifier,
        entity_type=entity_type,
        force=_enum_value(Force, force, "force"),
    )
    if marking is not None:
        message.marking.CopyFrom(marking)
    return message


def world_location(*, x: float, y: float, z: float) -> WorldLocation:
    """Build a geocentric ECEF position in metres."""

    return WorldLocation(x=x, y=y, z=z)


def orientation(*, psi: float = 0.0, theta: float = 0.0, phi: float = 0.0) -> Orientation:
    """Build Euler yaw/pitch/roll in radians."""

    return Orientation(psi=psi, theta=theta, phi=phi)


def velocity(*, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Velocity:
    """Build body-frame linear velocity in metres per second."""

    return Velocity(x=x, y=y, z=z)


def acceleration(*, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Acceleration:
    """Build body-frame linear acceleration in metres per second squared."""

    return Acceleration(x=x, y=y, z=z)


def angular_velocity(*, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> AngularVelocity:
    """Build body-frame angular velocity in radians per second."""

    return AngularVelocity(x=x, y=y, z=z)


def dead_reckoning(
    *, algorithm: int | str, parameters: bytes = b""
) -> DeadReckoningParameters:
    """Build the algorithm selector and its 15-octet parameter block."""

    return DeadReckoningParameters(
        algorithm=_enum_value(DeadReckoningAlgorithm, algorithm, "algorithm"),
        parameters=parameters,
    )


def spatial(
    *,
    world_location: WorldLocation,
    orientation: Orientation | None = None,
    velocity: Velocity | None = None,
    acceleration: Acceleration | None = None,
    angular_velocity: AngularVelocity | None = None,
    dead_reckoning: DeadReckoningParameters | None = None,
    is_frozen: bool = False,
) -> Spatial:
    """Compose a spatial state from already-built components."""

    message = Spatial(world_location=world_location, is_frozen=is_frozen)
    components = (
        ("orientation", orientation),
        ("velocity", velocity),
        ("acceleration", acceleration),
        ("angular_velocity", angular_velocity),
        ("dead_reckoning", dead_reckoning),
    )
    for field, value in components:
        if value is not None:
            getattr(message, field).CopyFrom(value)
    return message


def spatial_ecef(
    *,
    x: float,
    y: float,
    z: float,
    psi: float = 0.0,
    theta: float = 0.0,
    phi: float = 0.0,
    vx: float = 0.0,
    vy: float = 0.0,
    vz: float = 0.0,
    ax: float = 0.0,
    ay: float = 0.0,
    az: float = 0.0,
    wx: float = 0.0,
    wy: float = 0.0,
    wz: float = 0.0,
    is_frozen: bool = False,
    algorithm: int | str | None = None,
    parameters: bytes = b"",
) -> Spatial:
    """Build a spatial state from flat ECEF/body-frame numbers.

    ``algorithm`` is optional; without it no dead-reckoning block is attached.
    """

    dead_reckoning_message = None
    if algorithm is not None:
        dead_reckoning_message = dead_reckoning(
            algorithm=algorithm, parameters=parameters
        )
    return spatial(
        world_location=world_location(x=x, y=y, z=z),
        orientation=orientation(psi=psi, theta=theta, phi=phi),
        velocity=velocity(x=vx, y=vy, z=vz),
        acceleration=acceleration(x=ax, y=ay, z=az),
        angular_velocity=angular_velocity(x=wx, y=wy, z=wz),
        dead_reckoning=dead_reckoning_message,
        is_frozen=is_frozen,
    )


def physical_entity(*, base: BaseEntity, spatial: Spatial | None = None) -> PhysicalEntity:
    """Compose a base entity with its optional spatial state."""

    message = PhysicalEntity(base=base)
    if spatial is not None:
        message.spatial.CopyFrom(spatial)
    return message


def entity_state(
    *,
    entity_identifier: EntityIdentifier,
    entity_type: EntityType,
    force: int | str,
    marking: Marking | None = None,
    spatial: Spatial | None = None,
) -> PhysicalEntity:
    """Build a complete ``PhysicalEntity`` from identity, force and state."""

    base = base_entity(
        entity_identifier=entity_identifier,
        entity_type=entity_type,
        force=force,
        marking=marking,
    )
    return physical_entity(base=base, spatial=spatial)


def platform(
    *, physical: PhysicalEntity, kind: int | str = PlatformKind.PLATFORM_KIND_UNKNOWN
) -> Platform:
    """Build a platform record around a physical entity."""

    return Platform(
        physical=physical,
        kind=_enum_value(PlatformKind, kind, "kind"),
    )


def aircraft(*, platform: Platform) -> Aircraft:
    """Wrap a platform as an aircraft."""

    return Aircraft(platform=platform)


def aircraft_entity(
    *,
    entity_identifier: EntityIdentifier,
    entity_type: EntityType,
    force: int | str,
    spatial: Spatial | None = None,
    kind: int | str = PlatformKind.PLATFORM_KIND_UNKNOWN,
    marking: Marking | None = None,
) -> Aircraft:
    """Build a complete ``Aircraft`` from identity, force and state."""

    state = entity_state(
        entity_identifier=entity_identifier,
        entity_type=entity_type,
        force=force,
        marking=marking,
        spatial=spatial,
    )
    return aircraft(platform=platform(physical=state, kind=kind))


def _enum_value(enum_type, value: int | str, field: str) -> int:
    if isinstance(value, str):
        try:
            return enum_type.Value(value)
        except ValueError as exc:
            raise ValueError(f"{field}: unknown enum name {value!r}") from exc
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise TypeError(f"{field}: expected an enum name or integer, got {type(value).__name__}")


# ---------------------------------------------------------------------------
# Semantic validation, derived from docs/rpr-mapping.md.
# ---------------------------------------------------------------------------

_UINT8_FIELDS = ("kind", "domain", "category", "subcategory", "specific", "extra")
_IDENTITY_FIELDS = ("site", "application", "entity")


def validate(message: Message) -> list[str]:
    """Return every semantic-rule violation for ``message``.

    The list is empty when the message satisfies the rules documented in
    ``docs/rpr-mapping.md``. Rules are checked recursively over composed
    messages.
    """

    if not isinstance(message, Message):
        raise TypeError("validate() expects a protobuf message instance")
    errors: list[str] = []
    _validate_message(message, "", errors)
    return errors


def _validate_message(message: Message, prefix: str, errors: list[str]) -> None:
    if isinstance(message, entity_pb2.EntityIdentifier):
        for field in _IDENTITY_FIELDS:
            _check_max(getattr(message, field), 65535, prefix + field, errors)
    elif isinstance(message, entity_pb2.EntityType):
        for field in _UINT8_FIELDS:
            _check_max(getattr(message, field), 255, prefix + field, errors)
        _check_max(message.country, 65535, prefix + "country", errors)
    elif isinstance(message, entity_pb2.Marking):
        encoded = message.characters.encode("utf-8")
        if len(encoded) > 11:
            errors.append(
                f"{prefix}characters: {len(encoded)} UTF-8 octets exceeds 11"
            )
        if not message.characters.isprintable():
            errors.append(f"{prefix}characters: must be printable text")
    elif isinstance(message, entity_pb2.BaseEntity):
        if not message.HasField("entity_identifier"):
            errors.append(f"{prefix}entity_identifier: required")
        else:
            _validate_message(
                message.entity_identifier, prefix + "entity_identifier.", errors
            )
        if message.HasField("entity_type"):
            _validate_message(message.entity_type, prefix + "entity_type.", errors)
        if message.HasField("marking"):
            _validate_message(message.marking, prefix + "marking.", errors)
        _check_enum(message.force, Force, prefix + "force", errors)
    elif isinstance(message, entity_pb2.PhysicalEntity):
        if not message.HasField("base"):
            errors.append(f"{prefix}base: required")
        else:
            _validate_message(message.base, prefix + "base.", errors)
        if message.HasField("spatial"):
            _validate_message(message.spatial, prefix + "spatial.", errors)
    elif isinstance(message, spatial_pb2.WorldLocation):
        for field in ("x", "y", "z"):
            _check_finite(getattr(message, field), prefix + field, errors)
    elif isinstance(message, spatial_pb2.Orientation):
        for field in ("psi", "theta", "phi"):
            _check_finite(getattr(message, field), prefix + field, errors)
    elif isinstance(message, spatial_pb2.Velocity):
        for field in ("x", "y", "z"):
            _check_finite(getattr(message, field), prefix + field, errors)
    elif isinstance(message, spatial_pb2.Acceleration):
        for field in ("x", "y", "z"):
            _check_finite(getattr(message, field), prefix + field, errors)
    elif isinstance(message, spatial_pb2.AngularVelocity):
        for field in ("x", "y", "z"):
            _check_finite(getattr(message, field), prefix + field, errors)
    elif isinstance(message, spatial_pb2.DeadReckoningParameters):
        _check_enum(
            message.algorithm,
            DeadReckoningAlgorithm,
            prefix + "algorithm",
            errors,
        )
        if message.parameters and len(message.parameters) != 15:
            errors.append(
                f"{prefix}parameters: {len(message.parameters)} octets, expected 15 or empty"
            )
    elif isinstance(message, spatial_pb2.Spatial):
        if not message.HasField("world_location"):
            errors.append(f"{prefix}world_location: required")
        else:
            _validate_message(
                message.world_location, prefix + "world_location.", errors
            )
        for field in ("orientation", "velocity", "acceleration", "angular_velocity"):
            if message.HasField(field):
                _validate_message(getattr(message, field), prefix + field + ".", errors)
        if message.HasField("dead_reckoning"):
            _validate_message(
                message.dead_reckoning, prefix + "dead_reckoning.", errors
            )
    elif isinstance(message, platform_pb2.Platform):
        if not message.HasField("physical"):
            errors.append(f"{prefix}physical: required")
        else:
            _validate_message(message.physical, prefix + "physical.", errors)
        _check_enum(message.kind, PlatformKind, prefix + "kind", errors)
    elif isinstance(message, platform_pb2.Aircraft):
        if not message.HasField("platform"):
            errors.append(f"{prefix}platform: required")
        else:
            _validate_message(message.platform, prefix + "platform.", errors)
    else:
        raise TypeError(f"validate() does not know {type(message).__name__}")


def _check_max(value: int, maximum: int, path: str, errors: list[str]) -> None:
    if value > maximum:
        errors.append(f"{path}: {value} exceeds {maximum}")


def _check_finite(value: float, path: str, errors: list[str]) -> None:
    if not math.isfinite(value):
        errors.append(f"{path}: must be finite")


def _check_enum(value: int, enum_type, path: str, errors: list[str]) -> None:
    if value not in enum_type.DESCRIPTOR.values_by_number:
        errors.append(f"{path}: {value} is not a defined {enum_type.DESCRIPTOR.name} value")


MESSAGE_TYPES: dict[str, type[Message]] = {
    "EntityIdentifier": EntityIdentifier,
    "EntityType": EntityType,
    "Marking": Marking,
    "BaseEntity": BaseEntity,
    "PhysicalEntity": PhysicalEntity,
    "WorldLocation": WorldLocation,
    "Orientation": Orientation,
    "Velocity": Velocity,
    "Acceleration": Acceleration,
    "AngularVelocity": AngularVelocity,
    "DeadReckoningParameters": DeadReckoningParameters,
    "Spatial": Spatial,
    "Platform": Platform,
    "Aircraft": Aircraft,
}

__all__ = [
    "Acceleration",
    "Aircraft",
    "AngularVelocity",
    "BaseEntity",
    "DeadReckoningAlgorithm",
    "DeadReckoningParameters",
    "EntityIdentifier",
    "EntityType",
    "Force",
    "MESSAGE_TYPES",
    "Marking",
    "Orientation",
    "PhysicalEntity",
    "Platform",
    "PlatformKind",
    "RprDecodeError",
    "RprMalformedPayloadError",
    "RprUnknownFieldError",
    "Spatial",
    "Velocity",
    "WorldLocation",
    "acceleration",
    "aircraft",
    "aircraft_entity",
    "angular_velocity",
    "base_entity",
    "dead_reckoning",
    "decode",
    "encode",
    "entity_identifier",
    "entity_state",
    "entity_type",
    "from_dict",
    "marking",
    "orientation",
    "physical_entity",
    "platform",
    "spatial",
    "spatial_ecef",
    "to_dict",
    "validate",
    "velocity",
    "world_location",
]
