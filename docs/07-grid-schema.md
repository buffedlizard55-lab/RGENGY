<!-- GENERATED FILE - DO NOT EDIT: rendered by scripts/build_docs.py from the committed registries. Edit the source and re-run the generator. -->

# 07 - RotoGrinders grid schema and column mapping

RotoGrinders' projection grid is the artefact its users actually read, so reproducing its *shape* matters as much as reproducing its numbers. Column headers were transcribed from the live site on 2026-09-22 for MLB, NFL and WNBA only. Generated from `models.RG_GRID_COLUMNS`, `pipeline._COLUMN_MAP` and `pipeline.UNMAPPED_COLUMN_REASONS`.

> **IR-22.** The NBA and NHL grid headers were **not** transcribed, so
> `RG_GRID_COLUMNS` deliberately omits them. `grid_rows()` sets
> `rg_column_schema_observed=False` and writes an explicit note for those sports rather
> than presenting RGENGY's own schema as a reproduction of theirs.

## Coverage

| sport | columns observed | filled by RGENGY | left null | header transcribed |
| --- | ---: | ---: | ---: | :---: |
| MLB | 49 | 31 | 18 | yes |
| NFL | 38 | 26 | 12 | yes |
| WNBA | 33 | 21 | 12 | yes |
| NBA | not observed | 21 mapped | - | **no** |
| NHL | not observed | 19 mapped | - | **no** |

Two-way invariant, asserted by `tests/test_pipeline.py`: every observed column is either mapped or carries a written reason below, and every written reason refers to a column that actually exists. A null with no reason is indistinguishable from a bug.

## MLB (49 columns)

| # | column | RGENGY source | status |
| ---: | --- | --- | --- |
| 1 | `PLAYER` | name | filled |
| 2 | `SALARY` | salary | filled |
| 3 | `POS` | position | filled |
| 4 | `TEAM` | team | filled |
| 5 | `OPP` | opp | filled |
| 6 | `PA` | projected.pa | filled |
| 7 | `1B` | projected.1b | filled |
| 8 | `2B` | projected.2b | filled |
| 9 | `3B` | projected.3b | filled |
| 10 | `HR` | projected.hr | filled |
| 11 | `RBI` | projected.rbi | filled |
| 12 | `R` | projected.r | filled |
| 13 | `SB` | projected.sb | filled |
| 14 | `BB` | projected.bb | filled |
| 15 | `IP` | projected.ip | filled |
| 16 | `BBA` | projected.bba | filled |
| 17 | `K` | projected.k | filled |
| 18 | `W` | projected.win | filled |
| 19 | `ER` | projected.er | filled |
| 20 | `HA` | projected.ha | filled |
| 21 | `HBP` | projected.hbp | filled |
| 22 | `QS` | projected.qs | filled |
| 23 | `FPTS` | fpts | filled |
| 24 | `FPTS/$` | value_per_1k | filled - identity verified exactly against the public grid |
| 25 | `H` | Consistent with 1B + 2B + 3B + HR on the six public rows, but inferred rather than published, so it is not emitted. | **null** |
| 26 | `PARK` | Ballpark identifier. RGENGY derives a park FACTOR from observed splits (engines.park_factor_from_splits) rather than shipping a hard-coded park table, and exposes it in extra['park_factor']. | **null** |
| 27 | `BASES` | Consistent with 1B + 2*2B + 3*3B + 4*HR on the six public rows, but that is an inference, not a published definition, so it is not emitted. | **null** |
| 28 | `OUTS` | Zero for hitters on all six public rows and a pitcher statistic; not emitted for hitters rather than guessed. | **null** |
| 29 | `BATK` | Unpublished definition; not reproduced. | **null** |
| 30 | `HRRBI` | Unpublished definition; not reproduced. | **null** |
| 31 | `PC` | Empty on all six public rows; meaning undetermined. | **null** |
| 32 | `REFTM` | Reference team for a comparison view; a UI affordance rather than a projection. | **null** |
| 33 | `REFOPP` | Reference opponent for a comparison view; a UI affordance rather than a projection. | **null** |
| 34 | `OBFPTS` | RotoGrinders publishes OBFPTS at full float precision, ~1.08-1.13x FPTS, with no published definition (IR-21). Not reproduced. | **null** |
| 35 | `WIND` | weather.wind | filled |
| 36 | `TEMP` | weather.temp_f | filled |
| 37 | `TEMPDESC` | weather.desc | filled |
| 38 | `ORDER` | batting_order | filled |
| 39 | `UNDERDOG` | A partner-site projection. RotoGrinders does not publish how it differs from FPTS (it does differ on all six rows), so it is not reproduced. | **null** |
| 40 | `PRIZEPICKS` | Equalled FPTS exactly on all six public rows, i.e. RotoGrinders' own projection re-published under a partner brand. Not emitted, because RGENGY cannot verify that equivalence holds generally (IR-23). | **null** |
| 41 | `FLOOR` | floor | filled |
| 42 | `CEIL` | ceil | filled |
| 43 | `POWN` | pown | filled |
| 44 | `OPTO` | RotoGrinders' optimiser output. Its objective and constraints are unpublished, so RGENGY emits its own optimiser result separately instead of under this heading. | **null** |
| 45 | `SMASH` | Unpublished definition. RGENGY computes its own P(FPTS > 1.5x projection) into extra['smash'] and labels it as its own (IR-21). | **null** |
| 46 | `TOPVAL` | Unpublished definition; not reproduced. | **null** |
| 47 | `TEAMOWN` | Team-level ownership. RotoGrinders' aggregation is unpublished; RGENGY exposes per-player pOWN only rather than inventing a team roll-up (IR-22). | **null** |
| 48 | `DIFFERENCE` | Unpublished definition; not reproduced. | **null** |
| 49 | `LEV` | Unpublished definition. RGENGY computes its own value-share-minus-ownership-share into extra['lev'] and labels it as its own (IR-21). | **null** |

## NFL (38 columns)

| # | column | RGENGY source | status |
| ---: | --- | --- | --- |
| 1 | `PLAYER` | name | filled |
| 2 | `SALARY` | salary | filled |
| 3 | `POS` | position | filled |
| 4 | `TEAM` | team | filled |
| 5 | `OPP` | opp | filled |
| 6 | `INJURY` | status | filled |
| 7 | `PAATT` | projected.pa_att | filled |
| 8 | `CMP` | projected.pa_cmp | filled |
| 9 | `PAYDS` | projected.pa_yds | filled |
| 10 | `PATD` | projected.pa_td | filled |
| 11 | `INT` | projected.pa_int | filled |
| 12 | `RUATT` | projected.ru_att | filled |
| 13 | `RUYDS` | projected.ru_yds | filled |
| 14 | `RUTD` | projected.ru_td | filled |
| 15 | `TAR` | projected.rec_tgt | filled |
| 16 | `REC` | projected.rec | filled |
| 17 | `REYDS` | projected.rec_yds | filled |
| 18 | `RETD` | projected.rec_td | filled |
| 19 | `100RU` | projected.100ru | filled |
| 20 | `100RE` | projected.100rec | filled |
| 21 | `300PA` | projected.300pa | filled |
| 22 | `FPTS` | fpts | filled |
| 23 | `FPTS/$` | value_per_1k | filled - identity verified exactly against the public grid |
| 24 | `OBFPTS` | RotoGrinders publishes OBFPTS at full float precision, ~1.08-1.13x FPTS, with no published definition (IR-21). Not reproduced. | **null** |
| 25 | `PP` | Unpublished definition; not reproduced. | **null** |
| 26 | `UD` | Unpublished definition; not reproduced. | **null** |
| 27 | `TOTYD` | Unpublished combination rule; not reproduced. | **null** |
| 28 | `TOTTD` | Unpublished combination rule; not reproduced. | **null** |
| 29 | `PARUYD` | Unpublished definition; not reproduced. | **null** |
| 30 | `PARUTD` | Unpublished definition; not reproduced. | **null** |
| 31 | `RUREYD` | Unpublished definition; not reproduced. | **null** |
| 32 | `RURETD` | Unpublished definition; not reproduced. | **null** |
| 33 | `KPTS` | Kicker points; the NFL scoring table's DST/kicker tiers are unaudited (L-04). | **null** |
| 34 | `FLOOR` | floor | filled |
| 35 | `CEIL` | ceil | filled |
| 36 | `OPTO` | RotoGrinders' optimiser output. Its objective and constraints are unpublished, so RGENGY emits its own optimiser result separately instead of under this heading. | **null** |
| 37 | `POWN` | pown | filled |
| 38 | `SLATE` | NFL slate label; a UI grouping rather than a projection. | **null** |

## WNBA (33 columns)

| # | column | RGENGY source | status |
| ---: | --- | --- | --- |
| 1 | `PLAYER` | name | filled |
| 2 | `SALARY` | salary | filled |
| 3 | `POS` | position | filled |
| 4 | `TEAM` | team | filled |
| 5 | `OPP` | opp | filled |
| 6 | `TEAMNAME` | Full team name. RGENGY carries the team ABBREVIATION from the league feed and has no verified abbreviation-to-name table, so emitting one would be invented text in a column that looks like retrieved data. | **null** |
| 7 | `STATUS` | status | filled |
| 8 | `SPREAD` | game_line.spread | filled |
| 9 | `O/U` | game_line.over_under | filled |
| 10 | `TOTAL` | Published immediately after SPREAD and O/U on the WNBA grid with no definition. It may be RotoGrinders' own projected game total rather than the market line; filling it with Game.odds.over_under (which is already emitted under O/U) would present an unverified substitution as their number. Left null. IR-22. | **null** |
| 11 | `MINUTES` | projected.min | filled |
| 12 | `PTS` | projected.pts | filled |
| 13 | `REB` | projected.reb | filled |
| 14 | `AST` | projected.ast | filled |
| 15 | `3PM` | projected.three_pm | filled |
| 16 | `TO` | projected.to | filled |
| 17 | `STL` | projected.stl | filled |
| 18 | `BLK` | projected.blk | filled |
| 19 | `P-A` | Prop-style combined stat with an unpublished definition; not reproduced. | **null** |
| 20 | `P-R` | Prop-style combined stat with an unpublished definition; not reproduced. | **null** |
| 21 | `P-R-A` | Prop-style combined stat with an unpublished definition; not reproduced. | **null** |
| 22 | `B-S` | Prop-style combined stat with an unpublished definition; not reproduced. | **null** |
| 23 | `R-A` | Prop-style combined stat with an unpublished definition; not reproduced. | **null** |
| 24 | `UD` | Unpublished definition; not reproduced. | **null** |
| 25 | `PP` | Unpublished definition; not reproduced. | **null** |
| 26 | `FPTS` | fpts | filled |
| 27 | `FPTS/$` | value_per_1k | filled - identity verified exactly against the public grid |
| 28 | `RANGE` | Unpublished definition; not reproduced. | **null** |
| 29 | `FLOOR` | floor | filled |
| 30 | `CEIL` | ceil | filled |
| 31 | `POWN` | pown | filled |
| 32 | `POSDRK` | Position rank on DraftKings under an unpublished ranking rule; not reproduced. | **null** |
| 33 | `POSFAN` | Position rank on FanDuel under an unpublished ranking rule; not reproduced. | **null** |

## Columns left null, and why

These are RotoGrinders' own column headings. Publishing an invented number under one would be indistinguishable from having reproduced theirs, so they are emitted as `null` and listed in `unfilled_columns` with the reason attached.

- **`B-S`** (WNBA) - Prop-style combined stat with an unpublished definition; not reproduced.
- **`BASES`** (MLB) - Consistent with 1B + 2*2B + 3*3B + 4*HR on the six public rows, but that is an inference, not a published definition, so it is not emitted.
- **`BATK`** (MLB) - Unpublished definition; not reproduced.
- **`DIFFERENCE`** (MLB) - Unpublished definition; not reproduced.
- **`H`** (MLB) - Consistent with 1B + 2B + 3B + HR on the six public rows, but inferred rather than published, so it is not emitted.
- **`HRRBI`** (MLB) - Unpublished definition; not reproduced.
- **`INJURY`** (NFL) - Mapped for NFL; absent from the other grids.
- **`KPTS`** (NFL) - Kicker points; the NFL scoring table's DST/kicker tiers are unaudited (L-04).
- **`LEV`** (MLB) - Unpublished definition. RGENGY computes its own value-share-minus-ownership-share into extra['lev'] and labels it as its own (IR-21).
- **`OBFPTS`** (MLB, NFL) - RotoGrinders publishes OBFPTS at full float precision, ~1.08-1.13x FPTS, with no published definition (IR-21). Not reproduced.
- **`OPTO`** (MLB, NFL) - RotoGrinders' optimiser output. Its objective and constraints are unpublished, so RGENGY emits its own optimiser result separately instead of under this heading.
- **`OUTS`** (MLB) - Zero for hitters on all six public rows and a pitcher statistic; not emitted for hitters rather than guessed.
- **`P-A`** (WNBA) - Prop-style combined stat with an unpublished definition; not reproduced.
- **`P-R`** (WNBA) - Prop-style combined stat with an unpublished definition; not reproduced.
- **`P-R-A`** (WNBA) - Prop-style combined stat with an unpublished definition; not reproduced.
- **`PARK`** (MLB) - Ballpark identifier. RGENGY derives a park FACTOR from observed splits (engines.park_factor_from_splits) rather than shipping a hard-coded park table, and exposes it in extra['park_factor'].
- **`PARUTD`** (NFL) - Unpublished definition; not reproduced.
- **`PARUYD`** (NFL) - Unpublished definition; not reproduced.
- **`PC`** (MLB) - Empty on all six public rows; meaning undetermined.
- **`POSDRK`** (WNBA) - Position rank on DraftKings under an unpublished ranking rule; not reproduced.
- **`POSFAN`** (WNBA) - Position rank on FanDuel under an unpublished ranking rule; not reproduced.
- **`PP`** (NFL, WNBA) - Unpublished definition; not reproduced.
- **`PRIZEPICKS`** (MLB) - Equalled FPTS exactly on all six public rows, i.e. RotoGrinders' own projection re-published under a partner brand. Not emitted, because RGENGY cannot verify that equivalence holds generally (IR-23).
- **`R-A`** (WNBA) - Prop-style combined stat with an unpublished definition; not reproduced.
- **`RANGE`** (WNBA) - Unpublished definition; not reproduced.
- **`REFOPP`** (MLB) - Reference opponent for a comparison view; a UI affordance rather than a projection.
- **`REFTM`** (MLB) - Reference team for a comparison view; a UI affordance rather than a projection.
- **`RURETD`** (NFL) - Unpublished definition; not reproduced.
- **`RUREYD`** (NFL) - Unpublished definition; not reproduced.
- **`SLATE`** (NFL) - NFL slate label; a UI grouping rather than a projection.
- **`SMASH`** (MLB) - Unpublished definition. RGENGY computes its own P(FPTS > 1.5x projection) into extra['smash'] and labels it as its own (IR-21).
- **`TEAMNAME`** (WNBA) - Full team name. RGENGY carries the team ABBREVIATION from the league feed and has no verified abbreviation-to-name table, so emitting one would be invented text in a column that looks like retrieved data.
- **`TEAMOWN`** (MLB) - Team-level ownership. RotoGrinders' aggregation is unpublished; RGENGY exposes per-player pOWN only rather than inventing a team roll-up (IR-22).
- **`TOPVAL`** (MLB) - Unpublished definition; not reproduced.
- **`TOTAL`** (WNBA) - Published immediately after SPREAD and O/U on the WNBA grid with no definition. It may be RotoGrinders' own projected game total rather than the market line; filling it with Game.odds.over_under (which is already emitted under O/U) would present an unverified substitution as their number. Left null. IR-22.
- **`TOTTD`** (NFL) - Unpublished combination rule; not reproduced.
- **`TOTYD`** (NFL) - Unpublished combination rule; not reproduced.
- **`UD`** (NFL, WNBA) - Unpublished definition; not reproduced.
- **`UNDERDOG`** (MLB) - A partner-site projection. RotoGrinders does not publish how it differs from FPTS (it does differ on all six rows), so it is not reproduced.

## Cells that are mapped but empty on a given run

A mapped column can still come back null for every row when the input was absent - no weather feed, no market line, no batting order. `grid_rows()` distinguishes that case from an unmapped column and says so in `unfilled_column_reasons`, because the fix is different: one is a fetch problem, the other is a schema decision.
