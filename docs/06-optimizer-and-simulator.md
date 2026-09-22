# 06 - Optimizer and simulator

Two independent stages that both have to be *right*, not merely plausible: a
lineup an operator would reject is worthless however good its projection looks,
and a contest simulation whose invariants do not hold is worse than no simulation.

---

## Optimizer

`rgengy/optimizer.py`. A grouped knapsack solved exactly by dynamic programming
over salary, with the positional-eligibility structure handled by a
flex/fixed slot partition.

```
optimize(players, sport, site, salary_cap=None, salary_step=100,
         flex_candidates=8, max_flex_enumerations=400, rules=None) -> OptimizerResult

optimize_multi(..., n_lineups=10, max_exposure=1.0, jitter=0.12,
               rng_seed=20260922) -> dict
```

### How it solves

1. **`_split_slots(rules, pool)`** partitions the roster into *flex* slots (whose
   eligibility overlaps another slot's) and *fixed* slots (mutually exclusive).
   It repeatedly moves the single slot that removes the most conflicting pairs,
   stopping as soon as the rest are independent. For DraftKings MLB that is one
   flex slot (UTIL); for DraftKings NBA it is UTIL, G and F.
2. **Flex assignments** are enumerated as combinations, deduplicated by player id,
   scored by summed projected points, and the best `max_flex_enumerations` are
   solved. Truncation is reported through `exact=False` and `bound_note`, never
   hidden.
3. **Fixed slots** are solved exactly by `_group_knapsack` (one DP per slot group,
   iterating the chosen-count downwards so a player is used at most once within a
   group) and combined by `_convolve` into a single salary/value curve.
4. The best complete assignment wins. `_value()` returns **raw** projected points,
   so the objective is the operator's own scoring, not a value-per-dollar proxy.

### The conflict test must be over the pool

This was the most serious defect found in pass 3. Two slots are only safe to solve
independently when **no available player is eligible for both**. Testing whether
their *eligibility sets* intersect looks equivalent and is not:

| slot | eligible | 
| --- | --- |
| `C/1B` | C, 1B |
| `OF` | OF, LF, CF, RF |

Those sets are disjoint - but a player listed at both `1B` and `OF` matches both
slots. With the label-only test both stayed "fixed", each group knapsack picked
that player independently, and the published roster contained him **twice**, with
his points counted twice. Every operator rejects that lineup.

`_overlap_pairs(rules, members, pool)` now flags a conflict when any player in the
pool matches both slots. The consequence is honest: the number of flex slots is
**data-dependent**, because it depends on how many multi-position players the slate
actually contains, and the resulting enumeration truncation is reported rather than
absorbed.

Two guards back this up:

- `_solve_fixed` re-checks for duplicate ids among its chosen players and returns
  `None` (an infeasible solve) rather than emitting a duplicated roster;
- `_assert_valid_roster()` runs before `optimize()` returns and **raises** if the
  winning lineup contains a duplicate or exceeds the cap. An invalid roster that
  reaches a user looks exactly like a valid one, and its projected points are
  inflated, so this is a hard failure by design.

`tests/test_optimizer.py::TestRosterUniqueness` reproduces the exact defect: a
pool containing one `1B`/`OF` player, asserted to produce no duplicates in any
lineup, plus direct tests that `_overlap_pairs` sees the two slots as disjoint
without a pool and conflicting with one.

### Optimality is checked against brute force

The suite enumerates every legal roster for a small pool and asserts the DP finds
the same total. Note `n = sum(rule.count for rule in rules)`, not `len(rules)` -
DraftKings NFL is six *rules* covering nine *slots*.

### Infeasibility is reported completely

`optimize()` always returns an `OptimizerResult`; it never returns `None` and never
raises for an infeasible slate. `infeasible_reason` names **every** unfilled slot
and how many eligible candidates each had. It originally named only the first gap,
so a user would fix one slot and immediately hit the next - a frustrating loop that
tells them nothing about the real shape of the problem. `unfilled_slots` carries
the same detail structurally.

The pipeline propagates it: the optimizer stage reason and a run warning both carry
the full explanation plus the pool size and the salary cap, instead of a bare "no
feasible lineup could be built".

### Multiple lineups

Lineup 1 is the exact optimum. Each later lineup perturbs every player's projected
points by up to +/- `jitter` (12%) with a **seeded** PRNG
(`rng_seed=20260922`), so a run is reproducible bit for bit. Duplicates of an
earlier lineup are dropped, and no player may exceed `max_exposure` (a fraction of
`n_lineups`).

The output states plainly that lineups 2..N are **diversification variants and not
independent optima** - `bound_note` says so on each one. Presenting a jittered
variant as a second optimum would be a claim RGENGY cannot support.

### The slot breakdown must account for every player

`slots` maps each roster label to the players filling it. A second pass-3 defect:
`zip(flex_rules, picked)` paired one flex member per *rule*, but `picked` is the
flex members flattened in rule order, `rule.count` at a time. With a 3-count `OF`
flex slot the breakdown named one outfielder, so it accounted for 8 of the 10
players in the roster - a report that misrepresents which player fills which slot.
It now slices `picked` by `rule.count`, and raises if the breakdown's total does
not equal the roster size.

---

## Simulator

`rgengy/simulator.py`. Builds a synthetic field, samples outcomes, and reports
cash / top-10 / top-1 rates.

```
simulate_contest(lineups, player_pool, sport, site, n_sims=2000, field_size=200,
                 sharp_fraction=0.5, entry_fee=15.0, seed=20260922,
                 user_mode="poisson", field_mode="normal", payout=None, rules=None)
```

`lineups` is the **list** from `optimize_multi(...)['lineups']`. Passing the whole
dict used to fail with a confusing `AttributeError` deep inside the sampling loop;
it now raises a `TypeError` naming the mistake, and mode validation happens before
the empty-lineups short circuit so a bad `user_mode` is reported even when there is
nothing to simulate.

### Payouts

`PayoutStructure(entry_fee, payout_fractions)` maps a rank threshold to a
multiple. `multiple_for_rank(rank, field_size)` uses the smallest satisfied
threshold.

Two edge cases that were both wrong at some point:

- **Tiny fields.** When the field is too small for any threshold to match, rank 1
  gets the largest reachable multiple (or the maximum overall if none is
  reachable), flagged via `extrapolated_for_small_field`. The fallback originally
  applied to *every* rank, which paid 200x to **last place**. It now applies only
  to rank 1; every other rank gets 0.0 when no threshold matches.
- **Rounding.** All rates are rounded to 6 decimal places. They previously mixed
  4dp and 6dp, which broke the invariant that
  `cash rate >= top-10 rate >= top-1 rate` - the ordering a user actually reads,
  violated by nothing but display rounding.

### The field must not contain the user

On a small pool the "sharp" portion of the field collapsed onto the user's own
roster, producing a **100% cash rate** from self-competition. `build_field()` now
removes any field entry identical to one of the user's rosters and reports the
count in `field_duplicates_removed`, so the number is visible rather than quietly
absorbed.

### Known limitation

Player outcomes are drawn from a normal approximation built on the projected mean
and a standard deviation derived from the floor/ceiling band (**L-06**). Real
fantasy output is a sum of discrete, correlated events, so tail behaviour is
understated: a normal draw cannot produce a four-home-run game. The cash / top-10 /
top-1 *ordering* is preserved, but the magnitudes are not trustworthy for
large-field GPP decisions. Fixing it needs a per-stat correlated event model, which
needs historical play-by-play - see [10 - remaining work](10-roadmap-and-limitations.md).
