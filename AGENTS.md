# AGENTS

## Vision first (required)

Before you read code, edit files, or plan a change, read:

**`docs/breakdown/00-intent/intent.md`**

It states why this repository exists, what it commits to, and what it refuses
to become. Judge every change against it. If a change conflicts with the
intent, stop and surface the conflict; do not implement it silently.

## Repository focus

`pysos_rpr` owns the shared RPR-derived protobuf vocabulary for the `pysos_*`
family. It owns message and enumeration shapes plus their generated bindings.
It does not own transport, an engine, an RTI integration, or federation
lifecycle.

- Vocabulary areas: entity identity, spatial state and dead reckoning,
  marking, force, and platform/aircraft class.
- Dependency edges point both ways by kind, not by rank: the vocabulary and
  its reference codec depend on nothing, while a *projection* may import the
  artifact implementer it targets. Consumers never make the vocabulary depend
  on them.
- Projection: the flat schema table and the FMI `rpr` backend are generated
  from the proto; `schema_paths.py` is never hand-edited. The SysML port built
  from the vocabulary is an implementation asset of `pyfmi_rpr`
  (`repos/pyfmi_rpr/src/pyfmi_rpr/sysml/rpr_entity.sysml`, exposed as
  `pyfmi_rpr.rpr_entity()`), not this package's. Frame mode `identity` is an
  interop stand-in, not RPR conformance.

## Hard constraints

- **The proto is the single source of the vocabulary.** Message, field and
  enumeration definitions exist in the proto tree only. Every binding is
  generated from them. Never hand-write a parallel definition, and never edit
  generated output in place.
- **Field numbers are frozen.** A published field number is part of the
  contract. Evolution is additive: new fields get new numbers, removed fields
  become `reserved` numbers and names, and no number is reused.
- **No protobuf `map`.** Repeated entry messages keep ordering explicit and
  leave room for additive evolution that `map` entries cannot express.
- **Reserved ranges are honoured.** A number or name marked `reserved` is never
  reintroduced, not even under a different type.
- **One source, multiple projections.** Python and any future language binding
  project the same definitions. No projection may add vocabulary that the proto
  does not carry.
- **Not HLA-conformant.** No RTI, no federation services, no FOM module, no HLA
  object model, no join/resign/ownership/time-management concepts.
- **Dependencies follow the projection.** The schema and the reference codec
  import no sibling package. A projection module — the FMI adapter, the
  composition layer — may import the implementer it projects onto
  (`pyfmi_interop`, `pyfmi_sysml`); a structured dependency on the artifact
  implementer is what a projection is. No sibling ever imports this package's
  projection modules.
- **No application code.** This is a vocabulary and codec contract, not a CLI,
  engine, or federation manager.

## Code guidelines

- Keep the public vocabulary small and stable; additions are deliberate.
- Bindings are generated, not edited. Generated files are either build outputs
  or are accompanied by the exact command that reproduces them.
- Tests must pin field numbers and reserved ranges, not only round-trip
  encode/decode agreement.
- Cross-language compatibility is a stated goal: if only one binding can read a
  message, the schema is wrong.

## Environment

- Python >= 3.11, `src/` layout.
- Install: `pip install -e ".[dev]"`.
- Tests: `python -m pytest`; lint: `ruff check src tests` (line length 100,
  target py311).
