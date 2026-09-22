<!-- GENERATED FILE - DO NOT EDIT: rendered by scripts/build_docs.py from the committed registries. Edit the source and re-run the generator. -->

# 03 - Scoring verification

Fantasy points are the product of a scoring table and a projection, so a wrong coefficient corrupts every number downstream of it. Each shipped table below lists every coefficient with the number of independent sources that agree on it, its verification status, and the URLs those sources came from. Generated from `rgengy/data/scoring/*.json` - edit the tables (via `scripts/build_scoring_tables.py`), not this file.

## Evidence classes across all tables

| verification status | coefficients | meaning |
| --- | ---: | --- |
| `multi-source-consistent` | 77 | two or more independent sources agree |
| `single-source` | 49 | exactly one source - the weakest evidence class |
| `not-audited` | 35 | no source was retrieved; the value is a documented convention, not a finding |
| `not-applicable` | 12 |  |
| `disputed` | 7 | sources contradict each other; the majority value was adopted and flagged |
| `cross-validated-via-rg` | 3 |  |

## MLB / draftkings

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 50000 |
| audit date | 2026-09-22 |
| operator-confirmed | **False** (L-02) |
| coefficients | 21 |
| disputed | 2 |
| not audited | 0 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** Three independent secondary sources agree on every value listed. DraftKings' own scoring page is inside the logged-in app and could not be retrieved, so no value is marked operator-confirmed.

> **Notes.** 'cs' (caught stealing, -2) is reported by only one source and is therefore marked disputed.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `1b` | 3.0 | `multi-source-consistent` | 5 |  | - |
| `2b` | 5.0 | `multi-source-consistent` | 5 |  | - |
| `3b` | 8.0 | `multi-source-consistent` | 5 |  | - |
| `bb` | 2.0 | `multi-source-consistent` | 5 |  | - |
| `bba` | -0.6 | `multi-source-consistent` | 4 |  | - |
| `cg` | 2.5 | `multi-source-consistent` | 4 |  | - |
| `cgso` | 2.5 | `multi-source-consistent` | 4 |  | Additive with 'cg'; a complete-game shutout earns both bonuses. |
| `cs` | -2.0 | `single-source` | 1 | yes | Only RotoWire lists Caught Stealing = -2 for DraftKings. The 2026 fantasyteamadvice calculator and the DK/FD comparison tables omit it. FLAGGED in docs/09-irregularities.md (IR-04). |
| `er` | -2.0 | `multi-source-consistent` | 5 |  | - |
| `ha` | -0.6 | `multi-source-consistent` | 4 |  | - |
| `hbp` | 2.0 | `multi-source-consistent` | 4 |  | - |
| `hbpa` | -0.6 | `multi-source-consistent` | 4 |  | - |
| `hr` | 10.0 | `multi-source-consistent` | 5 |  | - |
| `ip` | 2.25 | `multi-source-consistent` | 5 |  | - |
| `k` | 2.0 | `multi-source-consistent` | 5 |  | - |
| `nohitter` | 5.0 | `multi-source-consistent` | 3 |  | - |
| `qs` | 0.0 | `disputed` | 2 | yes | sportsfanfocus and dailyfantasysports101 both show DraftKings Quality Start = 0 (i.e. no bonus); runpuresports lists '+4' under its DraftKings heading. Set to 0 and FLAGGED as IR-05 in docs/09-irregularities.md. |
| `r` | 2.0 | `multi-source-consistent` | 5 |  | - |
| `rbi` | 2.0 | `multi-source-consistent` | 5 |  | - |
| `sb` | 5.0 | `multi-source-consistent` | 5 |  | - |
| `win` | 4.0 | `multi-source-consistent` | 5 |  | - |

<details><summary>Sources consulted for this table</summary>

- [https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444)
- [https://fantasyteamadvice.com/mlb/fantasy-calculator](https://fantasyteamadvice.com/mlb/fantasy-calculator)
- [https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)
- [https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- [https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)

</details>

<details><summary>Per-stat source URLs</summary>

- `1b` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `2b` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `3b` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `bb` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `bba` (4): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `cg` (4): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[4]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `cgso` (4): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[4]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `cs` (1): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444)
- `er` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `ha` (4): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbp` (4): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbpa` (4): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hr` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `ip` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `k` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `nohitter` (3): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `qs` (3): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[2]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)
- `r` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `rbi` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `sb` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `win` (5): [[1]](https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)

</details>

_All 5 distinct URLs for this table are listed in the two blocks above._

## MLB / fanduel

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 35000 |
| audit date | 2026-09-22 |
| operator-confirmed | **False** (L-02) |
| coefficients | 22 |
| disputed | 1 |
| not audited | 0 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** Hitter values agree across four independent sources. Pitcher 'er' is disputed (-3 vs -1) and is flagged.

> **Notes.** FanDuel does not penalise pitchers for hits/walks/HBP allowed, so ha/bba/hbpa are 0. FanDuel scores per out (1 pt) rather than per inning; 3 outs = 1 inning = 3 pts, which reconciles the '+3 IP' and '+1 out' descriptions found in different sources. To avoid a double count, 'ip' carries the 3.0 and 'outs' is pinned at 0.0.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `1b` | 3.0 | `multi-source-consistent` | 5 |  | - |
| `2b` | 6.0 | `multi-source-consistent` | 5 |  | - |
| `3b` | 9.0 | `multi-source-consistent` | 5 |  | - |
| `bb` | 3.0 | `multi-source-consistent` | 5 |  | FanDuel pays a walk the same as a single - the single biggest hitter-scoring difference from DraftKings. |
| `bba` | 0.0 | `multi-source-consistent` | 3 |  | FanDuel does not penalise walks allowed. |
| `cg` | 0.0 | `single-source` | 1 |  | No FanDuel source lists a complete-game bonus. |
| `cgso` | 0.0 | `single-source` | 1 |  | - |
| `cs` | 0.0 | `single-source` | 1 |  | No FanDuel source lists a caught-stealing penalty. |
| `er` | -3.0 | `disputed` | 3 | yes | Three sources say -3, one (runpuresports) says -1. Majority value -3 adopted and FLAGGED as IR-06 in docs/09-irregularities.md. |
| `ha` | 0.0 | `multi-source-consistent` | 3 |  | FanDuel does not penalise hits allowed. |
| `hbp` | 3.0 | `multi-source-consistent` | 3 |  | - |
| `hbpa` | 0.0 | `single-source` | 1 |  | Inferred 0 from the absence of an HBP-allowed penalty in every FanDuel table consulted. |
| `hr` | 12.0 | `multi-source-consistent` | 5 |  | - |
| `ip` | 3.0 | `multi-source-consistent` | 4 |  | Equivalent to 1.0 per out recorded; see meta.notes. |
| `k` | 3.0 | `multi-source-consistent` | 4 |  | - |
| `nohitter` | 0.0 | `single-source` | 1 |  | - |
| `outs` | 0.0 | `multi-source-consistent` | 2 |  | FanDuel's own tables describe this as 'Out Recorded = 1 point', which is arithmetically identical to 'Inning Pitched = 3 points' (3 outs = 1 inning). Scoring BOTH would double count a pitcher's innings, so RGENGY scores 'ip' at 3.0 and pins 'outs' at 0.0. RotoGrinders publishes an OUTS column on its MLB grid, which is why the field is modelled at all. See IR-14 in docs/09-irregularities.md. |
| `qs` | 4.0 | `multi-source-consistent` | 4 |  | Quality Start = started the game, pitched at least 6 innings and allowed 3 or fewer earned runs (definition per https://intercom.help/boomfantasy/en/articles/9950352-mlb). |
| `r` | 3.2 | `multi-source-consistent` | 5 |  | - |
| `rbi` | 3.5 | `multi-source-consistent` | 5 |  | - |
| `sb` | 6.0 | `multi-source-consistent` | 5 |  | - |
| `win` | 6.0 | `multi-source-consistent` | 5 |  | - |

<details><summary>Sources consulted for this table</summary>

- [https://fantasyteamadvice.com/mlb/fdoba](https://fantasyteamadvice.com/mlb/fdoba)
- [https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet)
- [https://fantasyteamadvice.com/mlb/fantasy-calculator](https://fantasyteamadvice.com/mlb/fantasy-calculator)
- [https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- [https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- [https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)

</details>

<details><summary>Per-stat source URLs</summary>

- `1b` (5): [[1]](https://fantasyteamadvice.com/mlb/fdoba), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `2b` (5): [[1]](https://fantasyteamadvice.com/mlb/fdoba), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `3b` (5): [[1]](https://fantasyteamadvice.com/mlb/fdoba), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `bb` (5): [[1]](https://fantasyteamadvice.com/mlb/fdoba), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `bba` (3): [[1]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[2]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `cg` (1): [[1]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `cgso` (1): [[1]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `cs` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `er` (4): [[1]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/), [[4]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/)
- `ha` (3): [[1]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[2]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbp` (3): [[1]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hbpa` (1): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/)
- `hr` (5): [[1]](https://fantasyteamadvice.com/mlb/fdoba), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `ip` (4): [[1]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[4]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `k` (4): [[1]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[4]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `nohitter` (1): [[1]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `outs` (2): [[1]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[2]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `qs` (4): [[1]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[2]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[3]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[4]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `r` (5): [[1]](https://fantasyteamadvice.com/mlb/fdoba), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `rbi` (5): [[1]](https://fantasyteamadvice.com/mlb/fdoba), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `sb` (5): [[1]](https://fantasyteamadvice.com/mlb/fdoba), [[2]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[3]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)
- `win` (5): [[1]](https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet), [[2]](https://fantasyteamadvice.com/mlb/fantasy-calculator), [[3]](https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/), [[4]](https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/), [[5]](https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/)

</details>

_All 6 distinct URLs for this table are listed in the two blocks above._

## MLB / yahoo

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 200 |
| audit date | 2026-09-22 |
| operator-confirmed | **False** (L-02) |
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
| operator-confirmed | **False** (L-02) |
| coefficients | 9 |
| disputed | 0 |
| not audited | 0 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** DraftKings NBA values are identical across three independent sources retrieved 2026-09-22.

> **Notes.** DraftKings scores counting stats plus a 3PM bonus and double-double / triple-double bonuses. Field-goal and free-throw makes are NOT scored separately (they are already inside 'pts').

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `ast` | 1.5 | `multi-source-consistent` | 3 |  | - |
| `blk` | 2.0 | `multi-source-consistent` | 3 |  | - |
| `dd` | 1.5 | `multi-source-consistent` | 3 |  | Max 1 per player. |
| `pts` | 1.0 | `multi-source-consistent` | 3 |  | - |
| `reb` | 1.25 | `multi-source-consistent` | 3 |  | - |
| `stl` | 2.0 | `multi-source-consistent` | 3 |  | - |
| `td` | 3.0 | `multi-source-consistent` | 3 |  | Max 1 per player; additive with 'dd' per RotoWire's worked example. |
| `three_pm` | 0.5 | `multi-source-consistent` | 3 |  | - |
| `to` | -0.5 | `multi-source-consistent` | 3 |  | - |

<details><summary>Sources consulted for this table</summary>

- [https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246)
- [https://dfsbuild.com/dfs-guide/nba-dfs-guide/](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- [https://teamriseorfall.com/nba-dfs-strategy-guide/](https://teamriseorfall.com/nba-dfs-strategy-guide/)

</details>

<details><summary>Per-stat source URLs</summary>

- `ast` (3): [[1]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `blk` (3): [[1]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `dd` (3): [[1]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `pts` (3): [[1]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `reb` (3): [[1]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `stl` (3): [[1]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `td` (3): [[1]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `three_pm` (3): [[1]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://teamriseorfall.com/nba-dfs-strategy-guide/)
- `to` (3): [[1]](https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://teamriseorfall.com/nba-dfs-strategy-guide/)

</details>

_All 3 distinct URLs for this table are listed in the two blocks above._

## NBA / fanduel

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 60000 |
| audit date | 2026-09-22 |
| operator-confirmed | **False** (L-02) |
| coefficients | 11 |
| disputed | 5 |
| not audited | 0 |
| deliberately zero | 2 (IR-15) |

> **Audit method.** Five sources were retrieved and they disagree on two points, so both are marked 'disputed' and both readings are recorded. RotoGrinders' own FanDuel NBA guide (created 2014-02-11, last updated 2025-11-03) states: Point=1, Rebound=1.2, Assist=1.5, Steal=2, Block=2, TO=-1, and 'FanDuel does not give extra points for three-pointers'. occupyfantasy (2025-06-05) and dfsbuild (2025-10-07) both state Steal=3 and Block=3 and neither lists a 3PM bonus. sportingnews (2023-01-28) and lineups (2019-05-21) describe FanDuel in the MADE-SHOT representation (3PM +1, FGM +2, FTM +1), which is arithmetically identical to 1 point per point plus a +1 3PM bonus.

> **Notes.** TWO REPRESENTATION BUGS WERE FIXED HERE (IR-15). (1) The first pass of this audit encoded pts=1.0 AND two_pm=2.0 AND ftm=1.0 AND three_pm=3.0 at once. That is not either published representation - it is both of them summed, and it inflated every FanDuel NBA projection by roughly 2x (an 8-player demo lineup scored 763 points instead of ~300). RGENGY now uses the aggregate representation ('pts') and pins the made-shot keys at 0.0. (2) three_pm=3.0 came from a source that meant 'a made three is worth 3 points in total', not 'a made three earns a 3-point bonus'; the majority of recent sources say FanDuel pays no 3PM bonus at all, so it is 0.0 and disputed. NOTE ALSO: FanDuel's own rules page (https://sportsbook.fanduel.com/rules) is geo-verified and cannot be retrieved headlessly, which is why this table rests on secondary sources.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `ast` | 1.5 | `multi-source-consistent` | 5 |  | - |
| `blk` | 3.0 | `disputed` | 4 | yes | Same conflict and same resolution as 'stl'. IR-15. |
| `dd` | 0.0 | `disputed` | 2 | yes | Neither RotoGrinders' FanDuel scoring table nor dfsbuild's comparison lists a FanDuel double-double bonus. Flagged as IR-08. |
| `ftm` | 0.0 | `not-applicable` | 1 |  | Made-shot representation: sportingnews states 'free throw made (+1 point)', which is subsumed by pts=1.0. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `pts` | 1.0 | `multi-source-consistent` | 5 |  | 1 fantasy point per real point scored. Every retrieved source agrees. |
| `reb` | 1.2 | `multi-source-consistent` | 5 |  | 1.2, versus 1.25 on DraftKings - every source agrees. |
| `stl` | 3.0 | `disputed` | 4 | yes | CONFLICT: occupyfantasy (2025-06-05), dfsbuild (2025-10-07) and sportingnews (2023) say 3; RotoGrinders' own guide says 2. Majority of recent independent sources wins, but because the minority source is RotoGrinders itself this is flagged for manual review. IR-15. |
| `td` | 0.0 | `disputed` | 2 | yes | Same ambiguity as 'dd'. Flagged as IR-08. |
| `three_pm` | 0.0 | `disputed` | 5 | yes | CONFLICT. RotoGrinders (2025-11-03): 'FanDuel does not give extra points for three-pointers, so all buckets are treated the same.' dfsbuild (2025-10-07) shows '-' for FanDuel. sportingnews (2023-01-28) and lineups (2019-05-21) describe a +1 3PM bonus. Three of five sources and the two most recent say no bonus, so 0.0 is used. IR-15. |
| `to` | -1.0 | `multi-source-consistent` | 5 |  | Harsher than DraftKings' -0.5; every source agrees. |
| `two_pm` | 0.0 | `not-applicable` | 1 |  | Made-shot representation: lineups.com states '2 points per field goal made', which is subsumed by pts=1.0. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |

<details><summary>Sources consulted for this table</summary>

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

- `ast` (3): [[1]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[2]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- `blk` (4): [[1]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[4]](https://www.sportingnews.com/us/nba/news/nba-fanduel-picks-128-best-nba-dfs-lineup-advice-saturdays-daily-fantasy-basketball-tournaments/jqsghzxwekyboxtsm6mlw0jw)
- `dd` (2): [[1]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[2]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702)
- `ftm` (1): [[1]](https://www.lineups.com/betting/fanduel-nba-strategy/)
- `pts` (3): [[1]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[2]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- `reb` (3): [[1]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[2]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- `stl` (4): [[1]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[4]](https://www.sportingnews.com/us/nba/news/nba-fanduel-picks-128-best-nba-dfs-lineup-advice-saturdays-daily-fantasy-basketball-tournaments/jqsghzxwekyboxtsm6mlw0jw)
- `td` (2): [[1]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[2]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702)
- `three_pm` (5): [[1]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[2]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/), [[3]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[4]](https://www.sportingnews.com/us/nba/news/nba-fanduel-picks-128-best-nba-dfs-lineup-advice-saturdays-daily-fantasy-basketball-tournaments/jqsghzxwekyboxtsm6mlw0jw), [[5]](https://www.lineups.com/betting/fanduel-nba-strategy/)
- `to` (3): [[1]](https://rotogrinders.com/articles/fanduel-nba-strategy-239702), [[2]](https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/), [[3]](https://dfsbuild.com/dfs-guide/nba-dfs-guide/)
- `two_pm` (1): [[1]](https://www.lineups.com/betting/fanduel-nba-strategy/)

</details>

_All 5 distinct URLs for this table are listed in the two blocks above._

## NFL / draftkings

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 50000 |
| audit date | 2026-09-22 |
| operator-confirmed | **False** (L-02) |
| coefficients | 25 |
| disputed | 0 |
| not audited | 7 |
| deliberately zero | 6 (IR-15) |

> **Audit method.** Re-audited in pass 2 against four 2026 sources. Roster is QB, 2 RB, 3 WR, TE, FLEX(RB/WR/TE), DST = 9 slots with NO kicker, corroborated by a real published DraftKings lineup that totals exactly $50,000 (sportsbettingdime, 2026-09-19). Because no kicker can be rostered, all kicker coefficients are pinned at 0.

> **Notes.** TWO PASS-1 ERRORS FIXED (IR-18). (1) The 100-yard rushing / 100-yard receiving / 300-yard passing bonuses were assigned to FanDuel and set to 0 for DraftKings. fantasyfootballers (2026-08-15) shows the opposite - DraftKings 3 / 3 / 3, FanDuel 0 / 0 / 0 - and fantasyteamadvisors (2026-08-05) independently says 'DraftKings ... awards milestone bonuses for 100-yard and 300-yard performances'. (2) DraftKings was given field-goal and extra-point coefficients even though its classic roster has no kicker slot; those are now 0. RotoGrinders' NFL grid publishes 100RU / 100RE / 300PA columns, which corroborates that these bonuses are a projection target on at least one major site.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `100rec` | 3.0 | `cross-validated-via-rg` | 2 |  | CORRECTED IN PASS 2 (was 0.0). '100+ Receiving Yards: DraftKings 3, FanDuel 0'; corroborated by the 100RE grid column. |
| `100ru` | 3.0 | `cross-validated-via-rg` | 3 |  | CORRECTED IN PASS 2 (was 0.0). fantasyfootballers: '100+ Rushing Yards: DraftKings 3, FanDuel 0'. Also corroborated by the 100RU column on RotoGrinders' NFL grid. |
| `300pa` | 3.0 | `cross-validated-via-rg` | 2 |  | CORRECTED IN PASS 2 (was 0.0). '300+ Passing Yards: DraftKings 3, FanDuel 0'; corroborated by the 300PA grid column. |
| `dst_block` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `dst_fum_rec` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `dst_int` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `dst_pts_allowed` | 0.0 | `not-audited` | 0 |  | GAP: both sites also score team defence on points allowed (tiered). No tier table was retrieved, so the key is modelled at 0 and flagged. See limitation L-04. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `dst_sack` | 1.0 | `not-audited` | 0 |  | DraftKings team-defence scoring was NOT retrieved from any source during this audit. The values below follow the long-standing convention and are flagged 'not-audited'; the pipeline excludes them from published totals under --strict. See limitation L-04. |
| `dst_safety` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `dst_td` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `fg_0_39` | 0.0 | `not-applicable` | 1 |  | DraftKings' NFL classic roster has no kicker slot (9 slots: QB, 2 RB, 3 WR, TE, FLEX, DST), so field goals cannot be rostered or scored. fantasyfootballers lists 0-39 FG as DraftKings 0 / FanDuel 3. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `fg_40_49` | 0.0 | `not-applicable` | 1 |  | No DraftKings kicker slot. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `fg_50p` | 0.0 | `not-applicable` | 1 |  | No DraftKings kicker slot. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `fum_lost` | -1.0 | `multi-source-consistent` | 2 |  | fantasyfootballers (2026-08-15) lists Fumble Lost: DraftKings -1, FanDuel -2. |
| `pa_cmp` | 0.0 | `not-applicable` | 0 |  | Neither site pays per completion. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `pa_int` | -1.0 | `single-source` | 1 |  | Standard interception penalty; not restated by the other 2026 sources. |
| `pa_td` | 4.0 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `pa_yds` | 0.04 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `pat` | 0.0 | `not-applicable` | 1 |  | CORRECTED IN PASS 2 (was 1.0). fantasyfootballers lists 'Extra Point Kick: DraftKings 0, FanDuel 1' - consistent with DraftKings having no kicker slot. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `rec` | 1.0 | `multi-source-consistent` | 3 |  | DraftKings is FULL PPR: 'DraftKings uses full-point PPR scoring (1 point per reception)' - fantasyteamadvisors, 2026-08-05. |
| `rec_td` | 6.0 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `rec_yds` | 0.1 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `ru_td` | 6.0 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `ru_yds` | 0.1 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `two_pt` | 2.0 | `single-source` | 1 |  | 2-point conversion. Not restated by the other sources retrieved. |

<details><summary>Sources consulted for this table</summary>

- [https://rotogrinders.com/projected-stats/nfl](https://rotogrinders.com/projected-stats/nfl)
- [https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026](https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026)
- [https://fantasyteamadvisors.com/nfl-dfs-strategy/](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- [https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- [https://fantasyfootballers.org/featured/draftkings-vs-fanduel/](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- [https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)

</details>

<details><summary>Per-stat source URLs</summary>

- `100rec` (2): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[2]](https://rotogrinders.com/projected-stats/nfl)
- `100ru` (3): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/), [[3]](https://rotogrinders.com/projected-stats/nfl)
- `300pa` (2): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[2]](https://rotogrinders.com/projected-stats/nfl)
- `dst_block` (0): 
- `dst_fum_rec` (0): 
- `dst_int` (0): 
- `dst_pts_allowed` (0): 
- `dst_sack` (0): 
- `dst_safety` (0): 
- `dst_td` (0): 
- `fg_0_39` (1): [[1]](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)
- `fg_40_49` (1): [[1]](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)
- `fg_50p` (1): [[1]](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)
- `fum_lost` (2): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- `pa_cmp` (0): 
- `pa_int` (1): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- `pa_td` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `pa_yds` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `pat` (1): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `rec` (3): [[1]](https://fantasyteamadvisors.com/nfl-dfs-strategy/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[3]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `rec_td` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `rec_yds` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `ru_td` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `ru_yds` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `two_pt` (1): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)

</details>

_All 5 distinct URLs for this table are listed in the two blocks above._

## NFL / fanduel

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 60000 |
| audit date | 2026-09-22 |
| operator-confirmed | **False** (L-02) |
| coefficients | 25 |
| disputed | 0 |
| not audited | 7 |
| deliberately zero | 5 (IR-15) |

> **Audit method.** Re-audited in pass 2. Roster is QB, 2 RB, 3 WR, TE, FLEX(RB/WR/TE/K), DST = 9 slots; the kicker is reachable through the flex, which is why FanDuel carries kicker coefficients and DraftKings does not. Flex eligibility is disputed between two 2026 sources (IR-16).

> **Notes.** Pass 1 gave FanDuel the 100RU / 100RE / 300PA bonuses and DraftKings none. fantasyfootballers (2026-08-15) states the reverse, so the bonuses are now 0.0 here and 3.0 on DraftKings (IR-18). FanDuel's points-allowed tiers for team defence were not retrieved and remain a flagged gap.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `100rec` | 0.0 | `not-applicable` | 1 |  | CORRECTED IN PASS 2 (was 3.0). No FanDuel 100-yard receiving bonus. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `100ru` | 0.0 | `not-applicable` | 1 |  | CORRECTED IN PASS 2 (was 3.0). '100+ Rushing Yards: DraftKings 3, FanDuel 0' - FanDuel pays no yardage milestones. The 100RU column on RotoGrinders' grid is a DraftKings-site artefact. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `300pa` | 0.0 | `not-applicable` | 1 |  | CORRECTED IN PASS 2 (was 3.0). No FanDuel 300-yard passing bonus. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `dst_block` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `dst_fum_rec` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `dst_int` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `dst_pts_allowed` | 0.0 | `not-audited` | 0 |  | GAP: FanDuel scores team defence on points allowed in tiers; no tier table was retrieved. Limitation L-04. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `dst_sack` | 1.0 | `not-audited` | 0 |  | See the DraftKings table's 'dst_sack' note; limitation L-04. |
| `dst_safety` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `dst_td` | 2.0 | `not-audited` | 0 |  | See 'dst_sack'. |
| `fg_0_39` | 3.0 | `single-source` | 1 |  | '0-39 yard Field Goal: DraftKings 0, FanDuel 3'. |
| `fg_40_49` | 4.0 | `single-source` | 1 |  | '40-49 yard Field Goal: DraftKings 0, FanDuel 4'. |
| `fg_50p` | 5.0 | `single-source` | 1 |  | '50+ yard Field Goal: DraftKings 0, FanDuel 5'. |
| `fum_lost` | -2.0 | `multi-source-consistent` | 2 |  | Harsher than DraftKings' -1 (fantasyfootballers, 2026-08-15). |
| `pa_cmp` | 0.0 | `not-applicable` | 0 |  | Neither site pays per completion. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `pa_int` | -1.0 | `single-source` | 1 |  | Standard interception penalty. |
| `pa_td` | 4.0 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `pa_yds` | 0.04 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `pat` | 1.0 | `single-source` | 1 |  | CORRECTED IN PASS 2 (was 2.0). 'Extra Point Kick: DraftKings 0, FanDuel 1'. |
| `rec` | 0.5 | `multi-source-consistent` | 3 |  | FanDuel is HALF PPR: 'FanDuel uses half-point PPR scoring (0.5 points per reception)' - fantasyteamadvisors, 2026-08-05. |
| `rec_td` | 6.0 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `rec_yds` | 0.1 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `ru_td` | 6.0 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `ru_yds` | 0.1 | `multi-source-consistent` | 2 |  | Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard. |
| `two_pt` | 2.0 | `single-source` | 1 |  | 2-point conversion. |

<details><summary>Sources consulted for this table</summary>

- [https://rotogrinders.com/projected-stats/nfl](https://rotogrinders.com/projected-stats/nfl)
- [https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026](https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026)
- [https://fantasyteamadvisors.com/nfl-dfs-strategy/](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- [https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- [https://fantasyfootballers.org/featured/draftkings-vs-fanduel/](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- [https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/](https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/)

</details>

<details><summary>Per-stat source URLs</summary>

- `100rec` (1): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `100ru` (1): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `300pa` (1): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `dst_block` (0): 
- `dst_fum_rec` (0): 
- `dst_int` (0): 
- `dst_pts_allowed` (0): 
- `dst_sack` (0): 
- `dst_safety` (0): 
- `dst_td` (0): 
- `fg_0_39` (1): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `fg_40_49` (1): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `fg_50p` (1): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `fum_lost` (2): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- `pa_cmp` (0): 
- `pa_int` (1): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)
- `pa_td` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `pa_yds` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `pat` (1): [[1]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `rec` (3): [[1]](https://fantasyteamadvisors.com/nfl-dfs-strategy/), [[2]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[3]](https://fantasyfootballers.org/featured/draftkings-vs-fanduel/)
- `rec_td` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `rec_yds` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `ru_td` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `ru_yds` (2): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/), [[2]](https://fantasyteamadvisors.com/nfl-dfs-strategy/)
- `two_pt` (1): [[1]](https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/)

</details>

_All 3 distinct URLs for this table are listed in the two blocks above._

## NHL / draftkings

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 50000 |
| audit date | 2026-09-22 |
| operator-confirmed | **False** (L-02) |
| coefficients | 17 |
| disputed | 0 |
| not audited | 0 |
| deliberately zero | 1 (IR-15) |

> **Audit method.** Two mutually exclusive DraftKings NHL scoring tables were retrieved in pass 1: the 2014/2016 table (Goal 3, Assist 2, SOG 0.5, BLK 0.5, Goalie Win 3, Save 0.2, GA -1, SO 2) and the 2024 FTN table (Goal 8.5, Assist 5, SOG 1.5, BLK 1.3, Goalie Win 6, Save 0.7, GA -3.5, SO 4, OTL 2, plus threshold bonuses). In pass 2 the 2024 scheme was independently confirmed by DraftKings' own network site, so the conflict is RESOLVED and the values are marked multi-source-consistent with the historical table recorded as superseded.

> **Notes.** IRREGULARITY IR-09 (RESOLVED in pass 2). DraftKings Network (dknetwork.draftkings.com, DraftKings' own editorial property) published the identical table on 2025-09-30. Because it comes from the operator's own domain, the 2024/2025 scheme is now considered confirmed for the current season and the 2014 scheme is treated as historical rather than as a live contradiction. IMPORTANT SCORING INTERACTION: a goal also counts as a shot on goal, so a goal is worth 8.5 + 1.5 = 10.0 points. DraftKings Network states this explicitly with a worked example ('Center: +8.5 Pts (Goal) +1.5 (Shot on Goal) = 10 Pts'). The 'sog' projection fed to this table must therefore INCLUDE goals; there is no separate goal-shot coefficient. Pass 1 wrongly added a 'sog_goal' key for this, which would have double-counted every goal - it is removed (IR-14).

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `a` | 5.0 | `multi-source-consistent` | 2 |  | 2025 DraftKings Network and 2024 FTN agree on 5; the 2014-era table said 2. |
| `blk` | 1.3 | `multi-source-consistent` | 2 |  | 2025 DraftKings Network and 2024 FTN agree on 1.3; the 2014-era table said 0.5. |
| `g` | 8.5 | `multi-source-consistent` | 2 |  | 2025 DraftKings Network and 2024 FTN agree on 8.5; the 2014-era table said 3. |
| `g3_blk` | 3.0 | `multi-source-consistent` | 2 |  | Threshold bonus: '3+ Blocked Shots +3 Pts'. |
| `g3_pts` | 3.0 | `multi-source-consistent` | 2 |  | Threshold bonus: '3+ Points +3 Pts'. |
| `g5_sog` | 3.0 | `multi-source-consistent` | 2 |  | Threshold bonus: '5+ Shots +3 Pts'. |
| `ga` | -3.5 | `multi-source-consistent` | 2 |  | 2025 DraftKings Network and 2024 FTN agree on -3.5; the 2014-era table said -1. |
| `hat_trick` | 3.0 | `multi-source-consistent` | 2 |  | 'Hat Trick Bonus +3 Pts' - DraftKings Network 2025-09-30. The 2014-era table said 1.5 and is superseded. |
| `otl` | 2.0 | `single-source` | 1 |  | Goalie overtime-loss bonus, 'Overtime Loss +2 Pts'. |
| `ppp` | 0.0 | `not-applicable` | 1 |  | DraftKings has NO power-play point bonus; the +2 is for SHORT-HANDED points only ('shp'). FanDuel does pay +0.5 per power-play point, so the key exists in the shared stat vocabulary. Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already scored by another key in this table, and applying both would double count. See IR-15. |
| `shootout_goal` | 1.5 | `single-source` | 1 |  | 'Shootout Goal +1.5 Pts' - DraftKings Network 2025-09-30. Renamed from 'sog_goal' in pass 2: the old name suggested 'a shot on goal that is a goal', which would double count every goal (a goal already scores under both 'g' and 'sog'). IR-14. Not modelled by the hockey engine because shootout results are not in the box-score feeds. |
| `shp` | 2.0 | `multi-source-consistent` | 2 |  | Short-handed goal/assist bonus; both sources agree. |
| `so` | 4.0 | `multi-source-consistent` | 2 |  | Shutout bonus. 2025 DraftKings Network and 2024 FTN agree on 4; the 2014-era table said 2. DraftKings Network adds: shootout goals do not prevent a shutout. |
| `sog` | 1.5 | `multi-source-consistent` | 2 |  | 2025 DraftKings Network and 2024 FTN agree on 1.5; the 2014-era table said 0.5. A GOAL ALSO COUNTS AS A SHOT ON GOAL, so a goal scores 8.5 + 1.5 = 10.0. |
| `sv` | 0.7 | `multi-source-consistent` | 2 |  | 2025 DraftKings Network and 2024 FTN agree on 0.7; the 2014-era table said 0.2. |
| `sv35` | 3.0 | `single-source` | 1 |  | Goalie threshold bonus: '35+ Saves +3 Pts'. |
| `win_goalie` | 6.0 | `multi-source-consistent` | 2 |  | 2025 DraftKings Network and 2024 FTN agree on 6; the 2014-era table said 3. |

<details><summary>Sources consulted for this table</summary>

- [https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/)
- [https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- [https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- [https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
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
- `shp` (2): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey), [[2]](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/)
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
| operator-confirmed | **False** (L-02) |
| coefficients | 11 |
| disputed | 0 |
| not audited | 1 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** Single source retrieved (FTN Fantasy, 2024-04-15). Every value is therefore 'single-source' and provisional.

> **Notes.** IRREGULARITY IR-10: FanDuel NHL is sourced from exactly one document. FanDuel also scores +/-. The +/-' value is not present in that document and is set to 0 with status 'not-audited'.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `a` | 8.0 | `single-source` | 1 |  | - |
| `blk` | 1.6 | `single-source` | 1 |  | - |
| `g` | 12.0 | `single-source` | 1 |  | - |
| `ga` | -4.0 | `single-source` | 1 |  | - |
| `plus_minus` | 0.0 | `not-audited` | 0 |  | FanDuel scores +/- (per the Reddit thread) but no point value was retrieved. Left at 0 and flagged. |
| `ppp` | 0.5 | `single-source` | 1 |  | Power-play goal/assist. |
| `shp` | 2.0 | `single-source` | 1 |  | Short-handed goal/assist. |
| `so` | 8.0 | `single-source` | 1 |  | Goalie shutout. |
| `sog` | 1.6 | `single-source` | 1 |  | - |
| `sv` | 0.8 | `single-source` | 1 |  | - |
| `win_goalie` | 12.0 | `single-source` | 1 |  | - |

<details><summary>Sources consulted for this table</summary>

- [https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/](https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/)
- [https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- [https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th](https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th)
- [https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/](https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/)
- [https://occupyfantasy.com/nhl-dfs-strategy-guide/](https://occupyfantasy.com/nhl-dfs-strategy-guide/)

</details>

<details><summary>Per-stat source URLs</summary>

- `a` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `blk` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `g` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `ga` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `plus_minus` (0): 
- `ppp` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `shp` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `so` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `sog` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `sv` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)
- `win_goalie` (1): [[1]](https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey)

</details>

_All 1 distinct URLs for this table are listed in the two blocks above._

## WNBA / draftkings

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 50000 |
| audit date | 2026-09-22 |
| operator-confirmed | **False** (L-02) |
| coefficients | 9 |
| disputed | 0 |
| not audited | 9 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** No WNBA scoring page was retrieved during this audit. Stat keys are derived from the columns RotoGrinders publishes on its WNBA grid; point values are NOT audited and are set to 0 so the engine cannot silently produce a wrong total.

> **Notes.** All values are 0.0 and status 'not-audited' on purpose: the WNBA table must be filled from the operator's own scoring page before it is used. See docs/10-roadmap-and-limitations.md item L-03.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `ast` | 0.0 | `not-audited` | 1 |  | Column present on the RotoGrinders WNBA grid; point value not audited. |
| `blk` | 0.0 | `not-audited` | 1 |  | Column present on the RotoGrinders WNBA grid; point value not audited. |
| `dd` | 0.0 | `not-audited` | 1 |  | Column present on the RotoGrinders WNBA grid; point value not audited. |
| `pts` | 0.0 | `not-audited` | 1 |  | Column present on the RotoGrinders WNBA grid; point value not audited. |
| `reb` | 0.0 | `not-audited` | 1 |  | Column present on the RotoGrinders WNBA grid; point value not audited. |
| `stl` | 0.0 | `not-audited` | 1 |  | Column present on the RotoGrinders WNBA grid; point value not audited. |
| `td` | 0.0 | `not-audited` | 1 |  | Column present on the RotoGrinders WNBA grid; point value not audited. |
| `three_pm` | 0.0 | `not-audited` | 1 |  | Column present on the RotoGrinders WNBA grid; point value not audited. |
| `to` | 0.0 | `not-audited` | 1 |  | Column present on the RotoGrinders WNBA grid; point value not audited. |

<details><summary>Sources consulted for this table</summary>

- [https://rotogrinders.com/projected-stats/wnba](https://rotogrinders.com/projected-stats/wnba)

</details>

<details><summary>Per-stat source URLs</summary>

- `ast` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `blk` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `dd` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `pts` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `reb` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `stl` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `td` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `three_pm` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `to` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)

</details>

_All 1 distinct URLs for this table are listed in the two blocks above._

## WNBA / fanduel

| | |
| --- | --- |
| contest format | Classic (full slate) |
| salary cap | 40000 |
| audit date | 2026-09-22 |
| operator-confirmed | **False** (L-02) |
| coefficients | 11 |
| disputed | 0 |
| not audited | 11 |
| deliberately zero | 0 (IR-15) |

> **Audit method.** No WNBA scoring page was retrieved during this audit. Stat keys are derived from the columns RotoGrinders publishes on its WNBA grid; point values are NOT audited and are set to 0 so the engine cannot silently produce a wrong total.

> **Notes.** All values are 0.0 and status 'not-audited' on purpose: the WNBA table must be filled from the operator's own scoring page before it is used. See docs/10-roadmap-and-limitations.md item L-03.

| stat | value | evidence | sources agree | disputed | note |
| --- | ---: | --- | ---: | :---: | --- |
| `ast` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `blk` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `dd` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `ftm` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `pts` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `reb` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `stl` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `td` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `three_pm` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `to` | 0.0 | `not-audited` | 1 |  | Point value not audited. |
| `two_pm` | 0.0 | `not-audited` | 1 |  | Point value not audited. |

<details><summary>Sources consulted for this table</summary>

- [https://rotogrinders.com/projected-stats/wnba](https://rotogrinders.com/projected-stats/wnba)

</details>

<details><summary>Per-stat source URLs</summary>

- `ast` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `blk` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `dd` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `ftm` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `pts` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `reb` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `stl` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `td` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `three_pm` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `to` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)
- `two_pm` (1): [[1]](https://rotogrinders.com/projected-stats/wnba)

</details>

_All 1 distinct URLs for this table are listed in the two blocks above._
