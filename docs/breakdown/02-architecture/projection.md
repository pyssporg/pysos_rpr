---
id: INFO-003
type: info
title: FMI projection
summary: The flat schema table and the rpr FMI backend are generated from the proto; the SysML port is owned by pyfmi_rpr, and identity frames are an interop stand-in, not RPR conformance.
date: 2026-11-19
status: current
---

# FMI projection

The projection turns the vocabulary into a flat schema table and an `rpr`
FMI 2.0 payload backend. `tools/generate_schema_paths.py` reads the committed
`rpr.v2` descriptors; no field list is written by hand.

**Schema table.** `src/pysos_rpr/schema_paths.py` maps the flat port attribute
name to the dotted proto path and pins the proto type. The flat name is the
dotted path with `.` replaced by `_` (`spatial.world_location.x` ->
`spatial_world_location_x`); the mapping is not reversible because segments
already contain underscores, so this table is the authority. `bytes` fields
have no dialect representation: `spatial.dead_reckoning.parameters` is omitted
and the codec defaults it to empty.

**SysML port.** The `port def EntityState` built from this table is an
implementation asset of `pyfmi_rpr`, at
`repos/pyfmi_rpr/src/pyfmi_rpr/sysml/rpr_entity.sysml` and exposed as
`pyfmi_rpr.rpr_entity()`; that repository owns its attributes, metadata and
parameters. This package does not ship or generate it.

**Backend.** `RprSerialization` in `projection/fmi.py` is named `rpr`,
registered explicitly by `register()`; importing the module registers
nothing. It resolves paths against the committed `entity_pb2` descriptor and
reads proto sources from `proto/`. The payload is `rpr.v2.PhysicalEntity`;
`format_id` is `1`, the protobuf tag in the wire envelope's closed set (0
opaque, 1 protobuf, 2 packed), and `payload_message` (`PhysicalEntity`) and
`proto_package` (`rpr.v2`) distinguish the schema.

**Frames.** `frame_mode = "identity"` passes position, velocity, acceleration
and angular velocity through unconverted; orientation is a reorder over
`psi`/`theta`/`phi`. There is no origin shift, no ECEF conversion and no frame
maths: this is an interop stand-in, not RPR conformance. `"exact"` is reserved
and not implemented.

**Entry point.** `generate_entity_adapter()` lives in `composition/sysml.py`:
it loads the architecture, lowers it to a `ModelDefinition`, and generates,
builds and packages the FMU. The parser-free `projection/fmi.py` re-exports it
lazily, so `pysos_rpr.projection` keeps the entry point without importing
composition. Extras split too: `projection` pins `pyfmi-interop`,
`composition` adds `pyfmi-sysml`, and the base install stays `protobuf` only.

**Known gaps.**

- The proto tree is in the sdist but not the wheel, so the projection runs
  from a source checkout and raises `FileNotFoundError` without `proto/`.
- `model_id` hashes the wire interface (model name plus ordered value
  references and data types), not the RPR schema.
