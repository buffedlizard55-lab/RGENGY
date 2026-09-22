"""Data-quality and irregularity detection.

The brief for this project is explicit: *flag any irregularities for review*.
This module turns that into code rather than prose.  Every check emits a
:class:`Finding` with a severity, the offending record, and a ``review_action``
describing what a human should look at.

Checks are deliberately conservative.  A finding never edits or discards data -
it reports.  The pipeline includes every finding in the published artefacts so
nothing is silently dropped.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}


@dataclass
class Finding:
    check: str
    severity: str                     # "info" | "warning" | "critical"
    message: str
    entity: Optional[str] = None      # player id/name, game id, endpoint key...
    value: Any = None
    review_action: str = ""
    source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check": self.check,
            "severity": self.severity,
            "message": self.message,
            "entity": self.entity,
            "value": self.value,
            "review_action": self.review_action,
            "source": self.source,
        }


@dataclass
class QualityReport:
    findings: List[Finding] = field(default_factory=list)
    checks_run: List[str] = field(default_factory=list)

    def add(self, f: Finding) -> Finding:
        if f.severity not in SEVERITY_ORDER:
            raise ValueError(f"unknown severity {f.severity!r}")
        self.findings.append(f)
        return f

    def extend(self, fs: Iterable[Finding]) -> None:
        for f in fs:
            self.add(f)

    def by_severity(self) -> Dict[str, int]:
        out = {k: 0 for k in SEVERITY_ORDER}
        for f in self.findings:
            out[f.severity] += 1
        return out

    def by_check(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for f in self.findings:
            out[f.check] = out.get(f.check, 0) + 1
        return dict(sorted(out.items()))

    @property
    def has_critical(self) -> bool:
        return any(f.severity == "critical" for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "checks_run": sorted(set(self.checks_run)),
            "counts_by_severity": self.by_severity(),
            "counts_by_check": self.by_check(),
            "total_findings": len(self.findings),
            "has_critical": self.has_critical,
            "findings": [f.to_dict() for f in self.findings],
        }


# ---------------------------------------------------------------------------
# Thresholds.  Each is an RGENGY sanity bound, not an audited league rule.
# ---------------------------------------------------------------------------
MAX_MLB_PA = 8.0            # a batter cannot realistically exceed ~7 PA in 9 innings + extras
MAX_MLB_IP = 12.0
MAX_BASKETBALL_MINUTES = 60.0
MAX_HOCKEY_TOI = 45.0
MAX_NFL_SNAPS_EQUIV = 1.0   # NFL projections are per game, so opportunity is 1
STALE_AFTER_HOURS = 36


def check_zero_projection(players: Sequence[Any], site: str, report: QualityReport) -> None:
    """Players with a salary but no projected points cannot be ranked meaningfully."""
    report.checks_run.append("zero_projection")
    for p in players:
        pts = (p.fpts or {}).get(site)
        if p.salary and (pts is None or pts <= 0):
            report.add(Finding(
                check="zero_projection",
                severity="warning",
                message=f"{p.name} has salary {p.salary} but no projected {site} points",
                entity=p.player_id,
                value={"salary": p.salary, "fpts": pts, "projected": p.projected},
                review_action="Check whether the season-stats fetch returned an empty sample for this "
                              "player, or whether the scoring table is missing a stat key they need.",
                source=getattr(p, "site", site),
            ))


def check_duplicate_ids(players: Sequence[Any], report: QualityReport) -> None:
    report.checks_run.append("duplicate_player_id")
    seen: Dict[str, List[str]] = {}
    for p in players:
        seen.setdefault(p.player_id, []).append(p.name)
    for pid, names in seen.items():
        if len(names) > 1:
            report.add(Finding(
                check="duplicate_player_id",
                severity="critical",
                message=f"player id {pid} appears {len(names)} times: {names}",
                entity=pid, value=names,
                review_action="Duplicate ids corrupt ownership normalisation and roster uniqueness. "
                              "Determine whether the source is returning the same person twice or two "
                              "different people share an id namespace.",
            ))


def check_implausible_values(players: Sequence[Any], sport: str, report: QualityReport) -> None:
    """Range checks against physically impossible values."""
    report.checks_run.append("implausible_value")
    bounds = {
        "mlb": {"pa": MAX_MLB_PA, "ip": MAX_MLB_IP},
        "nba": {"min": MAX_BASKETBALL_MINUTES},
        "wnba": {"min": MAX_BASKETBALL_MINUTES},
        "nhl": {"toi": MAX_HOCKEY_TOI},
        "nfl": {},
    }.get(sport, {})
    for p in players:
        for stat, value in (p.projected or {}).items():
            if value is None:
                continue
            if value < 0 and stat not in ("er", "ga", "to", "pa_int", "fum_lost"):
                report.add(Finding(
                    check="implausible_value", severity="critical",
                    message=f"{p.name}: projected {stat}={value} is negative",
                    entity=p.player_id, value={stat: value},
                    review_action="A negative count stat means an environment ratio went negative. "
                                  "Inspect the implied totals and park factor inputs for this game.",
                ))
            limit = bounds.get(stat)
            if limit and value > limit:
                report.add(Finding(
                    check="implausible_value", severity="warning",
                    message=f"{p.name}: projected {stat}={value:.2f} exceeds the sanity bound {limit}",
                    entity=p.player_id, value={stat: value, "bound": limit},
                    review_action="Confirm the opportunity input (projected playing time / plate "
                                  "appearances). The bound itself is an RGENGY sanity limit, not a "
                                  "league rule.",
                ))
        if p.salary is not None and p.salary < 0:
            report.add(Finding(
                check="implausible_value", severity="critical",
                message=f"{p.name}: negative salary {p.salary}", entity=p.player_id,
                value=p.salary, review_action="Salaries must be non-negative; re-check the salary feed.",
            ))


def check_stale_provenance(provenance: Iterable[Dict[str, Any]], report: QualityReport,
                           now: Optional[_dt.datetime] = None) -> None:
    """Flag any input whose recorded fetch time is older than ``STALE_AFTER_HOURS``."""
    report.checks_run.append("stale_provenance")
    now = now or _dt.datetime.now(_dt.timezone.utc)
    for prov in provenance:
        ts = prov.get("fetched_at")
        if not ts:
            # A row that looks like a network fetch but records no fetch time cannot
            # be shown to be fresh, so it is reported rather than silently skipped.
            # Rows that are not fetches at all (static scoring tables carry
            # 'audit_date' and no 'url') are genuinely out of scope for this check.
            if prov.get("url") or prov.get("endpoint") or prov.get("status") is not None:
                report.add(Finding(
                    check="stale_provenance", severity="warning",
                    message=f"{prov.get('url') or prov.get('endpoint')} records no fetched_at, "
                            f"so its freshness cannot be verified",
                    entity=prov.get("url") or prov.get("endpoint"), value=prov,
                    review_action="Every network input must stamp the time it was retrieved. Treat "
                                  "this input as potentially stale until the timestamp is present.",
                ))
            continue
        try:
            when = _dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)
        except ValueError:
            report.add(Finding(
                check="stale_provenance", severity="warning",
                message=f"unparseable fetched_at {ts!r} for {prov.get('url')}",
                entity=prov.get("url"), value=ts,
                review_action="Provenance timestamps must be ISO-8601 UTC (YYYY-MM-DDTHH:MM:SSZ).",
            ))
            continue
        age_h = (now - when).total_seconds() / 3600.0
        if age_h > STALE_AFTER_HOURS:
            report.add(Finding(
                check="stale_provenance", severity="warning",
                message=f"{prov.get('url')} was fetched {age_h:.1f}h ago (> {STALE_AFTER_HOURS}h)",
                entity=prov.get("url"), value={"age_hours": round(age_h, 2)},
                review_action="Re-run the pipeline; projections built on stale inputs should not be "
                              "compared to a live commercial product.",
            ))


def check_endpoint_failures(fetch_summary: Dict[str, Any], report: QualityReport) -> None:
    """One finding per distinct failing URL, with the retry count stated.

    A retried endpoint fails once per attempt, and emitting one critical finding
    per attempt made a single dead endpoint look like two separate defects.  The
    attempt count is preserved in the finding instead of being thrown away.
    """
    report.checks_run.append("endpoint_failure")
    grouped: Dict[str, Dict[str, Any]] = {}
    for failure in fetch_summary.get("failures", []):
        url = failure.get("url") or "(no url)"
        entry = grouped.setdefault(url, {"url": url, "attempts": 0,
                                         "errors": [], "failure": failure})
        entry["attempts"] += 1
        err = str(failure.get("error"))
        if err not in entry["errors"]:
            entry["errors"].append(err)
    for entry in grouped.values():
        attempts = entry["attempts"]
        report.add(Finding(
            check="endpoint_failure", severity="critical",
            message=(f"{entry['url']} failed after {attempts} attempt"
                     f"{'s' if attempts != 1 else ''}: {'; '.join(entry['errors'])}"),
            entity=entry["url"], value=entry["failure"],
            review_action="This endpoint did not return data, so every projection downstream of it is "
                          "degraded. Confirm the endpoint is still live and that its shape has not "
                          "changed, then re-run. If the sandbox has no outbound network access this "
                          "is expected and the stage must be reported 'unavailable', never guessed.",
            source=entry["url"],
        ))


def check_cross_source_identity(primary: Sequence[Dict[str, Any]],
                                secondary: Sequence[Dict[str, Any]],
                                report: QualityReport,
                                label: str = "cross_source_identity") -> None:
    """Flag entities present in one source but absent from the official one.

    This is the check that catches the class of error observed on
    RotoGrinders' public NFL grid on 2026-09-22, where a row was published for
    "Frank Gore" against Buffalo.  Gore's NFL career ended years earlier, so a
    row like that is either an identity collision in the projection database or
    a stale roster join.  Comparing against the league's own feed surfaces it
    without RGENGY having to assert anything about who is retired.
    """
    report.checks_run.append(label)
    primary_names = {_normalise_name(x.get("name", "")) for x in primary if x.get("name")}
    for row in secondary:
        name = _normalise_name(row.get("name", ""))
        if not name:
            continue
        if name not in primary_names:
            report.add(Finding(
                check=label, severity="warning",
                message=f"{row.get('name')!r} (team {row.get('team')}) is not present in the official feed",
                entity=row.get("name"), value=row,
                review_action="Reconcile the two feeds before trusting this row. Either the projection "
                              "source has a stale/incorrect roster join, or the official feed is missing "
                              "the player (call-up, practice squad, expansion roster).",
                source=row.get("source"),
            ))


_SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}
_NON_WORD = re.compile(r"[^a-z0-9 ]+")


def _normalise_name(name: str) -> str:
    """Lowercase, strip punctuation and generational suffixes, collapse spaces."""
    cleaned = _NON_WORD.sub(" ", (name or "").lower())
    parts = [p for p in cleaned.split() if p and p not in _SUFFIXES]
    return " ".join(parts)


def check_ownership_normalisation(players: Sequence[Any], report: QualityReport) -> None:
    """pOWN across a slate should sum to roughly 1.0 (100%)."""
    report.checks_run.append("ownership_normalisation")
    total = sum(float(p.pown or 0.0) for p in players)
    if players and total > 0 and abs(total - 1.0) > 0.02:
        report.add(Finding(
            check="ownership_normalisation", severity="warning",
            message=f"projected ownership sums to {total:.4f}, expected ~1.0",
            entity="slate", value={"sum": round(total, 4)},
            review_action="Ownership shares must be normalised over the slate before they are compared "
                          "to a commercial pOWN column.",
        ))


def check_scoring_coverage(players: Sequence[Any], coefficients: Dict[str, float],
                           report: QualityReport,
                           scoring_table: Optional[Any] = None) -> None:
    """Any projected stat with no scoring coefficient is invisible to FPTS.

    ``scoring_table`` (an :class:`rgengy.scoring.ScoringTable`) lets the check
    tell a *deliberate* zero from an *unaudited* zero.  The distinction is the
    whole point: a key pinned at 0 because a second key already carries that
    production is correct and informational, whereas a key at 0 because nobody
    ever retrieved its value means the published FPTS understates the operator's
    real total, which is a genuine defect worth escalating.
    """
    report.checks_run.append("scoring_coverage")
    projected_stats = set()
    for p in players:
        projected_stats.update((p.projected or {}).keys())

    intentional = set(scoring_table.intentionally_zero) if scoring_table is not None else set()
    unaudited = set(scoring_table.not_audited) if scoring_table is not None else set()

    unscored = sorted(s for s in projected_stats if s not in coefficients)
    if unscored:
        report.add(Finding(
            check="scoring_coverage", severity="info",
            message=f"projected stats with no scoring coefficient: {unscored}",
            entity="scoring-table", value=unscored,
            review_action="Either the scoring table is missing these keys or they are projected for "
                          "context only (as RotoGrinders does with columns like BATK, BASES and PA). "
                          "Confirm which, and document it.",
        ))

    if scoring_table is not None:
        zeroed = sorted(s for s, v in coefficients.items()
                        if v == 0 and s in projected_stats and s not in intentional)
        gap = sorted(set(zeroed) & unaudited)
        if gap:
            report.add(Finding(
                check="scoring_coverage", severity="warning",
                message=f"unaudited scoring coefficients applied to projected stats: {gap}",
                entity="scoring-table", value=gap,
                review_action="These keys are 0.0 because no source was retrieved for them, so the "
                              "published FPTS understates the operator's real total. Read the value "
                              "from the operator's own scoring page. See "
                              "docs/10-roadmap-and-limitations.md.",
            ))
        other = sorted(set(zeroed) - set(gap))
        if other:
            report.add(Finding(
                check="scoring_coverage", severity="warning",
                message=f"scoring coefficients that are zero for projected stats: {other}",
                entity="scoring-table", value=other,
                review_action="A zero coefficient that is neither deliberate nor flagged unaudited "
                              "needs a human decision. See docs/09-irregularities.md.",
            ))
        if intentional & projected_stats:
            report.add(Finding(
                check="scoring_coverage", severity="info",
                message="stats deliberately scored at zero (another key carries the production): "
                        f"{sorted(intentional & projected_stats)}",
                entity="scoring-table", value=sorted(intentional & projected_stats),
                review_action="No action needed - these are documented representation overlaps, not "
                              "coverage gaps (see IR-15).",
            ))
        return

    # No table supplied: fall back to the original blunt behaviour.
    zeroed = sorted(s for s, v in coefficients.items() if v == 0 and s in projected_stats)
    if zeroed:
        report.add(Finding(
            check="scoring_coverage", severity="warning",
            message=f"scoring coefficients that are zero for projected stats: {zeroed}",
            entity="scoring-table", value=zeroed,
            review_action="A zero coefficient means the value was never audited or was deliberately "
                          "disabled. FPTS totals will understate the real operator total. Pass the "
                          "ScoringTable so deliberate zeros can be told apart from gaps.",
        ))


def check_representation_double_count(sport: str, site: str, report: QualityReport) -> None:
    """Fail loudly if the scoring table counts the same production twice.

    Uses :func:`rgengy.scoring.representation_audit`.  This is a table-level
    invariant rather than a data-level one, so it is checked once per run.
    """
    from rgengy import scoring
    report.checks_run.append("representation_double_count")
    key = f"{sport}:{site}"
    audit = scoring.representation_audit()
    if not any(f["key"] == key for f in audit) and key not in scoring.available():
        # "No findings" and "not applicable" must never look the same in a report:
        # an unshipped configuration has had NO invariant checked at all.
        report.add(Finding(
            check="representation_double_count", severity="warning",
            message=f"no scoring table is shipped for {key}, so its representation sets "
                    f"have not been audited at all",
            entity=key, value=sorted(scoring.available()),
            review_action=f"Shipped configurations: {sorted(scoring.available())}. Do not report "
                          f"{key} as clean; it was never checked.",
        ))
        return
    for finding in audit:
        if finding["key"] != key:
            continue
        report.add(Finding(
            check="representation_double_count", severity="critical",
            message=(f"{finding['key']} scores {'+'.join(finding['group'])} simultaneously "
                     f"({finding['values']}), counting the same production twice"),
            entity=finding["key"], value=finding["values"],
            review_action=finding["explanation"],
        ))


ALL_CHECKS: List[Callable[..., None]] = [
    check_zero_projection,
    check_duplicate_ids,
    check_implausible_values,
    check_stale_provenance,
    check_endpoint_failures,
    check_ownership_normalisation,
    check_scoring_coverage,
    check_representation_double_count,
]
