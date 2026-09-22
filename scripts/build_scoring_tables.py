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
    # ---------------------------------------------------------------------
    # Operator-published scoring pages, retrieved 2026-09-22 in the second
    # audit pass. These outrank every source above (see IR-18 for what happens
    # when they disagree).
    # ---------------------------------------------------------------------
    "FD_RULES": "https://www.fanduel.com/rules",
    "DK_NET_MLB_2020": "https://dknetwork.draftkings.com/2020/05/29/beginner-mlb-dfs-scoring/",
    "DK_NET_NFL_2025": "https://dknetwork.draftkings.com/2025/08/27/nfl-dfs-beginners-guide-draftkings/",
    "DK_NET_NBA_2025": "https://dknetwork.draftkings.com/2025/10/17/nba-daily-fantasy-101-how-to-play-dfs-on-draftkings/",
    # DraftKings' WNBA scoring is published on its Pick6 product page, not on a
    # DFS classic page; used as provisional evidence only (see the WNBA table).
    "DK_PICK6_WNBA": "https://pick6.draftkings.com/pick6-rules-and-scoring-wnba",
    # Secondary corroboration for DraftKings DST tiers (identical to FanDuel's).
    "DFS101_FOOTBALL": "https://www.dailyfantasysports101.com/football/",
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


def v(value, status, srcs, disputed=False, note=None, agreement=None, intentionally_zero=False,
      operator=False):
    """Build one scoring value record.

    ``operator=True`` marks the value as read from the operator's own published
    scoring page; the first source in ``srcs`` must then be an operator URL so
    the provenance test in tests/test_scoring.py can enforce the pairing.
    """
    rec = {
        "value": float(value),
        "verification_status": status,
        "agreement": agreement if agreement is not None else len(srcs),
        "disputed": bool(disputed),
        "confirmed_by_operator": bool(operator),
        "sources": [SOURCES[s] if s in SOURCES else s for s in srcs],
    }
    if intentionally_zero:
        rec["intentionally_zero"] = True
        note = (note + " " if note else "") + INTENTIONALLY_ZERO_NOTE
    if note:
        rec["note"] = note
    return rec


def table(sport, site, fmt, cap, method, notes, values, consulted, operator_table=None):
    return {
        "meta": {
            "sport": sport,
            "site": site,
            "contest_format": fmt,
            "salary_cap": cap,
            # Table-level flag: True only when EVERY NON-ZERO value was read
            # from the operator's own published page. Zeros are exempt - a zero
            # (deliberate, absent, or not-applicable) claims nothing that needs
            # operator authority.
            "confirmed_by_operator": (
                bool(operator_table) if operator_table is not None else all(
                    rec.get("confirmed_by_operator") or float(rec["value"]) == 0.0
                    for rec in values.values()
                )
            ),
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
NBA_CONSULTED = [SOURCES["DK_NET_NBA_2025"], SOURCES["DK_NBA_ROTOWIRE"], SOURCES["NBA_DFSBUILD"],
                 SOURCES["NBA_TRF"]]

nba_dk = table(
    "nba", "draftkings", "Classic (full slate)", 50000,
    "DraftKings NBA values were first agreed by three independent secondary sources (retrieved "
    "2026-09-22) and are now OPERATOR-CONFIRMED: DraftKings' own 'NBA Daily Fantasy 101' article "
    "(dknetwork.draftkings.com, published 2025-10-17, retrieved 2026-09-22) lists every value in "
    "this table identically - Point +1, Made 3pt +0.5, Rebound +1.25, Assist +1.5, Steal +2, "
    "Block +2, Turnover -0.5, Double-Double +1.5 (max 1 per player), Triple-Double +3 (max 1 per "
    "player).",
    "DraftKings scores counting stats plus a 3PM bonus and double-double / triple-double bonuses. "
    "Field-goal and free-throw makes are NOT scored separately (they are already inside 'pts'). "
    "Every value matches the operator's own published article.",
    {
        "pts": v(1.0, "multi-source-consistent", ["DK_NET_NBA_2025", "DK_NBA_ROTOWIRE",
                                                  "NBA_DFSBUILD", "NBA_TRF"], operator=True),
        "three_pm": v(0.5, "multi-source-consistent", ["DK_NET_NBA_2025", "DK_NBA_ROTOWIRE",
                                                       "NBA_DFSBUILD", "NBA_TRF"], operator=True),
        "reb": v(1.25, "multi-source-consistent", ["DK_NET_NBA_2025", "DK_NBA_ROTOWIRE",
                                                   "NBA_DFSBUILD", "NBA_TRF"], operator=True),
        "ast": v(1.5, "multi-source-consistent", ["DK_NET_NBA_2025", "DK_NBA_ROTOWIRE",
                                                  "NBA_DFSBUILD", "NBA_TRF"], operator=True),
        "stl": v(2.0, "multi-source-consistent", ["DK_NET_NBA_2025", "DK_NBA_ROTOWIRE",
                                                  "NBA_DFSBUILD", "NBA_TRF"], operator=True),
        "blk": v(2.0, "multi-source-consistent", ["DK_NET_NBA_2025", "DK_NBA_ROTOWIRE",
                                                  "NBA_DFSBUILD", "NBA_TRF"], operator=True),
        "to": v(-0.5, "multi-source-consistent", ["DK_NET_NBA_2025", "DK_NBA_ROTOWIRE",
                                                  "NBA_DFSBUILD", "NBA_TRF"], operator=True),
        "dd": v(1.5, "multi-source-consistent", ["DK_NET_NBA_2025", "DK_NBA_ROTOWIRE",
                                                 "NBA_DFSBUILD", "NBA_TRF"], operator=True,
                note="Max 1 per player - stated verbatim on the operator's scoring table."),
        "td": v(3.0, "multi-source-consistent", ["DK_NET_NBA_2025", "DK_NBA_ROTOWIRE",
                                                 "NBA_DFSBUILD", "NBA_TRF"], operator=True,
                note="Max 1 per player; additive with 'dd' per RotoWire's worked example."),
    },
    NBA_CONSULTED,
)

NBA_FD_CONSULTED = [SOURCES["FD_RULES"]] + NBA_CONSULTED + [
    SOURCES["RG_NBA_FD_STRATEGY"], SOURCES["NBA_OCCUPYFANTASY"], SOURCES["NBA_FANSCOUT"],
    SOURCES["NBA_SPORTINGNEWS_2023"], SOURCES["NBA_LINEUPS_2019"],
]

nba_fd = table(
    "nba", "fanduel", "Classic (full slate)", 60000,
    "OPERATOR-CONFIRMED in the second audit pass (2026-09-22): FanDuel's public rules page "
    "(https://www.fanduel.com/rules, Basketball section, retrieved that day) enumerates scoring as "
    "3-pt FG=3, 2-pt FG=2, FT=1, Rebound=1.2, Assist=1.5, Block=3, Steal=3, Turnover=-1 - and no "
    "double-double or triple-double bonus. Earlier secondary sources disagreed on steal/block "
    "(2 vs 3) and on a 3PM bonus; the operator page settles both: Steal=Block=3, and the "
    "3-pt FG=3 / 2-pt FG=2 pairing IS the aggregate representation (a made three's extra point "
    "sits inside the basket value), so under pts=1.0 the 3PM bonus is 0.",
    "TWO REPRESENTATION BUGS WERE FIXED HERE (IR-15). (1) The first pass of this audit encoded "
    "pts=1.0 AND two_pm=2.0 AND ftm=1.0 AND three_pm=3.0 at once. That is not either published "
    "representation - it is both of them summed, and it inflated every FanDuel NBA projection by "
    "roughly 2x (an 8-player demo lineup scored 763 points instead of ~300). RGENGY uses the "
    "aggregate representation ('pts') and pins the made-shot keys at 0.0. (2) three_pm was "
    "disputed at 0.0 vs a +1 bonus until FanDuel's own rules page settled it: a made three is "
    "worth 3 total and a made two 2 total, which is exactly pts=1.0 with no separate bonus "
    "(IR-08 has the full resolution). The operator page enumerates no double-double/triple-double "
    "bonus, so those stay 0.0 - now operator-backed rather than merely conservative.",
    {
        "pts": v(1.0, "multi-source-consistent", ["FD_RULES", "RG_NBA_FD_STRATEGY",
                                                  "NBA_OCCUPYFANTASY", "NBA_DFSBUILD"],
                 agreement=5, operator=True,
                 note="1 fantasy point per real point scored. Operator page: 2-pt FG=2 and FT=1, "
                      "which is this representation stated in made-shot terms."),
        "three_pm": v(0.0, "multi-source-consistent", ["FD_RULES", "RG_NBA_FD_STRATEGY",
                                                       "NBA_DFSBUILD", "NBA_OCCUPYFANTASY"],
                      agreement=5, operator=True,
                      note="RESOLVED BY THE OPERATOR PAGE (was 'disputed', IR-08/IR-15). FanDuel "
                           "scores a 3-pt FG at 3 points TOTAL and a 2-pt FG at 2 TOTAL; under "
                           "pts=1.0 a made three already scores 3, so the incremental bonus is 0. "
                           "The old +1-bonus reading describes the same arithmetic in made-shot "
                           "terms, not an additional payment."),
        "two_pm": v(0.0, "not-applicable", ["FD_RULES", "NBA_LINEUPS_2019"], intentionally_zero=True,
                    note="Operator page states 2-pt FG=2 as the basket's total value, which is "
                         "subsumed by pts=1.0."),
        "ftm": v(0.0, "not-applicable", ["FD_RULES", "NBA_LINEUPS_2019"], intentionally_zero=True,
                 note="Operator page states FT=1 as the shot's total value, subsumed by pts=1.0."),
        "reb": v(1.2, "multi-source-consistent", ["FD_RULES", "RG_NBA_FD_STRATEGY",
                                                  "NBA_OCCUPYFANTASY", "NBA_DFSBUILD"],
                 agreement=5, operator=True,
                 note="1.2, versus 1.25 on DraftKings - operator page and every secondary source agree."),
        "ast": v(1.5, "multi-source-consistent", ["FD_RULES", "RG_NBA_FD_STRATEGY",
                                                  "NBA_OCCUPYFANTASY", "NBA_DFSBUILD"],
                 agreement=5, operator=True),
        "stl": v(3.0, "multi-source-consistent", ["FD_RULES", "NBA_OCCUPYFANTASY", "NBA_DFSBUILD",
                                                  "NBA_SPORTINGNEWS_2023"],
                 agreement=4, operator=True,
                 note="RESOLVED BY THE OPERATOR PAGE (was 'disputed'): FanDuel states Steal=3pts. "
                      "The minority 2 reading came from RotoGrinders' own guide and is superseded."),
        "blk": v(3.0, "multi-source-consistent", ["FD_RULES", "NBA_OCCUPYFANTASY", "NBA_DFSBUILD",
                                                  "NBA_SPORTINGNEWS_2023"],
                 agreement=4, operator=True,
                 note="RESOLVED BY THE OPERATOR PAGE: FanDuel states Block=3pts."),
        "to": v(-1.0, "multi-source-consistent", ["FD_RULES", "RG_NBA_FD_STRATEGY",
                                                  "NBA_OCCUPYFANTASY", "NBA_DFSBUILD"],
                agreement=5, operator=True,
                note="Harsher than DraftKings' -0.5; operator page and every source agree."),
        "dd": v(0.0, "multi-source-consistent", ["FD_RULES", "NBA_DFSBUILD", "RG_NBA_FD_STRATEGY"],
                operator=True,
                note="RESOLVED (IR-08): FanDuel's published basketball scoring table enumerates no "
                     "double-double bonus. The zero is now operator-backed, not just conservative."),
        "td": v(0.0, "multi-source-consistent", ["FD_RULES", "NBA_DFSBUILD", "RG_NBA_FD_STRATEGY"],
                operator=True,
                note="Same operator-page absence as 'dd' (IR-08)."),
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
    "PROVISIONAL - single operator-family source. DraftKings' own WNBA scoring page "
    "(pick6.draftkings.com/rules-and-scoring-wnba, retrieved 2026-09-22) publishes Point +1, "
    "Made 3pt +0.5, Rebound +1.25, Assist +1.5, Steal +2, Block +2, Turnover -0.5, "
    "Double-Double +1.5, Triple-Double +3 - identical to the operator-confirmed DraftKings NBA "
    "classic table. CAVEAT: that page is for DraftKings PICK6, a different product from DraftKings "
    "DFS classic, so these values are NOT marked confirmed_by_operator; they are recorded here "
    "because the first pass shipped all zeros, which made WNBA projections impossible, and an "
    "operator-published WNBA table beats an empty one provided it is labelled provisional.",
    "Every value is 'single-source' from a DraftKings property that publishes WNBA scoring for a "
    "DIFFERENT product (Pick6). Treat the totals as provisional until a DraftKings WNBA classic "
    "scoring page is retrieved. The WNBA *roster* templates remain unaudited (L-03) - scoring and "
    "roster provenance are tracked separately.",
    {
        "pts": v(1.0, "single-source", ["DK_PICK6_WNBA"],
                 note="Operator Pick6 page; provisional for DFS classic (see meta)."),
        "three_pm": v(0.5, "single-source", ["DK_PICK6_WNBA"],
                      note="Operator Pick6 page; provisional for DFS classic."),
        "reb": v(1.25, "single-source", ["DK_PICK6_WNBA"],
                 note="Operator Pick6 page; provisional for DFS classic."),
        "ast": v(1.5, "single-source", ["DK_PICK6_WNBA"],
                 note="Operator Pick6 page; provisional for DFS classic."),
        "stl": v(2.0, "single-source", ["DK_PICK6_WNBA"],
                 note="Operator Pick6 page; provisional for DFS classic."),
        "blk": v(2.0, "single-source", ["DK_PICK6_WNBA"],
                 note="Operator Pick6 page; provisional for DFS classic."),
        "to": v(-0.5, "single-source", ["DK_PICK6_WNBA"],
                note="Operator Pick6 page; provisional for DFS classic."),
        "dd": v(1.5, "single-source", ["DK_PICK6_WNBA"],
                note="Max 1 per player. Operator Pick6 page; provisional for DFS classic."),
        "td": v(3.0, "single-source", ["DK_PICK6_WNBA"],
                note="Max 1 per player. Operator Pick6 page; provisional for DFS classic."),
    },
    [SOURCES["DK_PICK6_WNBA"], SOURCES["RG_WNBA_GRID"]],
)

wnba_fd = table(
    "wnba", "fanduel", "Classic (full slate)", 40000,
    "OPERATOR-CONFIRMED (2026-09-22): FanDuel's public rules page (https://www.fanduel.com/rules, "
    "Basketball section - the same section links the WNBA training guide) publishes one basketball "
    "scoring table for NBA and WNBA: 3-pt FG=3, 2-pt FG=2, FT=1, Rebound=1.2, Assist=1.5, "
    "Block=3, Steal=3, Turnover=-1, with no double-double/triple-double bonus. The aggregate "
    "representation (1 point per point scored, no separate 3PM bonus) follows exactly as in the "
    "NBA table.",
    "This table was all zeros / not-audited in the first pass; it is now filled from FanDuel's "
    "own published basketball scoring, which the operator applies to WNBA (the WNBA training "
    "guide hangs off the same rules section). The WNBA *roster* templates remain unaudited "
    "(L-03) - scoring and roster provenance are tracked separately.",
    {
        "pts": v(1.0, "multi-source-consistent", ["FD_RULES", "RG_WNBA_GRID"], operator=True,
                 note="Operator basketball table (2-pt FG=2 / FT=1), WNBA included."),
        "three_pm": v(0.0, "multi-source-consistent", ["FD_RULES", "RG_WNBA_GRID"], operator=True,
                      note="Operator 3-pt FG=3 TOTAL vs 2-pt FG=2 TOTAL => no incremental bonus "
                           "under pts=1.0 (see nba:fanduel)."),
        "two_pm": v(0.0, "not-applicable", ["FD_RULES"], intentionally_zero=True,
                    note="Made-shot value subsumed by pts=1.0."),
        "ftm": v(0.0, "not-applicable", ["FD_RULES"], intentionally_zero=True,
                 note="Made-shot value subsumed by pts=1.0."),
        "reb": v(1.2, "multi-source-consistent", ["FD_RULES", "RG_WNBA_GRID"], operator=True),
        "ast": v(1.5, "multi-source-consistent", ["FD_RULES", "RG_WNBA_GRID"], operator=True),
        "stl": v(3.0, "multi-source-consistent", ["FD_RULES"], operator=True),
        "blk": v(3.0, "multi-source-consistent", ["FD_RULES"], operator=True),
        "to": v(-1.0, "multi-source-consistent", ["FD_RULES"], operator=True),
        "dd": v(0.0, "multi-source-consistent", ["FD_RULES"], operator=True,
                note="No DD bonus in the operator's enumerated basketball scoring (IR-08)."),
        "td": v(0.0, "multi-source-consistent", ["FD_RULES"], operator=True,
                note="No TD bonus in the operator's enumerated basketball scoring (IR-08)."),
    },
    [SOURCES["FD_RULES"], SOURCES["RG_WNBA_GRID"]],
)

# ---------------------------------------------------------------------------
# NHL - two contradictory DraftKings tables exist.  This is a genuine,
# important irregularity and it is flagged rather than papered over.
# ---------------------------------------------------------------------------
NHL_CONSULTED = [SOURCES["DK_NETWORK_NHL"], SOURCES["NHL_FTN_2024"],
                 SOURCES["NHL_DAILYFACEOFF"], SOURCES["NHL_REDDIT_2014"],
                 SOURCES["FD_RULES"], SOURCES["NHL_OCCUPYFANTASY"]]

_DKN = ("DraftKings Network (dknetwork.draftkings.com, DraftKings' own editorial property) published "
        "the identical table on 2025-09-30; the second audit pass (2026-09-22) re-retrieved it and "
        "operator-confirmed every value below against it.")

nhl_dk = table(
    "nhl", "draftkings", "Classic (full slate)", 50000,
    "Two mutually exclusive DraftKings NHL scoring tables were retrieved in pass 1: the 2014/2016 "
    "table (Goal 3, Assist 2, SOG 0.5, BLK 0.5, Goalie Win 3, Save 0.2, GA -1, SO 2) and the 2024 "
    "FTN table (Goal 8.5, Assist 5, SOG 1.5, BLK 1.3, Goalie Win 6, Save 0.7, GA -3.5, SO 4, OTL 2, "
    "plus threshold bonuses). In pass 2 the 2024 scheme was independently confirmed by DraftKings' "
    "own network site, so the conflict is RESOLVED and the values are marked multi-source-consistent "
    "with the historical table recorded as superseded.",
    "IRREGULARITY IR-09 (RESOLVED; its register text was corrected in the third pass - the "
    "operator article states Goal = +8.5, and 8.5 is what has shipped all along). " + _DKN + " "
    "IMPORTANT SCORING INTERACTION: a goal also "
    "counts as a shot on goal, so a goal is worth 8.5 + 1.5 = 10.0 points. DraftKings Network states "
    "this explicitly with a worked example ('Center: +8.5 Pts (Goal) +1.5 (Shot on Goal) = 10 Pts'). "
    "The 'sog' projection fed to this table must therefore INCLUDE goals; there is no separate "
    "goal-shot coefficient. Pass 1 wrongly added a 'sog_goal' key for this, which would have "
    "double-counted every goal - it is removed (IR-14).",
    {
        "g": v(8.5, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, operator=True,
               note="Operator article: 'Goal +8.5 Pts'. The 2014-era table said 3."),
        "a": v(5.0, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, operator=True,
               note="Operator article: 'Assist +5 Pts'. The 2014-era table said 2."),
        "sog": v(1.5, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, operator=True,
               note="Operator article: 'Shot on Goal +1.5 Pts'. A GOAL ALSO COUNTS AS A SHOT ON "
                    "GOAL, so a goal scores 8.5 + 1.5 = 10.0 - the operator's own worked example."),
        "blk": v(1.3, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, operator=True,
               note="Operator article: 'Blocked Shot +1.3 Pts'. The 2014-era table said 0.5."),
        "shp": v(2.0, "multi-source-consistent", ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014"],
                 agreement=2, operator=True,
                 note="Operator article: 'Short Handed Point Bonus (Goal/Assist) +2 Pts'."),
        "shootout_goal": v(1.5, "single-source", ["DK_NETWORK_NHL"], operator=True,
                           note="Operator article: 'Shootout Goal +1.5 Pts'. Renamed "
                                "from 'sog_goal' in pass 2: the old name suggested 'a shot on goal "
                                "that is a goal', which would double count every goal (a goal already "
                                "scores under both 'g' and 'sog'). IR-14. Not modelled by the hockey "
                                "engine because shootout results are not in the box-score feeds."),
        "ppp": v(0.0, "not-applicable", ["DK_NETWORK_NHL"], intentionally_zero=True, operator=True,
                 note="DraftKings has NO power-play point bonus (its enumerated table lists none); "
                      "the +2 is for SHORT-HANDED points only ('shp'). FanDuel does pay +0.5 per "
                      "power-play point, so the key exists in the shared stat vocabulary."),
        "hat_trick": v(3.0, "multi-source-consistent", ["DK_NETWORK_NHL", "NHL_FTN_2024"],
                       agreement=2, operator=True,
                       note="Operator article: 'Hat Trick Bonus +3 Pts'. "
                            "The 2014-era table said 1.5 and is superseded."),
        "g5_sog": v(3.0, "multi-source-consistent", ["DK_NETWORK_NHL", "NHL_FTN_2024"],
                    agreement=2, operator=True,
                    note="Operator article: '5+ Shots +3 Pts'."),
        "g3_blk": v(3.0, "multi-source-consistent", ["DK_NETWORK_NHL", "NHL_FTN_2024"],
                    agreement=2, operator=True,
                    note="Operator article: '3+ Blocked Shots +3 Pts'."),
        "g3_pts": v(3.0, "multi-source-consistent", ["DK_NETWORK_NHL", "NHL_FTN_2024"],
                    agreement=2, operator=True,
                    note="Operator article: '3+ Points +3 Pts'."),
        "win_goalie": v(6.0, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, operator=True,
               note="Operator article: goalie 'Win +6 Pts'. The 2014-era table said 3."),
        "sv": v(0.7, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, operator=True,
               note="Operator article: goalie 'Save +0.7 Pts'. The 2014-era table said 0.2."),
        "ga": v(-3.5, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, operator=True,
               note="Operator article: goalie 'Goal Against -3.5 Pts'. The 2014-era table said -1."),
        "so": v(4.0, "multi-source-consistent",
               ["DK_NETWORK_NHL", "NHL_FTN_2024", "NHL_REDDIT_2014", "NHL_DAILYFACEOFF"],
               agreement=2, operator=True,
               note="Operator article: goalie 'Shutout Bonus +4 Pts', with the note that shootout "
                    "goals do not prevent a shutout. The 2014-era table said 2."),
        "otl": v(2.0, "single-source", ["DK_NETWORK_NHL"], operator=True,
                 note="Operator article: goalie 'Overtime Loss +2 Pts'."),
        "sv35": v(3.0, "single-source", ["DK_NETWORK_NHL"], operator=True,
                  note="Operator article: goalie '35+ Saves +3 Pts'."),
    },
    NHL_CONSULTED,
)

nhl_fd = table(
    "nhl", "fanduel", "Classic (full slate)", 40000,
    "OPERATOR-CONFIRMED (2026-09-22): FanDuel's public rules page (https://www.fanduel.com/rules, "
    "Hockey section, retrieved that day) states Goals=12, Assists=8, Shots on Goal=1.6, Short "
    "Handed Points=+2, Power Play Points=+0.5, Blocked Shots=1.6; goalies: Wins=12, Goals "
    "Against=-4, Saves=0.8, Shutouts=8. Every value matches FTN Fantasy's 2024 table exactly, so "
    "the single-source weakness is retired. The operator page also states that NO points are "
    "awarded for goals or saves during shootouts.",
    "IRREGULARITY IR-10 (RESOLVED): every non-zero value is now operator-confirmed from "
    "fanduel.com/rules. The same page contradicts an earlier Reddit claim that FanDuel scores "
    "plus/minus: no plus/minus stat appears anywhere in the operator's enumerated hockey scoring, "
    "so `plus_minus` stays 0.0 / not-audited with operator absence as the recorded evidence - "
    "scoring it would now be the change that requires proof.",
    {
        "g": v(12.0, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
               note="Operator page: 'Goals = 12pts'."),
        "a": v(8.0, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
               note="Operator page: 'Assists = 8pts'."),
        "sog": v(1.6, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
                 note="Operator page: 'Shots on Goal = 1.6pts'."),
        "blk": v(1.6, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
                 note="Operator page: 'Blocked Shots = 1.6pts'."),
        "shp": v(2.0, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
                 note="Operator page: 'Short Handed Points = +2pts'."),
        "ppp": v(0.5, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
                 note="Operator page: 'Power Play Points = +0.5pts' (DraftKings pays none)."),
        "win_goalie": v(12.0, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
                        note="Operator page: goalies 'Wins = 12pts'."),
        "so": v(8.0, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
                note="Operator page: goalies 'Shutouts = 8pts'."),
        "sv": v(0.8, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
                note="Operator page: goalies 'Saves = 0.8pts'."),
        "ga": v(-4.0, "multi-source-consistent", ["FD_RULES", "NHL_FTN_2024"], operator=True,
                note="Operator page: goalies 'Goals Against = -4pts'."),
        "plus_minus": v(0.0, "not-audited", [],
                        note="ABSENT from FanDuel's own published hockey scoring table (checked "
                             "2026-09-22, IR-10). An earlier Reddit claim that FanDuel scores +/- "
                             "is unconfirmed by the operator page. Left at 0 and flagged."),
    },
    NHL_CONSULTED,
)

# ---------------------------------------------------------------------------
# NFL - re-audited in pass 2 with 2026 sources.  Pass 1 had NO source for any
# NFL value and marked everything 'not-audited'; it also had the 100/300-yard
# bonuses on the wrong site and gave DraftKings kicker coefficients it cannot
# use (DraftKings' NFL classic roster has no kicker slot).
# ---------------------------------------------------------------------------
NFL_CONSULTED = [SOURCES["DK_NET_NFL_2025"], SOURCES["FD_RULES"], SOURCES["RG_NFL_GRID"],
                 SOURCES["STOKASTIC_RG_COMPARE"],
                 SOURCES["NFL_FTA_2026"], SOURCES["NFL_OCCUPYFANTASY_2026"],
                 SOURCES["NFL_FANTASYFOOTBALLERS_2026"], SOURCES["NFL_SPORTSBETTINGDIME_2026"]]

# occupyfantasy (2026-09-10) states the shared core for all sites:
#   "Award 1 point per 25 passing yards, 1 point per 10 yards rushing,
#    4 points per passing TD, and 6 points per rushing/receiving TD"
# 1 per 25 yards == 0.04 per yard; 1 per 10 yards == 0.1 per yard.
_YD_SRC = ["DK_NET_NFL_2025", "NFL_OCCUPYFANTASY_2026", "NFL_FTA_2026"]
_yd = ("OPERATOR-CONFIRMED for DraftKings by its own NFL DFS 101 article (dknetwork.draftkings.com, "
       "2025-08-27, retrieved 2026-09-22): 25 Passing Yards +1 Pt, 10 Rushing Yards +1 Pt, "
       "10 Receiving Yards +1 Pt, Passing TD +4, Rushing/Receiving TD +6. Corroborated for both "
       "sites by occupyfantasy (2026-09-10): '1 point per 25 passing yards, 1 point per 10 yards "
       "rushing, 4 points per passing TD, and 6 points per rushing/receiving TD' - identical on "
       "both sites. 1 per 25 yards = 0.04 per yard; 1 per 10 yards = 0.1 per yard.")

nfl_dk = table(
    "nfl", "draftkings", "Classic (full slate)", 50000,
    "Re-audited in pass 2 against four 2026 sources, then OPERATOR-CONFIRMED in the second audit "
    "pass for the offensive scoring: DraftKings' own NFL DFS 101 article (dknetwork.draftkings.com, "
    "2025-08-27, retrieved 2026-09-22) lists Passing TD +4, 25 passing yards +1, 300+ yard passing "
    "game +3, Interception -1, Rushing TD +6, 10 rushing yards +1, 100+ yard rushing game +3, "
    "Receiving TD +6, 10 receiving yards +1, 100+ yard receiving game +3, Reception +1, "
    "Punt/Kickoff/FG Return TD +6, Fumble Lost -1, 2-pt Conversion +2, Offensive Fumble Recovery "
    "TD +6. Roster is QB, 2 RB, 3 WR, TE, FLEX(RB/WR/TE), DST = 9 slots with NO kicker, "
    "corroborated by a real published DraftKings lineup that totals exactly $50,000 "
    "(sportsbettingdime, 2026-09-19). Because no kicker can be rostered, all kicker coefficients "
    "are pinned at 0.",
    "TWO PASS-1 ERRORS FIXED (IR-18). (1) The 100-yard rushing / 100-yard receiving / 300-yard "
    "passing bonuses were assigned to FanDuel and set to 0 for DraftKings; the operator pages now "
    "confirm both operators score them at 3.0. (2) DraftKings was given field-goal and extra-point "
    "coefficients even though its classic roster has no kicker slot; those are now 0. "
    "RotoGrinders' NFL grid publishes 100RU / 100RE / 300PA columns, which corroborates that these "
    "bonuses are a projection target on at least one major site. The DST block remains "
    "'not-audited': no DraftKings operator document for team defence was retrieved "
    "(limitation L-04).",
    {
        "pa_yds": v(0.04, "multi-source-consistent", _YD_SRC, operator=True, note=_yd),
        "pa_td": v(4.0, "multi-source-consistent", _YD_SRC, operator=True, note=_yd),
        "pa_int": v(-1.0, "multi-source-consistent", ["DK_NET_NFL_2025", "NFL_OCCUPYFANTASY_2026"],
                    operator=True,
                    note="Operator article: 'Interception (thrown) -1 Pt'."),
        "pa_cmp": v(0.0, "not-applicable", [], intentionally_zero=True,
                    note="Neither site pays per completion."),
        "ru_yds": v(0.1, "multi-source-consistent", _YD_SRC, operator=True, note=_yd),
        "ru_td": v(6.0, "multi-source-consistent", _YD_SRC, operator=True, note=_yd),
        "rec": v(1.0, "multi-source-consistent", ["DK_NET_NFL_2025", "NFL_FTA_2026",
                                                  "NFL_OCCUPYFANTASY_2026",
                                                  "NFL_FANTASYFOOTBALLERS_2026"], agreement=4,
                 operator=True,
                 note="Operator article: 'Reception +1 Pt' (full PPR). fantasyteamadvisors "
                      "(2026-08-05) corroborates: 'DraftKings uses full-point PPR scoring'."),
        "rec_yds": v(0.1, "multi-source-consistent", _YD_SRC, operator=True, note=_yd),
        "rec_td": v(6.0, "multi-source-consistent", _YD_SRC, operator=True, note=_yd),
        "two_pt": v(2.0, "multi-source-consistent", ["DK_NET_NFL_2025", "NFL_OCCUPYFANTASY_2026"],
                    operator=True,
                    note="Operator article: '2 Pt Conversion (Pass, Run, or Catch) +2 Pts'."),
        "fum_lost": v(-1.0, "multi-source-consistent", ["DK_NET_NFL_2025",
                                                        "NFL_FANTASYFOOTBALLERS_2026",
                                                        "NFL_OCCUPYFANTASY_2026"], agreement=3,
                      operator=True,
                      note="Operator article: 'Fumble Lost -1 Pt' (FanDuel is -2)."),
        "100ru": v(3.0, "multi-source-consistent", ["DK_NET_NFL_2025", "NFL_FANTASYFOOTBALLERS_2026",
                                                    "RG_NFL_GRID"], agreement=3, operator=True,
                   note="Operator article: '100+ Yard Rushing Game +3 Pts'. Also corroborated by "
                        "the 100RU column on RotoGrinders' NFL grid."),
        "100rec": v(3.0, "multi-source-consistent", ["DK_NET_NFL_2025", "NFL_FANTASYFOOTBALLERS_2026",
                                                     "RG_NFL_GRID"], agreement=3, operator=True,
                    note="Operator article: '100+ Yard Receiving Game +3 Pts'; corroborated by the "
                         "100RE grid column."),
        "300pa": v(3.0, "multi-source-consistent", ["DK_NET_NFL_2025", "NFL_FANTASYFOOTBALLERS_2026",
                                                    "RG_NFL_GRID"], agreement=3, operator=True,
                   note="Operator article: '300+ Yard Passing Game +3 Pts'; corroborated by the "
                        "300PA grid column."),
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
        "dst_sack": v(1.0, "not-audited", ["DFS101_FOOTBALL"],
                      note="DraftKings team-defence scoring was NOT retrieved from any OPERATOR "
                           "source. A secondary comparison table (dailyfantasysports101) shows DK "
                           "DST tiers identical to FanDuel's, so the convention values are kept as "
                           "'not-audited' secondary estimates; the pipeline excludes them from "
                           "published totals under --strict. See limitation L-04."),
        "dst_int": v(2.0, "not-audited", ["DFS101_FOOTBALL"], note="See 'dst_sack'."),
        "dst_fum_rec": v(2.0, "not-audited", ["DFS101_FOOTBALL"], note="See 'dst_sack'."),
        "dst_td": v(2.0, "not-audited", ["DFS101_FOOTBALL"], note="See 'dst_sack'."),
        "dst_safety": v(2.0, "not-audited", ["DFS101_FOOTBALL"], note="See 'dst_sack'."),
        "dst_block": v(2.0, "not-audited", ["DFS101_FOOTBALL"], note="See 'dst_sack'."),
        "dst_pts_allowed": v(0.0, "not-audited", [], intentionally_zero=True,
                            note="GAP: both sites also score team defence on points allowed (tiered). "
                                 "FanDuel's tier table is now operator-documented (see the FanDuel "
                                 "table); no DraftKings operator tier table was retrieved, and the "
                                 "engine does not yet model tiers. See limitation L-04."),
    },
    NFL_CONSULTED,
)

nfl_fd = table(
    "nfl", "fanduel", "Classic (full slate)", 60000,
    "OPERATOR-CONFIRMED (2026-09-22): FanDuel's public rules page (https://www.fanduel.com/rules, "
    "Football section, retrieved that day) was retrieved and every offensive and defensive value "
    "in this table is taken from it: Reception 0.5, Receiving/Rushing Yards 0.1 per yard, "
    "Passing Yards 0.04 per yard, all TDs 6 (pass/rush/receive/return), Passing TD 4, "
    "Interception -1, Fumble -2, 2-pt Conversion 2, bonuses 100+ receiving / 100+ rushing / 300+ "
    "passing = 3, field goals 3/4/5 by tier, extra point 1; defence: sack 1, fumble recovered 2, "
    "interception 2, safety 2, blocked punt 2, kick/punt return TD 6, extra-point return 2, and "
    "the exact points-allowed tiers 10/7/4/1/0/-1/-4 with FanDuel's own formula for points "
    "allowed. Roster is QB, 2 RB, 3 WR, TE, FLEX(RB/WR/TE/K), DST = 9 slots; the kicker is "
    "reachable through the flex, which is why FanDuel carries kicker coefficients and DraftKings "
    "does not. Flex eligibility itself is disputed between two 2026 sources (IR-16).",
    "IR-18 REVERSED A SECOND TIME: pass 2 set these bonuses to 0.0 on the strength of two 2026 "
    "secondary sources; FanDuel's own rules page (retrieved 2026-09-22) awards +3 for each of "
    "them, so both operators score the yardage milestones. The per-event DST coefficients are "
    "also operator-confirmed now; the tiered points-allowed scoring stays at 0.0 only because "
    "the engine does not yet model tiers - the operator's tier table is preserved verbatim under "
    "`operator_tier_tables.dst_points_allowed` (L-04).",
    {
        "pa_yds": v(0.04, "multi-source-consistent", ["FD_RULES"] + _YD_SRC, operator=True,
                    note="Operator page: 'Passing Yards = 0.04 Points'."),
        "pa_td": v(4.0, "multi-source-consistent", ["FD_RULES"] + _YD_SRC, operator=True,
                   note="Operator page: 'Passing Touchdown = 4 Points'."),
        "pa_int": v(-1.0, "multi-source-consistent", ["FD_RULES", "NFL_OCCUPYFANTASY_2026"],
                    operator=True, note="Operator page: 'Interception Thrown = -1 Points'."),
        "pa_cmp": v(0.0, "not-applicable", [], intentionally_zero=True,
                    note="Neither site pays per completion."),
        "ru_yds": v(0.1, "multi-source-consistent", ["FD_RULES"] + _YD_SRC, operator=True,
                    note="Operator page: 'Rushing Yards = 0.1 Point per Yard'."),
        "ru_td": v(6.0, "multi-source-consistent", ["FD_RULES"] + _YD_SRC, operator=True,
                   note="Operator page: 'Rushing Touchdown = 6 Points'."),
        "rec": v(0.5, "multi-source-consistent", ["FD_RULES", "NFL_FTA_2026",
                                                  "NFL_OCCUPYFANTASY_2026",
                                                  "NFL_FANTASYFOOTBALLERS_2026"], agreement=4,
                 operator=True,
                 note="Operator page: 'Points per Reception = 0.5 Points' (half PPR)."),
        "rec_yds": v(0.1, "multi-source-consistent", ["FD_RULES"] + _YD_SRC, operator=True,
                     note="Operator page: 'Receiving Yards = 0.1 Point per Yard'."),
        "rec_td": v(6.0, "multi-source-consistent", ["FD_RULES"] + _YD_SRC, operator=True,
                    note="Operator page: 'Receiving Touchdown = 6 Points'."),
        "two_pt": v(2.0, "multi-source-consistent", ["FD_RULES", "NFL_OCCUPYFANTASY_2026"],
                    operator=True,
                    note="Operator page: 'Two-Point Conversion = 2 Points' (pass, run or catch)."),
        "fum_lost": v(-2.0, "multi-source-consistent", ["FD_RULES", "NFL_FANTASYFOOTBALLERS_2026",
                                                        "NFL_OCCUPYFANTASY_2026"], agreement=3,
                      operator=True,
                      note="Operator page: 'Fumble = -2 Points' (DraftKings is -1)."),
        "100ru": v(3.0, "multi-source-consistent", ["FD_RULES", "NFL_FANTASYFOOTBALLERS_2026",
                                                    "RG_NFL_GRID"], agreement=3, operator=True,
                   note="REVERSED AGAIN BY THE OPERATOR PAGE (IR-18): FanDuel states '100+ Rushing "
                        "Yard Bonus = 3 Points'. The pass-2 zero came from secondary sources that "
                        "contradict the operator."),
        "100rec": v(3.0, "multi-source-consistent", ["FD_RULES", "NFL_FANTASYFOOTBALLERS_2026",
                                                     "RG_NFL_GRID"], agreement=3, operator=True,
                    note="REVERSED AGAIN BY THE OPERATOR PAGE (IR-18): FanDuel states '100+ "
                         "Receiving Yard Bonus = 3 Points'."),
        "300pa": v(3.0, "multi-source-consistent", ["FD_RULES", "NFL_FANTASYFOOTBALLERS_2026",
                                                    "RG_NFL_GRID"], agreement=3, operator=True,
                   note="REVERSED AGAIN BY THE OPERATOR PAGE (IR-18): FanDuel states '300+ Passing "
                        "Yard Bonus = 3 Points'."),
        "fg_0_39": v(3.0, "multi-source-consistent", ["FD_RULES", "NFL_FANTASYFOOTBALLERS_2026"],
                     operator=True,
                     note="Operator page: '0-39 Yard Field Goal = 3 Points'."),
        "fg_40_49": v(4.0, "multi-source-consistent", ["FD_RULES", "NFL_FANTASYFOOTBALLERS_2026"],
                      operator=True,
                      note="Operator page: '40-49 Yard Field Goal = 4 Points'."),
        "fg_50p": v(5.0, "multi-source-consistent", ["FD_RULES", "NFL_FANTASYFOOTBALLERS_2026"],
                    operator=True,
                    note="Operator page: '50+ Yard Field Goal = 5 Points'."),
        "pat": v(1.0, "multi-source-consistent", ["FD_RULES", "NFL_FANTASYFOOTBALLERS_2026"],
                 operator=True,
                 note="Operator page: 'Extra-Point Conversions = 1 Point'."),
        "dst_sack": v(1.0, "multi-source-consistent", ["FD_RULES", "DFS101_FOOTBALL"], operator=True,
                      note="Operator page (Defense column): 'Sacks = 1pt'."),
        "dst_int": v(2.0, "multi-source-consistent", ["FD_RULES", "DFS101_FOOTBALL"], operator=True,
                     note="Operator page: 'Interception = 2 Points'."),
        "dst_fum_rec": v(2.0, "multi-source-consistent", ["FD_RULES", "DFS101_FOOTBALL"],
                         operator=True,
                         note="Operator page: 'Fumble Recovered = 2 Points'."),
        "dst_td": v(0.0, "not-audited", ["DFS101_FOOTBALL"],
                    note="NO RETRIEVED VALUE - changed from an unaudited 2.0 to a documented 0.0 "
                         "in the second audit pass. FanDuel's rules page lists kick/punt return "
                         "TDs at 6 (defence) but no generic defensive-touchdown value, and the "
                         "secondary comparison tables list none either. The interception and "
                         "fumble-recovery events above ARE scored, so only the TD component is "
                         "missing; DST totals understate until a source is retrieved. See L-04."),
        "dst_safety": v(2.0, "multi-source-consistent", ["FD_RULES", "DFS101_FOOTBALL"],
                        operator=True,
                        note="Operator page: 'Safety = 2 Points'."),
        "dst_block": v(2.0, "multi-source-consistent", ["FD_RULES", "DFS101_FOOTBALL"],
                       operator=True,
                       note="Operator page: 'Blocked Punt = 2 Points'."),
        "dst_pts_allowed": v(0.0, "not-applicable", ["FD_RULES"], intentionally_zero=True,
                            note="TIERS NOW OPERATOR-DOCUMENTED (was 'no tier table retrieved'): "
                                 "FanDuel awards 10/7/4/1/0/-1/-4 for 0 / 1-6 / 7-13 / 14-20 / "
                                 "21-27 / 28-34 / 35+ points allowed, computed by its published "
                                 "formula. The full table is stored under "
                                 "`operator_tier_tables.dst_points_allowed`. The coefficient stays "
                                 "0.0 only because the engine models points allowed as a single "
                                 "expected value rather than a tier lookup (L-04, roadmap)."),
    },
    NFL_CONSULTED,
)

# FanDuel's own points-allowed tiers, transcribed verbatim from
# https://www.fanduel.com/rules (Football > Defense, retrieved 2026-09-22).
# Stored so no future pass has to re-retrieve it. Format: [min_allowed,
# max_allowed_inclusive, points] with None = unbounded.
_FD_DST_TIERS = [
    [0, 0, 10.0], [1, 6, 7.0], [7, 13, 4.0], [14, 20, 1.0],
    [21, 27, 0.0], [28, 34, -1.0], [35, None, -4.0],
]
nfl_fd["operator_tier_tables"] = {
    "dst_points_allowed": {
        "source": SOURCES["FD_RULES"],
        "retrieved": AUDIT_DATE,
        "formula_note": ("Operator page: for FanDuel defensive scoring, points allowed are "
                         "calculated as 6*(Rushing TD + Receiving TD + own fumbles recovered for "
                         "TD) + 2*(two-point conversions) + extra points + 3*(field goals). "
                         "Reduced tiers apply to 2nd-Half and 4th-Quarter-only slates."),
        "tiers": _FD_DST_TIERS,
    }
}


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
