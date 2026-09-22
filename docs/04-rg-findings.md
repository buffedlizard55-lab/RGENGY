<!-- GENERATED FILE - DO NOT EDIT: rendered by scripts/build_docs.py from the committed registries. Edit the source and re-run the generator. -->

# 04 - What was reverse-engineered from RotoGrinders

Source: [https://rotogrinders.com/projected-stats/mlb?site=draftkings](https://rotogrinders.com/projected-stats/mlb?site=draftkings), retrieved **2026-09-22**, free tier (6 rows). Saved verbatim to `tests/fixtures/rg_public_mlb_grid_2026-09-22.json` and recomputed by `scripts/analyze_rg_public_grid.py` on every documentation build, so no number below can drift from the fixture.

> **Read the sample size before trusting any of it.** All 6 free rows are batters from ONE team in ONE game (ARI at COL, park COL) on one date. Every pitcher column is 0 across all rows. RotoGrinders' paid tier would give a sample large enough to fit per-position models; the free tier gives enough to *validate a scoring table* and to *observe* the band and ownership conventions, and not much more. See IR-12 and L-05.

## 1. The scoring table reproduces RotoGrinders' published FPTS

> RGENGY's DraftKings MLB scoring table reproduces RotoGrinders' published FPTS for all 6 rows within 0.07 FPTS (0.56% worst case)

This is the strongest result in the audit and the reason the rest is worth reading: RGENGY's independently sourced DraftKings MLB coefficients, applied to RotoGrinders' own published stat projections, reproduce RotoGrinders' published FPTS. Two independently assembled things agreeing to within a rounding step is evidence that the coefficients are right, not merely that they are self-consistent.

| player | salary | pos | RG FPTS | RGENGY FPTS | delta | % error |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| Ketel Marte | 5200 | 2B | 13.48 | 13.55 | +0.07 | 0.519% |
| Gabriel Moreno | 4800 | C | 12.09 | 12.11 | +0.02 | 0.165% |
| Geraldo Perdomo | 4400 | SS | 11.16 | 11.2 | +0.04 | 0.358% |
| Ildemaro Vargas | 4000 | 1B/2B | 10.8 | 10.86 | +0.06 | 0.556% |
| Nolan Arenado | 4100 | 3B | 10.67 | 10.66 | -0.01 | 0.094% |
| Jordan Lawlar | 3300 | OF | 9.89 | 9.9 | +0.01 | 0.101% |

| | |
| --- | --- |
| coefficients used | 20 |
| max absolute delta | 0.07 FPTS |
| mean absolute delta | 0.035 FPTS |
| tolerance | 0.15 FPTS |
| **verdict** | **PASS** |

## 2. `FPTS/$` is exactly `FPTS / (SALARY / 1000)`

> `FPTS/$ == FPTS / (SALARY / 1000)` - max absolute error 0.0036 across 6 rows, which is pure 2dp display rounding.

| player | RG published | computed | abs error |
| --- | ---: | ---: | ---: |
| Ketel Marte | 2.59 | 2.5923 | 0.0023 |
| Gabriel Moreno | 2.52 | 2.5188 | 0.0012 |
| Geraldo Perdomo | 2.54 | 2.5364 | 0.0036 |
| Ildemaro Vargas | 2.7 | 2.7 | 0.0 |
| Nolan Arenado | 2.6 | 2.6024 | 0.0024 |
| Jordan Lawlar | 3.0 | 2.997 | 0.003 |

Because this identity is verified exactly, RGENGY **reproduces** the column and says so. It is the only RotoGrinders analytic column RGENGY claims to reproduce. `tests/test_rg_grid.py` pins it.

## 3. Floor and ceiling are ratios of the projection, and strongly asymmetric

| quantity | n | mean | min | max | sd |
| --- | ---: | ---: | ---: | ---: | ---: |
| `FLOOR / FPTS` | 5 | 0.303 | 0.269 | 0.3342 | 0.0214 |
| `CEIL / FPTS` | 6 | 2.2229 | 2.0571 | 2.5295 | 0.1749 |

> CEIL/FPTS (~2.2) is roughly 7x FLOOR/FPTS (~0.30), so RotoGrinders' bands are strongly asymmetric - upside is modelled far more widely than downside.

These became `engines.RG_OBSERVED_FLOOR_RATIO = 0.303` and `engines.RG_OBSERVED_CEIL_RATIO = 2.2229`, used only by the opt-in `rg_band` mode. n=5 for the floor ratio (non-zero floors only; 1 row(s) published FLOOR=0 and are excluded, see IR-25) and n=6 for the ceiling ratio, all from ONE team in ONE game at Coors Field on ONE date. These constants are used only as a sanity band, never as the primary projection mechanism; rgengy.engines defaults to deriving bands from its own outcome distribution. (IR-12)

**Rows excluded from the floor fit, and why:**

- **Jordan Lawlar** (FPTS 9.89, FLOOR 0.0, CEIL 23.53) - FLOOR is 0 while FPTS and CEIL are both non-zero; every other row has FLOOR between 0.27 and 0.34 of FPTS. Excluded from the fitted ratio and flagged as IR-19 rather than imputed.

## 4. Ownership and optimiser columns

> POWN sums to 100.68% across the six free rows, i.e. essentially the entire field, so POWN is a share of projected field usage rather than an independent probability. TEAMOWN is identical for all six rows (team-level). OPTO is a fantasy-point projection from RotoGrinders' optimiser, not a percentage - it ranges over the same units as CEIL. IR-22.

| player | POWN |
| --- | ---: |
| Ketel Marte | 23.36% |
| Gabriel Moreno | 14.56% |
| Geraldo Perdomo | 16.08% |
| Ildemaro Vargas | 22.73% |
| Nolan Arenado | 13.88% |
| Jordan Lawlar | 10.07% |

| | |
| --- | --- |
| POWN sum over 6 rows | 100.68% |
| POWN range | 10.07% - 23.36% |
| TEAMOWN (identical on every row) | 17.58% |
| OPTO range | 19.71 - 32.48 (FPTS units, not a percentage) |

POWN summing to ~100% over the free rows means it is a share of projected field usage. RGENGY's own pOWN is normalised the same way (`ownership.project_ownership` returns shares summing to 1.0), capped at `MAX_POWN`, and labelled `calibrated=False` because beta is not fitted to any ownership data (IR-13). RotoGrinders' method IS documented - [THE BAT ownership projections FAQ](https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773) - gradient-boosted over historical DraftKings ownership - and that data is not obtainable from any free official feed, which is why RGENGY substitutes a transparent choice model instead of claiming a reproduction.

## 5. OBFPTS is consistently 8-13% above FPTS, and undefined

> OBFPTS is consistently above FPTS by 8-13% and is published at full float precision while FPTS is rounded to 2dp, which suggests OBFPTS is an unrounded model output on a slightly different scale. Its definition is NOT published anywhere reachable, so RGENGY does not attempt to reproduce it. IR-21.

| player | OBFPTS / FPTS |
| --- | ---: |
| Ketel Marte | 1.1255 |
| Gabriel Moreno | 1.1032 |
| Geraldo Perdomo | 1.0874 |
| Ildemaro Vargas | 1.1019 |
| Nolan Arenado | 1.1123 |
| Jordan Lawlar | 1.0848 |

| | |
| --- | --- |
| n | 6 |
| mean ratio | 1.1025 |
| range | 1.0848 - 1.1255 |
| sd | 0.0139 |
| definition published | **False** |

## 6. Columns that were constant across every row

A column with the same value on all six rows is a slate-level or game-level quantity rendered per player, not a per-player projection. Treating one as per-player is how a reproduction goes quietly wrong.

| column | value on every row |
| --- | --- |
| `TEAM` | ARI |
| `OPP` | COL |
| `IP` | 0 |
| `BBA` | 0 |
| `K` | 0 |
| `W` | 0 |
| `ER` | 0 |
| `HA` | 0 |
| `HBP` | 0 |
| `QS` | 0 |
| `FPTS/$` | null |
| `PARK` | COL |
| `OUTS` | 0 |
| `PC` | null |
| `REFTM` | ARI |
| `REFOPP` | COL |
| `WIND` | COLOut6 |
| `TEMP` | 74 |
| `TEMPDESC` | neutraltemp |
| `SMASH` | 0.36 |
| `TOPVAL` | 0.134 |
| `TEAMOWN` | 0.1758 |
| `DIFFERENCE` | 0.1842 |
| `LEV` | 9 |

Note `LEV` = 9 and `SMASH` = 0.36 on every row: both are slate-level constants here, which is direct evidence against reading LEV as a per-player leverage score. RGENGY computes its own per-player `lev` and labels it as its own definition (IR-21).

## 7. Columns that varied per player

`PLAYER`, `SALARY`, `POS`, `PA`, `1B`, `2B`, `3B`, `HR`, `RBI`, `R`, `SB`, `BB`, `FPTS`, `H`, `BASES`, `BATK`, `HRRBI`, `OBFPTS`, `ORDER`, `UNDERDOG`, `PRIZEPICKS`, `FLOOR`, `CEIL`, `POWN`, `OPTO`

## 8. Columns whose definition could not be determined

> These columns are published without a definition anywhere reachable. Some are partly guessable from their inputs (BASES ~= 1B + 2*2B + 3*3B + 4*HR is consistent with the data to within rounding; H ~= 1B+2B+3B+HR) but RGENGY does not publish a value for any of them, and the grid writer marks them null with `unfilled_columns` rather than inventing one. See IR-21 and limitation L-05.

| column | published on the free tier | RGENGY |
| --- | :---: | --- |
| `BATK` | yes (varies per row) | **null** + written reason |
| `HRRBI` | yes (varies per row) | **null** + written reason |
| `BASES` | yes (varies per row) | **null** + written reason |
| `H` | yes (varies per row) | **null** + written reason |
| `PC` | yes (None) | **null** + written reason |
| `DIFFERENCE` | yes (0.1842) | **null** + written reason |
| `LEV` | yes (9) | **null** + written reason |
| `SMASH` | yes (0.36) | **null** + written reason |
| `TOPVAL` | yes (0.134) | **null** + written reason |

## 9. Strategies behind the product

What the grid's column set implies about how RotoGrinders expects its users to build lineups. Each inference is marked as an inference.

| observed feature | implied strategy | confidence |
| --- | --- | --- |
| `FPTS/$` published beside every projection, and verified exact | Salary efficiency, not raw projection, is the primary sort. A $3,000 player at 3.0 FPTS/$ beats a $6,000 player at 2.6. | **verified** |
| `FLOOR` and `CEIL` both published, ~7x asymmetric | Cash contests want the floor, GPPs want the ceiling; the asymmetry says upside is modelled far more widely than downside. | **verified ratios**, inferred intent |
| `POWN` normalised to ~100% of the field | Leverage is a share comparison: a player whose production share exceeds his ownership share is a GPP differentiator. | observed |
| `OPTO` in FPTS units, not a percentage | The optimiser's objective is projected points under a salary cap, not a value or upside ratio. | observed |
| `SMASH`, `TOPVAL`, `DIFFERENCE`, `LEV` published without definitions | Upside probability, top-value flag and a difference score are first-class UI concepts, but the thresholds are proprietary. | observed absence |
| `UNDERDOG` and `PRIZEPICKS` columns beside `FPTS` | RotoGrinders re-publishes partner projections in its own grid. PRIZEPICKS equalled FPTS exactly on all six rows while UNDERDOG differed, so at least one partner simply surfaces RotoGrinders' own number. | observed on 6 rows - **not** generalisable (IR-23) |
| `WIND`, `TEMP`, `TEMPDESC`, `PARK` per row | Environment is folded into the projection and shown to the user rather than hidden. `TEMPDESC` values like `neutraltemp` suggest a discrete classification of a continuous input. | observed |
| `ORDER` (batting order) per row | Lineup position is an input to plate appearances, which is why RGENGY resolves `batting_order` explicitly. | observed |
| `REFTM` / `REFOPP` constant per row | A comparison affordance, not a projection. | observed |

## 10. Data sources behind RotoGrinders' product

Only what is documented by RotoGrinders itself or observable in the grid. Anything beyond this is speculation and is not listed.

| feature | documented source | link |
| --- | --- | --- |
| Ownership projections | RotoGrinders' own FAQ: gradient-boosted trees (XGBoost) trained on historical DraftKings ownership data plus several hundred explanatory variables, tailored to DraftKings mid-stakes multi-entry tournaments, fully automated, refreshed on the same five-minute loop as the projections | [https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773](https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773) |
| Implied team totals | The Bryant formula attributed to co-founder Riley Bryant, with `AdjustedSpread` unpublished | [https://rotogrinders.com/articles/the-bat-vs-vegas-2016-results-1873096](https://rotogrinders.com/articles/the-bat-vs-vegas-2016-results-1873096) |
| MLB projections | THE BAT X (Chris Carty), licensed | not retrievable |
| Grid columns | Observed directly on the free tier of the MLB projection grid | [https://rotogrinders.com/projected-stats/mlb?site=draftkings](https://rotogrinders.com/projected-stats/mlb?site=draftkings) |
| FanDuel NBA scoring and value heuristics (5x/4x/6x) | RotoGrinders' own strategy article | [https://rotogrinders.com/articles/fanduel-nba-strategy-239702](https://rotogrinders.com/articles/fanduel-nba-strategy-239702) |

RGENGY's substitute sources for each of these are listed in [02-data-sources.md](02-data-sources.md), with the `replaces` field naming exactly which RotoGrinders feature each endpoint substitutes for.
