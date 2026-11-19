# Vocabulary subset

The first vocabulary covers five areas. This leaf fixes what each area means
and what it refuses. The concrete message shapes, field numbers and reserved
ranges live in `proto/rpr/v2/` and are mapped field by field in
`docs/rpr-mapping.md`.

## Entity identity

Every message that describes an object carries the same identity. The identity
is stable for the lifetime of the object, unique within an exchange, and cheap
to compare and hash.

- Identity never encodes mutable state (position, health, affiliation).
- Two implementations must be able to mint identities independently, without a
  shared registry or a central allocator.
- The RPR entity identifier shape (site, application, entity) is the starting
  point. The vocabulary keeps that triple as
  `EntityIdentifier.site/application/entity`.

## Spatial state and dead reckoning

One message describes where an entity is and how it is moving, in a single
frame and a single unit system, explicit enough that no consumer has to guess.

- The message carries the frame and unit convention as part of its contract,
  not as free-form prose.
- Dead-reckoning parameters travel with the state they extrapolate: algorithm,
  reference point, and the rates the algorithm needs.
- A receiver that misses updates must be able to extrapolate without asking a
  question. A receiver that trusts only fresh data must be able to tell.

## Marking

Marking is the human-readable label an operator sees. It is not identity and
must never be used as a key.

- Bounded length, printable text, no semantic parsing by consumers.
- Absent or empty marking is valid; identity still resolves the entity.

## Force

Force says which side an entity belongs to. It is a small closed enumeration,
not a free string.

- Unknown and unaligned are representable values, not errors.
- Force is an attribute of an entity at a point in time, not a routing rule.

## Platform/aircraft class

Platform class says what kind of object an entity is, at the granularity the
family actually uses: enough to choose a symbol and a kinematic default, not a
full order-of-battle taxonomy.

- The enumeration is closed and additive; new kinds receive new values, never
  reused ones.
- A neutral or unknown kind exists, so the field can be omitted in practice
  without losing the record.

## Reference implementation

The Python package publishes `pysos_rpr.messages` as a reference codec over the
generated bindings: deterministic `encode`, strict-by-default `decode` with an
explicit unknown-field policy, constructors that require identity and force,
protobuf JSON helpers, and `validate` for the semantic rules in
`docs/rpr-mapping.md`. Every constructor returns a generated message; the proto
remains the only schema definition. Conversions to `pysos_interop.EntityState`
stay in `pysos_interop`.

## Composition

The areas compose by reference, not by duplication. A state message refers to
an entity by identity; a platform record refers to no state at all. Each area
evolves additively, and no area is allowed to define a second identity or a
second spatial frame.
