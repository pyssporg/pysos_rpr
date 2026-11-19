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

```bash
pip install pysos-rpr
```

The source tree ships the proto definitions under `proto/rpr/v2/`, and the
package ships the committed Python bindings under `pysos_rpr._proto`, so
`protoc` is not needed at runtime. Regenerate the bindings with
`tools/generate_bindings.sh`; the field-level RPR and DIS mapping is in
`docs/rpr-mapping.md`.

## Status

0.1.0 is the published scaffold tag. The current tree carries the R2/R3
vocabulary (`proto/rpr/v2/`), its generated Python bindings, and the schema
contract tests that pin field numbers, reserved ranges and golden bytes.
