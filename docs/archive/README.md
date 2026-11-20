<!-- GENERATED FILE — do not edit. Regenerate with `pb registers`. -->

# Decision Stream

Flat, dated history of every committed design choice. Current state lives
in the layer leaves named by each record's `state:` field.

Records live in the cold-storage archive; extract one with `pb archive read <ID>`.

## By Layer

### Intent

- **DEC-001** — A projection may depend on the artifact implementer · accepted · 2026-11-19 · `DEC-001`
  The vocabulary and its reference codec stay dependency-free, while a projection module may import the implementer it targets — pyfmi_interop for the FMI adapter, the SysML parser for the port library.
