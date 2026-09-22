<!-- GENERATED FILE - DO NOT EDIT: rendered by scripts/build_docs.py from the committed registries. Edit the source and re-run the generator. -->

# 03 - Scoring verification

Fantasy points are the product of a scoring table and a projection, so a wrong coefficient corrupts every number downstream of it. Each shipped table below lists every coefficient with the number of independent sources that agree on it, its verification status, and the URLs those sources came from. Generated from `rgengy/data/scoring/*.json` - edit the tables (via `scripts/build_scoring_tables.py`), not this file.

## Evidence classes across all tables

| verification status | coefficients | meaning |
| --- | ---: | --- |
| `multi-source-consistent` | 121 | two or more independent sources agree |
| `single-source` | 40 | exactly one source - the weakest evidence class |
| `not-applicable` | 12 |  |
| `not-audited` | 9 | no source was retrieved; the value is a documented convention, not a finding |
| `disputed` | 1 | sources contradict each other; the majority value was adopted and flagged |

## MLB / draftkings

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 50000 |
| audit date | 2026-09-22 |
| operator-confirmed | False - 19/21 values |
| coefficients | 21 |
| disputed | 2 |
| not audited | 0 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** DraftKings' own MLB scoring article (dknetwork.draftkings.com, 'Beginner MLB DFS: Scoring', retrieved 2026-09-22) now operator-confirms every non-zero value in this table: hitters 1B +3, 2B +5, 3B +8, HR +10, RBI +2, R +2, BB +2, HBP +2, Sac Fly +1.25, Sac Hit +1.25, SB +5; pitchers IP +2.25, K +2, W +4, ER -2, Hit Against -0.6, BB Against -0.6, Hit Batsman -0.6, CG +2.5, CGSO +2.5, No-Hitter +5. Two values stay unconfirmed: caught stealing (-2, single secondary source, IR-04) and the quality-start bonus (0 vs +4 conflict, IR-05). One value stays disputed-by-registration: none. The operator article itself is internally inconsistent on the win value (table +4 vs prose 4.5) - see IR-26.

> **Notes.** 'cs' (caught stealing, -2) is reported by only one source and is therefore marked disputed. Second audit pass (2026-09-22): operator article added; sac-fly / sac-hit / CG / CGSO / no-hitter bonuses operator-confirmed; 'cs' and 'qs' remain the table's two open questions.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `1b` | 3.0 | `multi-source-consistent` | 5 |  | - |
| `2b` | 5.0 | `multi-source-consistent` | 5 |  | - |
| `3b` | 8.0 | `multi-source-consistent` | 5 |  | - |
| `bb` | 2.0 | `multi-source-consistent` | 5 |  | - |
| `bba` | -0.6 | `multi-source-consistent` | 4 |  | - |
| `cg` | 2.5 | `multi-source-consistent` | 4 |  | Operator article: 'Complete Game: +2.5 Pts' / 'Complete Game Shutout: +2.5 Pts'. |
| `cgso` | 2.5 | `multi-source-consistent` | 4 |  | Additive with 'cg'; a complete-game shutout earns both bonuses. Operator article: 'Complete Game: +2.5 Pts' / 'Complete Game Shutout: +2.5 Pts'. |
| `cs` | -2.0 | `single-source` | 1 | yes | Only RotoWire lists Caught Stealing = -2 for DraftKings. The 2026 fantasyteamadvice calculator and the DK/FD comparison tables omit it. FLAGGED in docs/09-irregularities.md (IR-04). Second audit pass: DraftKings' own MLB scoring article lists NO caught-stealing penalty either, so the operator document neither confirms nor refutes -2 (IR-04). |
| `er` | -2.0 | `multi-source-consistent` | 5 |  | - |
| `ha` | -0.6 | `multi-source-consistent` | 4 |  | Operator article prints 'Hit Against: 0.6 Pts' without the sign; its own negative-points section confirms walks/hit-batters are -0.6 and every secondary source gives -0.6, so the sign is read as negative. |
| `hbp` | 2.0 | `multi-source-consistent` | 4 |  | - |
| `hbpa` | -0.6 | `multi-source-consistent` | 4 |  | Operator article lists 'Hit Batsman: -0.6 Pts' under pitchers, matching this value. |
| `hr` | 10.0 | `multi-source-consistent` | 5 |  | - |
| `ip` | 2.25 | `multi-source-consistent` | 5 |  | - |
| `k` | 2.0 | `multi-source-consistent` | 5 |  | - |
| `nohitter` | 5.0 | `multi-source-consistent` | 3 |  | Operator article: 'No Hitter: +5 Pts'. |
| `qs` | 0.0 | `disputed` | 2 | yes | sportsfanfocus and dailyfantasysports101 both show DraftKings Quality Start = 0 (i.e. no bonus); runpuresports lists '+4' under its DraftKings heading. Set to 0 and FLAGGED as IR-05 in docs/09-irregularities.md. Second audit pass: the operator MLB article lists complete-game (+2.5), complete-game-shutout (+2.5) and no-hitter (+5) bonuses but NO quality-start bonus, which supports the 0.0 reading without proving it (IR-05). |
| `r` | 2.0 | `multi-source-consistent` | 5 |  | - |
| `rbi` | 2.0 | `multi-source-consistent` | 5 |  | - |
| `sb` | 5.0 | `multi-source-consistent` | 5 |  | - |
| `win` | 4.0 | `multi-source-consistent` | 5 |  | Operator table (DraftKings Network MLB scoring article) lists 'Win: +4 Pts'; its own prose later says wins are 'a nice chunk of points at 4.5' - the article contradicts itself (IR-26). The table value 4.0 is shipped, matching every secondary source. |

<details><summary>Sources consulted for this table</summary>

- [https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/)
- [https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444)
- [https://fantasyteamadvice.com/mlb/fantasy-calculator](https://fantasyteamadvice.com/mlb/fantasy-calculator)
- [https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)
- [https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- [https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)

</details>

<details><summary>Per-stat source URLs</summary>

- `1b` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `2b` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `3b` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `bb` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `bba` (5): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `cg` (5): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `cgso` (5): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `cs` (1): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444)
- `er` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `ha` (5): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbp` (5): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbpa` (5): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hr` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `ip` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `k` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `nohitter` (4): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `qs` (3): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[2]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)
- `r` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `rbi` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `sb` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `win` (6): [[1]](https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/), [[2]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)

</details>

_All 6 distinct URLs for this table are listed in the two blocks above._

## MLB / fanduel

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 35000 |
| audit date | 2026-09-22 |
| operator-confirmed | **True** - 14/22 values |
| coefficients | 22 |
| disputed | 0 |
| not audited | 0 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** OPERATOR-CONFIRMED (2026-09-22): FanDuel's public rules page (https://www.fanduel.com/rules, Baseball section, retrieved that day) states 1B=3, 2B=6, 3B=9, HR=12, RBI=3.5, R=3.2, BB=3, SB=6, HBP=3; pitchers W=6, QS=4, ER=-3, SO=3, IP=3 with fractional scoring per out, plus the QS definition. Every non-zero value in this table is read from that page; the zeros (hits/walks-allowed penalties, CG/CGSO/no-hitter bonuses, caught stealing) are consistent with the operator page listing no such events. The secondary sources below are retained as corroboration and for the audit trail.

> **Notes.** FanDuel does not penalise pitchers for hits/walks/HBP allowed, so ha/bba/hbpa are 0. FanDuel scores per out (1 pt) rather than per inning; 3 outs = 1 inning = 3 pts, which reconciles the '+3 IP' and '+1 out' descriptions found in different sources. To avoid a double count, 'ip' carries the 3.0 and 'outs' is pinned at 0.0.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `1b` | 3.0 | `multi-source-consistent` | 5 |  | - |
| `2b` | 6.0 | `multi-source-consistent` | 5 |  | - |
| `3b` | 9.0 | `multi-source-consistent` | 5 |  | - |
| `bb` | 3.0 | `multi-source-consistent` | 5 |  | FanDuel pays a walk the same as a single - the single biggest hitter-scoring difference from DraftKings. |
| `bba` | 0.0 | `multi-source-consistent` | 3 |  | FanDuel does not penalise walks allowed. |
| `cg` | 0.0 | `single-source` | 1 |  | No FanDuel source lists a complete-game bonus. FanDuel's own rules page (retrieved 2026-09-22) lists no such scoring event, consistent with 0.0. |
| `cgso` | 0.0 | `single-source` | 1 |  | FanDuel's own rules page (retrieved 2026-09-22) lists no such scoring event, consistent with 0.0. |
| `cs` | 0.0 | `single-source` | 1 |  | No FanDuel source lists a caught-stealing penalty. FanDuel's own rules page (retrieved 2026-09-22) lists no such scoring event, consistent with 0.0. |
| `er` | -3.0 | `multi-source-consistent` | 3 |  | RESOLVED BY THE OPERATOR PAGE (IR-06): FanDuel's rules page states ER = -3pts. runpuresports' -1 remains recorded as the outlier. Operator page: https://www.fanduel.com/rules (retrieved 2026-09-22). |
| `ha` | 0.0 | `multi-source-consistent` | 3 |  | FanDuel does not penalise hits allowed. |
| `hbp` | 3.0 | `multi-source-consistent` | 3 |  | - |
| `hbpa` | 0.0 | `single-source` | 1 |  | Inferred 0 from the absence of an HBP-allowed penalty in every FanDuel table consulted. FanDuel's own rules page (retrieved 2026-09-22) lists no such scoring event, consistent with 0.0. |
| `hr` | 12.0 | `multi-source-consistent` | 5 |  | - |
| `ip` | 3.0 | `multi-source-consistent` | 4 |  | Equivalent to 1.0 per out recorded; see meta.notes. Operator page: 'IP = 3pts' with fractional scoring per out - arithmetically identical to 1 point per out, so 'outs' stays pinned at 0.0 (IR-14). |
| `k` | 3.0 | `multi-source-consistent` | 4 |  | - |
| `nohitter` | 0.0 | `single-source` | 1 |  | FanDuel's own rules page (retrieved 2026-09-22) lists no such scoring event, consistent with 0.0. |
| `outs` | 0.0 | `multi-source-consistent` | 2 |  | FanDuel's own tables describe this as 'Out Recorded = 1 point', which is arithmetically identical to 'Inning Pitched = 3 points' (3 outs = 1 inning). Scoring BOTH would double count a pitcher's innings, so RGENGY scores 'ip' at 3.0 and pins 'outs' at 0.0. RotoGrinders publishes an OUTS column on its MLB grid, which is why the field is modelled at all. See IR-14 in docs/09-irregularities.md. |
| `qs` | 4.0 | `multi-source-consistent` | 4 |  | Operator page: 'Quality Start = 4pts', defined as a starting pitcher who completes at least six innings and permits no more than three earned runs (https://www.fanduel.com/rules, retrieved 2026-09-22; supersedes the Boom Fantasy definition cited earlier - Boom Fantasy is a FanDuel-family pick'em product, not FanDuel DFS). |
| `r` | 3.2 | `multi-source-consistent` | 5 |  | - |
| `rbi` | 3.5 | `multi-source-consistent` | 5 |  | - |
| `sb` | 6.0 | `multi-source-consistent` | 5 |  | - |
| `win` | 6.0 | `multi-source-consistent` | 5 |  | - |

<details><summary>Sources consulted for this table</summary>

- [https://www.fanduel.com/rules](https://www.fanduel.com/rules)
- [https://fantasyteamadvice.com/mlb/fdoba](https://fantasyteamadvice.com/mlb/fdoba)
- [https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet)
- [https://fantasyteamadvice.com/mlb/fantasy-calculator](https://fantasyteamadvice.com/mlb/fantasy-calculator)
- [https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- [https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- [https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)

</details>

<details><summary>Per-stat source URLs</summary>

- `1b` (6): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyteamadvice.com/mlb/fdoba), [[3]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[4]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `2b` (6): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyteamadvice.com/mlb/fdoba), [[3]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[4]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `3b` (6): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyteamadvice.com/mlb/fdoba), [[3]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[4]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `bb` (6): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyteamadvice.com/mlb/fdoba), [[3]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[4]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `bba` (3): [[1]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[2]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `cg` (1): [[1]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `cgso` (1): [[1]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `cs` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `er` (5): [[1]](https://www.fanduel.com/rules), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/), [[5]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)
- `ha` (3): [[1]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[2]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbp` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbpa` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hr` (6): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyteamadvice.com/mlb/fdoba), [[3]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[4]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `ip` (5): [[1]](https://www.fanduel.com/rules), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `k` (5): [[1]](https://www.fanduel.com/rules), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `nohitter` (1): [[1]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `outs` (2): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[2]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `qs` (5): [[1]](https://www.fanduel.com/rules), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `r` (6): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyteamadvice.com/mlb/fdoba), [[3]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[4]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `rbi` (6): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyteamadvice.com/mlb/fdoba), [[3]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[4]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `sb` (6): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyteamadvice.com/mlb/fdoba), [[3]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[4]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `win` (6): [[1]](https://www.fanduel.com/rules), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[5]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[6]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)

</details>

_All 7 distinct URLs for this table are listed in the two blocks above._

## MLB / yahoo

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 200 |
| audit date | 2026-09-22 |
| operator-confirmed | False - 0/22 values |
| coefficients | 22 |
| disputed | 0 |
| not audited | 0 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** Yahoo values come from one comparison table (sportsfanfocus.com, 2019). The document is seven years old at audit time, so every value is 'single-source' and provisional.

> **Notes.** IRREGULARITY IR-11: Yahoo scoring is sourced from a single 2019 document. RotoGrinders does offer a ?site=yahoo grid variant (verified 2026-09-22), so Yahoo is a real target even though its values here are weakly sourced.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `1b` | 2.6 | `single-source` | 1 |  | - |
| `2b` | 5.2 | `single-source` | 1 |  | - |
| `3b` | 7.8 | `single-source` | 1 |  | - |
| `bb` | 2.6 | `single-source` | 1 |  | - |
| `bba` | -0.9 | `single-source` | 1 |  | - |
| `cg` | 0.0 | `single-source` | 1 |  | Not listed for Yahoo. |
| `cgso` | 0.0 | `single-source` | 1 |  | Not listed for Yahoo. |
| `cs` | 0.0 | `single-source` | 1 |  | Not listed for Yahoo. |
| `er` | -2.0 | `single-source` | 1 |  | - |
| `ha` | -0.9 | `single-source` | 1 |  | - |
| `hbp` | 2.6 | `single-source` | 1 |  | - |
| `hbpa` | -0.9 | `single-source` | 1 |  | - |
| `hr` | 10.4 | `single-source` | 1 |  | - |
| `ip` | 0.0 | `single-source` | 1 |  | Set to 0 because Yahoo pays per out; scoring both would double count. |
| `k` | 2.0 | `single-source` | 1 |  | - |
| `nohitter` | 0.0 | `single-source` | 1 |  | Not listed for Yahoo. |
| `outs` | 1.0 | `single-source` | 1 |  | Yahoo scores per out recorded, not per inning; do not also score 'ip'. |
| `qs` | 0.0 | `single-source` | 1 |  | Not listed for Yahoo. |
| `r` | 1.9 | `single-source` | 1 |  | - |
| `rbi` | 1.9 | `single-source` | 1 |  | - |
| `sb` | 4.2 | `single-source` | 1 |  | - |
| `win` | 4.0 | `single-source` | 1 |  | - |

<details><summary>Sources consulted for this table</summary>

- [https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)

</details>

<details><summary>Per-stat source URLs</summary>

- `1b` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `2b` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `3b` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `bb` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `bba` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `cg` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `cgso` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `cs` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `er` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `ha` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbp` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbpa` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hr` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `ip` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `k` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `nohitter` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `outs` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `qs` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `r` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `rbi` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `sb` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `win` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)

</details>

_All 1 distinct URLs for this table are listed in the two blocks above._

## NBA / draftkings

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 50000 |
| audit date | 2026-09-22 |
| operator-confirmed | **True** - 9/9 values |
| coefficients | 9 |
| disputed | 0 |
| not audited | 0 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** DraftKings NBA values were first agreed by three independent secondary sources (retrieved 2026-09-22) and are now OPERATOR-CONFIRMED: DraftKings' own 'NBA Daily Fantasy 101' article (dknetwork.draftkings.com, published 2025-10-17, retrieved 2026-09-22) lists every value in this table identically - Point +1, Made 3pt +0.5, Rebound +1.25, Assist +1.5, Steal +2, Block +2, Turnover -0.5, Double-Double +1.5 (max 1 per player), Triple-Double +3 (max 1 per player).

> **Notes.** DraftKings scores counting stats plus a 3PM bonus and double-double / triple-double bonuses. Field-goal and free-throw makes are NOT scored separately (they are already inside 'pts'). Every value matches the operator's own published article.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `ast` | 1.5 | `multi-source-consistent` | 4 |  | - |
| `blk` | 2.0 | `multi-source-consistent` | 4 |  | - |
| `dd` | 1.5 | `multi-source-consistent` | 4 |  | Max 1 per player - stated verbatim on the operator's scoring table. |
| `pts` | 1.0 | `multi-source-consistent` | 4 |  | - |
| `reb` | 1.25 | `multi-source-consistent` | 4 |  | - |
| `stl` | 2.0 | `multi-source-consistent` | 4 |  | - |
| `td` | 3.0 | `multi-source-consistent` | 4 |  | Max 1 per player; additive with 'dd' per RotoWire's worked example. |
| `three_pm` | 0.5 | `multi-source-consistent` | 4 |  | - |
| `to` | -0.5 | `multi-source-consistent` | 4 |  | - |

<details><summary>Sources consulted for this table</summary>

- [https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
- [https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246)
- [https://dfsbuild.com/dfs-guide/nba-dfs-guide/](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- [https://teamriseorfall.com/nba-dfs-strategy-guide/](https://teamriseorfall.com/nba-dfs-strategy-guide/)

</details>

<details><summary>Per-stat source URLs</summary>

- `ast` (4): [[1]](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `blk` (4): [[1]](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `dd` (4): [[1]](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `pts` (4): [[1]](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `reb` (4): [[1]](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `stl` (4): [[1]](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `td` (4): [[1]](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `three_pm` (4): [[1]](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `to` (4): [[1]](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://teamriseorfall.com/nba-dfs-strategy-guide/)

</details>

_All 4 distinct URLs for this table are listed in the two blocks above._

## NBA / fanduel

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 60000 |
| audit date | 2026-09-22 |
| operator-confirmed | **True** - 9/11 values |
| coefficients | 11 |
| disputed | 0 |
| not audited | 0 |
| deliberately zero | 2 (IR-15) |

> **Audit method.** OPERATOR-CONFIRMED in the second audit pass (2026-09-22): FanDuel's public rules page (https://www.fanduel.com/rules, Basketball section, retrieved that day) enumerates scoring as 3-pt FG=3, 2-pt FG=2, FT=1, Rebound=1.2, Assist=1.5, Block=3, Steal=3, Turnover=-1 - and no double-double or triple-double bonus. Earlier secondary sources disagreed on steal/block (2 vs 3) and on a 3PM bonus; the operator page settles both: Steal=Block=3, and the 3-pt FG=3 / 2-pt FG=2 pairing IS the aggregate representation (a made three's extra point sits inside the basket value), so under pts=1.0 the 3PM bonus is 0.

> **Notes.** TWO REPRESENTATION BUGS WERE FIXED HERE (IR-15). (1) The first pass of this audit encoded pts=1.0 AND two_pm=2.0 AND ftm=1.0 AND three_pm=3.0 at once. That is not either published representation - it is both of them summed, and it inflated every FanDuel NBA projection by roughly 2x (an 8-player demo lineup scored 763 points instead of ~300). RGENGY uses the aggregate representation ('pts') and pins the made-shot keys at 0.0. (2) three_pm was disputed at 0.0 vs a +1 bonus until FanDuel's own rules page settled it: a made three is worth 3 total and a made two 2 total, which is exactly pts=1.0 with no separate bonus (IR-08 has the full resolution). The operator page enumerates no double-double/triple-double bonus, so those stay 0.0 - now operator-backed rather than merely conservative.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `ast` | 1.5 | `multi-source-consistent` | 5 |  | - |
| `blk` | 3.0 | `multi-source-consistent` | 4 |  | RESOLVED BY THE OPERATOR PAGE: FanDuel states Block=3pts. |
| `dd` | 0.0 | `multi-source-consistent` | 3 |  | RESOLVED (IR-08): FanDuel's published basketball scoring table enumerates no double-double bonus. The zero is now operator-backed, not just conservative. |
| `ftm` | 0.0 | `not-applicable` | 2 |  | Operator page states FT=1 as the shot's total value, subsumed by pts=1.0. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `pts` | 1.0 | `multi-source-consistent` | 5 |  | 1 fantasy point per real point scored. Operator page: 2-pt FG=2 and FT=1, which is this representation stated in made-shot terms. |
| `reb` | 1.2 | `multi-source-consistent` | 5 |  | 1.2, versus 1.25 on DraftKings - operator page and every secondary source agree. |
| `stl` | 3.0 | `multi-source-consistent` | 4 |  | RESOLVED BY THE OPERATOR PAGE (was 'disputed'): FanDuel states Steal=3pts. The minority 2 reading came from RotoGrinders' own guide and is superseded. |
| `td` | 0.0 | `multi-source-consistent` | 3 |  | Same operator-page absence as 'dd' (IR-08). |
| `three_pm` | 0.0 | `multi-source-consistent` | 5 |  | RESOLVED BY THE OPERATOR PAGE (was 'disputed', IR-08/IR-15). FanDuel scores a 3-pt FG at 3 points TOTAL and a 2-pt FG at 2 TOTAL; under pts=1.0 a made three already scores 3, so the incremental bonus is 0. The old +1-bonus reading describes the same arithmetic in made-shot terms, not an additional payment. |
| `to` | -1.0 | `multi-source-consistent` | 5 |  | Harsher than DraftKings' -0.5; operator page and every source agree. |
| `two_pm` | 0.0 | `not-applicable` | 2 |  | Operator page states 2-pt FG=2 as the basket's total value, which is subsumed by pts=1.0. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |

<details><summary>Sources consulted for this table</summary>

- [https://www.fanduel.com/rules](https://www.fanduel.com/rules)
- [https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/](https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
- [https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246)
- [https://dfsbuild.com/dfs-guide/nba-dfs-guide/](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- [https://teamriseorfall.com/nba-dfs-strategy-guide/](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- [https://rotogrinders.com/articles/fanduel-nba-strategy-239702](https://rotogrinders.com/articles/fanduel-nba-strategy-239702)
- [https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/)
- [https://fanscout.pro/nba-fanduel-optimizer](https://fanscout.pro/nba-fanduel-optimizer)
- [https://www.sportingnews.com/us/nba/news/nba-fanduel-picks-128-best-nba-dfs-lineup-advice-saturdays-daily-fantasy-basketball-tournaments/jqsghzxwekyboxtsm6mlw0jw](https://www.sportingnews.com/us/nba/news/nba-fanduel-picks-128-best-nba-dfs-lineup-advice-saturdays-daily-fantasy-basketball-tournaments/jqsghzxwekyboxtsm6mlw0jw)
- [https://www.lineups.com/betting/fanduel-nba-strategy/](https://www.lineups.com/betting/fanduel-nba-strategy/)

</details>

<details><summary>Per-stat source URLs</summary>

- `ast` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[3]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[4]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- `blk` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://www.sportingnews.com/us/nba/news/nba-fanduel-picks-128-best-nba-dfs-lineup-advice-saturdays-daily-fantasy-basketball-tournaments/jqsghzxwekyboxtsm6mlw0jw)
- `dd` (3): [[1]](https://www.fanduel.com/rules), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702)
- `ftm` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://www.lineups.com/betting/fanduel-nba-strategy/)
- `pts` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[3]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[4]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- `reb` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[3]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[4]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- `stl` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://www.sportingnews.com/us/nba/news/nba-fanduel-picks-128-best-nba-dfs-lineup-advice-saturdays-daily-fantasy-basketball-tournaments/jqsghzxwekyboxtsm6mlw0jw)
- `td` (3): [[1]](https://www.fanduel.com/rules), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702)
- `three_pm` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[4]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/)
- `to` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[3]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[4]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- `two_pm` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://www.lineups.com/betting/fanduel-nba-strategy/)

</details>

_All 6 distinct URLs for this table are listed in the two blocks above._

## NFL / draftkings

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 50000 |
| audit date | 2026-09-22 |
| operator-confirmed | False - 13/25 values |
| coefficients | 25 |
| disputed | 0 |
| not audited | 7 |
| deliberately zero | 6 (IR-15) |

> **Audit method.** Re-audited in pass 2 against four 2026 sources, then OPERATOR-CONFIRMED in the second audit pass for the offensive scoring: DraftKings' own NFL DFS 101 article (dknetwork.draftkings.com, 2025-08-27, retrieved 2026-09-22) lists Passing TD +4, 25 passing yards +1, 300+ yard passing game +3, Interception -1, Rushing TD +6, 10 rushing yards +1, 100+ yard rushing game +3, Receiving TD +6, 10 receiving yards +1, 100+ yard receiving game +3, Reception +1, Punt/Kickoff/FG Return TD +6, Fumble Lost -1, 2-pt Conversion +2, Offensive Fumble Recovery TD +6. Roster is QB, 2 RB, 3 WR, TE, FLEX(RB/WR/TE), DST = 9 slots with NO kicker, corroborated by a real published DraftKings lineup that totals exactly $50,000 (sportsbettingdime, 2026-09-19). Because no kicker can be rostered, all kicker coefficients are pinned at 0.

> **Notes.** TWO PASS-1 ERRORS FIXED (IR-18). (1) The 100-yard rushing / 100-yard receiving / 300-yard passing bonuses were assigned to FanDuel and set to 0 for DraftKings; the operator pages now confirm both operators score them at 3.0. (2) DraftKings was given field-goal and extra-point coefficients even though its classic roster has no kicker slot; those are now 0. RotoGrinders' NFL grid publishes 100RU / 100RE / 300PA columns, which corroborates that these bonuses are a projection target on at least one major site. The DST block remains 'not-audited': no DraftKings operator document for team defence was retrieved (limitation L-04).

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `100rec` | 3.0 | `multi-source-consistent` | 3 |  | Operator article: '100+ Yard Receiving Game +3 Pts'; corroborated by the 100RE grid column. |
| `100ru` | 3.0 | `multi-source-consistent` | 3 |  | Operator article: '100+ Yard Rushing Game +3 Pts'. Also corroborated by the 100RU column on RotoGrinders' NFL grid. |
| `300pa` | 3.0 | `multi-source-consistent` | 3 |  | Operator article: '300+ Yard Passing Game +3 Pts'; corroborated by the 300PA grid column. |
| `dst_block` | 2.0 | `not-audited` | 1 |  | See 'dst_sack'. |
| `dst_fum_rec` | 2.0 | `not-audited` | 1 |  | See 'dst_sack'. |
| `dst_int` | 2.0 | `not-audited` | 1 |  | See 'dst_sack'. |
| `dst_pts_allowed` | 0.0 | `not-audited` | 0 |  | GAP: both sites also score team defence on points allowed (tiered). FanDuel's tier table is now operator-documented (see the FanDuel table); no DraftKings operator tier table was retrieved, and the engine does not yet model tiers. See limitation L-04. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `dst_sack` | 1.0 | `not-audited` | 1 |  | DraftKings team-defence scoring was NOT retrieved from any OPERATOR source. A secondary comparison table (dailyfantasysports101) shows DK DST tiers identical to FanDuel's, so the convention values are kept as 'not-audited' secondary estimates; the pipeline excludes them from published totals under --strict. See limitation L-04. |
| `dst_safety` | 2.0 | `not-audited` | 1 |  | See 'dst_sack'. |
| `dst_td` | 2.0 | `not-audited` | 1 |  | See 'dst_sack'. |
| `fg_0_39` | 0.0 | `not-applicable` | 1 |  | DraftKings' NFL classic roster has no kicker slot (9 slots: QB, 2 RB, 3 WR, TE, FLEX, DST), so field goals cannot be rostered or scored. fantasyfootballers lists 0-39 FG as DraftKings 0 / FanDuel 3. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `fg_40_49` | 0.0 | `not-applicable` | 1 |  | No DraftKings kicker slot. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `fg_50p` | 0.0 | `not-applicable` | 1 |  | No DraftKings kicker slot. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `fum_lost` | -1.0 | `multi-source-consistent` | 3 |  | Operator article: 'Fumble Lost -1 Pt' (FanDuel is -2). |
| `pa_cmp` | 0.0 | `not-applicable` | 0 |  | Neither site pays per completion. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `pa_int` | -1.0 | `multi-source-consistent` | 2 |  | Operator article: 'Interception (thrown) -1 Pt'. |
| `pa_td` | 4.0 | `multi-source-consistent` | 3 |  | OPERATOR-CONFIRMED for DraftKings by its own NFL DFS 101 article (dknetwork.draftkings.com, 2025-08-27, retrieved 2026-09-22): 25 Passing Yards +1 Pt, 10 Rushing Yards +1 Pt, 10 Receiving Yards +1 Pt, Passing TD +4, Rushing/Receiving TD +6. Corroborated for both sites by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `pa_yds` | 0.04 | `multi-source-consistent` | 3 |  | OPERATOR-CONFIRMED for DraftKings by its own NFL DFS 101 article (dknetwork.draftkings.com, 2025-08-27, retrieved 2026-09-22): 25 Passing Yards +1 Pt, 10 Rushing Yards +1 Pt, 10 Receiving Yards +1 Pt, Passing TD +4, Rushing/Receiving TD +6. Corroborated for both sites by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `pat` | 0.0 | `not-applicable` | 1 |  | CORRECTED IN PASS 2 (was 1.0). fantasyfootballers lists 'Extra Point Kick: DraftKings 0, FanDuel 1' - consistent with DraftKings having no kicker slot. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `rec` | 1.0 | `multi-source-consistent` | 4 |  | Operator article: 'Reception +1 Pt' (full PPR). fantasyteamadvisors (2026-08-05) corroborates: 'DraftKings uses full-point PPR scoring'. |
| `rec_td` | 6.0 | `multi-source-consistent` | 3 |  | OPERATOR-CONFIRMED for DraftKings by its own NFL DFS 101 article (dknetwork.draftkings.com, 2025-08-27, retrieved 2026-09-22): 25 Passing Yards +1 Pt, 10 Rushing Yards +1 Pt, 10 Receiving Yards +1 Pt, Passing TD +4, Rushing/Receiving TD +6. Corroborated for both sites by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `rec_yds` | 0.1 | `multi-source-consistent` | 3 |  | OPERATOR-CONFIRMED for DraftKings by its own NFL DFS 101 article (dknetwork.draftkings.com, 2025-08-27, retrieved 2026-09-22): 25 Passing Yards +1 Pt, 10 Rushing Yards +1 Pt, 10 Receiving Yards +1 Pt, Passing TD +4, Rushing/Receiving TD +6. Corroborated for both sites by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `ru_td` | 6.0 | `multi-source-consistent` | 3 |  | OPERATOR-CONFIRMED for DraftKings by its own NFL DFS 101 article (dknetwork.draftkings.com, 2025-08-27, retrieved 2026-09-22): 25 Passing Yards +1 Pt, 10 Rushing Yards +1 Pt, 10 Receiving Yards +1 Pt, Passing TD +4, Rushing/Receiving TD +6. Corroborated for both sites by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `ru_yds` | 0.1 | `multi-source-consistent` | 3 |  | OPERATOR-CONFIRMED for DraftKings by its own NFL DFS 101 article (dknetwork.draftkings.com, 2025-08-27, retrieved 2026-09-22): 25 Passing Yards +1 Pt, 10 Rushing Yards +1 Pt, 10 Receiving Yards +1 Pt, Passing TD +4, Rushing/Receiving TD +6. Corroborated for both sites by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `two_pt` | 2.0 | `multi-source-consistent` | 2 |  | Operator article: '2 Pt Conversion (Pass, Run, or Catch) +2 Pts'. |

<details><summary>Sources consulted for this table</summary>

- [https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/)
- [https://www.fanduel.com/rules](https://www.fanduel.com/rules)
- [https://rotogrinders.com/projected-stats/nfl](https://rotogrinders.com/projected-stats/nfl)
- [https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026](https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026)
- [https://fantasyteamadvisors.com/nfl-dfs-strategy/](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- [https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- [https://fantasyfootballers.org/featured/draftkings-vs-fanduel/](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- [https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)

</details>

<details><summary>Per-stat source URLs</summary>

- `100rec` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[3]](https://rotogrinders.com/projected-stats/nfl)
- `100ru` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[3]](https://rotogrinders.com/projected-stats/nfl)
- `300pa` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[3]](https://rotogrinders.com/projected-stats/nfl)
- `dst_block` (1): [[1]](https://www.dailyfantasysports101.com/football/)
- `dst_fum_rec` (1): [[1]](https://www.dailyfantasysports101.com/football/)
- `dst_int` (1): [[1]](https://www.dailyfantasysports101.com/football/)
- `dst_pts_allowed` (0): 
- `dst_sack` (1): [[1]](https://www.dailyfantasysports101.com/football/)
- `dst_safety` (1): [[1]](https://www.dailyfantasysports101.com/football/)
- `dst_td` (1): [[1]](https://www.dailyfantasysports101.com/football/)
- `fg_0_39` (1): [[1]](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)
- `fg_40_49` (1): [[1]](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)
- `fg_50p` (1): [[1]](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)
- `fum_lost` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- `pa_cmp` (0): 
- `pa_int` (2): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- `pa_td` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[3]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `pa_yds` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[3]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `pat` (1): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `rec` (4): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[4]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `rec_td` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[3]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `rec_yds` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[3]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `ru_td` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[3]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `ru_yds` (3): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[3]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `two_pt` (2): [[1]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)

</details>

_All 7 distinct URLs for this table are listed in the two blocks above._

## NFL / fanduel

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 60000 |
| audit date | 2026-09-22 |
| operator-confirmed | **True** - 22/25 values |
| coefficients | 25 |
| disputed | 0 |
| not audited | 1 |
| deliberately zero | 2 (IR-15) |

> **Audit method.** OPERATOR-CONFIRMED (2026-09-22): FanDuel's public rules page (https://www.fanduel.com/rules, Football section, retrieved that day) was retrieved and every offensive and defensive value in this table is taken from it: Reception 0.5, Receiving/Rushing Yards 0.1 per yard, Passing Yards 0.04 per yard, all TDs 6 (pass/rush/receive/return), Passing TD 4, Interception -1, Fumble -2, 2-pt Conversion 2, bonuses 100+ receiving / 100+ rushing / 300+ passing = 3, field goals 3/4/5 by tier, extra point 1; defence: sack 1, fumble recovered 2, interception 2, safety 2, blocked punt 2, kick/punt return TD 6, extra-point return 2, and the exact points-allowed tiers 10/7/4/1/0/-1/-4 with FanDuel's own formula for points allowed. Roster is QB, 2 RB, 3 WR, TE, FLEX(RB/WR/TE/K), DST = 9 slots; the kicker is reachable through the flex, which is why FanDuel carries kicker coefficients and DraftKings does not. Flex eligibility itself is disputed between two 2026 sources (IR-16).

> **Notes.** IR-18 REVERSED A SECOND TIME: pass 2 set these bonuses to 0.0 on the strength of two 2026 secondary sources; FanDuel's own rules page (retrieved 2026-09-22) awards +3 for each of them, so both operators score the yardage milestones. The per-event DST coefficients are also operator-confirmed now; the tiered points-allowed scoring stays at 0.0 only because the engine does not yet model tiers - the operator's tier table is preserved verbatim under `operator_tier_tables.dst_points_allowed` (L-04).

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `100rec` | 3.0 | `multi-source-consistent` | 3 |  | REVERSED AGAIN BY THE OPERATOR PAGE (IR-18): FanDuel states '100+ Receiving Yard Bonus = 3 Points'. |
| `100ru` | 3.0 | `multi-source-consistent` | 3 |  | REVERSED AGAIN BY THE OPERATOR PAGE (IR-18): FanDuel states '100+ Rushing Yard Bonus = 3 Points'. The pass-2 zero came from secondary sources that contradict the operator. |
| `300pa` | 3.0 | `multi-source-consistent` | 3 |  | REVERSED AGAIN BY THE OPERATOR PAGE (IR-18): FanDuel states '300+ Passing Yard Bonus = 3 Points'. |
| `dst_block` | 2.0 | `multi-source-consistent` | 2 |  | Operator page: 'Blocked Punt = 2 Points'. |
| `dst_fum_rec` | 2.0 | `multi-source-consistent` | 2 |  | Operator page: 'Fumble Recovered = 2 Points'. |
| `dst_int` | 2.0 | `multi-source-consistent` | 2 |  | Operator page: 'Interception = 2 Points'. |
| `dst_pts_allowed` | 0.0 | `not-applicable` | 1 |  | TIERS NOW OPERATOR-DOCUMENTED (was 'no tier table retrieved'): FanDuel awards 10/7/4/1/0/-1/-4 for 0 / 1-6 / 7-13 / 14-20 / 21-27 / 28-34 / 35+ points allowed, computed by its published formula. The full table is stored under `operator_tier_tables.dst_points_allowed`. The coefficient stays 0.0 only because the engine models points allowed as a single expected value rather than a tier lookup (L-04, roadmap). Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `dst_sack` | 1.0 | `multi-source-consistent` | 2 |  | Operator page (Defense column): 'Sacks = 1pt'. |
| `dst_safety` | 2.0 | `multi-source-consistent` | 2 |  | Operator page: 'Safety = 2 Points'. |
| `dst_td` | 0.0 | `not-audited` | 1 |  | NO RETRIEVED VALUE - changed from an unaudited 2.0 to a documented 0.0 in the second audit pass. FanDuel's rules page lists kick/punt return TDs at 6 (defence) but no generic defensive-touchdown value, and the secondary comparison tables list none either. The interception and fumble-recovery events above ARE scored, so only the TD component is missing; DST totals understate until a source is retrieved. See L-04. |
| `fg_0_39` | 3.0 | `multi-source-consistent` | 2 |  | Operator page: '0-39 Yard Field Goal = 3 Points'. |
| `fg_40_49` | 4.0 | `multi-source-consistent` | 2 |  | Operator page: '40-49 Yard Field Goal = 4 Points'. |
| `fg_50p` | 5.0 | `multi-source-consistent` | 2 |  | Operator page: '50+ Yard Field Goal = 5 Points'. |
| `fum_lost` | -2.0 | `multi-source-consistent` | 3 |  | Operator page: 'Fumble = -2 Points' (DraftKings is -1). |
| `pa_cmp` | 0.0 | `not-applicable` | 0 |  | Neither site pays per completion. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `pa_int` | -1.0 | `multi-source-consistent` | 2 |  | Operator page: 'Interception Thrown = -1 Points'. |
| `pa_td` | 4.0 | `multi-source-consistent` | 4 |  | Operator page: 'Passing Touchdown = 4 Points'. |
| `pa_yds` | 0.04 | `multi-source-consistent` | 4 |  | Operator page: 'Passing Yards = 0.04 Points'. |
| `pat` | 1.0 | `multi-source-consistent` | 2 |  | Operator page: 'Extra-Point Conversions = 1 Point'. |
| `rec` | 0.5 | `multi-source-consistent` | 4 |  | Operator page: 'Points per Reception = 0.5 Points' (half PPR). |
| `rec_td` | 6.0 | `multi-source-consistent` | 4 |  | Operator page: 'Receiving Touchdown = 6 Points'. |
| `rec_yds` | 0.1 | `multi-source-consistent` | 4 |  | Operator page: 'Receiving Yards = 0.1 Point per Yard'. |
| `ru_td` | 6.0 | `multi-source-consistent` | 4 |  | Operator page: 'Rushing Touchdown = 6 Points'. |
| `ru_yds` | 0.1 | `multi-source-consistent` | 4 |  | Operator page: 'Rushing Yards = 0.1 Point per Yard'. |
| `two_pt` | 2.0 | `multi-source-consistent` | 2 |  | Operator page: 'Two-Point Conversion = 2 Points' (pass, run or catch). |

<details><summary>Sources consulted for this table</summary>

- [https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/)
- [https://www.fanduel.com/rules](https://www.fanduel.com/rules)
- [https://rotogrinders.com/projected-stats/nfl](https://rotogrinders.com/projected-stats/nfl)
- [https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026](https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026)
- [https://fantasyteamadvisors.com/nfl-dfs-strategy/](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- [https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- [https://fantasyfootballers.org/featured/draftkings-vs-fanduel/](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- [https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)

</details>

<details><summary>Per-stat source URLs</summary>

- `100rec` (3): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[3]](https://rotogrinders.com/projected-stats/nfl)
- `100ru` (3): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[3]](https://rotogrinders.com/projected-stats/nfl)
- `300pa` (3): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[3]](https://rotogrinders.com/projected-stats/nfl)
- `dst_block` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://www.dailyfantasysports101.com/football/)
- `dst_fum_rec` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://www.dailyfantasysports101.com/football/)
- `dst_int` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://www.dailyfantasysports101.com/football/)
- `dst_pts_allowed` (1): [[1]](https://www.fanduel.com/rules)
- `dst_sack` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://www.dailyfantasysports101.com/football/)
- `dst_safety` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://www.dailyfantasysports101.com/football/)
- `dst_td` (1): [[1]](https://www.dailyfantasysports101.com/football/)
- `fg_0_39` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `fg_40_49` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `fg_50p` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `fum_lost` (3): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- `pa_cmp` (0): 
- `pa_int` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- `pa_td` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[4]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `pa_yds` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[4]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `pat` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `rec` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[4]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `rec_td` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[4]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `rec_yds` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[4]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `ru_td` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[4]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `ru_yds` (4): [[1]](https://www.fanduel.com/rules), [[2]](https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/), [[3]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[4]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `two_pt` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)

</details>

_All 7 distinct URLs for this table are listed in the two blocks above._

## NHL / draftkings

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 50000 |
| audit date | 2026-09-22 |
| operator-confirmed | **True** - 17/17 values |
| coefficients | 17 |
| disputed | 0 |
| not audited | 0 |
| deliberately zero | 1 (IR-15) |

> **Audit method.** Two mutually exclusive DraftKings NHL scoring tables were retrieved in pass 1: the 2014/2016 table (Goal 3, Assist 2, SOG 0.5, BLK 0.5, Goalie Win 3, Save 0.2, GA -1, SO 2) and the 2024 FTN table (Goal 8.5, Assist 5, SOG 1.5, BLK 1.3, Goalie Win 6, Save 0.7, GA -3.5, SO 4, OTL 2, plus threshold bonuses). In pass 2 the 2024 scheme was independently confirmed by DraftKings' own network site, so the conflict is RESOLVED and the values are marked multi-source-consistent with the historical table recorded as superseded.

> **Notes.** IRREGULARITY IR-09 (RESOLVED; its register text was corrected in the third pass - the operator article states Goal = +8.5, and 8.5 is what has shipped all along). DraftKings Network (dknetwork.draftkings.com, DraftKings' own editorial property) published the identical table on 2025-09-30; the second audit pass (2026-09-22) re-retrieved it and operator-confirmed every value below against it. IMPORTANT SCORING INTERACTION: a goal also counts as a shot on goal, so a goal is worth 8.5 + 1.5 = 10.0 points. DraftKings Network states this explicitly with a worked example ('Center: +8.5 Pts (Goal) +1.5 (Shot on Goal) = 10 Pts'). The 'sog' projection fed to this table must therefore INCLUDE goals; there is no separate goal-shot coefficient. Pass 1 wrongly added a 'sog_goal' key for this, which would have double-counted every goal - it is removed (IR-14).

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `a` | 5.0 | `multi-source-consistent` | 2 |  | Operator article: 'Assist +5 Pts'. The 2014-era table said 2. |
| `blk` | 1.3 | `multi-source-consistent` | 2 |  | Operator article: 'Blocked Shot +1.3 Pts'. The 2014-era table said 0.5. |
| `g` | 8.5 | `multi-source-consistent` | 2 |  | Operator article: 'Goal +8.5 Pts'. The 2014-era table said 3. |
| `g3_blk` | 3.0 | `multi-source-consistent` | 2 |  | Operator article: '3+ Blocked Shots +3 Pts'. |
| `g3_pts` | 3.0 | `multi-source-consistent` | 2 |  | Operator article: '3+ Points +3 Pts'. |
| `g5_sog` | 3.0 | `multi-source-consistent` | 2 |  | Operator article: '5+ Shots +3 Pts'. |
| `ga` | -3.5 | `multi-source-consistent` | 2 |  | Operator article: goalie 'Goal Against -3.5 Pts'. The 2014-era table said -1. |
| `hat_trick` | 3.0 | `multi-source-consistent` | 2 |  | Operator article: 'Hat Trick Bonus +3 Pts'. The 2014-era table said 1.5 and is superseded. |
| `otl` | 2.0 | `single-source` | 1 |  | Operator article: goalie 'Overtime Loss +2 Pts'. |
| `ppp` | 0.0 | `not-applicable` | 1 |  | DraftKings has NO power-play point bonus (its enumerated table lists none); the +2 is for SHORT-HANDED points only ('shp'). FanDuel does pay +0.5 per power-play point, so the key exists in the shared stat vocabulary. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `shootout_goal` | 1.5 | `single-source` | 1 |  | Operator article: 'Shootout Goal +1.5 Pts'. Renamed from 'sog_goal' in pass 2: the old name suggested 'a shot on goal that is a goal', which would double count every goal (a goal already scores under both 'g' and 'sog'). IR-14. Not modelled by the hockey engine because shootout results are not in the box-score feeds. |
| `shp` | 2.0 | `multi-source-consistent` | 2 |  | Operator article: 'Short Handed Point Bonus (Goal/Assist) +2 Pts'. |
| `so` | 4.0 | `multi-source-consistent` | 2 |  | Operator article: goalie 'Shutout Bonus +4 Pts', with the note that shootout goals do not prevent a shutout. The 2014-era table said 2. |
| `sog` | 1.5 | `multi-source-consistent` | 2 |  | Operator article: 'Shot on Goal +1.5 Pts'. A GOAL ALSO COUNTS AS A SHOT ON GOAL, so a goal scores 8.5 + 1.5 = 10.0 - the operator's own worked example. |
| `sv` | 0.7 | `multi-source-consistent` | 2 |  | Operator article: goalie 'Save +0.7 Pts'. The 2014-era table said 0.2. |
| `sv35` | 3.0 | `single-source` | 1 |  | Operator article: goalie '35+ Saves +3 Pts'. |
| `win_goalie` | 6.0 | `multi-source-consistent` | 2 |  | Operator article: goalie 'Win +6 Pts'. The 2014-era table said 3. |

<details><summary>Sources consulted for this table</summary>

- [https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
- [https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- [https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- [https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/)
- [https://www.fanduel.com/rules](https://www.fanduel.com/rules)
- [https://occupyfantasy.com/nhl-dfs-strategy-guide/](https://occupyfantasy.com/nhl-dfs-strategy-guide/)

</details>

<details><summary>Per-stat source URLs</summary>

- `a` (4): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[3]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/), [[4]](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- `blk` (4): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[3]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/), [[4]](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- `g` (4): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[3]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/), [[4]](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- `g3_blk` (2): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `g3_pts` (2): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `g5_sog` (2): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `ga` (4): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[3]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/), [[4]](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- `hat_trick` (2): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `otl` (1): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
- `ppp` (1): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
- `shootout_goal` (1): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
- `shp` (3): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[3]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/)
- `so` (4): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[3]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/), [[4]](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- `sog` (4): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[3]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/), [[4]](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- `sv` (4): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[3]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/), [[4]](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- `sv35` (1): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
- `win_goalie` (4): [[1]](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[3]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/), [[4]](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)

</details>

_All 4 distinct URLs for this table are listed in the two blocks above._

## NHL / fanduel

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 40000 |
| audit date | 2026-09-22 |
| operator-confirmed | **True** - 10/11 values |
| coefficients | 11 |
| disputed | 0 |
| not audited | 1 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** OPERATOR-CONFIRMED (2026-09-22): FanDuel's public rules page (https://www.fanduel.com/rules, Hockey section, retrieved that day) states Goals=12, Assists=8, Shots on Goal=1.6, Short Handed Points=+2, Power Play Points=+0.5, Blocked Shots=1.6; goalies: Wins=12, Goals Against=-4, Saves=0.8, Shutouts=8. Every value matches FTN Fantasy's 2024 table exactly, so the single-source weakness is retired. The operator page also states that NO points are awarded for goals or saves during shootouts.

> **Notes.** IRREGULARITY IR-10 (RESOLVED): every non-zero value is now operator-confirmed from fanduel.com/rules. The same page contradicts an earlier Reddit claim that FanDuel scores plus/minus: no plus/minus stat appears anywhere in the operator's enumerated hockey scoring, so `plus_minus` stays 0.0 / not-audited with operator absence as the recorded evidence - scoring it would now be the change that requires proof.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `a` | 8.0 | `multi-source-consistent` | 2 |  | Operator page: 'Assists = 8pts'. |
| `blk` | 1.6 | `multi-source-consistent` | 2 |  | Operator page: 'Blocked Shots = 1.6pts'. |
| `g` | 12.0 | `multi-source-consistent` | 2 |  | Operator page: 'Goals = 12pts'. |
| `ga` | -4.0 | `multi-source-consistent` | 2 |  | Operator page: goalies 'Goals Against = -4pts'. |
| `plus_minus` | 0.0 | `not-audited` | 0 |  | ABSENT from FanDuel's own published hockey scoring table (checked 2026-09-22, IR-10). An earlier Reddit claim that FanDuel scores +/- is unconfirmed by the operator page. Left at 0 and flagged. |
| `ppp` | 0.5 | `multi-source-consistent` | 2 |  | Operator page: 'Power Play Points = +0.5pts' (DraftKings pays none). |
| `shp` | 2.0 | `multi-source-consistent` | 2 |  | Operator page: 'Short Handed Points = +2pts'. |
| `so` | 8.0 | `multi-source-consistent` | 2 |  | Operator page: goalies 'Shutouts = 8pts'. |
| `sog` | 1.6 | `multi-source-consistent` | 2 |  | Operator page: 'Shots on Goal = 1.6pts'. |
| `sv` | 0.8 | `multi-source-consistent` | 2 |  | Operator page: goalies 'Saves = 0.8pts'. |
| `win_goalie` | 12.0 | `multi-source-consistent` | 2 |  | Operator page: goalies 'Wins = 12pts'. |

<details><summary>Sources consulted for this table</summary>

- [https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
- [https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- [https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- [https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/)
- [https://www.fanduel.com/rules](https://www.fanduel.com/rules)
- [https://occupyfantasy.com/nhl-dfs-strategy-guide/](https://occupyfantasy.com/nhl-dfs-strategy-guide/)

</details>

<details><summary>Per-stat source URLs</summary>

- `a` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `blk` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `g` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `ga` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `plus_minus` (0): 
- `ppp` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `shp` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `so` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `sog` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `sv` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `win_goalie` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)

</details>

_All 2 distinct URLs for this table are listed in the two blocks above._

## WNBA / draftkings

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 50000 |
| audit date | 2026-09-22 |
| operator-confirmed | False - 0/9 values |
| coefficients | 9 |
| disputed | 0 |
| not audited | 0 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** PROVISIONAL - single operator-family source. DraftKings' own WNBA scoring page (pick6.draftkings.com/rules-and-scoring-wnba, retrieved 2026-09-22) publishes Point +1, Made 3pt +0.5, Rebound +1.25, Assist +1.5, Steal +2, Block +2, Turnover -0.5, Double-Double +1.5, Triple-Double +3 - identical to the operator-confirmed DraftKings NBA classic table. CAVEAT: that page is for DraftKings PICK6, a different product from DraftKings DFS classic, so these values are NOT marked confirmed_by_operator; they are recorded here because the first pass shipped all zeros, which made WNBA projections impossible, and an operator-published WNBA table beats an empty one provided it is labelled provisional.

> **Notes.** Every value is 'single-source' from a DraftKings property that publishes WNBA scoring for a DIFFERENT product (Pick6). Treat the totals as provisional until a DraftKings WNBA classic scoring page is retrieved. The WNBA *roster* templates remain unaudited (L-03) - scoring and roster provenance are tracked separately.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `ast` | 1.5 | `single-source` | 1 |  | Operator Pick6 page; provisional for DFS classic. |
| `blk` | 2.0 | `single-source` | 1 |  | Operator Pick6 page; provisional for DFS classic. |
| `dd` | 1.5 | `single-source` | 1 |  | Max 1 per player. Operator Pick6 page; provisional for DFS classic. |
| `pts` | 1.0 | `single-source` | 1 |  | Operator Pick6 page; provisional for DFS classic (see meta). |
| `reb` | 1.25 | `single-source` | 1 |  | Operator Pick6 page; provisional for DFS classic. |
| `stl` | 2.0 | `single-source` | 1 |  | Operator Pick6 page; provisional for DFS classic. |
| `td` | 3.0 | `single-source` | 1 |  | Max 1 per player. Operator Pick6 page; provisional for DFS classic. |
| `three_pm` | 0.5 | `single-source` | 1 |  | Operator Pick6 page; provisional for DFS classic. |
| `to` | -0.5 | `single-source` | 1 |  | Operator Pick6 page; provisional for DFS classic. |

<details><summary>Sources consulted for this table</summary>

- [https://pick6.draftkings.com/pick6-rules-and-scoring-wnba](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)
- [https://rotogrinders.com/projected-stats/wnba](https://rotogrinders.com/projected-stats/wnba)

</details>

<details><summary>Per-stat source URLs</summary>

- `ast` (1): [[1]](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)
- `blk` (1): [[1]](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)
- `dd` (1): [[1]](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)
- `pts` (1): [[1]](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)
- `reb` (1): [[1]](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)
- `stl` (1): [[1]](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)
- `td` (1): [[1]](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)
- `three_pm` (1): [[1]](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)
- `to` (1): [[1]](https://pick6.draftkings.com/pick6-rules-and-scoring-wnba)

</details>

_All 1 distinct URLs for this table are listed in the two blocks above._

## WNBA / fanduel

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 40000 |
| audit date | 2026-09-22 |
| operator-confirmed | **True** - 9/11 values |
| coefficients | 11 |
| disputed | 0 |
| not audited | 0 |
| deliberately zero | 2 (IR-15) |

> **Audit method.** OPERATOR-CONFIRMED (2026-09-22): FanDuel's public rules page (https://www.fanduel.com/rules, Basketball section - the same section links the WNBA training guide) publishes one basketball scoring table for NBA and WNBA: 3-pt FG=3, 2-pt FG=2, FT=1, Rebound=1.2, Assist=1.5, Block=3, Steal=3, Turnover=-1, with no double-double/triple-double bonus. The aggregate representation (1 point per point scored, no separate 3PM bonus) follows exactly as in the NBA table.

> **Notes.** This table was all zeros / not-audited in the first pass; it is now filled from FanDuel's own published basketball scoring, which the operator applies to WNBA (the WNBA training guide hangs off the same rules section). The WNBA *roster* templates remain unaudited (L-03) - scoring and roster provenance are tracked separately.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `ast` | 1.5 | `multi-source-consistent` | 2 |  | - |
| `blk` | 3.0 | `multi-source-consistent` | 1 |  | - |
| `dd` | 0.0 | `multi-source-consistent` | 1 |  | No DD bonus in the operator's enumerated basketball scoring (IR-08). |
| `ftm` | 0.0 | `not-applicable` | 1 |  | Made-shot value subsumed by pts=1.0. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `pts` | 1.0 | `multi-source-consistent` | 2 |  | Operator basketball table (2-pt FG=2 / FT=1), WNBA included. |
| `reb` | 1.2 | `multi-source-consistent` | 2 |  | - |
| `stl` | 3.0 | `multi-source-consistent` | 1 |  | - |
| `td` | 0.0 | `multi-source-consistent` | 1 |  | No TD bonus in the operator's enumerated basketball scoring (IR-08). |
| `three_pm` | 0.0 | `multi-source-consistent` | 2 |  | Operator 3-pt FG=3 TOTAL vs 2-pt FG=2 TOTAL => no incremental bonus under pts=1.0 (see nba:fanduel). |
| `to` | -1.0 | `multi-source-consistent` | 1 |  | - |
| `two_pm` | 0.0 | `not-applicable` | 1 |  | Made-shot value subsumed by pts=1.0. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |

<details><summary>Sources consulted for this table</summary>

- [https://www.fanduel.com/rules](https://www.fanduel.com/rules)
- [https://rotogrinders.com/projected-stats/wnba](https://rotogrinders.com/projected-stats/wnba)

</details>

<details><summary>Per-stat source URLs</summary>

- `ast` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://rotogrinders.com/projected-stats/wnba)
- `blk` (1): [[1]](https://www.fanduel.com/rules)
- `dd` (1): [[1]](https://www.fanduel.com/rules)
- `ftm` (1): [[1]](https://www.fanduel.com/rules)
- `pts` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://rotogrinders.com/projected-stats/wnba)
- `reb` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://rotogrinders.com/projected-stats/wnba)
- `stl` (1): [[1]](https://www.fanduel.com/rules)
- `td` (1): [[1]](https://www.fanduel.com/rules)
- `three_pm` (2): [[1]](https://www.fanduel.com/rules), [[2]](https://rotogrinders.com/projected-stats/wnba)
- `to` (1): [[1]](https://www.fanduel.com/rules)
- `two_pm` (1): [[1]](https://www.fanduel.com/rules)

</details>

_All 2 distinct URLs for this table are listed in the two blocks above._
