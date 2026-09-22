"""DFS scoring tables with explicit, per-number provenance.

RotoGrinders publishes ``FPTS`` per operator site (DraftKings, FanDuel, Yahoo),
so an open rebuild has to reproduce the operator scoring rules exactly or the
numbers are not comparable.

**Nothing in this module is a guess.**  Every point value lives in
``rgengy/data/scoring/*.json`` and carries:

* ``value``            - the number used by the engine
* ``agreement``        - how many independent sources agreed
* ``sources``          - URLs actually retrieved during the audit
* ``disputed``         - true when sources disagreed (see docs/09-irregularities.md)
* ``confirmed_by_operator`` - true only if read from the operator's own page

At the time of writing the operator scoring pages sit behind their logged-in
apps, so ``confirmed_by_operator`` is **false** for every value and the tables
are built from multiple independent secondary sources.  That limitation is
stated plainly in ``docs/10-roadmap-and-limitations.md`` and each disputed
value is flagged on the published site.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DATA_DIR = Path(__file__).resolve().parent / "data" / "scoring"

#: Every ``verification_status`` a value may carry.  Adding a status here is a
#: deliberate act: the audit below rejects anything else, so a typo cannot
#: silently downgrade a number to "verified".
VALID_STATUSES = frozenset({
    "multi-source-consistent",   # >= 2 independent retrieved sources agree
    "single-source",             # exactly one retrieved source; provisional
    "cross-validated-via-rg",    # corroborated by a column on RotoGrinders' own grid
    "disputed",                  # sources contradict; registered in docs/09
    "not-audited",               # no source retrieved; excluded under --strict
    "not-applicable",            # deliberately 0.0 (see `intentionally_zero`)
})

#: Sets of stat keys that, when ALL are non-zero, score the same production
#: twice.  Operators publish scoring either as an aggregate ("1 point per point
#: scored") or as its components ("2 per FG made, 1 per FT made, +1 per 3PM"); a
#: table that mixes the two silently roughly doubles every projection.
#:
#: The rule deliberately requires EVERY member of a set to be non-zero, not just
#: two of them.  That distinction matters: DraftKings NBA pays 1 point per point
#: PLUS a 0.5 bonus per three-pointer made, which is additive and legal, whereas
#: paying 1 point per point PLUS 2 per two-pointer PLUS 1 per free throw is the
#: same production counted twice.  `three_pm` on its own cannot reconstruct
#: `pts`; `two_pm` + `ftm` can.
#:
#: This check caught a real bug during review - FanDuel NBA scoring originally
#: carried pts, two_pm, three_pm AND ftm at once, inflating every projection by
#: roughly 2x (IR-15).
REPRESENTATION_SETS = (
    ("pts", "two_pm", "ftm"),                 # made-shot decomposition, no 3PM bonus
    ("pts", "two_pm", "three_pm", "ftm"),     # made-shot decomposition with 3PM bonus
    ("pts", "fgm", "ftm"),                    # field-goal decomposition
    ("ip", "outs"),                           # innings vs outs (3 outs = 1 inning)
    ("sog", "sog_goal"),                      # shots on goal vs goal-shots
)


class ScoringTable:
    """One ``sport x site`` scoring table."""

    def __init__(self, sport: str, site: str, payload: Dict[str, Any]) -> None:
        self.sport = sport
        self.site = site
        self.payload = payload
        self.points: Dict[str, float] = {
            k: float(v["value"]) for k, v in payload.get("values", {}).items()
        }
        self.meta: Dict[str, Any] = payload.get("meta", {})

    # -- lookups -----------------------------------------------------------
    def get(self, stat: str, default: float = 0.0) -> float:
        return self.points.get(stat, default)

    @property
    def disputed(self) -> List[str]:
        return sorted(
            k for k, v in self.payload.get("values", {}).items() if v.get("disputed")
        )

    @property
    def not_audited(self) -> List[str]:
        """Stats whose value was never retrieved from any source."""
        return sorted(k for k, v in self.payload.get("values", {}).items()
                      if v.get("verification_status") == "not-audited")

    @property
    def intentionally_zero(self) -> List[str]:
        """Stats pinned at 0.0 on purpose (representation overlap or no such slot).

        These are NOT coverage gaps: :mod:`rgengy.quality` reports them as
        informational rather than as warnings.
        """
        return sorted(k for k, v in self.payload.get("values", {}).items()
                      if v.get("intentionally_zero"))

    def validate(self) -> List[str]:
        """Structural self-check.  Returns a list of problems (empty == clean)."""
        problems: List[str] = []
        for stat, spec in self.payload.get("values", {}).items():
            status = spec.get("verification_status")
            if status not in VALID_STATUSES:
                problems.append(
                    f"{self.sport}:{self.site}:{stat} has unknown verification_status {status!r}")
            if not isinstance(spec.get("value"), (int, float)):
                problems.append(f"{self.sport}:{self.site}:{stat} value is not numeric")
            if status not in ("not-audited", "not-applicable") and not spec.get("sources"):
                problems.append(
                    f"{self.sport}:{self.site}:{stat} claims {status!r} but lists no sources")
            if spec.get("intentionally_zero") and float(spec.get("value", 0.0)) != 0.0:
                problems.append(
                    f"{self.sport}:{self.site}:{stat} is flagged intentionally_zero "
                    f"but its value is {spec.get('value')}")
        return problems

    @property
    def confirmed_by_operator(self) -> bool:
        return bool(self.meta.get("confirmed_by_operator", False))

    def provenance_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for stat, spec in self.payload.get("values", {}).items():
            rows.append(
                {
                    "stat": stat,
                    "value": spec["value"],
                    "agreement": spec.get("agreement"),
                    "disputed": bool(spec.get("disputed")),
                    "verification_status": spec.get("verification_status"),
                    "intentionally_zero": bool(spec.get("intentionally_zero", False)),
                    "confirmed_by_operator": bool(spec.get("confirmed_by_operator", False)),
                    "sources": spec.get("sources", []),
                    "note": spec.get("note"),
                }
            )
        rows.sort(key=lambda r: r["stat"])
        return rows

    def score(self, stats: Dict[str, float]) -> float:
        """Turn a dict of projected stats into fantasy points for this site."""
        total = 0.0
        for stat, value in self.points.items():
            n = stats.get(stat)
            if n:
                total += value * float(n)
        return round(total, 2)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ScoringTable {self.sport}:{self.site} n={len(self.points)}>"


_CACHE: Dict[str, ScoringTable] = {}


def available() -> List[str]:
    """Sorted list of ``sport:site`` keys that have a scoring table.

    Files are named ``{sport}_{site}.json``; the key uses ``:`` so callers can
    ``key.split(':')`` unambiguously.
    """
    keys = []
    for p in DATA_DIR.glob("*.json"):
        if "_" not in p.stem:
            continue
        sport, site = p.stem.split("_", 1)
        keys.append(f"{sport}:{site}")
    return sorted(keys)


def load(sport: str, site: str) -> ScoringTable:
    key = f"{sport}:{site}"
    if key in _CACHE:
        return _CACHE[key]
    path = DATA_DIR / f"{key.replace(':', '_')}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No scoring table for {key!r}. Available: {available()}"
        )
    table = ScoringTable(sport, site, json.loads(path.read_text(encoding="utf-8")))
    _CACHE[key] = table
    return table


def load_all() -> Dict[str, ScoringTable]:
    return {k: load(*k.split(":")) for k in available()}


def representation_audit() -> List[Dict[str, Any]]:
    """Find aggregate-vs-component double counting in every scoring table.

    Returns one record per offending ``sport:site`` listing the group of keys
    that are simultaneously non-zero.  An empty list means no table scores the
    same production twice.  This runs in :func:`audit` and in the test suite, so
    the bug cannot come back unnoticed.
    """
    findings: List[Dict[str, Any]] = []
    for key in available():
        sport, site = key.split(":")
        table = load(sport, site)
        for group in REPRESENTATION_SETS:
            live = [k for k in group if table.points.get(k)]
            if len(live) == len(group):
                findings.append({
                    "key": key,
                    "group": list(group),
                    "values": {k: table.points[k] for k in group},
                    "explanation": (
                        f"{key} scores {'+'.join(group)} simultaneously, which counts the same "
                        f"production twice. Pin the redundant keys to 0.0 and set "
                        f"intentionally_zero, or drop the aggregate."),
                })
    return findings


def audit() -> Dict[str, Any]:
    """Machine-readable audit of every scoring constant in the repo."""
    out: Dict[str, Any] = {
        "tables": [], "disputed_total": 0, "operator_confirmed_total": 0,
        "not_audited_total": 0, "intentionally_zero_total": 0,
        "structural_problems": [], "representation_double_counts": [],
        "source_count": 0,
    }
    all_sources: set = set()
    for key in available():
        sport, site = key.split(":")
        table = load(sport, site)
        rows = table.provenance_rows()
        disputed = [r["stat"] for r in rows if r["disputed"]]
        confirmed = [r["stat"] for r in rows if r["confirmed_by_operator"]]
        not_audited = table.not_audited
        izero = table.intentionally_zero
        srcs = sorted({u for r in rows for u in r["sources"]})
        all_sources.update(srcs)
        out["tables"].append(
            {
                "key": key,
                "n_values": len(rows),
                "disputed": disputed,
                "not_audited": not_audited,
                "intentionally_zero": izero,
                "operator_confirmed": confirmed,
                "sources": srcs,
                "problems": table.validate(),
            }
        )
        out["disputed_total"] += len(disputed)
        out["operator_confirmed_total"] += len(confirmed)
        out["not_audited_total"] += len(not_audited)
        out["intentionally_zero_total"] += len(izero)
        out["structural_problems"].extend(table.validate())
    out["representation_double_counts"] = representation_audit()
    out["source_count"] = len(all_sources)
    out["clean"] = not (out["structural_problems"] or out["representation_double_counts"])
    return out


def scoring_rows_for_site(sport: str, sites: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
    """Flat rows for the documentation/site renderer."""
    sites = list(sites) if sites else [k.split(":")[1] for k in available() if k.startswith(sport + ":")]
    rows: List[Dict[str, Any]] = []
    stats: List[str] = []
    for site in sites:
        try:
            table = load(sport, site)
        except FileNotFoundError:
            continue
        for stat in table.points:
            if stat not in stats:
                stats.append(stat)
    for stat in sorted(stats):
        row: Dict[str, Any] = {"stat": stat}
        for site in sites:
            try:
                table = load(sport, site)
            except FileNotFoundError:
                continue
            spec = table.payload.get("values", {}).get(stat)
            row[site] = spec["value"] if spec else None
            row[f"{site}_disputed"] = bool(spec and spec.get("disputed"))
        rows.append(row)
    return rows
