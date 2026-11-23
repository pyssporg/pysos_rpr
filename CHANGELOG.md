# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Generated flat schema table for the entity state
  (`src/pysos_rpr/schema_paths.py`), flat because the dialect has no record
  type; `bytes` fields are omitted and defaulted empty.
- `pysos_rpr.projection`: an `rpr` serialization backend whose FMI payload is
  `rpr.v2.PhysicalEntity`, and `generate_entity_adapter()`.
- `frame_mode` is `identity`: values pass through unconverted and orientation is
  a pure reorder. `exact` is reserved and raises. Identity is an interop
  stand-in, not RPR conformance; it is recorded in the packaged
  `resources/rpr_projection.json`.
- `projection` optional extra (DEC-001: a projection may depend on the artifact
  implementer it targets).

### Changed

- Follow the RPR entity-state SysML asset to `pyfmi_rpr`'s packaged location
  (`src/pyfmi_rpr/sysml/rpr_entity.sysml`, exposed as `pyfmi_rpr.rpr_entity()`);
  the projection e2e test now fails instead of skipping when the asset is
  missing (2026-11-23).
- The RPR entity-state SysML port moved to `pyfmi_rpr`
  (`sysml/rpr_entity.sysml`); this package keeps the protobuf contract and the
  generated `schema_paths.py` table (2026-11-23).
- Import the SysML projection from `pyfmi_sysml` 0.2.0 and require
  `pyfmi-interop>=0.6.0`; `pyfmi_interop.sysml` and `pyfmi_sysml2` are gone
  (2026-11-22).
- Generate through `BuildConfig` and drop the retired `fmi_layer`/`sysml_source`
  options (2026-11-22).

## [0.1.0] - 2026-11-19

### Added

- Repository scaffold: hatchling package metadata with a dynamic version,
  `src/` layout, CI for Python 3.11, and the vocabulary intent record under
  `docs/breakdown/`.
- `pysos_rpr.__version__` and an explicit public surface.
- Package metadata tests: import, semver, and the pinned release version.
- RPR-derived v2 vocabulary under `proto/rpr/v2/`: entity identity, spatial
  state and dead reckoning, marking, force, and platform/aircraft class, split
  into `entity.proto`, `spatial.proto` and `platform.proto` with package
  `rpr.v2`.
- Committed Python bindings under `src/pysos_rpr/_proto/`, generated with
  `grpcio-tools`; `protoc` is not required at runtime.
- Schema contract tests: frozen field numbers and enum values, reserved ranges
  and names, no `map` fields, and a deterministic golden `Aircraft` encoding.
- `docs/rpr-mapping.md`: field-by-field RPR and DIS 1278.1 mapping, plus the
  statement of what "RPR-derived, not conformant" excludes.
- `pysos_rpr.messages`: the documented reference codec over the generated
  bindings, with deterministic `encode`, typed `decode`, `RprDecodeError`
  subclasses, and an explicit unknown-field policy.
- Ergonomic constructors for the whole subset (`entity_identifier`,
  `entity_type`, `marking`, `base_entity`, `spatial_ecef`, `entity_state`,
  `aircraft_entity`, and the component constructors). Identity and force are
  required; constructors return generated messages.
- `validate(message) -> list[str]` for the semantic rules now listed in
  `docs/rpr-mapping.md`, and `to_dict` / `from_dict` via protobuf JSON.
- Protobuf JSON fixtures `tests/fixtures/aircraft.proto.json` and
  `tests/fixtures/base_entity.proto.json`, plus codec, validation,
  unknown-field and cross-process determinism tests.

### Changed

- `pyproject.toml` now depends on `protobuf` at runtime and `grpcio-tools`
  under `[dev]`; ruff excludes the generated bindings.
- The sdist ships `proto/` and `tools/generate_bindings.sh`; the wheel ships
  the generated `_proto` bindings and does not require `docs/`.

### Release

- The `v0.1.0` tag was re-pointed from the scaffold commit `6d8aa37` to this
  release commit before any GitHub release or consumer existed. The tag now
  names the first release that carries the proto schema and generated bindings.
