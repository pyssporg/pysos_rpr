# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-19

### Added

- Repository scaffold: hatchling package metadata with a dynamic version,
  `src/` layout, CI for Python 3.11, and the vocabulary intent record under
  `docs/breakdown/`.
- `pysos_rpr.__version__` and an explicit public surface.
- Package metadata tests: import, semver, and the pinned release version.

Proto definitions and generated bindings are deliberately absent; they belong
to the schema and projection units.
