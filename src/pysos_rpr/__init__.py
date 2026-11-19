"""RPR-derived protobuf vocabulary shared by the pysos implementations.

The vocabulary covers entity identity, spatial state and dead reckoning,
marking, force, and platform/aircraft class. It is derived from the RPR FOM
where RPR is clear and useful, but it is explicitly **not** HLA-conformant:
there is no RTI, no federation service, no FOM module, and no HLA object model.

The proto definitions are the single source of the vocabulary. Python and any
other bindings are generated projections of them, never hand-written second
definitions.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
