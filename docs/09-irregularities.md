<!-- GENERATED FILE - DO NOT EDIT: rendered by scripts/build_docs.py from the committed registries. Edit the source and re-run the generator. -->

# 09 - Irregularities

Everything found during the audit that is wrong, conflicting, undefined or unverifiable. Generated from `rgengy/findings.py`, which is the single source of truth: the scoring tables, module docstrings and quality findings all cite these ids, and `tests/test_findings.py` fails if the two disagree in either direction.

**32 findings** on 2026-09-22: 26 irregularities and 6 limitations - 17 open, 3 stated assumptions, 9 resolved, 3 declared-unused identifiers, 1 critical.

> Gaps in the numbering are **declared, not silent**. An id that was consumed during the
> audit and then folded into another finding stays on the register with status
> `unused-id`, because renumbering would quietly invalidate every cross-reference already
> written into the scoring tables.

## Index

| id | severity | status | title |
| --- | --- | --- | --- |
| [IR-01](#ir01) | warning | OPEN | ESPN's site API is undocumented and publishes no terms of use |
| [IR-02](#ir02) | warning | OPEN | RotoGrinders publishes the Bryant formula but not its AdjustedSpread input |
| [IR-03](#ir03) | warning | STATED ASSUMPTION | The score-distribution sigmas used to turn a margin into a win probability are unaudited |
| [IR-04](#ir04) | info | OPEN | DraftKings MLB caught-stealing (-2) is reported by only one source |
| [IR-05](#ir05) | warning | OPEN | DraftKings MLB quality-start bonus is directly contradicted between sources |
| [IR-06](#ir06) | info | OPEN | FanDuel MLB earned-run penalty is -3 in three sources and -1 in one |
| [IR-07](#ir07) | info | UNUSED IDENTIFIER | Identifier IR-07 is deliberately unused |
| [IR-08](#ir08) | info | OPEN | FanDuel NBA double-double and triple-double bonuses are unconfirmed |
| [IR-09](#ir09) | info | RESOLVED | RESOLVED: DraftKings NHL goal value was missing, then mis-documented |
| [IR-10](#ir10) | warning | RESOLVED | RESOLVED: FanDuel NHL scoring is now operator-confirmed; +/- is absent from the operator page |
| [IR-11](#ir11) | warning | OPEN | Yahoo MLB scoring is sourced from a single 2019 document |
| [IR-12](#ir12) | warning | STATED ASSUMPTION | RotoGrinders' floor/ceiling ratios are calibrated on six rows |
| [IR-13](#ir13) | warning | STATED ASSUMPTION | The ownership model's beta is an uncalibrated default |
| [IR-14](#ir14) | info | RESOLVED | RESOLVED: DraftKings NHL was double-counting goals via shots-on-goal |
| [IR-15](#ir15) | info | RESOLVED | RESOLVED: representation overlaps let one event satisfy two scoring keys |
| [IR-16](#ir16) | warning | OPEN | FanDuel NFL and DraftKings NBA flex eligibility is disputed between sources |
| [IR-17](#ir17) | critical | RESOLVED | RESOLVED: roster templates that produced illegal lineups |
| [IR-18](#ir18) | warning | RESOLVED | RESOLVED: the NFL 100/300-yard bonuses are scored by BOTH operators (FanDuel's own page) |
| [IR-19](#ir19) | warning | RESOLVED | RESOLVED: players with no usable sample were silently dropped |
| [IR-20](#ir20) | info | UNUSED IDENTIFIER | Identifier IR-20 is deliberately unused |
| [IR-21](#ir21) | warning | OPEN | RotoGrinders publishes OBFPTS, SMASH, LEV, TOPVAL and DIFFERENCE without definitions |
| [IR-22](#ir22) | warning | OPEN | RotoGrinders' grid schema was only transcribed for three sports |
| [IR-23](#ir23) | warning | OPEN | Team win probability had two competing origins, and PRIZEPICKS equals FPTS only on six rows |
| [IR-24](#ir24) | warning | RESOLVED | RESOLVED: the registered NHL club-schedule endpoint 404'd when actually fetched |
| [IR-25](#ir25) | warning | RESOLVED | RESOLVED: the shipped floor-ratio constant did not match its own sample |
| [IR-26](#ir26) | info | OPEN | DraftKings' own MLB scoring article contradicts itself on the pitcher win value |
| [L-01](#l01) | info | UNUSED IDENTIFIER | Identifier L-01 is deliberately unused |
| [L-02](#l02) | warning | OPEN | No raw-socket network access from the build sandbox; operator rules coverage is now partial, not absent |
| [L-03](#l03) | warning | OPEN | The WNBA roster templates are unconfirmed |
| [L-04](#l04) | warning | OPEN | DraftKings team-defence tiers remain unaudited; FanDuel's are operator-documented but not yet modelled |
| [L-05](#l05) | warning | OPEN | RotoGrinders' paywalled features could not be inspected at all |
| [L-06](#l06) | warning | OPEN | Player outcomes are simulated from a normal approximation, not a per-stat model |

---

## IR-01

**ESPN's site API is undocumented and publishes no terms of use**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/sources.py` |

**What was found.** The slate, score, venue and odds data for NFL, NBA, NHL and WNBA comes from https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard. It was retrieved live on 2026-09-22 (HTTP 200) and its field names were confirmed by inspection, but ESPN publishes no documentation and no terms for it. It is an internal feed for espn.com, not a product.

**Why it matters.** The feed can change shape or be withdrawn without notice, and continued use is a compliance risk for any published or commercial deployment.

**What RGENGY does about it.** The endpoint is marked official=False with a terms_url of null in the registry, so every artefact that used it says so. Replace it with a licensed provider before any commercial use. `rgengy probe` re-checks the live shape.

**Sources retrieved.**

- [https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard](https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard)
- [https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c](https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c)

---

## IR-02

**RotoGrinders publishes the Bryant formula but not its AdjustedSpread input**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/vegas.py` |

**What was found.** RotoGrinders attributes this implied-team-total formula to co-founder Riley Bryant: (TotalPoints / 2) - (Spread * (100 / (AdjustedSpread + 100))) / 2. The derivation of `AdjustedSpread` is not published anywhere on the site.

**Why it matters.** The formula cannot be reproduced end to end from published information alone. Any number produced by guessing AdjustedSpread would look exactly like a reproduction and would not be one.

**What RGENGY does about it.** `vegas.bryant_published()` transcribes the formula verbatim and takes `adjusted_spread` as a REQUIRED argument, so it raises rather than invents one. It is shipped for inspection, not as the default path; `vegas.implied_totals()` is the default and documents its own method.

**Sources retrieved.**

- [https://rotogrinders.com/articles/the-bat-vs-vegas-2016-results-1873096](https://rotogrinders.com/articles/the-bat-vs-vegas-2016-results-1873096)

---

## IR-03

**The score-distribution sigmas used to turn a margin into a win probability are unaudited**

| | |
| --- | --- |
| kind | irregularity |
| status | STATED ASSUMPTION |
| severity | warning |
| cited in | `rgengy/engines.py`, `rgengy/pipeline.py` |

**What was found.** Where no market line exists, a team win probability is derived from the expected output differential divided by a per-sport sigma (`engines.SIGMA_BY_SPORT`). Those sigmas are conventional values, not fitted to data, and none is confirmed by an official source.

**Why it matters.** Derived win probabilities are sensitive to sigma. The NFL value of 13.5 is known to understate heavy favourites, so a moneyline-derived probability should be preferred wherever one exists.

**What RGENGY does about it.** The preference order is enforced in one place (`engines.team_win_probability`): market line first, differential second, and the method actually used is written into the projection note and into the artefact. No win probability is ever emitted without its origin.

---

## IR-04

**DraftKings MLB caught-stealing (-2) is reported by only one source**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | info |
| cited in | `rgengy/data/scoring/mlb_draftkings.json` |

**What was found.** Only RotoWire lists Caught Stealing = -2 for DraftKings MLB. The 2026 fantasyteamadvice calculator and the DraftKings/FanDuel comparison tables omit it entirely, which is not the same as contradicting it. In the second audit pass DraftKings' own MLB scoring article (DraftKings Network, retrieved 2026-09-22) was checked specifically for this stat: it lists NO caught-stealing penalty either, so the operator document neither confirms nor refutes RotoWire's -2. (A low-reliability comparison site, rotopicks.com, claims DraftKings deducts 1 point per caught stealing, but the same document also gives DraftKings pitching values that contradict the operator's own page, so it is recorded only as noise.)

**Why it matters.** A hitter's FPTS may be overstated by up to 2 points per caught stealing.

**What RGENGY does about it.** The value is shipped as `verification_status: single-source`, `disputed: true`, `agreement: 1`, so `rgengy scoring` and the site both show it as the weakest evidence class on the table.

**Sources retrieved.**

- [https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444)

---

## IR-05

**DraftKings MLB quality-start bonus is directly contradicted between sources**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/data/scoring/mlb_draftkings.json` |

**What was found.** sportsfanfocus and dailyfantasysports101 both show DraftKings Quality Start = 0 (no bonus); runpuresports lists +4 under its DraftKings heading. This is a genuine contradiction, not an omission. Second audit pass, 2026-09-22: DraftKings' own MLB scoring article (DraftKings Network) was retrieved and lists complete-game (+2.5), complete-game-shutout (+2.5) and no-hitter (+5) bonuses but NO quality-start bonus - operator-page absence now supports the 0.0 reading, though absence is still not a positive operator statement of zero.

**Why it matters.** A starting pitcher's FPTS is understated by 4.0 if runpuresports is right. That is large relative to a pitcher's typical projection and would change roster selection.

**What RGENGY does about it.** Set to 0.0 (the two-source majority) and marked `disputed: true`. Resolving it needs DraftKings' own scoring page, which is inside the logged-in app and could not be retrieved. `rgengy scoring` prints the conflict next to the value.

**Sources retrieved.**

- [https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- [https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- [https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)

---

## IR-06

**FanDuel MLB earned-run penalty is -3 in three sources and -1 in one**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | info |
| cited in | `rgengy/data/scoring/mlb_fanduel.json` |

**What was found.** Three independent sources give FanDuel MLB Earned Run = -3. runpuresports gives -1. The majority value was adopted.

**Why it matters.** If the outlier is correct, FanDuel pitcher FPTS is understated by 2.0 per earned run - a material error over a 5-run outing.

**What RGENGY does about it.** Shipped as -3.0 with the conflict recorded in the value's note and surfaced by `rgengy scoring`. Needs FanDuel's own scoring page to settle.

**Sources retrieved.**

- [https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)

---

## IR-07

**Identifier IR-07 is deliberately unused**

| | |
| --- | --- |
| kind | irregularity |
| status | UNUSED IDENTIFIER |
| severity | info |
| cited in | `rgengy/findings.py` |

**What was found.** No finding in this register, in the scoring tables, or anywhere in the source tree cites IR-07. The id was consumed during the audit by an item that was resolved before the register was written and then folded into IR-05 and IR-06, which cover the same class of problem (single-source and contradicted scoring values).

**Why it matters.** A gap in the numbering. Left undeclared it would invite the assumption that a finding had been suppressed.

**What RGENGY does about it.** Declared here rather than renumbered: renumbering would silently invalidate every IR-nn cross-reference already written into the scoring tables and module docstrings.

---

## IR-08

**FanDuel NBA double-double and triple-double bonuses are unconfirmed**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | info |
| cited in | `rgengy/data/scoring/nba_fanduel.json`, `scripts/build_scoring_tables.py` |

**What was found.** Neither RotoGrinders' own FanDuel NBA strategy article nor dfsbuild's comparison table lists a FanDuel double-double or triple-double bonus, but FanDuel has historically scored them. Absence from two secondary sources is not evidence of absence from the operator's rules.

**Why it matters.** A player reaching a double-double may be understated. Both keys are shipped at 0.0, which is the conservative direction - it never overstates a projection.

**What RGENGY does about it.** Both keys are marked `disputed: true` with the ambiguity stated in their notes, and `quality.check_scoring_coverage` reports them as a coverage question rather than letting the zero pass silently.

**Sources retrieved.**

- [https://rotogrinders.com/articles/fanduel-nba-strategy-239702](https://rotogrinders.com/articles/fanduel-nba-strategy-239702)

---

## IR-09

**RESOLVED: DraftKings NHL goal value was missing, then mis-documented**

| | |
| --- | --- |
| kind | irregularity |
| status | RESOLVED |
| severity | info |
| cited in | `rgengy/data/scoring/nhl_draftkings.json`, `scripts/build_scoring_tables.py` |

**What was found.** Pass 1 had no sourced value for a DraftKings NHL goal. Pass 2 adopted the operator value from DraftKings' own NHL DFS 101 article (dknetwork.draftkings.com, an operator property). CORRECTION in the third pass: the register text previously said the operator article 'states goal = 10.0' - that was a documentation error. The operator article states Goal = +8.5 Pts (and shows a worked example of a goal plus its shot-on-goal totalling 10.0). The shipped table has been 8.5 all along, which matches the operator document; only this register entry was wrong. The full operator table (retrieved 2026-09-22) is: Goal +8.5, Assist +5, Shot on Goal +1.5, Blocked Shot +1.3, Short-Handed Point bonus +2, Shootout Goal +1.5, Hat Trick +3, 5+ Shots +3, 3+ Blocked Shots +3, 3+ Points +3; goalies: Win +6, Save +0.7, Goal Against -3.5, Shutout +4, Overtime Loss +2, 35+ Saves +3.

**Why it matters.** Resolved twice over: the value is operator-sourced, and the register itself is now consistent with both the operator document and the shipped table.

**What RGENGY does about it.** Adopted 8.5 from dknetwork.draftkings.com with the operator URL in the value's source list, and every value in the nhl:draftkings table is now marked `confirmed_by_operator: true` against that same document.

**Sources retrieved.**

- [https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101)

---

## IR-10

**RESOLVED: FanDuel NHL scoring is now operator-confirmed; +/- is absent from the operator page**

| | |
| --- | --- |
| kind | irregularity |
| status | RESOLVED |
| severity | warning |
| cited in | `rgengy/data/scoring/nhl_fanduel.json`, `rgengy/quality.py` |

**What was found.** The FanDuel NHL table originally rested on exactly one document (ftnfantasy), and a Reddit thread claimed FanDuel also scores plus/minus. RESOLVED in the second audit pass (2026-09-22): FanDuel's public rules page (https://www.fanduel.com/rules, Hockey section, retrieved that day) states Goals=12, Assists=8, Shots on Goal=1.6, Short Handed Points=+2, Power Play Points=+0.5, Blocked Shots=1.6; goalies: Wins=12, Goals Against=-4, Saves=0.8, Shutouts=8 - every one matches the shipped values, so the single-source weakness is gone. The SAME page contradicts the plus/minus claim: no plus/minus stat appears anywhere in the operator's enumerated hockey scoring.

**Why it matters.** Settled for every non-zero coefficient. The plus/minus key stays 0.0, but it can no longer be described as a likely understatement: the operator's own published table does not list plus/minus at all.

**What RGENGY does about it.** Every nhl:fanduel value is marked `confirmed_by_operator: true` with the rules-page URL; `plus_minus` stays `not-audited` at 0.0 with a note recording that the operator page omits it and that scoring it would now be the change requiring evidence. The operator note 'no points are awarded for goals or saves during shootouts' is recorded in the table notes.

**Sources retrieved.**

- [https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)

---

## IR-11

**Yahoo MLB scoring is sourced from a single 2019 document**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/data/scoring/mlb_yahoo.json`, `scripts/build_scoring_tables.py` |

**What was found.** `mlb:yahoo` rests on one document published in 2019. RotoGrinders does offer a Yahoo projection view, but its scoring values are behind the subscription and could not be retrieved.

**Why it matters.** Yahoo's scoring may have changed in the intervening seasons. Every Yahoo number RGENGY publishes is older than the audit by up to seven years.

**What RGENGY does about it.** The table's meta records the single-source status and the document's age, and the site shows Yahoo last. Yahoo is not used for any validated comparison.

---

## IR-12

**RotoGrinders' floor/ceiling ratios are calibrated on six rows**

| | |
| --- | --- |
| kind | irregularity |
| status | STATED ASSUMPTION |
| severity | warning |
| cited in | `rgengy/engines.py`, `scripts/analyze_rg_public_grid.py` |

**What was found.** The free tier of RotoGrinders' MLB projection grid exposes six rows. From those, FLOOR/FPTS averaged 0.3030 and CEIL/FPTS averaged 2.2229, giving `RG_OBSERVED_FLOOR_RATIO` and `RG_OBSERVED_CEIL_RATIO`.

**Why it matters.** n=6 is far too small to treat as a distribution. The ratios also come from one sport, one site and one slate, and only hitters and pitchers in whatever proportion those six rows happened to contain.

**What RGENGY does about it.** The sample size is stored next to the constants (`RG_OBSERVED_SAMPLE_SIZE = 6`) and printed wherever the rg_band mode is used. `rg_band` is opt-in; the default band comes from RGENGY's own distribution model, not from these ratios.

**Sources retrieved.**

- [https://rotogrinders.com/projected-stats/mlb?site=draftkings](https://rotogrinders.com/projected-stats/mlb?site=draftkings)

---

## IR-13

**The ownership model's beta is an uncalibrated default**

| | |
| --- | --- |
| kind | irregularity |
| status | STATED ASSUMPTION |
| severity | warning |
| cited in | `rgengy/ownership.py`, `rgengy/pipeline.py` |

**What was found.** RotoGrinders' pOWN is gradient-boosted (XGBoost) over historical DraftKings ownership plus several hundred explanatory variables, trained on mid-stakes multi-entry tournaments. Historical per-contest ownership is not available from any free official feed, so that model cannot be reproduced. RGENGY substitutes a softmax choice model over player value with one parameter, beta, defaulted to 0.35.

**Why it matters.** pOWN is a transparent modelling choice, not a measurement. Its absolute level is arbitrary; only its ordering is meaningful.

**What RGENGY does about it.** `default_model()` returns `calibrated=False`, the ownership stage reports `degraded` with this id in the reason, and `calibrate_beta()` fits beta by deterministic grid search the moment real ownership data is supplied.

**Sources retrieved.**

- [https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773](https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773)

---

## IR-14

**RESOLVED: DraftKings NHL was double-counting goals via shots-on-goal**

| | |
| --- | --- |
| kind | irregularity |
| status | RESOLVED |
| severity | info |
| cited in | `rgengy/scoring.py`, `rgengy/quality.py`, `scripts/build_scoring_tables.py` |

**What was found.** A goal is also a shot on goal. Pass 1 scored a goal under both `g` and `sog`, which counted the same event twice.

**Why it matters.** Resolved. Goaler and skater FPTS were overstated before the fix.

**What RGENGY does about it.** The overlap is now declared in `scoring.REPRESENTATION_SETS` so `quality.check_representation_double_count` fails the run loudly if any shipped table reintroduces it. The redundant key is pinned to 0.0 and marked `intentionally_zero` so the coverage check reports it as deliberate, not as a gap.

**Sources retrieved.**

- [https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101)

---

## IR-15

**RESOLVED: representation overlaps let one event satisfy two scoring keys**

| | |
| --- | --- |
| kind | irregularity |
| status | RESOLVED |
| severity | info |
| cited in | `rgengy/scoring.py`, `rgengy/quality.py` |

**What was found.** Several stat families are nested - a hit is also a single/double/triple/homer, a shot on goal is also a goal, a strikeout is also an out. Scoring both keys counts the production twice.

**Why it matters.** Silent FPTS inflation, which is worse than a visible error because the total still looks plausible.

**What RGENGY does about it.** `scoring.REPRESENTATION_SETS` declares every overlap; `scoring.representation_audit()` and `check_representation_double_count()` run on every configuration at every run and raise a critical finding if any table scores two members of a set simultaneously. tests/test_quality.py asserts all 11 shipped tables are clean.

---

## IR-16

**FanDuel NFL and DraftKings NBA flex eligibility is disputed between sources**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/models.py`, `rgengy/data/scoring/nfl_fanduel.json` |

**What was found.** fanscout.pro and RotoGrinders disagree on the FanDuel NBA roster shape, and two 2026 sources disagree on which positions the FanDuel NFL FLEX accepts. `nfl:fanduel` is therefore marked `disputed`.

**Why it matters.** A roster template that is wrong produces lineups the operator rejects outright - a hard failure, not a scoring error.

**What RGENGY does about it.** Both templates carry `verification_status: disputed` with the conflicting sources listed, and `models.default_roster()` returns that status in its output so no caller can miss it. tests/test_models.py pins the disputed flag so it cannot be quietly upgraded to 'consistent'.

**Sources retrieved.**

- [https://fanscout.pro/nba-fanduel-optimizer](https://fanscout.pro/nba-fanduel-optimizer)
- [https://rotogrinders.com/articles/fanduel-nba-strategy-239702](https://rotogrinders.com/articles/fanduel-nba-strategy-239702)

---

## IR-17

**RESOLVED: roster templates that produced illegal lineups**

| | |
| --- | --- |
| kind | irregularity |
| status | RESOLVED |
| severity | critical |
| cited in | `rgengy/models.py`, `tests/test_models.py` |

**What was found.** Pass 1 listed separate C and 1B slots for DraftKings MLB, requiring 11 players where the operator's classic roster combines them into one C/1B slot for 10. Similar off-by-one errors affected the NHL and NBA templates (a shape with 2 UTILs is not a legal DraftKings NHL roster).

**Why it matters.** Every lineup produced was illegal and would have been rejected at submission. This is the highest-severity class of defect in the project because it is invisible in the projection output.

**What RGENGY does about it.** Templates were corrected against the operators' published rosters, and `models.default_roster()` now self-checks that the slot counts sum to the documented player count and raises if they do not. tests/test_models.py and tests/test_optimizer.py assert the exact slot shape per sport and site, including the combined C/1B slot and the absence of a DraftKings NFL kicker.

**Sources retrieved.**

- [https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- [https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup)

---

## IR-18

**RESOLVED: the NFL 100/300-yard bonuses are scored by BOTH operators (FanDuel's own page)**

| | |
| --- | --- |
| kind | irregularity |
| status | RESOLVED |
| severity | warning |
| cited in | `rgengy/data/scoring/nfl_draftkings.json`, `rgengy/data/scoring/nfl_fanduel.json`, `scripts/build_scoring_tables.py` |

**What was found.** This finding has been reversed twice, which is itself the lesson. Pass 1 applied the 100-yard rushing, 100-yard receiving and 300-yard passing bonuses to both operators. Pass 2 'corrected' FanDuel to 0.0 on the strength of two 2026 secondary sources (fantasyfootballers, fantasyteamadvisors). In the second audit pass of this session (2026-09-22) FanDuel's own public rules page (https://www.fanduel.com/rules, Football section) was retrieved and it states: 100+ Receiving Yard Bonus = 3 Points, 100+ Rushing Yard Bonus = 3 Points, 300+ Passing Yard Bonus = 3 Points. The operator page outranks the secondary sources, so both operators score all three bonuses at 3.0, and DraftKings' side is independently confirmed by its own NFL DFS 101 article (dknetwork.draftkings.com, 2025-08-27).

**Why it matters.** The pass-2 change UNDERSTATED FanDuel NFL FPTS by up to 3.0 per qualifying player - the exact error the pass-2 note warned about, committed in the opposite direction by trusting secondary sources over the operator.

**What RGENGY does about it.** `nfl:fanduel` ships 100ru / 100rec / 300pa = 3.0 marked `confirmed_by_operator: true` with the rules-page URL. The rule this register draws from the double reversal: when an operator page is reachable, it is retrieved and preferred even when multiple recent secondary sources agree on the contrary value.

**Sources retrieved.**

- [https://fantasyfootballers.org/featured/draftkings-vs-fanduel/](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- [https://fantasyteamadvisors.com/nfl-dfs-strategy/](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- [https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)

---

## IR-19

**RESOLVED: players with no usable sample were silently dropped**

| | |
| --- | --- |
| kind | irregularity |
| status | RESOLVED |
| severity | warning |
| cited in | `rgengy/pipeline.py`, `rgengy/quality.py`, `scripts/analyze_rg_public_grid.py` |

**What was found.** Pass 1 removed any player for whom no projection could be produced. On RotoGrinders' own public grid the same situation is visible as a row published with no projection.

**Why it matters.** Dropping a player makes any roster slot that only they could fill impossible to satisfy, which silently converts one missing season sample into 'no lineup exists for this sport at all'. The failure is reported at the optimizer, far from its cause.

**What RGENGY does about it.** Players are retained at 0.0 with a run warning naming them, and an all-zero projection is flagged separately from an empty one because the fixes differ. `quality.check_zero_projection` reports every paid player with no projection in the run report.

**Sources retrieved.**

- [https://rotogrinders.com/projected-stats/mlb?site=draftkings](https://rotogrinders.com/projected-stats/mlb?site=draftkings)

---

## IR-20

**Identifier IR-20 is deliberately unused**

| | |
| --- | --- |
| kind | irregularity |
| status | UNUSED IDENTIFIER |
| severity | info |
| cited in | `rgengy/findings.py` |

**What was found.** No finding in this register, in the scoring tables, or anywhere in the source tree cites IR-20. The id was consumed during pass 2 by a simulator payout issue that was fixed outright and is now covered by tests/test_simulator.py rather than by an open finding.

**Why it matters.** A gap in the numbering, declared rather than silently renumbered.

**What RGENGY does about it.** Declared here. IR-21 to IR-23 were assigned after this gap opened and renumbering them would invalidate references already written into pipeline.py.

---

## IR-21

**RotoGrinders publishes OBFPTS, SMASH, LEV, TOPVAL and DIFFERENCE without definitions**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/pipeline.py`, `rgengy/ownership.py`, `scripts/analyze_rg_public_grid.py` |

**What was found.** The free tier of the MLB projection grid (retrieved 2026-09-22) exposes these columns with values but no formula. Observed: OBFPTS is published at full float precision at roughly 1.08-1.13x FPTS; LEV was 9 for all six free rows, i.e. a slate-level constant rather than a per-player quantity; OPTO is expressed in FPTS units, not as a percentage.

**Why it matters.** These are the columns most likely to be mistaken for reproduced features. Guessing a formula would produce numbers that look like RotoGrinders' and are not.

**What RGENGY does about it.** RGENGY leaves OBFPTS, TOPVAL, DIFFERENCE and OPTO null and computes its OWN clearly labelled `lev` (value share minus ownership share) and `smash` (P(FPTS > 1.5x projection)) into `extra`. `attach_ownership` writes an `analytics_provenance` block onto every player stating, per column, whether it is reproduced, RGENGY's own, or not computed - and tests/test_ownership.py asserts that block exists and says the right thing for each column.

**Sources retrieved.**

- [https://rotogrinders.com/projected-stats/mlb?site=draftkings](https://rotogrinders.com/projected-stats/mlb?site=draftkings)

---

## IR-22

**RotoGrinders' grid schema was only transcribed for three sports**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/models.py`, `rgengy/pipeline.py`, `tests/test_pipeline.py` |

**What was found.** Column headers were transcribed from the live site on 2026-09-22 for MLB (49 columns), NFL (38) and WNBA (33), and all three counts were re-verified against fresh retrievals later the same day (second audit pass). The NBA and NHL grid headers were NOT transcribed, so `models.RG_GRID_COLUMNS` deliberately omits them. TEAMOWN is a team-level roll-up whose aggregation RotoGrinders does not publish. The WNBA TOTAL column sits beside SPREAD and O/U with no published definition, but its values are arithmetically consistent with the OPPONENT-side implied total (O/U - SPREAD)/2 on every non-zero row of the re-verified slate (4 distinct games): RGENGY records that consistency as an observation and still leaves TOTAL null, because RotoGrinders publishes no formula and four rows prove nothing about the general rule.

**Why it matters.** Emitting an NBA or NHL grid under RotoGrinders' column headings would present RGENGY's own schema as a reproduction of theirs. Omitting a column silently would make the artefact impossible to diff against their grid.

**What RGENGY does about it.** `grid_rows()` sets `rg_column_schema_observed=False` and writes an explicit note for NBA/NHL. Every observed column is either mapped or listed in `unfilled_columns` with a written reason in `UNMAPPED_COLUMN_REASONS`, and every row carries the full column shape with nulls rather than omitting keys. tests/test_pipeline.py asserts the two-way invariant: no column without a mapping or a reason, and no reason without a column.

**Sources retrieved.**

- [https://rotogrinders.com/projected-stats/mlb?site=draftkings](https://rotogrinders.com/projected-stats/mlb?site=draftkings)

---

## IR-23

**Team win probability had two competing origins, and PRIZEPICKS equals FPTS only on six rows**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/engines.py`, `rgengy/pipeline.py`, `tests/test_engines.py` |

**What was found.** Two issues in the same class. (1) A win probability was being derived inside the projection engines as well as from the market line in the pipeline, so the same quantity could come from two places with different values. (2) On the six free MLB grid rows the PRIZEPICKS column equalled RotoGrinders' FPTS exactly, while UNDERDOG differed; that equivalence cannot be verified as a general rule from six rows.

**Why it matters.** A pitcher's win projection and a goalie's win projection would silently disagree with the market line shown beside them. Claiming PRIZEPICKS == FPTS generally would be an unverified extrapolation presented as a finding.

**What RGENGY does about it.** All win probabilities now come from one function, `engines.team_win_probability()`, with a fixed preference order (market line, then expected-output differential, then 0.0 with the source labelled 'unavailable'). It returns the source label alongside the probability and that label is written into the projection notes and the artefact. No engine may invent 0.5. PRIZEPICKS is left null with the six-row observation recorded rather than generalised.

**Sources retrieved.**

- [https://rotogrinders.com/projected-stats/mlb?site=draftkings](https://rotogrinders.com/projected-stats/mlb?site=draftkings)

---

## IR-24

**RESOLVED: the registered NHL club-schedule endpoint 404'd when actually fetched**

| | |
| --- | --- |
| kind | irregularity |
| status | RESOLVED |
| severity | warning |
| cited in | `rgengy/sources.py`, `rgengy/cli.py` |

**What was found.** The first pass registered the club schedule as https://api-web.nhle.com/v1/club/schedule/{club}/{season} with status 'documented' - a status meaning a third-party document described it, not that a response was ever observed. The second audit pass (2026-09-22) fetched it: HTTP 404. The plausible variant /v1/club-schedule/{club}/{season} also returned 404. The route that actually exists and returned HTTP 200 with a full 20262027 season schedule is /v1/club-schedule-season/{club}/{season}, which is now the registered template.

**Why it matters.** `rgengy probe --endpoint nhl.club_schedule` would have reported a 404 for every club, and any future caller of the endpoint would have inherited a dead URL that looked audited.

**What RGENGY does about it.** Template corrected, endpoint live-verified with the observed response fields recorded in the registry, and the lesson recorded: 'documented' is the weakest status in the vocabulary, and this register treats a template that 404s under test as a defect, not a footnote.

**Sources retrieved.**

- [https://api-web.nhle.com/v1/club-schedule-season/TOR/20262027](https://api-web.nhle.com/v1/club-schedule-season/TOR/20262027)

---

## IR-25

**RESOLVED: the shipped floor-ratio constant did not match its own sample**

| | |
| --- | --- |
| kind | irregularity |
| status | RESOLVED |
| severity | warning |
| cited in | `rgengy/engines.py`, `scripts/analyze_rg_public_grid.py`, `tests/test_engines.py` |

**What was found.** engines.py shipped RG_OBSERVED_FLOOR_RATIO = 0.3030 with RG_OBSERVED_SAMPLE_SIZE = 6, and the register (IR-12) claimed 0.3030 was the mean FLOOR/FPTS over the six audited rows. Recomputing from the committed fixture in the second audit pass gives 0.2525 over all six rows and 0.30296 over the five rows with a non-zero floor. The 0.3030 figure was therefore a five-row mean stored with a six-row sample size - the row published with FLOOR = 0 had been silently excluded.

**Why it matters.** The constant is only used by the opt-in `rg_band` mode, so no published projection was wrong, but the provenance chain (fixture -> analysis -> constant -> register) did not reproduce, which is exactly what this project exists to prevent.

**What RGENGY does about it.** The exclusion is now explicit: RG_OBSERVED_FLOOR_RATIO = 0.30296 with RG_OBSERVED_FLOOR_SAMPLE_SIZE = 5, the ceiling keeps its all-rows mean (2.2229, n = 6), `scripts/analyze_rg_public_grid.py` emits both the all-rows and non-zero means and states the exclusion rule, and tests pin the constants to the fixture arithmetic. Silent exclusion is replaced by documented exclusion.

**Sources retrieved.**

- [https://rotogrinders.com/projected-stats/mlb?site=draftkings](https://rotogrinders.com/projected-stats/mlb?site=draftkings)

---

## IR-26

**DraftKings' own MLB scoring article contradicts itself on the pitcher win value**

| | |
| --- | --- |
| kind | irregularity |
| status | OPEN |
| severity | info |
| cited in | `scripts/build_scoring_tables.py` |

**What was found.** DraftKings Network's 'Beginner MLB DFS: Scoring' (retrieved 2026-09-22) lists 'Win: +4 Pts' in its scoring table, but its own strategy prose later says wins are 'a nice chunk of points at 4.5'. The two statements cannot both be right. The table value of 4.0 is also the value every secondary source agrees on, so 4.0 is shipped.

**Why it matters.** If 4.5 were correct, every DraftKings MLB pitcher projection is understated by 0.5 per win - small next to the other coefficients but not zero.

**What RGENGY does about it.** The shipped value stays 4.0 (table beats prose, unanimous secondary agreement), the conflict is recorded in the value's note, and it stays flagged here until DraftKings' canonical in-app rules page can be retrieved.

**Sources retrieved.**

- [https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/)

---

## L-01

**Identifier L-01 is deliberately unused**

| | |
| --- | --- |
| kind | limitation |
| status | UNUSED IDENTIFIER |
| severity | info |
| cited in | `rgengy/findings.py` |

**What was found.** No limitation in this register or in the source tree cites L-01. The id was consumed during the audit by the absence of any outbound network access in the build environment, which turned out to be an environment property rather than a limitation of the system, and is documented in the README instead.

**Why it matters.** A gap in the numbering, declared rather than silently renumbered.

**What RGENGY does about it.** Declared here so the L-nn sequence can be read as complete.

---

## L-02

**No raw-socket network access from the build sandbox; operator rules coverage is now partial, not absent**

| | |
| --- | --- |
| kind | limitation |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/cli.py`, `rgengy/sources.py`, `.github/workflows/pages.yml` |

**What was found.** Raw HTTPS fetches from the build workspace fail with a TLS/SSL EOF error, so the runtime pipeline still cannot fetch live feeds from inside the sandbox. The first audit also recorded that 'no operator scoring page could be retrieved' - that half is now OUTDATED: the second audit pass (2026-09-22) verified, through the platform's document-retrieval channel, that FanDuel publishes its full DFS scoring rules publicly at https://www.fanduel.com/rules, and that DraftKings publishes operator- domain scoring articles on dknetwork.draftkings.com (NHL 2025-09-30, NFL 2025-08-27, NBA 2025-10-17, MLB 2020-05-29). DraftKings' canonical in-app rules page remains unretrieved, and those operator articles are editorial pages rather than the contractual rules - hence 'partial', not 'complete'.

**Why it matters.** Live feeds still cannot be exercised from the sandbox, so the pipeline is tested against synthetic and cached inputs and the slate stage honestly reports `unavailable` rather than substituting invented games. Scoring coverage, however, is materially stronger than the first pass claimed: large parts of five tables are now marked `confirmed_by_operator`.

**What RGENGY does about it.** `rgengy probe` and `rgengy verify` exist to be run from a networked machine; they stamp each endpoint - and, added in this pass, every URL cited by the scoring tables - with its live status and write verification.json. The GitHub Pages workflow runs them on every build so the published site reflects the live state rather than the audit state. `data/` is gitignored and regenerated.

**Sources retrieved.**

- [https://help.fanduel.com/](https://help.fanduel.com/)
- [https://www.draftkings.com/](https://www.draftkings.com/)
- [https://www.fanduel.com/rules](https://www.fanduel.com/rules)

---

## L-03

**The WNBA roster templates are unconfirmed**

| | |
| --- | --- |
| kind | limitation |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/models.py`, `tests/test_models.py` |

**What was found.** No source for the WNBA roster shape was retrieved during the audit. The templates were treated as the NBA shape reduced to six slots.

**Why it matters.** A WNBA lineup built from these templates may be rejected by the operator. Both `wnba:draftkings` and `wnba:fanduel` have zero sources and are marked `not-audited`.

**What RGENGY does about it.** `models.default_roster()` returns the `not-audited` status and a note beginning UNCONFIRMED for both, and tests/test_models.py asserts that any template with no sources must be marked `not-audited` and must say UNCONFIRMED - so the templates cannot be quietly upgraded without a source being added.

---

## L-04

**DraftKings team-defence tiers remain unaudited; FanDuel's are operator-documented but not yet modelled**

| | |
| --- | --- |
| kind | limitation |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/data/scoring/nfl_draftkings.json`, `rgengy/data/scoring/nfl_fanduel.json`, `rgengy/pipeline.py`, `rgengy/quality.py` |

**What was found.** The first pass could not retrieve DraftKings team-defence scoring from any source. The second audit pass (2026-09-22) improved the FanDuel half: FanDuel's public rules page (https://www.fanduel.com/rules, Football/Defense section) documents sacks = 1, fumble recovered = 2, interception = 2, safety = 2, blocked punt = 2, kick/punt return TD = 6, extra-point return = 2, and the exact points-allowed tiers (0 -> 10, 1-6 -> 7, 7-13 -> 4, 14-20 -> 1, 21-27 -> 0, 28-34 -> -1, 35+ -> -4) plus the formula FanDuel uses to compute points allowed. A secondary comparison table (dailyfantasysports101) shows DraftKings DST tiers identical to FanDuel's, but no DraftKings operator document for DST was retrieved. The shipped `dst_pts_allowed` coefficient is still 0.0 because RGENGY's engine models points allowed as a single expected value, not as a tier lookup.

**Why it matters.** DraftKings DST and kicker-projection error remains unknown (L-04 as originally filed). For FanDuel, the per-event DST coefficients are now operator-confirmed, but the tiered points-allowed scoring - often the largest DST term - is still not applied, so FanDuel DST FPTS remains understated by an unknown amount.

**What RGENGY does about it.** The FanDuel per-event keys are marked `confirmed_by_operator: true`. The operator tier table is stored verbatim in the FanDuel table JSON under `operator_tier_tables.dst_points_allowed` so no one has to re-retrieve it, and `dst_pts_allowed` stays 0.0 / intentionally_zero until the engine grows a tier lookup (roadmap: 'Model FanDuel's tiered DST points-allowed scoring'). Under `--strict` the unaudited DraftKings DST keys stay excluded from published totals.

**Sources retrieved.**

- [https://www.fanduel.com/rules](https://www.fanduel.com/rules)
- [https://www.dailyfantasysports101.com/football/](https://www.dailyfantasysports101.com/football/)
- [https://www.draftkings.com/](https://www.draftkings.com/)

---

## L-05

**RotoGrinders' paywalled features could not be inspected at all**

| | |
| --- | --- |
| kind | limitation |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/pipeline.py`, `scripts/analyze_rg_public_grid.py` |

**What was found.** The subscription tier - the full projection grid beyond six rows, the optimizer, ownership projections, THE BAT X projections, contest simulation and the partner-site columns (UNDERDOG, PRIZEPICKS) - is not retrievable without an account.

**Why it matters.** Every claim about those features rests on the free tier, on RotoGrinders' own published articles, or on nothing at all. Where nothing was available, RGENGY implements its own documented equivalent and says so.

**What RGENGY does about it.** The rebuild is explicit about which is which. `analytics_provenance` labels each column reproduced / RGENGY-own / not computed; the site carries the same three-way split; and no paywalled quantity is emitted under RotoGrinders' column heading without that label.

**Sources retrieved.**

- [https://rotogrinders.com/projected-stats/mlb?site=draftkings](https://rotogrinders.com/projected-stats/mlb?site=draftkings)
- [https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773](https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773)
- [https://rotogrinders.com/articles/the-bat-vs-vegas-2016-results-1873096](https://rotogrinders.com/articles/the-bat-vs-vegas-2016-results-1873096)

---

## L-06

**Player outcomes are simulated from a normal approximation, not a per-stat model**

| | |
| --- | --- |
| kind | limitation |
| status | OPEN |
| severity | warning |
| cited in | `rgengy/simulator.py` |

**What was found.** `simulator.sample_player_fpts` draws each player's score from a normal distribution built on the projected mean and a standard deviation derived from the floor/ceiling band. Real fantasy output is a sum of discrete, correlated events (a hit is also a run and an RBI; a pitcher's innings correlate with his strikeouts).

**Why it matters.** Tail behaviour is understated: a normal draw cannot produce a 4-home-run game, so simulated top-1 rates are conservative and the cash/top-10/top-1 ordering is preserved but the magnitudes are not trustworthy for large-field GPPs. The band is also over-dispersed relative to a true event model.

**What RGENGY does about it.** Documented in the simulator module docstring and surfaced in every simulation result. Replacing it needs a per-stat correlated event model, which needs the historical play-by-play data listed as future work in docs/10.
