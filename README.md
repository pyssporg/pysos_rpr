# pysos_rpr

`pysos_rpr` is the shared RPR-derived protobuf vocabulary for the `pysos_*` family. It gives two independent implementations one schema for the entity facts they exchange, so neither has to adopt the other's runtime.

## What it is

- A protobuf vocabulary for entity identity, spatial state and dead reckoning, marking, force, and platform/aircraft class.
- Derived from the RPR FOM. Names, field meanings and enumerations follow RPR where RPR is clear and useful.
- One source, multiple projections. The proto definitions are the single definition; language bindings are generated from them, never hand-written twice.

## What it is not

- **Not HLA-conformant.** There is no RTI, no federation service, no FOM module and no HLA object model. RPR is an influence, not a contract.
- **Not a runtime.** No transport, no scheduling, no federation lifecycle, no simulation engine.
- **Not the in-process model.** `pysos_interop.EntityState` remains the model engines use locally; this vocabulary is what crosses the wire between implementations.
- **Not an application.** No CLI and no sources or sinks.

## Install

Python 3.11 or newer is required. The runtime dependency is `protobuf`
(`>=5.29,<6`); `protoc` and `grpcio-tools` are needed only to regenerate the
committed bindings.

```bash
pip install pysos-rpr
pip install -e ".[dev]"              # this checkout: tests, lint, grpcio-tools
pip install -e "repos/pysos_rpr[dev]"  # from the workspace root
```

The optional `projection` and `composition` extras add the FMI adapter and the
source-ingestion layer (`pyfmi-interop`, `pyfmi-sysml`); the base install stays
vocabulary-only.

The source tree ships the proto definitions under `proto/rpr/v2/`, and the
package ships the committed Python bindings under `pysos_rpr._proto`, so
`protoc` is not needed at runtime. Regenerate the bindings with
`bash tools/generate_bindings.sh`; the field-level RPR and DIS mapping is in
`docs/rpr-mapping.md`.

## API

`pysos_rpr.messages` is the documented Python reference surface over the
generated bindings. It wraps the proto; it never redefines it.

- `encode(message) -> bytes` serializes deterministically.
- `decode(cls, data, *, strict=True)` parses a payload. Malformed data raises
  `RprMalformedPayloadError` (a `RprDecodeError`, never a protobuf
  `DecodeError`). Unknown fields are rejected in strict mode with
  `RprUnknownFieldError`; pass `strict=False` to preserve them.
- Constructors return generated messages and require identity and force:
  `entity_identifier`, `entity_type`, `marking`, `base_entity`,
  `world_location`, `orientation`, `velocity`, `acceleration`,
  `angular_velocity`, `dead_reckoning`, `spatial`, `spatial_ecef`,
  `physical_entity`, `entity_state`, `platform`, `aircraft`,
  `aircraft_entity`.
- `validate(message) -> list[str]` returns every semantic-rule violation; the
  rules are documented in `docs/rpr-mapping.md`.
- `to_dict` / `from_dict` use protobuf JSON (`json_format`) for fixture and
  test interchange. The example fixtures live in `tests/fixtures/`.

```python
from pysos_rpr import messages as rpr

aircraft = rpr.aircraft_entity(
    entity_identifier=rpr.entity_identifier(site=1, application=2, entity=1001),
    entity_type=rpr.entity_type(kind=1, domain=2, country=840),
    force="FORCE_FRIENDLY",
    spatial=rpr.spatial_ecef(x=4533212.5, y=611234.25, z=4482341.75),
    kind="PLATFORM_FIXED_WING",
)
payload = rpr.encode(aircraft)
assert rpr.decode(rpr.Aircraft, payload) == aircraft
assert rpr.validate(aircraft) == []
```

### Unknown-field policy

Decoding is strict by default: a payload carrying fields absent from the schema
raises `RprUnknownFieldError`. `decode(..., strict=False)` keeps those fields on
the message, and `encode` emits them again. For a payload produced by `encode`,
the non-strict decode/re-encode pair is byte-identical.

## Status

0.1.0 is the first published release. It ships the `rpr.v2` vocabulary
(`proto/rpr/v2/`), its generated Python bindings, the schema contract tests that
pin field numbers, reserved ranges and golden bytes, and the
`pysos_rpr.messages` reference codec.

## Development

```bash
python -m pytest
ruff check src tests
bash tools/generate_bindings.sh                  # regenerate _proto from proto/
python tools/generate_schema_paths.py            # regenerate schema_paths.py
```

Ruff is configured in `pyproject.toml` (line length 100, target `py311`) and
excludes the generated `src/pysos_rpr/_proto` bindings. Read
[`AGENTS.md`](AGENTS.md), the
[vocabulary subset](docs/breakdown/02-architecture/vocabulary-subset.md) and the
[projection](docs/breakdown/02-architecture/projection.md) before changing the
schema or a projection.
