<!-- GENERATED FILE - DO NOT EDIT: rendered by scripts/build_docs.py from the committed registries. Edit the source and re-run the generator. -->

# 10 - Limitations and remaining work

What RGENGY cannot do yet, what would have to be true to do it, and what to build next. The limitations section is generated from `rgengy/findings.py`; the roadmap below is the prioritised work that would retire them.

## Limitations

| id | severity | status | limitation |
| --- | --- | --- | --- |
| [L-01](09-irregularities.md#l01) | info | UNUSED IDENTIFIER | Identifier L-01 is deliberately unused |
| [L-02](09-irregularities.md#l02) | critical | OPEN | No outbound network access in the build environment |
| [L-03](09-irregularities.md#l03) | warning | OPEN | The WNBA roster templates are unconfirmed |
| [L-04](09-irregularities.md#l04) | warning | OPEN | NFL team-defence and kicker scoring tiers were never retrieved |
| [L-05](09-irregularities.md#l05) | warning | OPEN | RotoGrinders' paywalled features could not be inspected at all |
| [L-06](09-irregularities.md#l06) | warning | OPEN | Player outcomes are simulated from a normal approximation, not a per-stat model |

### L-01 - Identifier L-01 is deliberately unused

No limitation in this register or in the source tree cites L-01. The id was consumed during the audit by the absence of any outbound network access in the build environment, which turned out to be an environment property rather than a limitation of the system, and is documented in the README instead.

**Consequence.** A gap in the numbering, declared rather than silently renumbered.

**Current mitigation.** Declared here so the L-nn sequence can be read as complete.

### L-02 - No outbound network access in the build environment

Raw HTTPS fetches from this workspace fail with a TLS/SSL EOF error. The pages retrieved during the audit were read through a proxy that can reach rotogrinders.com; fanduel.com is additionally geo-blocked, and both operators keep their authoritative scoring pages inside their logged-in apps.

**Consequence.** No scoring value in this repository is marked `confirmed_by_operator`, because no operator scoring page could be retrieved. Every value rests on secondary sources. The live feeds cannot be exercised here, so the pipeline is tested against synthetic and cached inputs and the slate stage honestly reports `unavailable` rather than substituting invented games.

**Current mitigation.** `rgengy probe` and `rgengy verify` exist to be run from a networked machine; they stamp each endpoint with its live status and write verification.json. The GitHub Pages workflow runs them on every build so the published site reflects the live state rather than the audit state. `data/` is gitignored and regenerated.

### L-03 - The WNBA roster templates are unconfirmed

No source for the WNBA roster shape was retrieved during the audit. The templates were treated as the NBA shape reduced to six slots.

**Consequence.** A WNBA lineup built from these templates may be rejected by the operator. Both `wnba:draftkings` and `wnba:fanduel` have zero sources and are marked `not-audited`.

**Current mitigation.** `models.default_roster()` returns the `not-audited` status and a note beginning UNCONFIRMED for both, and tests/test_models.py asserts that any template with no sources must be marked `not-audited` and must say UNCONFIRMED - so the templates cannot be quietly upgraded without a source being added.

### L-04 - NFL team-defence and kicker scoring tiers were never retrieved

DraftKings team-defence scoring was not retrieved from any source during the audit. The shipped values follow the long-standing convention (points allowed and yardage tiers, sacks, turnovers, defensive touchdowns) but are marked `not-audited`.

**Consequence.** DST and KPTS projections carry an unknown error. The NFL grid's KPTS column is left null rather than filled from unaudited tiers.

**Current mitigation.** The seven `dst_*` keys are `not-audited` in both NFL tables, so `quality.check_scoring_coverage` escalates them to a warning whenever a DST is actually projected. Under `--strict` the pipeline excludes unaudited coefficients from published totals.

### L-05 - RotoGrinders' paywalled features could not be inspected at all

The subscription tier - the full projection grid beyond six rows, the optimizer, ownership projections, THE BAT X projections, contest simulation and the partner-site columns (UNDERDOG, PRIZEPICKS) - is not retrievable without an account.

**Consequence.** Every claim about those features rests on the free tier, on RotoGrinders' own published articles, or on nothing at all. Where nothing was available, RGENGY implements its own documented equivalent and says so.

**Current mitigation.** The rebuild is explicit about which is which. `analytics_provenance` labels each column reproduced / RGENGY-own / not computed; the site carries the same three-way split; and no paywalled quantity is emitted under RotoGrinders' column heading without that label.

### L-06 - Player outcomes are simulated from a normal approximation, not a per-stat model

`simulator.sample_player_fpts` draws each player's score from a normal distribution built on the projected mean and a standard deviation derived from the floor/ceiling band. Real fantasy output is a sum of discrete, correlated events (a hit is also a run and an RBI; a pitcher's innings correlate with his strikeouts).

**Consequence.** Tail behaviour is understated: a normal draw cannot produce a 4-home-run game, so simulated top-1 rates are conservative and the cash/top-10/top-1 ordering is preserved but the magnitudes are not trustworthy for large-field GPPs. The band is also over-dispersed relative to a true event model.

**Current mitigation.** Documented in the simulator module docstring and surfaced in every simulation result. Replacing it needs a per-stat correlated event model, which needs the historical play-by-play data listed as future work in docs/10.

## Stated assumptions

These are not defects and not verified facts: they are the places where RGENGY proceeds on a documented assumption because no source settles it. Each is labelled wherever its output is surfaced.

| id | assumption | where it is labelled |
| --- | --- | --- |
| [IR-03](09-irregularities.md#ir03) | The score-distribution sigmas used to turn a margin into a win probability are unaudited | `rgengy/engines.py`, `rgengy/pipeline.py` |
| [IR-12](09-irregularities.md#ir12) | RotoGrinders' floor/ceiling ratios are calibrated on six rows | `rgengy/engines.py`, `scripts/analyze_rg_public_grid.py` |
| [IR-13](09-irregularities.md#ir13) | The ownership model's beta is an uncalibrated default | `rgengy/ownership.py`, `rgengy/pipeline.py` |

## Remaining work, prioritised

Ordered by how much of the gap to RotoGrinders' data quality each one closes. Priority reflects the severity of the finding it retires, not the effort involved.

### 1. Retrieve the operators' own scoring pages

**Priority: critical.**

No coefficient in this repository is `confirmed_by_operator` (L-02). Every value rests on secondary sources, and three are actively contradicted (IR-05, IR-06, IR-16). DraftKings and FanDuel both keep their authoritative tables inside their logged-in apps, so this needs an authenticated session or a direct operator relationship.

**Payoff.** Settles IR-04, IR-05, IR-06, IR-08, IR-10, IR-16, L-04.

### 2. Fit the ownership model on real ownership data

**Priority: high.**

pOWN is a softmax choice model with an uncalibrated beta (IR-13). RotoGrinders' is gradient-boosted over historical DraftKings ownership. `ownership.calibrate_beta()` already fits beta by deterministic grid search; what is missing is the data. Operator-published ownership after a contest settles is the cheapest legal source.

**Payoff.** Turns the ownership stage from `degraded` to `complete`.

### 3. Replace the normal-approximation simulator with a correlated event model

**Priority: high.**

Player outcomes are drawn from a normal built on the mean and the floor/ceiling band (L-06). Real output is a sum of discrete correlated events, so tail behaviour is understated and a 4-home-run game cannot occur. Needs historical play-by-play to fit per-stat distributions and their correlations.

**Payoff.** Makes simulated top-1 rates usable for large-field GPP decisions.

### 4. Verify the live player-stat endpoints

**Priority: high.**

The slate endpoints are live-verified but the per-player season-stat endpoints are marked `unverified` (L-02). `rgengy probe` exists to check their shape; until it has been run from a networked machine, `run()` refuses to synthesise season stats and says so.

**Payoff.** Unblocks real projections end to end instead of caller-supplied data.

### 5. Transcribe the NBA and NHL grid headers

**Priority: medium.**

`RG_GRID_COLUMNS` covers MLB, NFL and WNBA only (IR-22). Without the NBA and NHL headers the grid artefacts for those sports cannot be diffed against RotoGrinders' and are labelled as RGENGY's own schema.

**Payoff.** Makes all five supported sports schema-comparable.

### 6. Confirm the WNBA roster templates

**Priority: medium.**

Both WNBA templates have zero sources and are marked `not-audited` (L-03); they were assumed to be the NBA shape reduced to six slots. A wrong template produces lineups the operator rejects outright (the IR-17 failure class).

**Payoff.** Removes the only roster template that could produce an illegal lineup.

### 7. Enlarge the RotoGrinders calibration sample

**Priority: medium.**

The floor/ceiling ratios come from six free-tier rows (IR-12), one sport, one site, one slate. The paid tier would give a sample large enough to fit per-position bands and to test whether the ratios are stable across slates.

**Payoff.** Would let `rg_band` become a defensible default rather than an opt-in curiosity.

### 8. Licence a weather feed with a validated run-scoring sensitivity

**Priority: low.**

Air density is computed exactly from the retrieved pressure, temperature and humidity, but `WEATHER_AIR_DENSITY_COEFFICIENT` is 0 - the adjustment is disabled, because applying an unvalidated sensitivity would fabricate precision. Enabling it needs a coefficient fitted against observed run production.

**Payoff.** Turns an already-computed input into an actual adjustment.

### 9. Add per-operator roster templates beyond Classic

**Priority: low.**

Only the Classic (full-slate) template is shipped per sport and site. Showdown, single-game and 3-player-stack formats have different shapes and caps, and would each need their own verified provenance entry.

**Payoff.** Widens the optimizer to the formats most GPP players actually use.

## What would have to be true to reach parity

RotoGrinders' projection quality rests on three things RGENGY does not have and cannot obtain from free official feeds:

1. **Historical per-contest ownership.** Their pOWN is gradient-boosted over it (IR-13). No operator publishes it historically; some publish it after a contest settles.
2. **A proprietary projection engine.** THE BAT X and their in-house models are fitted to years of outcomes. RGENGY ships a transparent rate x opportunity x environment engine whose inputs are all sourced, which is auditable but will not match a fitted model's accuracy.
3. **Licensed data.** Player news, injury timing, lineup confirmation and weather come from paid feeds. RGENGY uses official free feeds and says so per endpoint (docs/02).

What RGENGY does better is *auditability*: every coefficient, every roster slot and every derived column carries its evidence class and its source URLs, and every quantity it cannot verify is null with a written reason rather than a plausible number.
