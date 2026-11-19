# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

### Changed

- `pyproject.toml` now depends on `protobuf` at runtime and `grpcio-tools`
  under `[dev]`; ruff excludes the generated bindings.

## [0.1.0] - 2026-11-19

### Added

- Repository scaffold: hatchling package metadata with a dynamic version,
  `src/` layout, CI for Python 3.11, and the vocabulary intent record under
  `docs/breakdown/`.
- `pysos_rpr.__version__` and an explicit public surface.
- Package metadata tests: import, semver, and the pinned release version.

Proto definitions and generated bindings are deliberately absent; they belong
to the schema and projection units.
