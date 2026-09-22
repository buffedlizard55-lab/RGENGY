# 01 - Method

How this audit was run, and the rules every claim in `docs/` had to satisfy.

---

## The four rules

**1. A claim needs a retrieved source, or it is not a claim.**
Every scoring coefficient, roster slot and endpoint carries the URLs it came from
and an evidence class. Where nothing was retrieved, the value is marked
`not-audited` and excluded from published totals under `--strict`. Guessing a
value and marking it verified is the failure mode this whole structure exists to
prevent.

**2. Official beats secondary, and the gap is recorded.**
A league's own feed or an operator's own document outranks a strategy blog. In the
second audit pass FanDuel's public rules page (fanduel.com/rules) and DraftKings'
Network scoring articles were retrieved, so 122 coefficients across 7 of the 11
tables are `confirmed_by_operator`; every value still resting on secondary
evidence says so per value (IR-04, IR-05, the DraftKings DST block under L-04).
A value may only claim `confirmed_by_operator` if its source URL is on the
operator's own domain - the tests enforce this.

**3. Conflicts are shipped, not resolved silently.**
Where two sources disagree, the majority value is adopted **and the conflict is
recorded next to it** with both URLs. IR-05 (quality start 0 vs +4), IR-06
(earned run -3 vs -1) and IR-16 (flex eligibility) are all live examples. A
single-source value is marked `single-source` even when it is probably right
(IR-04).

**4. Reproduced, own-definition, or null - never a blend.**
Each RotoGrinders column is classified as one of:
- **reproduced** - the derivation is verified against their published numbers
  (`FPTS/$` only);
- **RGENGY's own** - they publish the column without a formula, so RGENGY computes
  a documented equivalent and labels it as its own (`lev`, `smash`);
- **not computed** - left `null` with a written reason (`OBFPTS`, `TOPVAL`,
  `DIFFERENCE`, `OPTO`, `TEAMOWN`).

Publishing an invented number under their heading would be indistinguishable from
having reproduced it, which is the one outcome worse than reproducing nothing.

---

## Passes

The work ran in three passes, each building on the last, and each pass found
defects the previous one had introduced.

**Pass 1 - implement and verify.**
Endpoints registered and probed, scoring tables assembled from retrieved sources,
projection engines, optimizer, simulator, quality gates, CLI.

**Pass 2 - review for bugs, wrong assumptions and edge cases.**
Found and fixed, among others:
- **IR-17** - roster templates that produced *illegal* lineups (separate C and 1B
  slots where DraftKings MLB combines them into one C/1B slot, so 11 players
  instead of 10). Highest severity in the project: invisible in the projections,
  rejected at submission.
- **IR-18** - NFL 100/300-yard bonuses applied to FanDuel, which does not score them.
- **IR-14 / IR-15** - a goal double-counted via shots-on-goal; representation
  overlaps made a standing invariant with a check that fails the run.
- **Leverage** was subtracting an ownership probability from an unnormalised
  ratio - dimensionally meaningless. Rewritten so both terms are field shares.
- **`vegas.win_probability`** was imported by the pipeline but did not exist.
  Replaced with `market_win_probability()` plus explicit context fields.
- The **payout fallback for tiny fields** paid 200x to *last place*. Restricted to
  rank 1.
- **Simulator self-competition** - on small pools the sharp field collapsed onto
  the user's own roster, producing a 100% cash rate. The field now excludes the
  user's exact rosters and counts what it removed.

**Pass 3 - re-check against the original request.**
Found and fixed:
- **A duplicated player in published lineups.** `_overlap_pairs` tested whether
  two slots' *eligibility sets* intersected. DraftKings MLB `C/1B` (C, 1B) and
  `OF` (OF, LF, CF, RF) are disjoint as sets, so both stayed "fixed" and were
  solved as independent group knapsacks - and a player listed at both 1B and OF
  was picked by *both*, appearing twice with his points counted twice. The
  conflict test is now over the **pool**: two slots are independent only if no
  available player is eligible for both. `_assert_valid_roster()` now refuses to
  return a lineup containing a duplicate or exceeding the cap.
- **The slot breakdown dropped players.** `zip(flex_rules, picked)` paired one
  flex member per *rule*, so a 3-count `OF` flex slot reported a single name and
  the breakdown accounted for 8 of 10 roster players.
- **The NHL goalie projection was silently empty.** `project_goalie` used the
  engine's default stat keys, which for hockey are the *skater* keys - so `sv` and
  `ga` were dropped and a goalie projected to nothing but a win probability. A
  plausible-looking number that was wrong. Same defect class as the pitcher fix.
- **`MAX_POWN` was defeated.** Capping a share at 0.95 and then re-normalising by
  the new total scales every share back up, so a dominant player came out at
  exactly **1.0** - 100% projected ownership, which is what the cap exists to
  forbid, and it corrupted leverage and the simulated field. Replaced with capped
  water-filling that redistributes the freed mass to the players still below the cap.
- **Grid rows omitted unmapped columns entirely** instead of emitting them as
  `null`, so the artefact could not be diffed against RotoGrinders' grid - the
  entire point of shipping their schema.
- **Mapped-but-empty columns reported no reason.** A null because the weather feed
  was absent and a null because RotoGrinders' formula is unpublished are different
  problems with different fixes; they now read differently.
- **A network input with no `fetched_at` was assumed fresh.** Now flagged - with a
  deliberate exception for static scoring-table provenance, which carries
  `audit_date` and is not a fetch.
- **An unshipped sport/site reported "clean"** on the representation audit.
  "No findings" and "never checked" now read differently.
- **Four WNBA grid columns** had neither a mapping nor a reason. `SPREAD` and
  `O/U` are now filled from the retrieved market line; `TOTAL` and `TEAMNAME` are
  left null with written reasons (IR-22).
- **`run()` raised** for an unsupported sport instead of returning a report that
  says the sport is not implemented.

## Test suite

<!-- RGENGY:TESTS:START - generated by scripts/build_docs.py; do not edit by hand -->
**460 tests** across 12 modules, all passing, run with
`python3 -m unittest discover -s tests -t tests`.

| module | tests | covers |
| --- | ---: | --- |
| `test_site` | 60 | the markdown renderer, link integrity, README/dashboard accuracy |
| `test_pipeline` | 59 | end-to-end run, grid schema invariants, artefacts |
| `test_ownership` | 53 | choice model, cap, leverage, smash, pipeline integration |
| `test_quality` | 47 | every quality gate fires *and* stays silent when it should |
| `test_engines` | 43 | position dispatch, no-fabrication, win probability, bands |
| `test_vegas` | 37 | vig removal, implied totals, Bryant formula, market win probability |
| `test_simulator` | 34 | payouts, field construction, cash/top-10/top-1 invariants |
| `test_optimizer` | 33 | optimality vs brute force, roster uniqueness, slot breakdown |
| `test_models` | 27 | roster provenance, grid schema, run report |
| `test_scoring` | 25 | all 11 tables, representation overlaps, evidence classes |
| `test_rg_grid` | 24 | the saved RotoGrinders fixture: identity, ratios, validation |
| `test_findings` | 18 | the IR/L register agrees with every citation in the tree |
<!-- RGENGY:TESTS:END -->

Three properties are worth calling out because they are what stop regressions:

- **Optimality is checked against brute force**, not against the optimizer's own
  opinion of itself. `test_optimizer` enumerates every legal roster for a small
  pool and asserts the DP finds the same total.
- **Quality gates are tested in both directions.** A check that always fires is as
  useless as one that never does, because the report becomes noise nobody reads.
- **The findings register is cross-checked against the tree.** An id cited in code
  but missing from the register is an undocumented irregularity; an id in the
  register that nothing cites is dead prose; an id *declared unused* that turns out
  to be cited is a lie. Generated files are excluded from the citation scan, since
  counting a document rendered from the register as evidence for the register is
  circular.

## Environment constraints

Recorded because they shaped what could be verified (L-02):

- **No outbound network** for raw fetches from the workspace (TLS/SSL EOF). Pages
  were read through a proxy that reaches rotogrinders.com.
- **DraftKings' canonical in-app rules page was not retrievable**; FanDuel's
  public rules page was (fanduel.com/rules, 2026-09-22), and DraftKings'
  operator-domain Network articles were used for DraftKings - clearly labelled as
  such, never as the in-app document of record.
- The site is therefore **static**, and the GitHub Pages workflow regenerates the
  `data/` artefacts on every build so the published numbers cannot disagree with
  the committed code.
- `pytest` is not available; the suite is stdlib `unittest`.
