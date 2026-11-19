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

The protobuf definitions and generated bindings are not part of 0.1.0. That release is the repository scaffold: package metadata, CI and the vocabulary intent record.

## Status

0.1.0 is a scaffold. The schema lands in the next unit, and the Python projection after it.
