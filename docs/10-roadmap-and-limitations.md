<!-- GENERATED FILE - DO NOT EDIT: rendered by scripts/build_docs.py from the committed registries. Edit the source and re-run the generator. -->

# 10 - Limitations and remaining work

What RGENGY cannot do yet, what would have to be true to do it, and what to build next. The limitations section is generated from `rgengy/findings.py`; the roadmap below is the prioritised work that would retire them.

## Limitations

| id | severity | status | limitation |
| --- | --- | --- | --- |
| [L-01](09-irregularities.md#l01) | info | UNUSED IDENTIFIER | Identifier L-01 is deliberately unused |
| [L-02](09-irregularities.md#l02) | warning | OPEN | No raw-socket network access from the build sandbox; operator rules coverage is now partial, not absent |
| [L-03](09-irregularities.md#l03) | warning | OPEN | The WNBA roster templates are unconfirmed |
| [L-04](09-irregularities.md#l04) | warning | OPEN | DraftKings team-defence tiers remain unaudited; FanDuel's are operator-documented but not yet modelled |
| [L-05](09-irregularities.md#l05) | warning | OPEN | RotoGrinders' paywalled features could not be inspected at all |
| [L-06](09-irregularities.md#l06) | warning | OPEN | Player outcomes are simulated from a normal approximation, not a per-stat model |

### L-01 - Identifier L-01 is deliberately unused

No limitation in this register or in the source tree cites L-01. The id was consumed during the audit by the absence of any outbound network access in the build environment, which turned out to be an environment property rather than a limitation of the system, and is documented in the README instead.

**Consequence.** A gap in the numbering, declared rather than silently renumbered.

**Current mitigation.** Declared here so the L-nn sequence can be read as complete.

### L-02 - No raw-socket network access from the build sandbox; operator rules coverage is now partial, not absent

Raw HTTPS fetches from the build workspace fail with a TLS/SSL EOF error, so the runtime pipeline still cannot fetch live feeds from inside the sandbox. The first audit also recorded that 'no operator scoring page could be retrieved' - that half is now OUTDATED: the second audit pass (2026-09-22) verified, through the platform's document-retrieval channel, that FanDuel publishes its full DFS scoring rules publicly at https://www.fanduel.com/rules, and that DraftKings publishes operator- domain scoring articles on dknetwork.draftkings.com (NHL 2025-09-30, NFL 2025-08-27, NBA 2025-10-17, MLB 2020-05-29). DraftKings' canonical in-app rules page remains unretrieved, and those operator articles are editorial pages rather than the contractual rules - hence 'partial', not 'complete'.

**Consequence.** Live feeds still cannot be exercised from the sandbox, so the pipeline is tested against synthetic and cached inputs and the slate stage honestly reports `unavailable` rather than substituting invented games. Scoring coverage, however, is materially stronger than the first pass claimed: large parts of five tables are now marked `confirmed_by_operator`.

**Current mitigation.** `rgengy probe` and `rgengy verify` exist to be run from a networked machine; they stamp each endpoint - and, added in this pass, every URL cited by the scoring tables - with its live status and write verification.json. The GitHub Pages workflow runs them on every build so the published site reflects the live state rather than the audit state. `data/` is gitignored and regenerated.

### L-03 - The WNBA roster templates are unconfirmed

No source for the WNBA roster shape was retrieved during the audit. The templates were treated as the NBA shape reduced to six slots.

**Consequence.** A WNBA lineup built from these templates may be rejected by the operator. Both `wnba:draftkings` and `wnba:fanduel` have zero sources and are marked `not-audited`.

**Current mitigation.** `models.default_roster()` returns the `not-audited` status and a note beginning UNCONFIRMED for both, and tests/test_models.py asserts that any template with no sources must be marked `not-audited` and must say UNCONFIRMED - so the templates cannot be quietly upgraded without a source being added.

### L-04 - DraftKings team-defence tiers remain unaudited; FanDuel's are operator-documented but not yet modelled

The first pass could not retrieve DraftKings team-defence scoring from any source. The second audit pass (2026-09-22) improved the FanDuel half: FanDuel's public rules page (https://www.fanduel.com/rules, Football/Defense section) documents sacks = 1, fumble recovered = 2, interception = 2, safety = 2, blocked punt = 2, kick/punt return TD = 6, extra-point return = 2, and the exact points-allowed tiers (0 -> 10, 1-6 -> 7, 7-13 -> 4, 14-20 -> 1, 21-27 -> 0, 28-34 -> -1, 35+ -> -4) plus the formula FanDuel uses to compute points allowed. A secondary comparison table (dailyfantasysports101) shows DraftKings DST tiers identical to FanDuel's, but no DraftKings operator document for DST was retrieved. The shipped `dst_pts_allowed` coefficient is still 0.0 because RGENGY's engine models points allowed as a single expected value, not as a tier lookup.

**Consequence.** DraftKings DST and kicker-projection error remains unknown (L-04 as originally filed). For FanDuel, the per-event DST coefficients are now operator-confirmed, but the tiered points-allowed scoring - often the largest DST term - is still not applied, so FanDuel DST FPTS remains understated by an unknown amount.

**Current mitigation.** The FanDuel per-event keys are marked `confirmed_by_operator: true`. The operator tier table is stored verbatim in the FanDuel table JSON under `operator_tier_tables.dst_points_allowed` so no one has to re-retrieve it, and `dst_pts_allowed` stays 0.0 / intentionally_zero until the engine grows a tier lookup (roadmap: 'Model FanDuel's tiered DST points-allowed scoring'). Under `--strict` the unaudited DraftKings DST keys stay excluded from published totals.

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

### 1. Retrieve DraftKings' canonical in-app scoring rules

**Priority: high.**

FanDuel's public rules page (fanduel.com/rules) and DraftKings' Network articles are now retrieved and operator-confirm large parts of five tables (see IR-06, IR-08, IR-09, IR-10, IR-18). What is still missing is DraftKings' canonical rules page inside its logged-in app, which is the document of record: it would settle the two values the operator articles leave ambiguous (MLB caught stealing, IR-04; the article's own 4.0-vs-4.5 win inconsistency, IR-26) and confirm the DraftKings DST tiers that currently rest on a secondary source (L-04). This needs an authenticated session or a direct operator relationship.

**Payoff.** Retires the last two open scoring irregularities and upgrades L-04 to fully operator-sourced.

### 2. Model FanDuel's tiered DST points-allowed scoring

**Priority: high.**

FanDuel's rules page documents the exact points-allowed tiers (0->10, 1-6->7, 7-13->4, 14-20->1, 21-27->0, 28-34->-1, 35+->-4) and the formula for points allowed; the tier table is stored verbatim in the FanDuel table JSON under `operator_tier_tables`. The engine still models points allowed as a single expected value, so `dst_pts_allowed` ships at 0.0 and FanDuel DST projections are understated by an unknown amount.

**Payoff.** Turns the largest missing DST term from a flagged gap into a scored coefficient on FanDuel.

### 3. Fit the ownership model on real ownership data

**Priority: high.**

pOWN is a softmax choice model with an uncalibrated beta (IR-13). RotoGrinders' is gradient-boosted over historical DraftKings ownership. `ownership.calibrate_beta()` already fits beta by deterministic grid search; what is missing is the data. Operator-published ownership after a contest settles is the cheapest legal source.

**Payoff.** Turns the ownership stage from `degraded` to `complete`.

### 4. Replace the normal-approximation simulator with a correlated event model

**Priority: high.**

Player outcomes are drawn from a normal built on the mean and the floor/ceiling band (L-06). Real output is a sum of discrete correlated events, so tail behaviour is understated and a 4-home-run game cannot occur. Needs historical play-by-play to fit per-stat distributions and their correlations.

**Payoff.** Makes simulated top-1 rates usable for large-field GPP decisions.

### 5. Transcribe the NBA and NHL grid headers

**Priority: medium.**

`RG_GRID_COLUMNS` covers MLB, NFL and WNBA only (IR-22). Without the NBA and NHL headers the grid artefacts for those sports cannot be diffed against RotoGrinders' and are labelled as RGENGY's own schema.

**Payoff.** Makes all five supported sports schema-comparable.

### 6. Confirm the WNBA roster templates

**Priority: medium.**

Both WNBA templates have zero sources and are marked `not-audited` (L-03); they were assumed to be the NBA shape reduced to six slots. A wrong template produces lineups the operator rejects outright (the IR-17 failure class). WNBA *scoring* is no longer a gap - the FanDuel basketball table covers WNBA and DraftKings' own Pick6 WNBA page corroborates the DK values - but the roster shapes remain unconfirmed.

**Payoff.** Removes the only roster template that could produce an illegal lineup.

### 7. Enlarge the RotoGrinders calibration sample

**Priority: medium.**

The floor/ceiling ratios come from six free-tier rows (IR-12, IR-25), one sport, one site, one slate. The paid tier would give a sample large enough to fit per-position bands and to test whether the ratios are stable across slates.

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
