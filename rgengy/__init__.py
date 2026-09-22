"""RGENGY - an open, auditable sports projection system.

RGENGY rebuilds the *class* of tooling that RotoGrinders sells behind a
subscription (projections, projected ownership, a lineup optimizer, a contest
simulator and a weather layer) using only free, official or publicly
documented data endpoints.

Design rules that every module in this package follows:

1.  **Zero runtime dependencies.**  Standard library only.  If a module cannot
    reach the network it must fail loudly, never invent data.
2.  **No silent guesses.**  Any numeric constant that is *not* derived from
    official data at runtime is declared in :mod:`rgengy.scoring` or
    :mod:`rgengy.models` together with a ``PROVENANCE`` entry stating where the
    number came from and whether it has been validated.
3.  **Every artefact carries provenance.**  Output rows record which endpoint
    they were built from, the HTTP status observed and the fetch timestamp.

See ``docs/VERIFICATION.md`` for the no-hallucination protocol this package is
held to.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
