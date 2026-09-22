# 05 - Projection engines

One formulation across five sports, with sport-specific stat keys and
position-specific dispatch.

```
projection = rate x opportunity x environment
```

- **rate** - per-opportunity production from the player's own season sample
  (per plate appearance, per minute, per game, per 60 minutes of ice time);
- **opportunity** - the chance to produce it (plate appearances, minutes, snaps,
  time on ice). An opportunity is never scaled by the run/point environment:
  a hotter game produces more hits, not more plate appearances;
- **environment** - the multiplicative adjustment for team output, opponent
  quality, park, pace and weather.

`rgengy/engines.py`. `engine_for(sport, band_mode)` returns the right engine;
`Engine.project_player` dispatches on position.

---

## Why position dispatch matters

Baseball and hockey project two fundamentally different kinds of participant from
the same feed. Using hitter stat keys for a pitcher produces a **wrong but
plausible** score - the strikeouts line up and everything else is silently
missing. So:

| engine | dispatches on | branches |
| --- | --- | --- |
| `BaseballEngine` | `positions` | `project_pitcher` / `project_hitter` |
| `HockeyEngine` | `positions` | `project_goalie` / `project_skater` |
| `BasketballEngine` | - | one branch, per-minute rates |
| `FootballEngine` | - | per-game rates plus yardage-bonus probabilities |

Both position-specific branches must pass their own key list explicitly to
`rates()`. Twice during the audit one of them did not, and the default fell back
to the *other* branch's keys: a pitcher projected with hitter keys, and a goalie
projected with skater keys. The goalie case returned nothing but a win
probability, which looked like a legitimate low-value goalie rather than an empty
projection. `tests/test_engines.py` now asserts that a goalie gets `sv`/`ga` and
never `g`, and that a hitter gets `pa`/`hr` and never `ip`/`er`/`win`.

## No fabrication

An engine that cannot project returns `{}` and records why in `ctx.notes`. It
never substitutes a league-average line, never assumes a 0.5 win probability, and
never invents a sample. The pipeline then keeps the player at 0.0 with a run
warning (IR-19) rather than dropping them, because dropping a player makes any
roster slot only they could fill impossible to satisfy - which converts one
missing season sample into "no lineup exists for this sport at all", reported at
the optimizer, far from its cause.

`tests/test_engines.py` covers this directly: no season sample, no games, and a
goalie with saves but no games played all return `{}` with a note.

## Environment ratio

`ProjectionContext.environment_ratio()` returns the adjustment **broken out by
term** so it can be audited, and `combined_ratio()` multiplies them:

| sport | terms |
| --- | --- |
| MLB | `team_output_ratio`, `opp_pitching_ratio`, `park_factor`, `weather_ratio` |
| others | `team_output_ratio`, `opp_defense_ratio`, `pace_ratio`, `weather_ratio` |

Every term is a ratio of a retrieved number to another retrieved number
(`team_expected_output / team_season_output_pg`,
`opp_season_allowed_pg / league_average`). Where an input is missing the term is
absent from the dict rather than defaulted to something plausible. The whole dict
is written into `player.extra["environment_ratio"]` in every artefact.

### Weather is computed exactly and then disabled

Air density is computed from the retrieved pressure, temperature and humidity
(`sources.air_density`), exactly against the ISA standard
(`vegas.ISA_AIR_DENSITY_KG_M3 = 1.225`). The scoring adjustment is that delta
multiplied by `WEATHER_AIR_DENSITY_COEFFICIENT`, which is **0.0** - the adjustment
is off.

That is deliberate. Denser air suppresses flight, so the sign and shape are known,
but the *magnitude* has not been fitted to anything. Applying an unvalidated
sensitivity would fabricate precision: the projection would move by a
small, confident-looking amount that no evidence supports. Setting the coefficient
explicitly, and documenting the evidence, turns it on. `tests/test_pipeline.py`
asserts the ratio is exactly 1.0 at every density while the coefficient is 0, and
that thinner air helps once it is not.

## Win probability: one origin

`team_win_probability(ctx)` returns `(probability, source_label)` with a fixed
preference order:

1. **`ctx.win_prob`** - derived from the market line in the pipeline by
   `vegas.market_win_probability()`. Label: `market (<method>)`.
2. **Expected-output differential** - `engines.win_probability()` over
   `SIGMA_BY_SPORT`. Label names the sigma and flags it as unaudited (IR-03).
3. **`0.0` with the label `"unavailable"`** - a legal answer.

No engine may invent 0.5. Before this was centralised, a win probability could be
derived in two places with two different values, so a pitcher's win projection
could silently disagree with the market line printed beside it (IR-23). The label
is written into the projection notes and the artefact, so every published win
probability says where it came from.

| sport | sigma | note |
| --- | ---: | --- |
| `mlb` | 2.9 | runs |
| `nhl` | 2.5 | goals |
| `nba` | 12.0 | points |
| `wnba` | 11.0 | points |
| `nfl` | 13.5 | points - **known to understate heavy favourites** |
| `ncaaf` | 18.0 | points |

These are conventional values, not fitted ones (IR-03). The market line is always
preferred where one exists.

A pitcher's win is `team_win_probability x P(quality start)`; a goalie's is
`team_win_probability` directly.

## Bands: floor, ceiling, standard deviation

Two modes, selected per run by `band_mode`:

**`distribution` (default).** The projection is a mean; the floor and ceiling come
from `fpts_distribution()` at `FLOOR_Z = 1.0` and `CEIL_Z = 2.0` standard
deviations. Asymmetric on purpose: a bust performance is bounded by the player
getting nothing, while upside is not bounded at all.

**`rg_band` (opt-in).** Floor and ceiling are fixed ratios of the projection,
`0.3030` and `2.2229`, observed on RotoGrinders' own public grid. Those constants
come from **six rows, one team, one game, one date** (IR-12). The sample size is
stored beside them (`RG_OBSERVED_SAMPLE_SIZE = 6`) and printed wherever the mode
is used. It is opt-in precisely because six rows cannot support a default.

`score_and_band()` attaches `fpts`, `sd`, `floor`, `ceil` and `fpts_per_1k` in one
call, so the value a user sorts on and the value the optimizer ranks by are the
same number from the same place.

## Other derived quantities

| function | what it does | honesty note |
| --- | --- | --- |
| `quality_start_probability` | P(QS) from the projected line | uses the shipped `qs` coefficient's disputed status (IR-05) |
| `park_factor_from_splits` | derives a park factor from observed home/away splits | RotoGrinders publishes a `PARK` *identifier*, not a factor; RGENGY derives the factor and does not claim to reproduce their column |
| `fpts_distribution` | mean/sd of the scored distribution | the basis of the default band and of the simulator |
| `band_from_distribution` / `band_from_ratio` | the two band modes | kept separate so the mode is always explicit |
