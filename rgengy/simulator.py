"""Contest simulator - an open rebuild of the SimLabs class of tool.

What RotoGrinders sells
-----------------------
SimLabs lets a subscriber "easily simulate every aspect of a DFS slate, from the
plays in each game down to the results of a DFS contest"
(https://rotogrinders.com/premium/mlb, retrieved 2026-09-22).  A third-party
comparison describes the difference between a *game* simulator and a *contest*
simulator: the latter "sims the tournament itself and ranks builds by simulated
ROI" (https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026,
retrieved 2026-09-22).  RGENGY implements the contest simulator.

How it works
------------
1.  **Field construction (once per run, not per simulation).**  A field of
    ``field_size`` lineups is built the way a real field is built: a
    ``sharp_fraction`` of it comes from the optimiser under seeded value
    perturbations (different players solving the same slate slightly
    differently), and the rest comes from proportional sampling of projected
    ownership (the casual part of a field).  A field made only of proportional
    sampling is far weaker than an optimised lineup and produces absurd cash
    rates; a field made only of optimiser output is far stronger than reality.
    The mixture is the honest model and the ratio is an explicit parameter.

2.  **Outcome simulation (per simulation).**  Each projected raw stat is an
    independent Poisson variable around its projected mean, and a lineup's score
    is the sum of its players' fantasy points under the audited scoring table.
    Two modes are offered:

    ``poisson``  draws every stat for every player in every lineup.  Most
                 faithful, and the mode used for the user's own lineups.
    ``normal``   draws each *lineup total* from a normal with the analytically
                 exact mean and variance of that Poisson sum
                 (``mean = sum(c_i*mu_i)``, ``var = sum(c_i^2*mu_i)``).  Used for
                 the field, where the per-stat detail cannot change the ranking
                 but would cost orders of magnitude more time.

3.  **Payouts and reporting.**  Field and user scores are ranked together; each
    user lineup gets a cash rate, top-10% rate, top-1 rate, mean finish
    percentile and ROI.

Everything is seeded, so a run reproduces exactly.  The payout structure in
:data:`PayoutStructure` is RGENGY's generic top-heavy GPP shape and is **not**
transcribed from any operator's real contest - inventing a real prize structure
would be a fabrication.  Pass the operator's published structure when you have
it.  The Poisson assumption under-disperses stats that are in reality
over-dispersed; see ``docs/10-roadmap-and-limitations.md`` item L-06.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from rgengy.models import Player, default_roster
from rgengy.scoring import load


@dataclass
class PayoutStructure:
    """Flat top-heavy payout structure, expressed as multiples of the entry fee."""

    entry_fee: float = 15.0
    #: set when a field was too small for any published bucket to apply and the
    #: top multiple had to be awarded by definition rather than by threshold
    extrapolated_for_small_field: bool = False
    payout_fractions: Dict[float, float] = field(default_factory=lambda: {
        0.0002: 200.0,   # first place in a very large field
        0.001: 100.0,
        0.005: 40.0,
        0.01: 20.0,
        0.02: 10.0,
        0.05: 4.0,
        0.10: 2.0,
        0.20: 1.0,       # double-up / cash
    })

    def multiple_for_rank(self, rank: int, field_size: int) -> float:
        """Payout multiple for a 1-based ``rank`` in a field of ``field_size``.

        The bucket is the *smallest* threshold the finish fraction satisfies, so
        a better finish always maps to a better multiple.  (An earlier revision
        took the LAST matching bucket, which paid first place the cash prize.)

        Very small fields need one extra rule.  The thresholds are percentages of
        the field, so in a 5-entry field even the winner sits at frac=0.2 and no
        top bucket can match - yet first place obviously wins something.  The top
        prize for a field of this size is therefore the largest multiple among
        thresholds the field can actually reach (``threshold * field_size >= 1``),
        and if the field is smaller than every threshold can reach, the largest
        multiple in the structure is awarded and the extrapolation is recorded.
        """
        if field_size <= 0 or rank <= 0:
            return 0.0
        if not self.payout_fractions:
            return 0.0
        frac = rank / field_size
        for threshold, multiple in sorted(self.payout_fractions.items()):
            if frac <= threshold:
                return multiple
        # Only the WINNER can be paid outside the thresholds.  Applying this
        # fallback to any rank would pay 200x to last place in a small field.
        if rank != 1:
            return 0.0
        reachable = [m for t, m in self.payout_fractions.items() if t * field_size >= 1.0]
        if reachable:
            return max(reachable)
        self.extrapolated_for_small_field = True
        return max(self.payout_fractions.values())

    @property
    def cash_fraction(self) -> float:
        return max(self.payout_fractions) if self.payout_fractions else 0.0


# ---------------------------------------------------------------------------
# outcome maths
# ---------------------------------------------------------------------------

def lineup_moments(players: Sequence[Player], site: str,
                   coefficients: Dict[str, float]) -> Tuple[float, float]:
    """Analytic ``(mean, sd)`` of a lineup's fantasy points.

    Exact for a sum of independent Poisson components scaled by scoring
    coefficients.  Used by the ``normal`` draw mode and for the reported sd.
    """
    mean = 0.0
    var = 0.0
    for p in players:
        for stat, mu in (p.projected or {}).items():
            c = coefficients.get(stat, 0.0)
            if not c or not mu or mu <= 0:
                continue
            mean += c * mu
            var += (c * c) * mu
    return mean, math.sqrt(max(0.0, var))


def _poisson_draw(lam: float, rng: random.Random) -> int:
    """Knuth's algorithm, with a normal approximation for large lambdas."""
    if lam <= 0:
        return 0
    if lam > 400:
        return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))
    threshold = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= threshold:
            return k
        k += 1
        if k > 100000:      # pathological guard; unreachable for realistic lambdas
            return k


def sample_player_fpts(player: Player, site: str, coefficients: Dict[str, float],
                       rng: random.Random) -> float:
    """One simulated fantasy-point outcome for ``player`` (per-stat Poisson)."""
    total = 0.0
    for stat, mu in (player.projected or {}).items():
        c = coefficients.get(stat, 0.0)
        if not c or not mu or mu <= 0:
            continue
        total += c * _poisson_draw(float(mu), rng)
    return total


# ---------------------------------------------------------------------------
# field construction
# ---------------------------------------------------------------------------

def _eligible_for(player: Player, rule) -> bool:
    return any(pos in rule.eligible for pos in player.positions)


def build_field(player_pool: Sequence[Player], sport: str, site: str,
                field_size: int, sharp_fraction: float = 0.5,
                seed: int = 20260922,
                rules: Optional[Sequence[Any]] = None) -> Dict[str, Any]:
    """Build a mixed field of lineups: part optimised, part proportional-sampled.

    Returns ``{"lineups": [[player, ...], ...], "n_sharp": int, "n_casual": int}``.
    Deterministic for a given seed.
    """
    if not (0.0 <= sharp_fraction <= 1.0):
        raise ValueError("sharp_fraction must be between 0 and 1")
    rng = random.Random(seed)
    template = list(rules) if rules is not None else default_roster(sport, site)["slots"]
    n_sharp = int(round(field_size * sharp_fraction))
    n_casual = max(0, field_size - n_sharp)

    lineups: List[List[Player]] = []

    if n_sharp:
        from rgengy.optimizer import optimize_multi
        multi = optimize_multi(
            player_pool, sport, site, n_lineups=n_sharp,
            flex_candidates=6, max_flex_enumerations=120,
            max_exposure=1.0, jitter=0.18, rng_seed=seed, rules=template,
        )
        by_id = {p.player_id: p for p in player_pool}
        for entry in multi.get("lineups", []):
            roster = [by_id[e["id"]] for e in entry["players"] if e["id"] in by_id]
            if roster:
                lineups.append(roster)
        n_sharp = len(lineups)

    if n_casual:
        weights = [
            (p.pown if p.pown and p.pown > 0
             else max(1e-9, (p.fpts.get(site) or 0.0)) ** 2)
            for p in player_pool
        ]
        for _ in range(n_casual):
            roster = _sample_roster(player_pool, weights, template, rng)
            if roster:
                lineups.append(roster)

    return {"lineups": lineups, "n_sharp": n_sharp,
            "n_casual": len(lineups) - n_sharp,
            "requested": field_size, "sharp_fraction": sharp_fraction}


def _sample_roster(pool: Sequence[Player], weights: Sequence[float],
                   template: Sequence[Any], rng: random.Random) -> List[Player]:
    roster: List[Player] = []
    used: set = set()
    for rule in template:
        for _slot in range(rule.count):
            candidates = [(p, w) for p, w in zip(pool, weights)
                          if p.player_id not in used and _eligible_for(p, rule)]
            if not candidates:
                continue
            total = sum(w for _p, w in candidates)
            if total <= 0:
                continue
            r = rng.random() * total
            acc = 0.0
            pick = candidates[-1][0]
            for p, w in candidates:
                acc += w
                if r <= acc:
                    pick = p
                    break
            used.add(pick.player_id)
            roster.append(pick)
    return roster


# ---------------------------------------------------------------------------
# contest simulation
# ---------------------------------------------------------------------------

@dataclass
class LineupResult:
    label: str
    projected: float
    simulated_mean: float
    simulated_sd: float
    simulated_max: float
    cash_rate: float
    top10_rate: float
    top1_rate: float
    mean_rank_pct: float
    roi: float
    n_sims: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "projected_points": round(self.projected, 3),
            "simulated_mean": round(self.simulated_mean, 3),
            "simulated_sd": round(self.simulated_sd, 3),
            "simulated_max": round(self.simulated_max, 3),
            # All rates round to the same precision: mixing 4dp and 6dp broke the
            # cash >= top10 >= top1 invariant purely through rounding.
            "cash_rate": round(self.cash_rate, 6),
            "top10_rate": round(self.top10_rate, 6),
            "top1_rate": round(self.top1_rate, 6),
            "mean_rank_pct": round(self.mean_rank_pct, 6),
            "roi": round(self.roi, 6),
            "n_sims": self.n_sims,
        }


def _count_greater(sorted_desc: Sequence[float], x: float) -> int:
    """Count of entries in a descending-sorted list strictly greater than ``x``."""
    lo, hi = 0, len(sorted_desc)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_desc[mid] > x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def simulate_contest(lineups: Sequence[Dict[str, Any]], player_pool: Sequence[Player],
                     sport: str, site: str = "draftkings", n_sims: int = 2000,
                     field_size: int = 200, sharp_fraction: float = 0.5,
                     entry_fee: float = 15.0, seed: int = 20260922,
                     user_mode: str = "poisson", field_mode: str = "normal",
                     payout: Optional[PayoutStructure] = None,
                     rules: Optional[Sequence[Any]] = None) -> Dict[str, Any]:
    """Rank the user's lineups against a simulated field and report ROI.

    ``lineups`` is the output of :func:`rgengy.optimizer.optimize_multi`.
    Deterministic for a given ``seed``.
    """
    # Argument validation happens BEFORE any short circuit, so a bad mode is
    # reported even when there are no lineups to simulate.
    if user_mode not in ("poisson", "normal") or field_mode not in ("poisson", "normal"):
        raise ValueError(f"mode must be 'poisson' or 'normal', got user_mode={user_mode!r} "
                         f"field_mode={field_mode!r}")
    if not lineups:
        return {"results": [], "note": "no lineups supplied", "n_sims": 0}
    # `lineups` must be the LIST at result["lineups"], not the whole dict returned
    # by optimize_multi.  Iterating that dict yields its keys, which then fails
    # deep inside the ranking loop with a confusing AttributeError, so the shape
    # is checked up front with a message that names the mistake.
    if isinstance(lineups, dict):
        raise TypeError(
            "simulate_contest expects the list of lineups, but was given the whole "
            "optimize_multi() result dict. Pass result['lineups'].")
    for i, entry in enumerate(lineups):
        if not isinstance(entry, dict):
            raise TypeError(
                f"lineups[{i}] is {type(entry).__name__}, expected a dict with a 'players' "
                f"list as produced by optimizer.optimize_multi(...)['lineups']")

    rng = random.Random(seed)
    payout = payout or PayoutStructure(entry_fee=entry_fee)
    coefficients = load(sport, site).points
    by_id = {p.player_id: p for p in player_pool}

    # --- build the field once -------------------------------------------
    field_build = build_field(player_pool, sport, site, field_size,
                              sharp_fraction=sharp_fraction, seed=seed, rules=rules)
    field_lineups: List[List[Player]] = field_build["lineups"]
    if not field_lineups:
        return {"results": [], "note": "could not build a simulated field", "n_sims": 0}

    # --- resolve the user's lineups to players ---------------------------
    user_rosters: List[List[Player]] = []
    user_labels: List[str] = []
    user_projected: List[float] = []
    for i, entry in enumerate(lineups):
        roster = [by_id[p["id"]] for p in entry.get("players", []) if p.get("id") in by_id]
        if not roster:
            continue
        user_rosters.append(roster)
        user_labels.append(entry.get("label") or f"lineup_{i + 1}")
        user_projected.append(float(entry.get("projected_points") or 0.0))
    if not user_rosters:
        return {"results": [], "note": "no user lineup resolved to known players", "n_sims": 0}

    # A simulated field that contains the user's own exact roster means the user
    # is competing against themselves and cannot lose, which is what produced a
    # 100% cash rate for an "all-sharp" field on a small player pool.  Identical
    # rosters are removed and the count is reported.
    user_keys = {frozenset(p.player_id for p in r) for r in user_rosters}
    duplicates_removed = sum(1 for r in field_lineups
                             if frozenset(p.player_id for p in r) in user_keys)
    if duplicates_removed:
        field_lineups = [r for r in field_lineups
                         if frozenset(p.player_id for p in r) not in user_keys]
    if not field_lineups:
        return {"results": [], "n_sims": 0,
                "note": ("every simulated field entry was identical to one of the user's own "
                         "lineups, so there is no opponent to rank against. Increase the player "
                         "pool or lower sharp_fraction."),
                "field_duplicates_removed": duplicates_removed}

    field_moments = [lineup_moments(roster, site, coefficients) for roster in field_lineups]
    user_moments = [lineup_moments(r, site, coefficients) for r in user_rosters]

    scores: List[List[float]] = [[] for _ in user_rosters]
    ranks: List[List[float]] = [[] for _ in user_rosters]
    payouts: List[List[float]] = [[] for _ in user_rosters]
    winners: List[float] = []
    field_means: List[float] = []

    for _sim in range(n_sims):
        f_scores: List[float] = []
        for (mu, sd), roster in zip(field_moments, field_lineups):
            if field_mode == "poisson":
                f_scores.append(sum(sample_player_fpts(p, site, coefficients, rng) for p in roster))
            else:
                f_scores.append(max(0.0, rng.gauss(mu, sd)))
        f_scores.sort(reverse=True)
        winners.append(f_scores[0])
        if _sim == 0:
            field_means = f_scores

        for ui, roster in enumerate(user_rosters):
            mu, sd = user_moments[ui]
            if user_mode == "poisson":
                score = sum(sample_player_fpts(p, site, coefficients, rng) for p in roster)
            else:
                score = max(0.0, rng.gauss(mu, sd))
            scores[ui].append(score)
            rank = 1 + _count_greater(f_scores, score)
            ranks[ui].append(rank / len(f_scores))
            payouts[ui].append(payout.multiple_for_rank(rank, len(f_scores)) * payout.entry_fee)

    results: List[LineupResult] = []
    for ui in range(len(user_rosters)):
        s = scores[ui]
        mean = sum(s) / len(s)
        sd = math.sqrt(sum((x - mean) ** 2 for x in s) / max(1, len(s) - 1)) if len(s) > 1 else 0.0
        pay = payouts[ui]
        cost = payout.entry_fee * len(s)
        results.append(LineupResult(
            label=user_labels[ui],
            projected=user_projected[ui],
            simulated_mean=mean, simulated_sd=sd,
            simulated_max=max(s) if s else 0.0,
            cash_rate=sum(1 for x in pay if x > 0) / len(pay),
            top10_rate=sum(1 for r in ranks[ui] if r <= 0.10) / len(ranks[ui]),
            top1_rate=sum(1 for r in ranks[ui] if r <= 1.0 / len(field_lineups)) / len(ranks[ui]),
            mean_rank_pct=sum(ranks[ui]) / len(ranks[ui]),
            roi=(sum(pay) - cost) / cost if cost else 0.0,
            n_sims=n_sims,
        ))

    return {
        "sport": sport,
        "site": site,
        "n_sims": n_sims,
        "field_size": len(field_lineups),
        "field_size_requested": field_size,
        "field_duplicates_removed": duplicates_removed,
        "field_sharp": field_build["n_sharp"],
        "field_casual": field_build["n_casual"],
        "sharp_fraction": sharp_fraction,
        "user_mode": user_mode,
        "field_mode": field_mode,
        "entry_fee": payout.entry_fee,
        "payout_structure": {str(k): v for k, v in sorted(payout.payout_fractions.items())},
        "seed": seed,
        "field_winners": {
            "mean": round(sum(winners) / len(winners), 3) if winners else None,
            "min": round(min(winners), 3) if winners else None,
            "max": round(max(winners), 3) if winners else None,
        },
        "results": [r.to_dict() for r in results],
        "assumptions": [
            "raw stats are independent Poisson variables around their projected means",
            "the field is a mixture of optimiser output and ownership-proportional sampling; "
            "the ratio is `sharp_fraction` and is a modelling choice, not a measurement",
            "field totals are drawn from the analytic normal approximation by default "
            "(`field_mode='normal'`); pass `field_mode='poisson'` for per-stat draws",
            "the payout structure is RGENGY's generic top-heavy GPP shape unless the caller "
            "supplies the operator's published structure",
            "players shared between lineups are simulated independently, so correlated "
            "outcomes (a stack all having the same good night) are NOT modelled",
            "field entries identical to one of the user's own lineups are removed, so the "
            "user is never ranked against a copy of themselves",
        ],
    }
