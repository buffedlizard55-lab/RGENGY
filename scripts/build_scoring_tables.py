#!/usr/bin/env python3
"""Generate the remaining ``rgengy/data/scoring/*.json`` tables.

Why a generator?  Every table needs the *same* schema and the *same*
per-value provenance contract consumed by :mod:`rgengy.scoring`.  Writing nine
near-identical JSON blobs by hand invites drift.  This script keeps the audited
values and their source URLs in one reviewable place and emits well-formed
JSON that is committed to the repo (so the runtime never needs the generator).

The two hand-written tables (``mlb_draftkings.json`` and ``mlb_fanduel.json``)
are **not** overwritten - they are the worked example of the target format.

PROVENANCE RULES
----------------
``verification_status`` is one of:

* ``multi-source-consistent`` - >= 2 independent sources retrieved during the
  2026-09-22 audit agree, and no source contradicts.
* ``single-source``           - only one source retrieved; treat as provisional.
* ``cross-validated-via-rg``  - the value's existence is independently
  corroborated by a column on RotoGrinders' own published grid.
* ``disputed``                - sources contradict; the majority value is used
  and the conflict is registered in ``docs/09-irregularities.md``.
* ``not-audited``             - the value is standard practice but was NOT
  retrieved from any source during this audit.  Such values are excluded from
  published fantasy-point totals by default (see ``--strict``).

Run:  ``python3 scripts/build_scoring_tables.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "rgengy" / "data" / "scoring"

AUDIT_DATE = "2026-09-22"

# ---------------------------------------------------------------------------
# Source registry - every URL below was returned by the retrieval tools during
# the audit session.  Keys are short handles used by the tables.
# ---------------------------------------------------------------------------
SOURCES = {
    "DK_NBA_ROTOWIRE": "https://www.rotowire.com/basketball/article/dfs-basketball-101-how-to-win-on-draftkings-19246",
    "NBA_DFSBUILD": "https://dfsbuild.com/dfs-guide/nba-dfs-guide/",
    "NBA_TRF": "https://teamriseorfall.com/nba-dfs-strategy-guide/",
    "NHL_REDDIT_2014": "https://www.reddit.com/r/hockey/comments/2iop7w/is_anyone_doing_nhl_fanduel/",
    "NHL_FTN_2024": "https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey",
    "NHL_DAILYFACEOFF": "https://www.dailyfaceoff.com/news/draftkings-fantasy-hockey-cheat-sheet-march-9th",
    "MLB_STOKASTIC_FD": "https://www.stokastic.com/articles/dfs-strategy/fanduel-mlb-dfs-cheat-sheet",
    "RG_NFL_GRID": "https://rotogrinders.com/projected-stats/nfl",
    "RG_WNBA_GRID": "https://rotogrinders.com/projected-stats/wnba",
    "RG_MLB_GRID": "https://rotogrinders.com/projected-stats/mlb",
    "MLB_SPORTSFANFOCUS": "https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/",
    "MLB_DFS101": "https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/",
    "MLB_RUNPURE": "https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/",
    "MLB_FTA_CALC": "https://fantasyteamadvice.com/mlb/fantasy-calculator",
    "MLB_ROTOWIRE_DK": "https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444",
    "STOKASTIC_RG_COMPARE": "https://www.stokastic.com/articles/nfl-dfs/stokastic-sims-vs-sabersim-vs-rotogrinders-nfl-2026",
    # Added in review pass 2/3 - these are the sources that resolved (or sharply
    # narrowed) several scoring conflicts found by the first pass.
    "RG_NBA_FD_STRATEGY": "https://rotogrinders.com/articles/fanduel-nba-strategy-239702",
    "NBA_OCCUPYFANTASY": "https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/",
    "NBA_FANSCOUT": "https://fanscout.pro/nba-fanduel-optimizer",
    "DK_NETWORK_NHL": "https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101-how-to-play-dfs-on-draftkings/",
    "NHL_OCCUPYFANTASY": "https://occupyfantasy.com/nhl-dfs-strategy-guide/",
    "NFL_FTA_2026": "https://fantasyteamadvisors.com/nfl-dfs-strategy/",
    "NFL_OCCUPYFANTASY_2026": "https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/",
    "NFL_FANTASYFOOTBALLERS_2026": "https://fantasyfootballers.org/featured/draftkings-vs-fanduel/",
    "NFL_SPORTSBETTINGDIME_2026": "https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/",
    "NBA_SPORTINGNEWS_2023": "https://www.sportingnews.com/us/nba/news/nba-fanduel-picks-128-best-nba-dfs-lineup-advice-saturdays-daily-fantasy-basketball-tournaments/jqsghzxwekyboxtsm6mlw0jw",
    "NBA_LINEUPS_2019": "https://www.lineups.com/betting/fanduel-nba-strategy/",
}

#: Stat keys that are deliberately pinned at 0.0 because a SECOND key already
#: carries the same production.  Operators publish scoring either as an aggregate
#: ("1 point per point scored") or as its components ("2 per FG made, 1 per FT
#: made, +1 per 3PM"); applying both representations at once double counts.
#: `rgengy.quality` treats these as informational, not as a coverage gap.
INTENTIONALLY_ZERO_NOTE = (
    "Pinned at 0.0 on purpose: this stat is an alternative REPRESENTATION of production already "
    "scored by another key in this table, and applying both would double count. See IR-15."
)


def v(value, status, srcs, disputed=False, note=None, agreement=None, intentionally_zero=False):
    """Build one scoring value record."""
    rec = {
        "value": float(value),
        "verification_status": status,
        "agreement": agreement if agreement is not None else len(srcs),
        "disputed": bool(disputed),
        "confirmed_by_operator": False,
        "sources": [SOURCES[s] if s in SOURCES else s for s in srcs],
    }
    if intentionally_zero:
        rec["intentionally_zero"] = True
        note = (note + " " if note else "") + INTENTIONALLY_ZERO_NOTE
    if note:
        rec["note"] = note
    return rec


def table(sport, site, fmt, cap, method, notes, values, consulted):
    return {
        "meta": {
            "sport": sport,
            "site": site,
            "contest_format": fmt,
            "salary_cap": cap,
            "confirmed_by_operator": False,
            "audit_date": AUDIT_DATE,
            "audit_method": method,
            "sources_consulted": consulted,
            "notes": notes,
        },
        "values": values,
    }


# ---------------------------------------------------------------------------
# NBA
# ---------------------------------------------------------------------------
NBA_CONSULTED = [SOURCES["DK_NBA_ROTOWIRE"], SOURCES["NBA_DFSBUILD"], SOURCES["NBA_TRF"]]

nba_dk = table(
    "nba", "draftkings", "Classic (full slate)", 50000,
    "DraftKings NBA values are identical across three independent sources retrieved 2026-09-22.",
    "DraftKings scores counting stats plus a 3PM bonus and double-double / triple-double bonuses. "
    "Field-goal and free-throw makes are NOT scored separately (they are already inside 'pts').",
    {
        "pts": v(1.0, "multi-source-consistent", ["DK_NBA_ROTOWIRE", "NBA_DFSBUILD", "NBA_TRF"]),
        "three_pm": v(0.5, "multi-source-consistent", ["DK_NBA_ROTOWIRE", "NBA_DFSBUILD", "NBA_TRF"]),
        "reb": v(1.25, "multi-source-consistent", ["DK_NBA_ROTOWIRE", "NBA_DFSBUILD", "NBA_TRF"]),
        "ast": v(1.5, "multi-source-consistent", ["DK_NBA_ROTOWIRE", "NBA_DFSBUILD", "NBA_TRF"]),
        "stl": v(2.0, "multi-source-consistent", ["DK_NBA_ROTOWIRE", "NBA_DFSBUILD", "NBA_TRF"]),
        "blk": v(2.0, "multi-source-consistent", ["DK_NBA_ROTOWIRE", "NBA_DFSBUILD", "NBA_TRF"]),
        "to": v(-0.5, "multi-source-consistent", ["DK_NBA_ROTOWIRE", "NBA_DFSBUILD", "NBA_TRF"]),
        "dd": v(1.5, "multi-source-consistent", ["DK_NBA_ROTOWIRE", "NBA_DFSBUILD", "NBA_TRF"],
                note="Max 1 per player."),
        "td": v(3.0, "multi-source-consistent", ["DK_NBA_ROTOWIRE", "NBA_DFSBUILD", "NBA_TRF"],
                note="Max 1 per player; additive with 'dd' per RotoWire's worked example."),
    },
    NBA_CONSULTED,
)

NBA_FD_CONSULTED = NBA_CONSULTED + [
    SOURCES["RG_NBA_FD_STRATEGY"], SOURCES["NBA_OCCUPYFANTASY"], SOURCES["NBA_FANSCOUT"],
    SOURCES["NBA_SPORTINGNEWS_2023"], SOURCES["NBA_LINEUPS_2019"],
]

nba_fd = table(
    "nba", "fanduel", "Classic (full slate)", 60000,
    "Five sources were retrieved and they disagree on two points, so both are marked 'disputed' "
    "and both readings are recorded. RotoGrinders' own FanDuel NBA guide (created 2014-02-11, last "
    "updated 2025-11-03) states: Point=1, Rebound=1.2, Assist=1.5, Steal=2, Block=2, TO=-1, and "
    "'FanDuel does not give extra points for three-pointers'. occupyfantasy (2025-06-05) and "
    "dfsbuild (2025-10-07) both state Steal=3 and Block=3 and neither lists a 3PM bonus. "
    "sportingnews (2023-01-28) and lineups (2019-05-21) describe FanDuel in the MADE-SHOT "
    "representation (3PM +1, FGM +2, FTM +1), which is arithmetically identical to 1 point per "
    "point plus a +1 3PM bonus.",
    "TWO REPRESENTATION BUGS WERE FIXED HERE (IR-15). (1) The first pass of this audit encoded "
    "pts=1.0 AND two_pm=2.0 AND ftm=1.0 AND three_pm=3.0 at once. That is not either published "
    "representation - it is both of them summed, and it inflated every FanDuel NBA projection by "
    "roughly 2x (an 8-player demo lineup scored 763 points instead of ~300). RGENGY now uses the "
    "aggregate representation ('pts') and pins the made-shot keys at 0.0. (2) three_pm=3.0 came "
    "from a source that meant 'a made three is worth 3 points in total', not 'a made three earns a "
    "3-point bonus'; the majority of recent sources say FanDuel pays no 3PM bonus at all, so it is "
    "0.0 and disputed. NOTE ALSO: FanDuel's own rules page "
    "(https://sportsbook.fanduel.com/rules) is geo-verified and cannot be retrieved headlessly, "
    "which is why this table rests on secondary sources.",
    {
        "pts": v(1.0, "multi-source-consistent", ["RG_NBA_FD_STRATEGY", "NBA_OCCUPYFANTASY", "NBA_DFSBUILD"],
                 agreement=5,
                 note="1 fantasy point per real point scored. Every retrieved source agrees."),
        "three_pm": v(0.0, "disputed", ["RG_NBA_FD_STRATEGY", "NBA_DFSBUILD", "NBA_OCCUPYFANTASY",
                                        "NBA_SPORTINGNEWS_2023", "NBA_LINEUPS_2019"],
                      disputed=True, agreement=5,
                      note="CONFLICT. RotoGrinders (2025-11-03): 'FanDuel does not give extra points "
                           "for three-pointers, so all buckets are treated the same.' dfsbuild "
                           "(2025-10-07) shows '-' for FanDuel. sportingnews (2023-01-28) and "
                           "lineups (2019-05-21) describe a +1 3PM bonus. Three of five sources and "
                           "the two most recent say no bonus, so 0.0 is used. IR-15."),
        "two_pm": v(0.0, "not-applicable", ["NBA_LINEUPS_2019"], intentionally_zero=True,
                    note="Made-shot representation: lineups.com states '2 points per field goal "
                         "made', which is subsumed by pts=1.0."),
        "ftm": v(0.0, "not-applicable", ["NBA_LINEUPS_2019"], intentionally_zero=True,
                 note="Made-shot representation: sportingnews states 'free throw made (+1 point)', "
                      "which is subsumed by pts=1.0."),
        "reb": v(1.2, "multi-source-consistent", ["RG_NBA_FD_STRATEGY", "NBA_OCCUPYFANTASY", "NBA_DFSBUILD"],
                 agreement=5, note="1.2, versus 1.25 on DraftKings - every source agrees."),
        "ast": v(1.5, "multi-source-consistent", ["RG_NBA_FD_STRATEGY", "NBA_OCCUPYFANTASY", "NBA_DFSBUILD"],
                 agreement=5),
        "stl": v(3.0, "disputed", ["NBA_OCCUPYFANTASY", "NBA_DFSBUILD", "RG_NBA_FD_STRATEGY",
                                   "NBA_SPORTINGNEWS_2023"],
                 disputed=True, agreement=4,
                 note="CONFLICT: occupyfantasy (2025-06-05), dfsbuild (2025-10-07) and sportingnews "
                      "(2023) say 3; RotoGrinders' own guide says 2. Majority of recent independent "
                      "sources wins, but because the minority source is RotoGrinders itself this is "
                      "flagged for manual review. IR-15."),
        "blk": v(3.0, "disputed", ["NBA_OCCUPYFANTASY", "NBA_DFSBUILD", "RG_NBA_FD_STRATEGY",
                                   "NBA_SPORTINGNEWS_2023"],
                 disputed=True, agreement=4, note="Same conflict and same resolution as 'stl'. IR-15."),
        "to": v(-1.0, "multi-source-consistent", ["RG_NBA_FD_STRATEGY", "NBA_OCCUPYFANTASY", "NBA_DFSBUILD"],
                agreement=5, note="Harsher than DraftKings' -0.5; every source agrees."),
        "dd": v(0.0, "disputed", ["NBA_DFSBUILD", "RG_NBA_FD_STRATEGY"], disputed=True,
                note="Neither RotoGrinders' FanDuel scoring table nor dfsbuild's comparison lists a "
                     "FanDuel double-double bonus. Flagged as IR-08."),
        "td": v(0.0, "disputed", ["NBA_DFSBUILD", "RG_NBA_FD_STRATEGY"], disputed=True,
                note="Same ambiguity as 'dd'. Flagged as IR-08."),
    },
    NBA_FD_CONSULTED,
)

# ---------------------------------------------------------------------------
# WNBA - RotoGrinders publishes a WNBA grid, and its columns (MINUTES, PTS,
# REB, AST, 3PM, TO, STL, BLK, plus the prop columns P-A / P-R / P-R-A / B-S /
# R-A) are direct evidence of which stats the underlying scoring rewards.
# ---------------------------------------------------------------------------
wnba_dk = table(
    "wnba", "draftkings", "Classic (full slate)", 50000,
    "No WNBA scoring page was retrieved during this audit. Stat keys are derived from the columns "
    "RotoGrinders publishes on its WNBA grid; point values are NOT audited and are set to 0 so the "
    "engine cannot silently produce a wrong total.",
    "All values are 0.0 and status 'not-audited' on purpose: the WNBA table must be filled from the "
    "operator's own scoring page before it is used. See docs/10-roadmap-and-limitations.md item L-03.",
    {k: v(0.0, "not-audited", ["RG_WNBA_GRID"], note="Column present on the RotoGrinders WNBA grid; point value not audited.")
     for k in ("pts", "three_pm", "reb", "ast", "stl", "blk", "to", "dd", "td")},
    [SOURCES["RG_WNBA_GRID"]],
)

wnba_fd = table(
    "wnba", "fanduel", "Classic (full slate)", 40000,
    wnba_dk["meta"]["audit_method"],
    wnba_dk["meta"]["notes"],
    {k: v(0.0, "not-audited", ["RG_WNBA_GRID"], note="Point value not audited.")
     for k in ("pts", "three_pm", "two_pm", "ftm", "reb", "ast", "stl", "blk", "to", "dd", "td")},
    [SOURCES["RG_WNBA_GRID"]],
)

# ---------------------------------------------------------------------------
# NHL - two contradictory DraftKings tables exist.  This is a genuine,
# important irregularity and it is flagged rather than papered over.
# ---------------------------------------------------------------------------
NHL_CONSULTED = [SOURCES["NHL_REDDIT_2014"], SOURCES["NHL_FTN_2024"],
                 SOURCES["NHL_DAILYFACEOFF"], SOURCES["DK_NETWORK_NHL"],
                 SOURCES["NHL_OCCUPYFANTASY"]]

_DKN = ("DraftKings Network (dknetwork.draftkings.com, DraftKings' own editorial property) published "
        "the identical table on 2025-09-30. Because it comes from the operator's own domain, the "
        "2024/2025 scheme is now considered confirmed for the current season and the 2014 scheme is "
        "treated as historical rather than as a live contradiction.")

nhl_dk = table(
    "nhl", "draftkings", "Classic (full slate)", 50000,
    "Two mutually exclusive DraftKings NHL scoring tables were retrieved in pass 1: the 2014/2016 "
    "table (Goal 3, Assist 2, SOG 0.5, BLK 0.5, Goalie Win 3, Save 0.2, GA -1, SO 2) and the 2024 "
    "FTN table (Goal 8.5, Assist 5, SOG 1.5, BLK 1.3, Goalie Win 6, Save 0.7, GA -3.5, SO 4, OTL 2, "
    "plus threshold bonuses). In pass 2 the 2024 scheme was independently confirmed by DraftKings' "
    "own network site, so the conflict is RESOLVED and the values are marked multi-source-consistent "
    "with the historical table recorded as superseded.",
    "IRREGULARITY IR-09 (RESOLVED in pass 2). " + _DKN + " IMPORTANT SCORING INTERACTION: a goal also "
    "counts as a shot on goal, so a goal is worth 8.5 + 1.5 = 10.0 points. DraftKings Network states "
    "this explicitly with a worked example ('Center: +8.5 Pts (Goal) +1.5 (Shot on Goal) = 10 Pts'). "
    "The 'sog' projection fed to this table must therefore INCLUDE goals; there is no separate "
    "goal-shot coefficient. Pass 1 wrongly added a 'sog_goal' key for this, which would have "
    "double-counted every goal - it is removed (IR-14).",
    {
        "g": v(8.5, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, note="2025 DraftKings Network and 2024 FTN agree on 8.5; the 2014-era table said 3."),
        "a": v(5.0, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, note="2025 DraftKings Network and 2024 FTN agree on 5; the 2014-era table said 2."),
        "sog": v(1.5, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, note="2025 DraftKings Network and 2024 FTN agree on 1.5; the 2014-era table said 0.5. A GOAL ALSO COUNTS AS A SHOT ON GOAL, so a goal scores 8.5 + 1.5 = 10.0."),
        "blk": v(1.3, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, note="2025 DraftKings Network and 2024 FTN agree on 1.3; the 2014-era table said 0.5."),
        "shp": v(2.0, "multi-source-consistent", ["NHL_FTN_2024", "NHL_REDDIT_2014"],
                 note="Short-handed goal/assist bonus; both sources agree."),
        "shootout_goal": v(1.5, "single-source", ["DK_NETWORK_NHL"],
                           note="'Shootout Goal +1.5 Pts' - DraftKings Network 2025-09-30. Renamed "
                                "from 'sog_goal' in pass 2: the old name suggested 'a shot on goal "
                                "that is a goal', which would double count every goal (a goal already "
                                "scores under both 'g' and 'sog'). IR-14. Not modelled by the hockey "
                                "engine because shootout results are not in the box-score feeds."),
        "ppp": v(0.0, "not-applicable", ["DK_NETWORK_NHL"], intentionally_zero=True,
                 note="DraftKings has NO power-play point bonus; the +2 is for SHORT-HANDED points "
                      "only ('shp'). FanDuel does pay +0.5 per power-play point, so the key exists in "
                      "the shared stat vocabulary."),
        "hat_trick": v(3.0, "multi-source-consistent", ["DK_NETWORK_NHL", "NHL_FTN_2024"],
                       agreement=2, note="'Hat Trick Bonus +3 Pts' - DraftKings Network 2025-09-30. "
                                          "The 2014-era table said 1.5 and is superseded."),
        "g5_sog": v(3.0, "multi-source-consistent", ["DK_NETWORK_NHL", "NHL_FTN_2024"],
                    agreement=2, note="Threshold bonus: '5+ Shots +3 Pts'."),
        "g3_blk": v(3.0, "multi-source-consistent", ["DK_NETWORK_NHL", "NHL_FTN_2024"],
                    agreement=2, note="Threshold bonus: '3+ Blocked Shots +3 Pts'."),
        "g3_pts": v(3.0, "multi-source-consistent", ["DK_NETWORK_NHL", "NHL_FTN_2024"],
                    agreement=2, note="Threshold bonus: '3+ Points +3 Pts'."),
        "win_goalie": v(6.0, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, note="2025 DraftKings Network and 2024 FTN agree on 6; the 2014-era table said 3."),
        "sv": v(0.7, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, note="2025 DraftKings Network and 2024 FTN agree on 0.7; the 2014-era table said 0.2."),
        "ga": v(-3.5, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, note="2025 DraftKings Network and 2024 FTN agree on -3.5; the 2014-era table said -1."),
        "so": v(4.0, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, note="Shutout bonus. 2025 DraftKings Network and 2024 FTN agree on 4; the 2014-era table said 2. DraftKings Network adds: shootout goals do not prevent a shutout."),
        "otl": v(2.0, "single-source", ["DK_NETWORK_NHL"], note="Goalie overtime-loss bonus, "
                 "'Overtime Loss +2 Pts'."),
        "sv35": v(3.0, "single-source", ["DK_NETWORK_NHL"], note="Goalie threshold bonus: "
                  "'35+ Saves +3 Pts'."),
    },
    NHL_CONSULTED,
)

nhl_fd = table(
    "nhl", "fanduel", "Classic (full slate)", 40000,
    "Single source retrieved (FTN Fantasy, 2024-04-15). Every value is therefore 'single-source' and provisional.",
    "IRREGULARITY IR-10: FanDuel NHL is sourced from exactly one document. FanDuel also scores +/-. "
    "The +/-' value is not present in that document and is set to 0 with status 'not-audited'.",
    {
        "g": v(12.0, "single-source", ["NHL_FTN_2024"]),
        "a": v(8.0, "single-source", ["NHL_FTN_2024"]),
        "sog": v(1.6, "single-source", ["NHL_FTN_2024"]),
        "blk": v(1.6, "single-source", ["NHL_FTN_2024"]),
        "shp": v(2.0, "single-source", ["NHL_FTN_2024"], note="Short-handed goal/assist."),
        "ppp": v(0.5, "single-source", ["NHL_FTN_2024"], note="Power-play goal/assist."),
        "win_goalie": v(12.0, "single-source", ["NHL_FTN_2024"]),
        "so": v(8.0, "single-source", ["NHL_FTN_2024"], note="Goalie shutout."),
        "sv": v(0.8, "single-source", ["NHL_FTN_2024"]),
        "ga": v(-4.0, "single-source", ["NHL_FTN_2024"]),
        "plus_minus": v(0.0, "not-audited", [], note="FanDuel scores +/- (per the Reddit thread) but no "
                                                     "point value was retrieved. Left at 0 and flagged."),
    },
    NHL_CONSULTED,
)

# ---------------------------------------------------------------------------
# NFL - re-audited in pass 2 with 2026 sources.  Pass 1 had NO source for any
# NFL value and marked everything 'not-audited'; it also had the 100/300-yard
# bonuses on the wrong site and gave DraftKings kicker coefficients it cannot
# use (DraftKings' NFL classic roster has no kicker slot).
# ---------------------------------------------------------------------------
NFL_CONSULTED = [SOURCES["RG_NFL_GRID"], SOURCES["STOKASTIC_RG_COMPARE"],
                 SOURCES["NFL_FTA_2026"], SOURCES["NFL_OCCUPYFANTASY_2026"],
                 SOURCES["NFL_FANTASYFOOTBALLERS_2026"], SOURCES["NFL_SPORTSBETTINGDIME_2026"]]

# occupyfantasy (2026-09-10) states the shared core for all sites:
#   "Award 1 point per 25 passing yards, 1 point per 10 yards rushing,
#    4 points per passing TD, and 6 points per rushing/receiving TD"
# 1 per 25 yards == 0.04 per yard; 1 per 10 yards == 0.1 per yard.
_YD_SRC = ["NFL_OCCUPYFANTASY_2026", "NFL_FTA_2026"]
_yd = ("Confirmed by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards "
       "rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on both "
       "sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard.")

nfl_dk = table(
    "nfl", "draftkings", "Classic (full slate)", 50000,
    "Re-audited in pass 2 against four 2026 sources. Roster is QB, 2 RB, 3 WR, TE, FLEX(RB/WR/TE), "
    "DST = 9 slots with NO kicker, corroborated by a real published DraftKings lineup that totals "
    "exactly $50,000 (sportsbettingdime, 2026-09-19). Because no kicker can be rostered, all kicker "
    "coefficients are pinned at 0.",
    "TWO PASS-1 ERRORS FIXED (IR-18). (1) The 100-yard rushing / 100-yard receiving / 300-yard "
    "passing bonuses were assigned to FanDuel and set to 0 for DraftKings. fantasyfootballers "
    "(2026-08-15) shows the opposite - DraftKings 3 / 3 / 3, FanDuel 0 / 0 / 0 - and "
    "fantasyteamadvisors (2026-08-05) independently says 'DraftKings ... awards milestone bonuses "
    "for 100-yard and 300-yard performances'. (2) DraftKings was given field-goal and extra-point "
    "coefficients even though its classic roster has no kicker slot; those are now 0. "
    "RotoGrinders' NFL grid publishes 100RU / 100RE / 300PA columns, which corroborates that these "
    "bonuses are a projection target on at least one major site.",
    {
        "pa_yds": v(0.04, "multi-source-consistent", _YD_SRC, note=_yd),
        "pa_td": v(4.0, "multi-source-consistent", _YD_SRC, note=_yd),
        "pa_int": v(-1.0, "single-source", ["NFL_OCCUPYFANTASY_2026"],
                    note="Standard interception penalty; not restated by the other 2026 sources."),
        "pa_cmp": v(0.0, "not-applicable", [], intentionally_zero=True,
                    note="Neither site pays per completion."),
        "ru_yds": v(0.1, "multi-source-consistent", _YD_SRC, note=_yd),
        "ru_td": v(6.0, "multi-source-consistent", _YD_SRC, note=_yd),
        "rec": v(1.0, "multi-source-consistent", ["NFL_FTA_2026", "NFL_OCCUPYFANTASY_2026",
                                                  "NFL_FANTASYFOOTBALLERS_2026"], agreement=3,
                 note="DraftKings is FULL PPR: 'DraftKings uses full-point PPR scoring (1 point per "
                      "reception)' - fantasyteamadvisors, 2026-08-05."),
        "rec_yds": v(0.1, "multi-source-consistent", _YD_SRC, note=_yd),
        "rec_td": v(6.0, "multi-source-consistent", _YD_SRC, note=_yd),
        "two_pt": v(2.0, "single-source", ["NFL_OCCUPYFANTASY_2026"],
                    note="2-point conversion. Not restated by the other sources retrieved."),
        "fum_lost": v(-1.0, "multi-source-consistent", ["NFL_FANTASYFOOTBALLERS_2026",
                                                        "NFL_OCCUPYFANTASY_2026"], agreement=2,
                      note="fantasyfootballers (2026-08-15) lists Fumble Lost: DraftKings -1, "
                           "FanDuel -2."),
        "100ru": v(3.0, "cross-validated-via-rg", ["NFL_FANTASYFOOTBALLERS_2026", "NFL_FTA_2026",
                                                   "RG_NFL_GRID"], agreement=3,
                   note="CORRECTED IN PASS 2 (was 0.0). fantasyfootballers: '100+ Rushing Yards: "
                        "DraftKings 3, FanDuel 0'. Also corroborated by the 100RU column on "
                        "RotoGrinders' NFL grid."),
        "100rec": v(3.0, "cross-validated-via-rg", ["NFL_FANTASYFOOTBALLERS_2026", "RG_NFL_GRID"],
                    agreement=2,
                    note="CORRECTED IN PASS 2 (was 0.0). '100+ Receiving Yards: DraftKings 3, "
                         "FanDuel 0'; corroborated by the 100RE grid column."),
        "300pa": v(3.0, "cross-validated-via-rg", ["NFL_FANTASYFOOTBALLERS_2026", "RG_NFL_GRID"],
                   agreement=2,
                   note="CORRECTED IN PASS 2 (was 0.0). '300+ Passing Yards: DraftKings 3, "
                        "FanDuel 0'; corroborated by the 300PA grid column."),
        "fg_0_39": v(0.0, "not-applicable", ["NFL_SPORTSBETTINGDIME_2026"], intentionally_zero=True,
                     note="DraftKings' NFL classic roster has no kicker slot (9 slots: QB, 2 RB, "
                          "3 WR, TE, FLEX, DST), so field goals cannot be rostered or scored. "
                          "fantasyfootballers lists 0-39 FG as DraftKings 0 / FanDuel 3."),
        "fg_40_49": v(0.0, "not-applicable", ["NFL_SPORTSBETTINGDIME_2026"], intentionally_zero=True,
                      note="No DraftKings kicker slot."),
        "fg_50p": v(0.0, "not-applicable", ["NFL_SPORTSBETTINGDIME_2026"], intentionally_zero=True,
                    note="No DraftKings kicker slot."),
        "pat": v(0.0, "not-applicable", ["NFL_FANTASYFOOTBALLERS_2026"], intentionally_zero=True,
               note="CORRECTED IN PASS 2 (was 1.0). fantasyfootballers lists 'Extra Point Kick: "
                    "DraftKings 0, FanDuel 1' - consistent with DraftKings having no kicker slot."),
        "dst_sack": v(1.0, "not-audited", [],
                      note="DraftKings team-defence scoring was NOT retrieved from any source during "
                           "this audit. The values below follow the long-standing convention and are "
                           "flagged 'not-audited'; the pipeline excludes them from published totals "
                           "under --strict. See limitation L-04."),
        "dst_int": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_fum_rec": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_td": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_safety": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_block": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_pts_allowed": v(0.0, "not-audited", [], intentionally_zero=True,
                            note="GAP: both sites also score team defence on points allowed (tiered). "
                                 "No tier table was retrieved, so the key is modelled at 0 and "
                                 "flagged. See limitation L-04."),
    },
    NFL_CONSULTED,
)

nfl_fd = table(
    "nfl", "fanduel", "Classic (full slate)", 60000,
    "Re-audited in pass 2. Roster is QB, 2 RB, 3 WR, TE, FLEX(RB/WR/TE/K), DST = 9 slots; the "
    "kicker is reachable through the flex, which is why FanDuel carries kicker coefficients and "
    "DraftKings does not. Flex eligibility is disputed between two 2026 sources (IR-16).",
    "Pass 1 gave FanDuel the 100RU / 100RE / 300PA bonuses and DraftKings none. fantasyfootballers "
    "(2026-08-15) states the reverse, so the bonuses are now 0.0 here and 3.0 on DraftKings (IR-18). "
    "FanDuel's points-allowed tiers for team defence were not retrieved and remain a flagged gap.",
    {
        "pa_yds": v(0.04, "multi-source-consistent", _YD_SRC, note=_yd),
        "pa_td": v(4.0, "multi-source-consistent", _YD_SRC, note=_yd),
        "pa_int": v(-1.0, "single-source", ["NFL_OCCUPYFANTASY_2026"],
                    note="Standard interception penalty."),
        "pa_cmp": v(0.0, "not-applicable", [], intentionally_zero=True,
                    note="Neither site pays per completion."),
        "ru_yds": v(0.1, "multi-source-consistent", _YD_SRC, note=_yd),
        "ru_td": v(6.0, "multi-source-consistent", _YD_SRC, note=_yd),
        "rec": v(0.5, "multi-source-consistent", ["NFL_FTA_2026", "NFL_OCCUPYFANTASY_2026",
                                                  "NFL_FANTASYFOOTBALLERS_2026"], agreement=3,
                 note="FanDuel is HALF PPR: 'FanDuel uses half-point PPR scoring (0.5 points per "
                      "reception)' - fantasyteamadvisors, 2026-08-05."),
        "rec_yds": v(0.1, "multi-source-consistent", _YD_SRC, note=_yd),
        "rec_td": v(6.0, "multi-source-consistent", _YD_SRC, note=_yd),
        "two_pt": v(2.0, "single-source", ["NFL_OCCUPYFANTASY_2026"], note="2-point conversion."),
        "fum_lost": v(-2.0, "multi-source-consistent", ["NFL_FANTASYFOOTBALLERS_2026",
                                                        "NFL_OCCUPYFANTASY_2026"], agreement=2,
                      note="Harsher than DraftKings' -1 (fantasyfootballers, 2026-08-15)."),
        "100ru": v(0.0, "not-applicable", ["NFL_FANTASYFOOTBALLERS_2026"], intentionally_zero=True,
                   note="CORRECTED IN PASS 2 (was 3.0). '100+ Rushing Yards: DraftKings 3, "
                        "FanDuel 0' - FanDuel pays no yardage milestones. The 100RU column on "
                        "RotoGrinders' grid is a DraftKings-site artefact."),
        "100rec": v(0.0, "not-applicable", ["NFL_FANTASYFOOTBALLERS_2026"], intentionally_zero=True,
                    note="CORRECTED IN PASS 2 (was 3.0). No FanDuel 100-yard receiving bonus."),
        "300pa": v(0.0, "not-applicable", ["NFL_FANTASYFOOTBALLERS_2026"], intentionally_zero=True,
                   note="CORRECTED IN PASS 2 (was 3.0). No FanDuel 300-yard passing bonus."),
        "fg_0_39": v(3.0, "single-source", ["NFL_FANTASYFOOTBALLERS_2026"],
                     note="'0-39 yard Field Goal: DraftKings 0, FanDuel 3'."),
        "fg_40_49": v(4.0, "single-source", ["NFL_FANTASYFOOTBALLERS_2026"],
                      note="'40-49 yard Field Goal: DraftKings 0, FanDuel 4'."),
        "fg_50p": v(5.0, "single-source", ["NFL_FANTASYFOOTBALLERS_2026"],
                    note="'50+ yard Field Goal: DraftKings 0, FanDuel 5'."),
        "pat": v(1.0, "single-source", ["NFL_FANTASYFOOTBALLERS_2026"],
                 note="CORRECTED IN PASS 2 (was 2.0). 'Extra Point Kick: DraftKings 0, FanDuel 1'."),
        "dst_sack": v(1.0, "not-audited", [], note="See the DraftKings table's 'dst_sack' note; "
                                                    "limitation L-04."),
        "dst_int": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_fum_rec": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_td": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_safety": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_block": v(2.0, "not-audited", [], note="See 'dst_sack'."),
        "dst_pts_allowed": v(0.0, "not-audited", [], intentionally_zero=True,
                            note="GAP: FanDuel scores team defence on points allowed in tiers; no "
                                 "tier table was retrieved. Limitation L-04."),
    },
    NFL_CONSULTED,
)


# ---------------------------------------------------------------------------
# MLB - Yahoo (RotoGrinders offers a Yahoo grid variant: ?site=yahoo)
# ---------------------------------------------------------------------------
mlb_yahoo = table(
    "mlb", "yahoo", "Classic (full slate)", 200,
    "Yahoo values come from one comparison table (sportsfanfocus.com, 2019). The document is seven years "
    "old at audit time, so every value is 'single-source' and provisional.",
    "IRREGULARITY IR-11: Yahoo scoring is sourced from a single 2019 document. RotoGrinders does offer a "
    "?site=yahoo grid variant (verified 2026-09-22), so Yahoo is a real target even though its values here "
    "are weakly sourced.",
    {
        "1b": v(2.6, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "2b": v(5.2, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "3b": v(7.8, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "hr": v(10.4, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "r": v(1.9, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "rbi": v(1.9, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "bb": v(2.6, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "hbp": v(2.6, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "sb": v(4.2, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "cs": v(0.0, "single-source", ["MLB_SPORTSFANFOCUS"], note="Not listed for Yahoo."),
        "k": v(2.0, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "win": v(4.0, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "er": v(-2.0, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "outs": v(1.0, "single-source", ["MLB_SPORTSFANFOCUS"],
                  note="Yahoo scores per out recorded, not per inning; do not also score 'ip'."),
        "ip": v(0.0, "single-source", ["MLB_SPORTSFANFOCUS"],
                note="Set to 0 because Yahoo pays per out; scoring both would double count."),
        "ha": v(-0.9, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "bba": v(-0.9, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "hbpa": v(-0.9, "single-source", ["MLB_SPORTSFANFOCUS"]),
        "qs": v(0.0, "single-source", ["MLB_SPORTSFANFOCUS"], note="Not listed for Yahoo."),
        "cg": v(0.0, "single-source", ["MLB_SPORTSFANFOCUS"], note="Not listed for Yahoo."),
        "cgso": v(0.0, "single-source", ["MLB_SPORTSFANFOCUS"], note="Not listed for Yahoo."),
        "nohitter": v(0.0, "single-source", ["MLB_SPORTSFANFOCUS"], note="Not listed for Yahoo."),
    },
    [SOURCES["MLB_SPORTSFANFOCUS"]],
)

TABLES = {
    "nba_draftkings": nba_dk,
    "nba_fanduel": nba_fd,
    "wnba_draftkings": wnba_dk,
    "wnba_fanduel": wnba_fd,
    "nhl_draftkings": nhl_dk,
    "nhl_fanduel": nhl_fd,
    "nfl_draftkings": nfl_dk,
    "nfl_fanduel": nfl_fd,
    "mlb_yahoo": mlb_yahoo,
}


def main(argv):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    strict = "--strict" in argv
    written = []
    for name, payload in sorted(TABLES.items()):
        if strict:
            for stat, rec in payload["values"].items():
                if rec["verification_status"] == "not-audited":
                    rec["value"] = 0.0
        path = OUT_DIR / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(str(path.relative_to(OUT_DIR.parent.parent.parent)))
    print(f"wrote {len(written)} scoring tables:")
    for w in written:
        print(f"  {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
