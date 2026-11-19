# Intent — `pysos_rpr`

## Why

The `pysos_*` family has more than one implementation that needs to exchange
entity facts: what exists, where it is, how it moves, which side it is on, and
what kind of platform it is. Without a shared schema each implementation grows
its own shape and a pairwise adapter for every peer, and the seam is owned by
whoever wrote the first adapter.

`pysos_rpr` fixes that seam. It publishes one protobuf vocabulary for the parts
of the RPR FOM that the implementations genuinely share. The vocabulary is
plain protobuf; it borrows RPR semantics without importing HLA machinery.

## Commitments

- **One schema, many projections.** The proto definitions are the single
  source. Every language binding is generated from them.
- **RPR-derived, not RPR.** Names, enumerations and field meanings follow the
  RPR FOM where it is clear, stable and useful. Where an HLA concept does not
  map (interaction ordering, ownership transfer, federate handles), the
  vocabulary stays silent.
- **Stable at the edges.** Field numbers are part of the contract from the
  first published tag. Evolution is additive.
- **Implementable twice.** The vocabulary must be expressible by an independent
  second implementation without reading the first one's code.
- **No runtime.** The package carries definitions, not transport, not an RTI,
  not federation services.

## Vocabulary subset

The first version covers five areas, each defined at intent level:

- **Entity identity** — stable naming of an object across implementations.
- **Spatial state and dead reckoning** — position, orientation and velocity,
  plus the dead-reckoning parameters that let a receiver extrapolate between
  updates.
- **Marking** — the human-readable label carried with an entity.
- **Force** — which side an entity belongs to.
- **Platform/aircraft class** — what kind of object it is, at the granularity
  the family actually uses.

## Non-goals

- **Not HLA-conformant.** No RTI ambassador, no federation services, no FOM
  module, no HLA object model. A FOM XML file is not part of this repository.
- **Not a runtime or engine.** No dynamics, no scheduling, no transport.
- **Not a federation manager.** No join, resign, ownership or time management.
- **Not a scenario format.** Entity catalogues and exercise files stay outside.
- **Not the in-process model.** `pysos_interop.EntityState` remains the model
  engines use locally; this vocabulary is what crosses the wire between
  implementations.
