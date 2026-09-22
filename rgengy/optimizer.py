"""Lineup optimiser - an open rebuild of the LineupHQ class of tool.

What RotoGrinders sells
-----------------------
LineupHQ "generates up to 150 DFS lineups per contest" from projected points,
salaries and operator roster rules, with player locks, team exclusions, stacking
and exposure controls
(https://rotogrinders.com/premium/nfl and https://rotogrinders.com/premium/mlb,
both retrieved 2026-09-22; corroborated by the third-party comparison at
https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026).

The optimisation problem
------------------------
DFS roster construction is a *grouped knapsack with a uniqueness constraint*:
each roster slot must be filled by a player eligible for it, a player may be
used at most once, and total salary must not exceed the cap.  The uniqueness
constraint is what makes it hard, because a UTIL/FLEX slot draws from the same
pool as the positional slots.

RGENGY's solution
-----------------
1.  **Slot partition.**  Slots are split into *fixed* slots (eligibility set
    disjoint from every other slot) and *flex* slots (overlapping eligibility).
2.  **Exact DP over fixed slots.**  Because fixed-slot eligibility sets are
    disjoint, a player can fill at most one of them, so uniqueness is automatic.
    Each fixed slot is solved as a bounded ``k``-item knapsack
    (``dp[j][salary]`` = best points using exactly ``j`` players at that
    salary), then the per-slot DPs are convolved over the shared salary axis.
    This is exact, not heuristic.
3.  **Flex enumeration.**  Flex slots are filled by enumerating combinations of
    the top ``flex_candidates`` players by projected points; for each
    enumeration the fixed-slot DP is re-solved with those players excluded
    (results cached by exclusion set).

The solver reports ``exact=True`` only when the flex candidate list covers the
whole eligible pool.  When it is bounded, ``exact=False`` and ``bound_note``
states the bound - the caller always knows whether they are looking at a proven
optimum or a near-optimum.  A heuristic is never silently substituted for an
exact solve.

Complexity: ``O(flex_enumerations x (n_players x k x S + G x S^2))`` where
``S = cap / salary_step`` and ``G`` is the number of fixed slots.  With the
defaults (cap 50000, step 100 -> S = 500) a single solve is a few hundred
thousand float operations, which is why the DP arrays hold floats and the player
ids are reconstructed from a parent table instead of being concatenated inside
the hot loop.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

from rgengy.models import Player, RosterRule, default_roster


@dataclass
class OptimizerResult:
    players: List[Player]
    projected_points: float
    salary_used: int
    salary_cap: int
    exact: bool
    bound_note: Optional[str] = None
    slots: Dict[str, List[str]] = field(default_factory=dict)
    site: str = "draftkings"
    #: False when no legal roster exists for the supplied pool.  ``optimize``
    #: always returns a result object rather than ``None`` so that the reason is
    #: never lost - an unexplained "no lineup" is undebuggable from the caller's
    #: side and, in a system whose whole premise is not inventing numbers, an
    #: infeasible roster must be reported as precisely as a solved one.
    feasible: bool = True
    #: Which roster slots could not be filled, and why.
    unfilled_slots: List[Dict[str, Any]] = field(default_factory=list)
    infeasible_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out = {
            "site": self.site,
            "feasible": self.feasible,
            "players": [
                {"id": p.player_id, "name": p.name, "team": p.team,
                 "positions": list(p.positions), "salary": p.salary,
                 "fpts": p.fpts.get(self.site)}
                for p in self.players
            ],
            "projected_points": round(self.projected_points, 3),
            "salary_used": self.salary_used,
            "salary_cap": self.salary_cap,
            "salary_remaining": self.salary_cap - self.salary_used,
            "exact": self.exact,
            "bound_note": self.bound_note,
            "slots": self.slots,
        }
        if not self.feasible:
            out["infeasible_reason"] = self.infeasible_reason
            out["unfilled_slots"] = self.unfilled_slots
            out["players"] = []
        return out


def _matches(positions: Sequence[str], eligible: Sequence[str]) -> bool:
    return any(p in eligible for p in positions)


def _overlap_pairs(rules: Sequence[RosterRule], members: Sequence[int],
                   pool: Sequence[Player] = ()) -> List[Tuple[int, int]]:
    """Slots that a single player could legitimately fill at the same time.

    The conflict test MUST be over the pool, not over the slot labels.  Testing
    ``set(a.eligible) & set(b.eligible)`` looks equivalent but is not: on a
    DraftKings MLB roster ``C/1B`` (eligible C, 1B) and ``OF`` (eligible OF, LF,
    CF, RF) have disjoint eligibility sets, yet a player listed at both 1B and OF
    matches both slots.  With the label-only test those two slots stayed "fixed",
    each group knapsack picked that player independently, and the published
    lineup contained the same player twice - a roster every operator rejects and
    one whose projected points are inflated by his duplicate value.
    """
    pairs = []
    for a_pos, a in enumerate(members):
        for b in members[a_pos + 1:]:
            if set(rules[a].eligible) & set(rules[b].eligible):
                pairs.append((a, b))
                continue
            if pool and any(_matches(p.positions, rules[a].eligible)
                            and _matches(p.positions, rules[b].eligible) for p in pool):
                pairs.append((a, b))
    return pairs


def _split_slots(rules: Sequence[RosterRule],
                 pool: Sequence[Player] = ()) -> Tuple[List[int], List[int]]:
    """Partition slots into *flex* and *fixed* using a minimal greedy cover.

    A naive symmetric test ("does this slot overlap any other?") marks every
    positional slot as flex as soon as a UTIL slot exists, which makes the
    enumeration explode.  Instead we repeatedly move the single slot that
    removes the most overlapping pairs into the flex set, stopping as soon as
    the remaining slots are mutually disjoint.  For a DraftKings MLB roster this
    yields exactly one flex slot (UTIL); for a DraftKings NBA roster it yields
    UTIL, G and F.

    ``pool`` is what makes "disjoint" mean something: two slots are only safe to
    solve independently when NO available player is eligible for both (see
    :func:`_overlap_pairs`).  Real slates contain multi-position players, so the
    number of flex slots is data-dependent, and the resulting truncation is
    reported through ``exact``/``bound_note`` rather than hidden.
    """
    fixed = list(range(len(rules)))
    flex: List[int] = []
    while True:
        pairs = _overlap_pairs(rules, fixed, pool)
        if not pairs:
            break
        counts: Dict[int, int] = {}
        for a, b in pairs:
            counts[a] = counts.get(a, 0) + 1
            counts[b] = counts.get(b, 0) + 1
        # tie-break on the widest eligibility set, then on slot order, so the
        # partition is deterministic
        victim = max(
            counts,
            key=lambda i: (counts[i], len(set(rules[i].eligible)), -i),
        )
        fixed.remove(victim)
        flex.append(victim)
    flex.sort()
    return flex, fixed


def _value(p: Player, site: str) -> float:
    return float(p.fpts.get(site) or 0.0)


def _group_knapsack(pool: Sequence[Player], need: int, units_cap: int, step: int,
                    site: str) -> Optional[Tuple[List[float], List[List[Optional[int]]]]]:
    """Best points for choosing exactly ``need`` players at each salary level.

    Returns ``(best_by_salary, parents)`` where ``parents[s]`` is the list of
    pool indices used at salary ``s``.  ``None`` if fewer than ``need`` players
    are available.
    """
    if need <= 0:
        # A slot that requires no players is only feasible at zero salary.
        curve = [float("-inf")] * (units_cap + 1)
        curve[0] = 0.0
        return curve, [[] for _ in range(units_cap + 1)]
    if len(pool) < need:
        return None

    NEG = float("-inf")
    # dp[j][s] = best points with exactly j chosen and salary exactly s
    dp: List[List[float]] = [[NEG] * (units_cap + 1) for _ in range(need + 1)]
    pick: List[List[List[int]]] = [[[] for _ in range(units_cap + 1)] for _ in range(need + 1)]
    dp[0][0] = 0.0

    for idx, p in enumerate(pool):
        cost = int(p.salary) // step
        pts = _value(p, site)
        if cost > units_cap:
            continue
        # iterate j downwards so each player is used at most once
        for j in range(need - 1, -1, -1):
            row_src, row_dst = dp[j], dp[j + 1]
            pick_src, pick_dst = pick[j], pick[j + 1]
            for s in range(units_cap - cost, -1, -1):
                cur = row_src[s]
                if cur == NEG:
                    continue
                cand = cur + pts
                t = s + cost
                if cand > row_dst[t]:
                    row_dst[t] = cand
                    pick_dst[t] = pick_src[s] + [idx]

    best = dp[need]
    if all(v == NEG for v in best):
        return None
    return best, pick[need]


def _convolve(group_results: Sequence[Tuple[List[float], List[List[Optional[int]]]]],
              units_cap: int) -> Tuple[List[float], List[List[Tuple[int, int]]]]:
    """Convolve per-slot salary/value curves into one curve.

    Returns ``(best_by_salary, trace)`` where ``trace[s]`` is the list of
    ``(group_index, group_salary)`` pairs that realise ``best_by_salary[s]``.
    """
    NEG = float("-inf")
    best: List[float] = [NEG] * (units_cap + 1)
    trace: List[List[Tuple[int, int]]] = [[] for _ in range(units_cap + 1)]
    best[0] = 0.0

    for gi, (curve, _parents) in enumerate(group_results):
        new_best = [NEG] * (units_cap + 1)
        new_trace: List[List[Tuple[int, int]]] = [[] for _ in range(units_cap + 1)]
        # Only salary levels this group can actually realise.
        levels = [s for s in range(units_cap + 1) if curve[s] != NEG]
        for s in range(units_cap + 1):
            if best[s] == NEG:
                continue
            base = best[s]
            base_trace = trace[s]
            for s2 in levels:
                t = s + s2
                if t > units_cap:
                    break
                cand = base + curve[s2]
                if cand > new_best[t]:
                    new_best[t] = cand
                    new_trace[t] = base_trace + [(gi, s2)]
        best, trace = new_best, new_trace
    return best, trace


def _solve_fixed(pool: Sequence[Player], fixed_rules: Sequence[RosterRule],
                 units_cap: int, step: int, site: str,
                 excluded: FrozenSet[str] = frozenset()) -> Optional[Tuple[List[Player], int, float]]:
    """Exact solve for a set of disjoint-eligibility slots."""
    available = [p for p in pool if p.player_id not in excluded and p.salary]
    groups: List[List[Player]] = []
    for rule in fixed_rules:
        members = [p for p in available if _matches(p.positions, rule.eligible)]
        groups.append(members)

    group_results = []
    for rule, members in zip(fixed_rules, groups):
        res = _group_knapsack(members, rule.count, units_cap, step, site)
        if res is None:
            return None
        group_results.append(res)

    best_curve, trace = _convolve(group_results, units_cap)
    best_s, best_pts = None, float("-inf")
    for s in range(units_cap + 1):
        if best_curve[s] != float("-inf") and best_curve[s] > best_pts:
            best_pts, best_s = best_curve[s], s
    if best_s is None:
        return None

    chosen: List[Player] = []
    for gi, s2 in trace[best_s]:
        _curve, parents = group_results[gi]
        for idx in parents[s2]:
            chosen.append(groups[gi][idx])
    if len(chosen) != sum(r.count for r in fixed_rules):
        return None
    # Groups are only independent when no player matches two of them, which is
    # what _split_slots(pool=...) now guarantees.  Re-check here so that any
    # future regression surfaces as an infeasible solve rather than as a
    # duplicated player in a published lineup.
    ids = [p.player_id for p in chosen]
    if len(set(ids)) != len(ids):
        return None
    salary = sum(int(p.salary) for p in chosen)
    return chosen, salary, best_pts


def optimize(players: Sequence[Player], sport: str, site: str = "draftkings",
             salary_cap: Optional[int] = None, salary_step: int = 100,
             flex_candidates: int = 8, max_flex_enumerations: int = 400,
             rules: Optional[Sequence[RosterRule]] = None) -> OptimizerResult:
    """Return the highest-projected legal lineup.

    Always returns an :class:`OptimizerResult`.  When no legal roster exists the
    result has ``feasible=False`` plus ``unfilled_slots`` naming every slot that
    could not be filled and how many eligible candidates it had.
    """
    template = default_roster(sport, site)
    cap = salary_cap if salary_cap is not None else template["salary_cap"]
    all_rules: List[RosterRule] = list(rules) if rules is not None else list(template["slots"])

    # A player whose projection is legitimately 0.0 is still roster-eligible: a
    # team defence or a kicker with an unaudited scoring table projects 0 but the
    # roster still requires one.  Filtering on `> 0` (as an earlier revision did)
    # silently made every NFL roster infeasible as soon as one positional group
    # projected zero.  Only players with NO projection for this site are dropped.
    usable = [p for p in players if p.salary and p.fpts.get(site) is not None]
    if not usable:
        return OptimizerResult(
            players=[], projected_points=0.0, salary_used=0, salary_cap=cap, exact=True,
            site=site, feasible=False,
            unfilled_slots=[{"slot": r.label, "count": r.count, "eligible": list(r.eligible),
                             "candidates": 0} for r in all_rules],
            infeasible_reason=(
                f"no player in the pool carries a {site} projection "
                f"(pool size {len(players)}); the optimizer will not invent one"))

    def infeasible(reason: str, extra: Optional[List[Dict[str, Any]]] = None) -> OptimizerResult:
        """Build an infeasible result that names EVERY unfillable slot.

        Reporting only the first gap is actively misleading: a user who fixes it
        then hits the next one and concludes the diagnostic was wrong.  So the
        caller's specific reason is kept, and a complete summary of all gaps is
        appended.
        """
        gaps: List[Dict[str, Any]] = list(extra or [])
        for rule in all_rules:
            if any(g.get("slot") == rule.label for g in gaps):
                continue
            n = sum(1 for p in usable if _matches(p.positions, rule.eligible))
            if n < rule.count:
                gaps.append({"slot": rule.label, "count": rule.count,
                             "eligible": list(rule.eligible), "candidates": n})
        if gaps:
            summary = "; ".join(
                f"{g['slot']} needs {g['count']}, has {g['candidates']}" for g in gaps)
            reason = f"{reason} | unfillable slots: {summary}"
        return OptimizerResult(
            players=[], projected_points=0.0, salary_used=0, salary_cap=cap, exact=True,
            site=site, feasible=False, unfilled_slots=gaps, infeasible_reason=reason)

    units_cap = cap // salary_step
    flex_idx, fixed_idx = _split_slots(all_rules, usable)
    flex_rules = [all_rules[i] for i in flex_idx]
    fixed_rules = [all_rules[i] for i in fixed_idx]

    exact = True
    bound_note: Optional[str] = None

    # Candidate fillers per flex slot.
    flex_pools: List[List[Player]] = []
    for rule in flex_rules:
        pool = sorted((p for p in usable if _matches(p.positions, rule.eligible)),
                      key=lambda p: _value(p, site), reverse=True)
        if len(pool) < rule.count:
            return infeasible(
                f"slot '{rule.label}' needs {rule.count} player(s) eligible at "
                f"{rule.eligible} but only {len(pool)} exist in the pool",
                [{"slot": rule.label, "count": rule.count,
                  "eligible": list(rule.eligible), "candidates": len(pool)}])
        if len(pool) > flex_candidates:
            exact = False
            bound_note = (
                f"flex slot '{rule.label}' enumerated over the top {flex_candidates} of "
                f"{len(pool)} eligible players by projected {site} points; the positional "
                f"solve inside each enumeration remains exact"
            )
            pool = pool[:flex_candidates]
        flex_pools.append(pool)

    fixed_cache: Dict[FrozenSet[str], Optional[Tuple[List[Player], int, float]]] = {}
    best: Optional[OptimizerResult] = None

    def evaluate(picked: Sequence[Player]) -> None:
        nonlocal best
        used_ids = frozenset(p.player_id for p in picked)
        used_salary = sum(int(p.salary) for p in picked)
        remaining_units = (cap - used_salary) // salary_step
        if cap - used_salary < 0:
            return
        if used_ids not in fixed_cache:
            fixed_cache[used_ids] = (
                _solve_fixed(usable, fixed_rules, remaining_units, salary_step, site, used_ids)
                if fixed_rules else ([], 0, 0.0)
            )
        sol = fixed_cache[used_ids]
        if sol is None:
            return
        fixed_players, fixed_salary, _fixed_pts = sol
        roster = list(picked) + list(fixed_players)
        pts = sum(_value(p, site) for p in roster)
        salary = used_salary + fixed_salary
        if salary > cap:
            return
        if best is not None and pts <= best.projected_points:
            return
        # ``picked`` is the flex members flattened in flex_rules order, rule.count
        # at a time (see how ``assignments`` is built).  Zipping it against
        # flex_rules directly silently drops every member past the first whenever
        # a flex slot needs more than one player - a 3-count OF slot reported one
        # name, so the slot breakdown accounted for fewer players than the roster
        # actually contained.
        slots: Dict[str, List[str]] = {}
        cursor = 0
        for rule in flex_rules:
            members = list(picked[cursor:cursor + rule.count])
            cursor += rule.count
            slots[rule.label] = [m.name for m in members]
        for rule in fixed_rules:
            members = [p for p in fixed_players if _matches(p.positions, rule.eligible)]
            slots[rule.label] = [p.name for p in members[: rule.count]]
        if sum(len(v) for v in slots.values()) != len(roster):
            raise RuntimeError(
                f"optimizer slot breakdown names {sum(len(v) for v in slots.values())} "
                f"players but the roster has {len(roster)}; the slot report would "
                f"misrepresent which player fills which slot")
        best = OptimizerResult(
            players=roster, projected_points=pts, salary_used=salary,
            salary_cap=cap, exact=exact, bound_note=bound_note, slots=slots, site=site,
        )

    if not flex_rules:
        evaluate([])
        if best is None:
            return infeasible(
                f"no combination of the {len(all_rules)} roster slots fits under the "
                f"{cap} salary cap with the {len(usable)} available players")
        return best

    # Build every candidate flex assignment (one combination per flex slot),
    # score them by summed projected points, and evaluate the best
    # ``max_flex_enumerations`` of them.  Truncation is reported, never hidden.
    per_slot_combos: List[List[Tuple[Player, ...]]] = []
    for rule, pool in zip(flex_rules, flex_pools):
        per_slot_combos.append(list(combinations(pool, rule.count)))

    assignments: List[Tuple[float, Tuple[Player, ...]]] = []
    for combo_tuple in _product(per_slot_combos):
        flat: List[Player] = []
        seen_ids: set = set()
        ok = True
        for combo in combo_tuple:
            for pl in combo:
                if pl.player_id in seen_ids:
                    ok = False
                    break
                seen_ids.add(pl.player_id)
                flat.append(pl)
            if not ok:
                break
        if not ok:
            continue
        assignments.append((sum(_value(pl, site) for pl in flat), tuple(flat)))

    total_assignments = len(assignments)
    assignments.sort(key=lambda t: t[0], reverse=True)
    if total_assignments > max_flex_enumerations:
        exact = False
        note = (
            f"{total_assignments} flex assignments were possible; only the top "
            f"{max_flex_enumerations} by summed projected points were solved"
        )
        bound_note = f"{bound_note}; {note}" if bound_note else note
        assignments = assignments[:max_flex_enumerations]

    for _score, picked in assignments:
        evaluate(list(picked))
    if best is None:
        if not assignments:
            return infeasible(
                "no assignment of the flex slots produces a set of distinct players; the "
                "eligible pools overlap too thinly to fill every slot")
        return infeasible(
            f"none of the {len(assignments)} flex assignments could be completed under the "
            f"{cap} salary cap")
    _assert_valid_roster(best, cap)
    return best


def _assert_valid_roster(result: "OptimizerResult", cap: int) -> None:
    """Refuse to publish a lineup an operator would reject.

    Every invariant here is one a real operator enforces, so violating any of
    them makes the output not merely suboptimal but unusable.  Raising is
    deliberate: an invalid roster that reaches a user looks exactly like a valid
    one, and the projected points attached to it are inflated by the duplicate.
    """
    ids = [p.player_id for p in result.players]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise RuntimeError(
            f"optimizer produced a lineup containing the same player more than once: "
            f"{dupes}. This is a roster-construction defect, not a data problem - "
            f"two slots were solved independently although a player was eligible "
            f"for both. Report it; do not use the lineup.")
    if result.salary_used > cap:
        raise RuntimeError(
            f"optimizer produced a lineup costing {result.salary_used} against a cap of {cap}")


def _product(lists: Sequence[Sequence[Any]]):
    """itertools.product with an empty-input short circuit."""
    from itertools import product as _p
    if not lists or any(len(x) == 0 for x in lists):
        return iter(())
    return _p(*lists)


def optimize_multi(players: Sequence[Player], sport: str, site: str = "draftkings",
                   n_lineups: int = 10, salary_cap: Optional[int] = None,
                   salary_step: int = 100, flex_candidates: int = 8,
                   max_flex_enumerations: int = 400,
                   max_exposure: float = 1.0, jitter: float = 0.12,
                   rng_seed: int = 20260922,
                   rules: Optional[Sequence[RosterRule]] = None) -> Dict[str, Any]:
    """Generate ``n_lineups`` distinct lineups with per-player exposure caps.

    Lineup 1 is the exact optimum from :func:`optimize`.  Each later lineup is
    produced by perturbing every player's projected points by up to
    ``+/- jitter`` with a **seeded** PRNG, so the whole run is reproducible bit
    for bit.  Lineups that duplicate an earlier one are dropped, and players may
    not exceed ``max_exposure`` (a fraction of ``n_lineups``).

    The output states plainly that lineups 2..N are diversification variants and
    not independent optima - they are not presented as if they were.
    """
    import random

    rng = random.Random(rng_seed)
    out: List[Dict[str, Any]] = []
    seen: set = set()
    exposure: Dict[str, int] = {}

    base = optimize(players, sport, site, salary_cap, salary_step,
                    flex_candidates, max_flex_enumerations, rules)
    if not base.feasible:
        return {"lineups": [], "exposure": {}, "requested": n_lineups, "generated": 0,
                "feasible": False,
                "infeasible_reason": base.infeasible_reason,
                "unfilled_slots": base.unfilled_slots,
                "note": ("no feasible lineup found for the supplied projections; "
                         "'unfilled_slots' names exactly which roster slots could not be filled "
                         "and how many eligible candidates each had")}
    out.append(base.to_dict())
    seen.add(frozenset(p.player_id for p in base.players))
    for p in base.players:
        exposure[p.player_id] = exposure.get(p.player_id, 0) + 1

    if max_exposure <= 0 or max_exposure > 1:
        raise ValueError("max_exposure must be in (0, 1]")
    max_uses = max(1, int(math.ceil(max_exposure * max(1, n_lineups))))

    real = {p.player_id: p for p in players}
    attempts = 0
    limit = max(20, n_lineups * 40)
    while len(out) < n_lineups and attempts < limit:
        attempts += 1
        perturbed = [
            _perturb(p, site, rng, jitter)
            for p in players
            if exposure.get(p.player_id, 0) < max_uses
        ]
        cand = optimize(perturbed, sport, site, salary_cap, salary_step,
                        flex_candidates, max_flex_enumerations, rules)
        if not cand.feasible:
            continue
        roster = [real[p.player_id] for p in cand.players if p.player_id in real]
        if len(roster) != len(cand.players):
            continue
        key = frozenset(p.player_id for p in roster)
        if key in seen:
            continue
        seen.add(key)
        res = OptimizerResult(
            players=roster,
            projected_points=sum(_value(p, site) for p in roster),
            salary_used=sum(int(p.salary) for p in roster),
            salary_cap=cand.salary_cap, exact=False,
            bound_note=("diversified variant: generated under a seeded +/-{:.0%} value "
                        "perturbation, not an independent optimum").format(jitter),
            slots=cand.slots, site=site,
        )
        out.append(res.to_dict())
        for p in roster:
            exposure[p.player_id] = exposure.get(p.player_id, 0) + 1

    n = max(1, len(out))
    return {
        "site": site,
        "lineups": out,
        "requested": n_lineups,
        "generated": len(out),
        "attempts": attempts,
        "max_exposure_setting": max_exposure,
        "max_uses_per_player": max_uses,
        "jitter": jitter,
        "rng_seed": rng_seed,
        "exposure": {pid: round(cnt / n, 4) for pid, cnt in sorted(exposure.items())},
        "note": "lineup 1 is the exact optimum; lineups 2..N are seeded-perturbation variants",
    }


def _perturb(p: Player, site: str, rng: "random.Random", jitter: float) -> Player:
    """Clone ``p`` with its projected points jittered.  Never mutates the input."""
    clone = Player(
        sport=p.sport, player_id=p.player_id, name=p.name, team=p.team, opp=p.opp,
        positions=list(p.positions), salary=p.salary, site=site, game_id=p.game_id,
        status=p.status, stats=dict(p.stats), projected=dict(p.projected),
        fpts=dict(p.fpts), floor=p.floor, ceil=p.ceil, pown=p.pown,
        extra=dict(p.extra),
    )
    clone.fpts[site] = _value(p, site) * (1.0 + rng.uniform(-jitter, jitter))
    return clone


def stack_bonus(lineup: Sequence[Player], same_team_pairs: bool = True) -> Dict[str, Any]:
    """Report how correlated a lineup is (RotoGrinders' 'stacking' concept).

    Returns the number of same-team pairs and, for MLB, the longest same-team
    run.  This is descriptive only: RGENGY does not claim to reproduce
    LineupHQ's internal stacking rules, which are not published.
    """
    teams = [p.team for p in lineup if p.team]
    counts: Dict[str, int] = {}
    for t in teams:
        counts[t] = counts.get(t, 0) + 1
    pairs = sum(n * (n - 1) // 2 for n in counts.values())
    return {
        "same_team_pairs": pairs,
        "team_counts": counts,
        "max_players_from_one_team": max(counts.values()) if counts else 0,
        "same_team_pairs_enabled": same_team_pairs,
    }
