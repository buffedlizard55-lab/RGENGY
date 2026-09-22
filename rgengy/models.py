"""Core data structures shared by every engine.

The shapes here are deliberately close to the column schema that
RotoGrinders publishes on its ``/projected-stats/{sport}`` grids, because that
schema *is* the specification we are trying to match.  The exact columns
observed on 2026-09-22 are transcribed in ``docs/04-data-schema-catalog.md``
and mirrored by :data:`RG_GRID_COLUMNS` below.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Observed RotoGrinders grid columns (verified 2026-09-22, see docs/04-*.md)
# ---------------------------------------------------------------------------

RG_GRID_COLUMNS: Dict[str, List[str]] = {
    "mlb": [
        "PLAYER", "SALARY", "POS", "TEAM", "OPP", "PA", "1B", "2B", "3B", "HR",
        "RBI", "R", "SB", "BB", "IP", "BBA", "K", "W", "ER", "HA", "HBP", "QS",
        "FPTS", "FPTS/$", "H", "PARK", "BASES", "OUTS", "BATK", "HRRBI", "PC",
        "REFTM", "REFOPP", "OBFPTS", "WIND", "TEMP", "TEMPDESC", "ORDER",
        "UNDERDOG", "PRIZEPICKS", "FLOOR", "CEIL", "POWN", "OPTO", "SMASH",
        "TOPVAL", "TEAMOWN", "DIFFERENCE", "LEV",
    ],
    "nfl": [
        "PLAYER", "SALARY", "POS", "TEAM", "OPP", "INJURY", "PAATT", "CMP",
        "PAYDS", "PATD", "INT", "RUATT", "RUYDS", "RUTD", "TAR", "REC", "REYDS",
        "RETD", "100RU", "100RE", "300PA", "FPTS", "FPTS/$", "OBFPTS", "PP",
        "UD", "TOTYD", "TOTTD", "PARUYD", "PARUTD", "RUREYD", "RURETD", "KPTS",
        "FLOOR", "CEIL", "OPTO", "POWN", "SLATE",
    ],
    "wnba": [
        "PLAYER", "SALARY", "POS", "TEAM", "OPP", "TEAMNAME", "STATUS", "SPREAD",
        "O/U", "TOTAL", "MINUTES", "PTS", "REB", "AST", "3PM", "TO", "STL",
        "BLK", "P-A", "P-R", "P-R-A", "B-S", "R-A", "UD", "PP", "FPTS",
        "FPTS/$", "RANGE", "FLOOR", "CEIL", "POWN", "POSDRK", "POSFAN",
    ],
}

SPORTS_COVERED_BY_RG = [
    "nfl", "nba", "mlb", "nhl", "pga", "wnba", "mma", "nascar",
    "cfb", "cbb", "soccer", "tennis", "f1", "lol", "cs2",
]


def _clean(x: Optional[float], nd: int = 2) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return round(float(x), nd)


@dataclass
class Odds:
    """A market line.  ``provider`` records who set it."""

    provider: Optional[str] = None
    spread: Optional[float] = None          # home spread, negative = home favourite
    over_under: Optional[float] = None
    home_ml: Optional[int] = None
    away_ml: Optional[int] = None
    details: Optional[str] = None           # e.g. "BUF -6.5"
    source: Optional[str] = None            # endpoint the line came from

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Weather:
    """Game-time weather, reconstructed from the NWS gridpoint feed.

    Field names mirror the NWS ``forecastGridData`` properties so the mapping
    is 1:1 and auditable.
    """

    temperature_f: Optional[float] = None
    temperature_c: Optional[float] = None
    wind_speed_mph: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    pressure_mb: Optional[float] = None
    relative_humidity_pct: Optional[float] = None
    precip_prob_pct: Optional[float] = None
    sky_cover_pct: Optional[float] = None
    air_density_kg_m3: Optional[float] = None
    roof: Optional[str] = None              # "open" | "closed" | "retractable"
    source: Optional[str] = None
    # Human-readable descriptor, mirroring RG's TEMPDESC / WIND columns.
    temp_desc: Optional[str] = None
    wind_desc: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Game:
    """One contest on a slate."""

    sport: str
    game_id: str
    starts_utc: str
    home_team: str
    away_team: str
    home_id: Optional[str] = None
    away_id: Optional[str] = None
    venue: Optional[str] = None
    venue_id: Optional[str] = None
    venue_lat: Optional[float] = None
    venue_lon: Optional[float] = None
    league: Optional[str] = None
    status: Optional[str] = None
    odds: Optional[Odds] = None
    weather: Optional[Weather] = None
    home_implied_total: Optional[float] = None
    away_implied_total: Optional[float] = None
    implied_total_method: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    provenance: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class Player:
    """A roster entry with whatever inputs the engine managed to gather."""

    sport: str
    player_id: str
    name: str
    team: str
    opp: Optional[str] = None
    positions: List[str] = field(default_factory=list)
    salary: Optional[float] = None
    site: Optional[str] = None
    game_id: Optional[str] = None
    status: Optional[str] = None            # injury / scratch / lineup info
    stats: Dict[str, float] = field(default_factory=dict)   # raw inputs
    projected: Dict[str, float] = field(default_factory=dict)  # stat projections
    fpts: Dict[str, float] = field(default_factory=dict)    # per-site fantasy points
    floor: Optional[float] = None
    ceil: Optional[float] = None
    pown: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    provenance: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # -- convenience -------------------------------------------------------
    @property
    def primary_fpts(self) -> Optional[float]:
        if not self.fpts:
            return None
        # Prefer DraftKings, then FanDuel, then whatever exists.
        for key in ("draftkings", "fanduel", "yahoo"):
            if key in self.fpts:
                return self.fpts[key]
        return next(iter(self.fpts.values()))

    def value(self, site: str = "draftkings") -> float:
        """FPTS per $1000 of salary - the ``FPTS/$`` column normalised."""
        pts = self.fpts.get(site)
        if pts is None or not self.salary:
            return 0.0
        return pts / (self.salary / 1000.0)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["projected"] = {k: _clean(v) for k, v in self.projected.items()}
        d["fpts"] = {k: _clean(v) for k, v in self.fpts.items()}
        d["floor"] = _clean(self.floor)
        d["ceil"] = _clean(self.ceil)
        d["pown"] = _clean(self.pown, 4)
        return d


@dataclass
class Slate:
    """Everything the pipeline produced for one sport/day/site."""

    sport: str
    date: str
    site: str = "draftkings"
    games: List[Game] = field(default_factory=list)
    players: List[Player] = field(default_factory=list)
    lineups: List[Dict[str, Any]] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sport": self.sport,
            "date": self.date,
            "site": self.site,
            "meta": self.meta,
            "games": [g.to_dict() for g in self.games],
            "players": [p.to_dict() for p in self.players],
            "lineups": self.lineups,
        }

    def to_json(self, **kw: Any) -> str:
        return json.dumps(self.to_dict(), **kw)


@dataclass
class RosterRule:
    """One roster slot, e.g. ``2 x OF`` or ``1 x UTIL(any hitter)``."""

    label: str
    count: int
    eligible: List[str]
    salary_group: Optional[str] = None


ROSTER_PROVENANCE = {
    "mlb:draftkings": {
        "salary_cap": 50000,
        "slots": [
            RosterRule("P", 2, ["P", "SP", "RP"]),
            RosterRule("C/1B", 1, ["C", "1B"]),
            RosterRule("2B", 1, ["2B"]),
            RosterRule("3B", 1, ["3B"]),
            RosterRule("SS", 1, ["SS"]),
            RosterRule("OF", 3, ["OF", "LF", "CF", "RF"]),
            RosterRule("UTIL", 1, ["C", "1B", "2B", "3B", "SS", "OF", "LF", "CF", "RF"]),
        ],
        "n_players": 10,
        "verification_status": "single-source",
        "sources": ["https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/"],
        "note": ("DraftKings' MLB classic roster combines catcher and first base into one "
                 "C/1B slot. An earlier draft of this file listed separate C and 1B slots and "
                 "therefore required 11 players - an off-by-one that makes every DK MLB lineup "
                 "illegal. See IR-17."),
    },
    "mlb:fanduel": {
        "salary_cap": 35000,
        "slots": [
            RosterRule("P", 1, ["P", "SP", "RP"]),
            RosterRule("C/1B", 1, ["C", "1B"]),
            RosterRule("2B", 1, ["2B"]),
            RosterRule("3B", 1, ["3B"]),
            RosterRule("SS", 1, ["SS"]),
            RosterRule("OF", 3, ["OF", "LF", "CF", "RF"]),
            RosterRule("UTIL", 1, ["C", "1B", "2B", "3B", "SS", "OF", "LF", "CF", "RF"]),
        ],
        "n_players": 9,
        "verification_status": "single-source",
        "sources": ["https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/"],
        "note": "One pitcher only, versus two on DraftKings - the single biggest MLB site difference.",
    },
    "nba:draftkings": {
        "salary_cap": 50000,
        "slots": [
            RosterRule("PG", 1, ["PG"]),
            RosterRule("SG", 1, ["SG"]),
            RosterRule("G", 1, ["PG", "SG"]),
            RosterRule("SF", 1, ["SF"]),
            RosterRule("PF", 1, ["PF"]),
            RosterRule("F", 1, ["SF", "PF"]),
            RosterRule("C", 1, ["C"]),
            RosterRule("UTIL", 1, ["PG", "SG", "SF", "PF", "C"]),
        ],
        "n_players": 8,
        "verification_status": "multi-source-consistent",
        "agreement": 2,
        "sources": [
            "https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/",
            "https://dfsbuild.com/dfs-guide/nba-dfs-guide/",
        ],
        "note": ("'Requires just 1 player per position with an extra spot for Guard (PG/SG), "
                 "Forward (SF/PF), and Utility (any position)' - occupyfantasy, 2025-06-05."),
    },
    "nba:fanduel": {
        "salary_cap": 60000,
        "slots": [
            RosterRule("PG", 2, ["PG"]),
            RosterRule("SG", 2, ["SG"]),
            RosterRule("SF", 2, ["SF"]),
            RosterRule("PF", 2, ["PF"]),
            RosterRule("C", 1, ["C"]),
        ],
        "n_players": 9,
        "verification_status": "multi-source-consistent",
        "agreement": 3,
        "sources": [
            "https://rotogrinders.com/articles/fanduel-nba-strategy-239702",
            "https://occupyfantasy.com/nba-dfs-strategy-guide-draftkings-fanduel/",
            "https://fanscout.pro/nba-fanduel-optimizer",
        ],
        "note": ("RotoGrinders' own guide is explicit: 'you must select a 9-man lineup made up of "
                 "two players per position except for center (only one required)' and 'FanDuel has "
                 "no utility spots in basketball'. fanscout.pro disagrees (8 slots with G/F/UTIL); "
                 "RotoGrinders is the reference system being replicated and two independent sources "
                 "agree with it, so the rigid 2/2/2/2/1 roster is used. See IR-16."),
    },
    "nhl:draftkings": {
        "salary_cap": 50000,
        "slots": [
            RosterRule("C", 2, ["C"]),
            RosterRule("W", 3, ["LW", "RW", "W"]),
            RosterRule("D", 2, ["D"]),
            RosterRule("UTIL", 1, ["C", "LW", "RW", "W", "D", "G"]),
            RosterRule("G", 1, ["G"]),
        ],
        "n_players": 9,
        "verification_status": "single-source",
        "sources": ["https://occupyfantasy.com/nhl-dfs-strategy-guide/"],
        "note": ("'Require you roster 2 Centers, 3 Wings, 2 Defensemen, 1 FLEX, and 1 Goalie' "
                 "(occupyfantasy, 2025-03-03). An earlier draft of this file required 2 goalies "
                 "and 2 UTILs (10 players), which is not a legal DraftKings NHL roster. See IR-17."),
    },
    "nhl:fanduel": {
        "salary_cap": 40000,
        "slots": [
            RosterRule("C", 2, ["C"]),
            RosterRule("W", 2, ["LW", "RW", "W"]),
            RosterRule("D", 2, ["D"]),
            RosterRule("UTIL", 2, ["C", "LW", "RW", "W", "D", "G"]),
            RosterRule("G", 1, ["G"]),
        ],
        "n_players": 9,
        "verification_status": "single-source",
        "sources": ["https://occupyfantasy.com/nhl-dfs-strategy-guide/"],
        "note": "'Require you roster 2 Centers, 2 Wings, 2 Defensemen, 2 Utility, and 1 Goalie.'",
    },
    "nfl:draftkings": {
        "salary_cap": 50000,
        "slots": [
            RosterRule("QB", 1, ["QB"]),
            RosterRule("RB", 2, ["RB"]),
            RosterRule("WR", 3, ["WR"]),
            RosterRule("TE", 1, ["TE"]),
            RosterRule("FLEX", 1, ["RB", "WR", "TE"]),
            RosterRule("DST", 1, ["DST", "D"]),
        ],
        "n_players": 9,
        "verification_status": "multi-source-consistent",
        "agreement": 3,
        "sources": [
            "https://fantasyteamadvisors.com/nfl-dfs-strategy/",
            "https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/",
            "https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup-draftkings-picks-for-sunday/",
        ],
        "note": ("QB, 2 RB, 3 WR, TE, FLEX(RB/WR/TE), DST - no kicker slot, which is why "
                 "DraftKings' NFL scoring table carries no kicker coefficients. Corroborated by a "
                 "real published 9-row DraftKings lineup totalling exactly $50,000 "
                 "(sportsbettingdime, 2026-09-19). An earlier draft of this file had 2 WR and no "
                 "FLEX (8 players). See IR-17."),
    },
    "nfl:fanduel": {
        "salary_cap": 60000,
        "slots": [
            RosterRule("QB", 1, ["QB"]),
            RosterRule("RB", 2, ["RB"]),
            RosterRule("WR", 3, ["WR"]),
            RosterRule("TE", 1, ["TE"]),
            RosterRule("FLEX", 1, ["RB", "WR", "TE", "K"]),
            RosterRule("DST", 1, ["DST", "D"]),
        ],
        "n_players": 9,
        "verification_status": "disputed",
        "sources": [
            "https://fantasyteamadvisors.com/nfl-dfs-strategy/",
            "https://fantasyfootballers.org/featured/draftkings-vs-fanduel/",
        ],
        "note": ("fanDuel's flex eligibility is disputed: fantasyteamadvisors (2026-08-05) lists "
                 "FLEX as RB/WR/TE/K, while fantasyfootballers (2026-08-15) states 'As of the start "
                 "of the 2018 NFL season, FanDuel has replaced the Kicker position with the Flex "
                 "(RB/WR/TE) position'. RGENGY permits K in the flex (the more permissive reading) "
                 "and flags it. See IR-16."),
    },
    "wnba:draftkings": {
        "salary_cap": 50000,
        "slots": [
            RosterRule("G", 2, ["G", "PG", "SG"]),
            RosterRule("F", 2, ["F", "SF", "PF"]),
            RosterRule("C", 1, ["C"]),
            RosterRule("UTIL", 1, ["G", "F", "C", "PG", "SG", "SF", "PF"]),
        ],
        "n_players": 6,
        "verification_status": "not-audited",
        "sources": [],
        "note": ("UNCONFIRMED - no source for the WNBA roster was retrieved during this audit. "
                 "Treated as the NBA shape reduced to six slots. Do not use without confirming "
                 "against the operator. See limitation L-03."),
    },
    "wnba:fanduel": {
        "salary_cap": 40000,
        "slots": [
            RosterRule("G", 2, ["G", "PG", "SG"]),
            RosterRule("F", 2, ["F", "SF", "PF"]),
            RosterRule("C", 1, ["C"]),
            RosterRule("UTIL", 1, ["G", "F", "C", "PG", "SG", "SF", "PF"]),
        ],
        "n_players": 6,
        "verification_status": "not-audited",
        "sources": [],
        "note": "UNCONFIRMED - see wnba:draftkings and limitation L-03.",
    },
}


def default_roster(sport: str, site: str) -> Dict[str, Any]:
    """Roster template for a classic (full-slate) contest.

    Returns a dict with ``salary_cap``, ``slots`` (a list of :class:`RosterRule`),
    ``n_players``, ``verification_status``, ``sources`` and ``note``.

    Every template carries its own provenance in :data:`ROSTER_PROVENANCE`, and
    templates whose provenance is ``not-audited`` say so in their note rather
    than presenting themselves as official.  A roster template that is wrong is
    worse than a projection that is wrong: it produces lineups the operator
    would reject outright, so these are verified separately from scoring.
    """
    key = f"{sport}:{site}"
    tmpl = ROSTER_PROVENANCE.get(key)
    if tmpl is None:
        raise KeyError(
            f"No roster template for {key!r}. Known templates: {sorted(ROSTER_PROVENANCE)}"
        )
    total = sum(rule.count for rule in tmpl["slots"])
    if total != tmpl["n_players"]:
        # Self-check: a slot list that does not sum to the documented player
        # count is exactly the IR-17 bug class, so it fails loudly here.
        raise ValueError(
            f"roster template {key!r} is internally inconsistent: slots sum to {total} "
            f"but n_players is {tmpl['n_players']}"
        )
    return tmpl
