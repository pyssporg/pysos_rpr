# RPR mapping

This document maps every field in `proto/rpr/v2/` to the RPR FOM attribute it is
derived from and, where one exists, the DIS IEEE 1278.1 field it corresponds to.

## What "RPR-derived, not conformant" excludes

The vocabulary borrows RPR names, field meanings and enumeration values. It is
not a conformance claim, and the following are explicitly outside it:

- **No RTI and no HLA services.** There is no federation management, declaration
  management, object management, ownership management, time management, data
  distribution management, or join/resign lifecycle.
- **No FOM module or HLA object model.** There is no FOM XML file, no object
  model discovery, and no HLA object or attribute handles. `proto/rpr/v2/` is
  the only schema artifact.
- **No HLA encoding rules and no transport.** Messages serialize with the
  deterministic protobuf wire format. Nothing here promises an HLA-conformant
  encoding, a DIS PDU layout, or a transport.
- **No shared field-number namespace with RPR or DIS.** The numbers in the
  proto files are `pysos_rpr` contract numbers. The RPR attribute names and the
  DIS field names in the tables below describe semantics, not wire offsets.
- **No interoperability claim beyond the vocabulary.** A conformant RPR
  federate or a DIS encoder needs a projection to and from these messages. This
  package does not supply that projection.
- **Not a scenario format and not the in-process model.** Entity catalogues and
  `pysos_interop.EntityState` stay outside this repository.

## Spatial and value conventions

- **Position** (`WorldLocation.x/y/z`) is geocentric ECEF in metres, stored as
  `double`, matching the DIS 64-bit Entity Location.
- **Linear velocity and acceleration** (`Velocity`, `Acceleration`) are in the
  entity body frame, in m/s and m/s², stored as `float`.
- **Orientation** (`Orientation.psi/theta/phi`) is Euler yaw/pitch/roll in
  radians, stored as `float`.
- **Angular velocity** (`AngularVelocity.x/y/z`) is in the entity body frame,
  in rad/s, stored as `float`.
- **Entity identifiers** are the RPR/DIS `(site, application, entity)` triple.
  They are `uint32` because proto3 has no 16-bit scalar; valid values are
  0..65535.
- **Entity type octets** are `uint32`; valid ranges are the DIS ranges (Kind,
  Domain, Category, Subcategory, Specific, Extra 0..255; Country 0..65535).
- **Marking** is printable text bounded to 11 octets, matching DIS. Proto3 has
  no fixed-length string; the bound is a contract, not a type constraint.
- **Force is an enum, not a message.** The set is closed and small, and no
  value carries a payload, so a message would only add a wrapper. Value 0 is
  `FORCE_OTHER`, a real value, not an "unset" marker, matching DIS ForceID 0.
- **Field numbers are frozen.** Every message reserves `1000 to 1999` as a
  never-use block and names that would duplicate an existing field. Additive
  fields take new numbers outside the block. Every enum reserves a never-use
  value range and names; additive enumeration values start at 100.
- **No `map` fields.** Ordering and future additive evolution stay explicit.
- `Spatial.world_location` is the dead-reckoning reference point. The rates
  needed by the algorithm live on `Spatial.acceleration` and
  `Spatial.angular_velocity`; `DeadReckoningParameters` does not duplicate them.

## Field mapping

| RPR attribute | Proto message.field | DIS 1278.1 field |
| --- | --- | --- |
| `EntityIdentifier.SiteID` | `EntityIdentifier.site` | `EntityID.Site` |
| `EntityIdentifier.ApplicationID` | `EntityIdentifier.application` | `EntityID.Application` |
| `EntityIdentifier.EntityNumber` | `EntityIdentifier.entity` | `EntityID.Entity` |
| `EntityType.Kind` | `EntityType.kind` | `EntityType.Kind` |
| `EntityType.Domain` | `EntityType.domain` | `EntityType.Domain` |
| `EntityType.Country` | `EntityType.country` | `EntityType.Country` |
| `EntityType.Category` | `EntityType.category` | `EntityType.Category` |
| `EntityType.Subcategory` | `EntityType.subcategory` | `EntityType.Subcategory` |
| `EntityType.Specific` | `EntityType.specific` | `EntityType.Specific` |
| `EntityType.Extra` | `EntityType.extra` | `EntityType.Extra` |
| `Marking.CharacterSet` | `Marking.character_set` | `Marking.CharacterSet` |
| `Marking.Characters` | `Marking.characters` | `Marking.Characters` |
| `BaseEntity.EntityIdentifier` | `BaseEntity.entity_identifier` | Entity State PDU `EntityID` |
| `BaseEntity.EntityType` | `BaseEntity.entity_type` | Entity State PDU `EntityType` |
| `BaseEntity.Marking` | `BaseEntity.marking` | Entity State PDU `Marking` |
| `BaseEntity.Force` | `BaseEntity.force` | Entity State PDU `ForceID` |
| `PhysicalEntity` inherited `BaseEntity` attributes | `PhysicalEntity.base` | Entity State PDU identity/type/marking/force |
| `PhysicalEntity.Spatial` | `PhysicalEntity.spatial` | Entity State PDU spatial fields |
| `Spatial.WorldLocation.X` | `WorldLocation.x` | `Entity Location.X` |
| `Spatial.WorldLocation.Y` | `WorldLocation.y` | `Entity Location.Y` |
| `Spatial.WorldLocation.Z` | `WorldLocation.z` | `Entity Location.Z` |
| `Spatial.Orientation.Psi` | `Orientation.psi` | `Entity Orientation.Psi` |
| `Spatial.Orientation.Theta` | `Orientation.theta` | `Entity Orientation.Theta` |
| `Spatial.Orientation.Phi` | `Orientation.phi` | `Entity Orientation.Phi` |
| `Spatial.Velocity.X` | `Velocity.x` | `Entity Linear Velocity.X` |
| `Spatial.Velocity.Y` | `Velocity.y` | `Entity Linear Velocity.Y` |
| `Spatial.Velocity.Z` | `Velocity.z` | `Entity Linear Velocity.Z` |
| `Spatial.Acceleration.X` | `Acceleration.x` | `Entity Linear Acceleration.X` |
| `Spatial.Acceleration.Y` | `Acceleration.y` | `Entity Linear Acceleration.Y` |
| `Spatial.Acceleration.Z` | `Acceleration.z` | `Entity Linear Acceleration.Z` |
| `Spatial.AngularVelocity.X` | `AngularVelocity.x` | `Entity Angular Velocity.X` |
| `Spatial.AngularVelocity.Y` | `AngularVelocity.y` | `Entity Angular Velocity.Y` |
| `Spatial.AngularVelocity.Z` | `AngularVelocity.z` | `Entity Angular Velocity.Z` |
| `Spatial.DeadReckoningParameters.Algorithm` | `DeadReckoningParameters.algorithm` | `Dead Reckoning Algorithm` |
| `Spatial.DeadReckoningParameters.Parameters` | `DeadReckoningParameters.parameters` | `Dead Reckoning Parameters` (15 octets) |
| `Spatial.WorldLocation` | `Spatial.world_location` | `Entity Location` (dead-reckoning reference point) |
| `Spatial.IsFrozen` | `Spatial.is_frozen` | n/a |
| `Spatial.Orientation` | `Spatial.orientation` | `Entity Orientation` |
| `Spatial.Velocity` | `Spatial.velocity` | `Entity Linear Velocity` |
| `Spatial.Acceleration` | `Spatial.acceleration` | `Entity Linear Acceleration` |
| `Spatial.AngularVelocity` | `Spatial.angular_velocity` | `Entity Angular Velocity` |
| `Spatial.DeadReckoningParameters` | `Spatial.dead_reckoning` | `Dead Reckoning Parameters` |
| `PhysicalEntity` inherited attributes | `Platform.physical` | n/a (composition) |
| `Platform`/`Aircraft` class | `Platform.kind` | n/a (derived from `EntityType.Kind`/`Domain`/`Category`) |
| `Platform` inherited attributes | `Aircraft.platform` | n/a (composition) |

## Enumerations

### `Force`

| RPR value | Proto value | DIS 1278.1 `ForceID` |
| --- | --- | --- |
| `Force.Other` | `FORCE_OTHER` | 0 |
| `Force.Friendly` | `FORCE_FRIENDLY` | 1 |
| `Force.Opposing` | `FORCE_OPPOSING` | 2 |
| `Force.Neutral` | `FORCE_NEUTRAL` | 3 |

### `DeadReckoningAlgorithm`

The DIS triple is fixed/rotating, position/velocity, world/body.

| RPR value | Proto value | DIS 1278.1 value |
| --- | --- | --- |
| `DeadReckoningAlgorithm.Other` | `DR_ALGORITHM_OTHER` | 0 |
| `DeadReckoningAlgorithm.Static` | `DR_ALGORITHM_STATIC` | 1 |
| `DeadReckoningAlgorithm.Fpw` | `DR_ALGORITHM_FPW` | 2 |
| `DeadReckoningAlgorithm.Fvw` | `DR_ALGORITHM_FVW` | 3 |
| `DeadReckoningAlgorithm.Fpb` | `DR_ALGORITHM_FPB` | 4 |
| `DeadReckoningAlgorithm.Fvb` | `DR_ALGORITHM_FVB` | 5 |
| `DeadReckoningAlgorithm.Rpw` | `DR_ALGORITHM_RPW` | 6 |
| `DeadReckoningAlgorithm.Rvw` | `DR_ALGORITHM_RVW` | 7 |
| `DeadReckoningAlgorithm.Rpb` | `DR_ALGORITHM_RPB` | 8 |
| `DeadReckoningAlgorithm.Rvb` | `DR_ALGORITHM_RVB` | 9 |

### `PlatformKind`

RPR has no single "platform kind" attribute; the values are derived from the
`Platform`/`Aircraft` object classes and the DIS `EntityType` fields.

| Proto value | RPR object class | DIS 1278.1 `EntityType` |
| --- | --- | --- |
| `PLATFORM_KIND_UNKNOWN` | n/a | n/a |
| `PLATFORM_FIXED_WING` | `Aircraft` | Kind 1, Domain 2 |
| `PLATFORM_ROTARY_WING` | `Aircraft` | Kind 1, Domain 2 |
| `PLATFORM_UNMANNED_AIRCRAFT` | `Aircraft` | Kind 1, Domain 2 |
| `PLATFORM_SPACECRAFT` | `Spacecraft` | Kind 1, Domain 4 |
| `PLATFORM_SURFACE_VESSEL` | `Surface` | Kind 1, Domain 3 |
| `PLATFORM_SUBMERSIBLE` | `Submersible` | Kind 1, Domain 3 |
| `PLATFORM_GROUND_VEHICLE` | `Ground` | Kind 1, Domain 1 |

## Generated bindings

The Python bindings are generated from the proto sources and committed, so
tests and consumers do not need `protoc` at runtime. From the repository root:

```bash
python -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=src/pysos_rpr/_proto \
  proto/rpr/v2/entity.proto proto/rpr/v2/spatial.proto proto/rpr/v2/platform.proto
```

`tools/generate_bindings.sh` runs exactly that command. The generated modules
live under `src/pysos_rpr/_proto/rpr/v2/` and are re-exported by
`pysos_rpr._proto`; they are never edited by hand. The `protobuf` runtime is a
package dependency, and `grpcio-tools` is a development dependency used only to
regenerate the bindings.

The golden encoding test in `tests/test_vocabulary.py` pins one representative
`Aircraft` message to exact bytes. Because protobuf wire tags derive from field
numbers, changing any field number changes the golden hex and fails the test.
