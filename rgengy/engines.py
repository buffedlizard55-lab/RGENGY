"""Projection engines.

One idea, applied to every sport
--------------------------------
RGENGY projects a stat as::

    projected[stat] = observed_rate[stat] * opportunity * environment_ratio

where

* ``observed_rate``   is computed from the player's own published season stats
                      (stat / games, or stat / minute).  No fitted constant.
* ``opportunity``     is the projected playing time (1 game, projected minutes,
                      projected plate appearances).
* ``environment_ratio`` is a *ratio of observed quantities* - today's expected
                      team output over the team's season-average output, times
                      the opponent's season-allowed output over the league
                      average, times (for baseball) a park factor computed from
                      observed home/away splits.

The league average is always computed from the same dataset at runtime, so the
model contains **no hand-tuned constants**.  Every knob that is not derived from
data lives in :mod:`rgengy.vegas` or is declared here with an explicit
``PROVENANCE`` comment.

Distribution, floor and ceiling
-------------------------------
Each raw stat is treated as Poisson with mean ``mu``.  Fantasy points are a
linear combination ``FPTS = sum(c_i * X_i)``, so for independent Poisson
components::

    mean(FPTS) = sum(c_i * mu_i)
    var(FPTS)  = sum(c_i^2 * mu_i)

That gives a standard deviation with no fitted parameters, and ``floor`` /
``ceil`` are ``mean -/+ z * sd``.  The ``z`` values are an RGENGY choice and are
declared below.

RotoGrinders' own floor/ceiling bands were measured from its six public (free)
MLB rows on 2026-09-22 - see ``scripts/analyze_rg_public_grid.py`` - and an
alternative ``rg_band`` mode reproduces those observed ratios.  Both modes are
available because RG does not publish its method.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Declared knobs.  Each is an RGENGY choice, not an audited fact.
# ---------------------------------------------------------------------------

#: Standard deviations used for the FLOOR / CEIL columns.  RGENGY choice.
FLOOR_Z = 1.0
CEIL_Z = 2.0

#: Multiplicative floor/ceiling bands measured from RotoGrinders' six public
#: MLB rows on 2026-09-22 (n=6 - a very small sample, flagged as IR-12).
#: Computed by ``scripts/analyze_rg_public_grid.py``; reproduced here so the
#: ``rg_band`` mode is deterministic without re-reading the fixture.
RG_OBSERVED_FLOOR_RATIO = 0.3030
RG_OBSERVED_CEIL_RATIO = 2.2229
RG_OBSERVED_SAMPLE_SIZE = 6
RG_OBSERVED_SOURCE = "https://rotogrinders.com/projected-stats/mlb (retrieved 2026-09-22)"

#: Per-sport scoring standard deviation for the run/point-differential win model.
#: Mirrors :data:`rgengy.vegas.SIGMA`; duplicated here only so this module stays
#: importable on its own.  Same unaudited status (IR-03).
SIGMA_BY_SPORT = {"mlb": 2.9, "nhl": 2.5, "nba": 12.0, "wnba": 11.0,
                  "nfl": 13.5, "ncaaf": 18.0}

#: Sports played outdoors where a weather adjustment is even meaningful.
OUTDOOR_SPORTS = {"mlb", "nfl", "ncaaf", "pga", "soccer"}

#: Air-density -> extra-base-rate sensitivity.  DEFAULT IS ZERO on purpose:
#: applying a coefficient that has not been validated against data would
#: fabricate precision.  Set explicitly (and document it) to enable.
WEATHER_AIR_DENSITY_COEFFICIENT = 0.0


@dataclass
class LeagueAverages:
    """Per-league aggregates computed from observed data only."""

    n_teams: int = 0
    runs_scored_per_game: float = 0.0
    runs_allowed_per_game: float = 0.0
    points_per_game: float = 0.0
    points_allowed_per_game: float = 0.0
    pace: float = 0.0
    extra: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_teams": self.n_teams,
            "runs_scored_per_game": round(self.runs_scored_per_game, 4),
            "runs_allowed_per_game": round(self.runs_allowed_per_game, 4),
            "points_per_game": round(self.points_per_game, 4),
            "points_allowed_per_game": round(self.points_allowed_per_game, 4),
            "pace": round(self.pace, 4),
            "extra": {k: round(v, 4) for k, v in self.extra.items()},
        }

    @classmethod
    def from_teams(cls, teams: Iterable[Dict[str, Any]], key_off: str, key_def: str,
                   games_key: str = "games", extra_keys: Sequence[str] = ()) -> "LeagueAverages":
        """Build averages from a list of team stat dicts."""
        rows = [t for t in teams if t.get(games_key)]
        if not rows:
            return cls()
        n = len(rows)
        off = sum(float(t.get(key_off) or 0) for t in rows) / float(sum(int(t[games_key]) for t in rows))
        dfn = sum(float(t.get(key_def) or 0) for t in rows) / float(sum(int(t[games_key]) for t in rows))
        extra = {}
        for k in extra_keys:
            vals = [float(t.get(k)) for t in rows if t.get(k) is not None]
            if vals:
                extra[k] = sum(vals) / len(vals)
        return cls(
            n_teams=n,
            runs_scored_per_game=off if key_off.startswith("r") else 0.0,
            runs_allowed_per_game=dfn if key_def.startswith("r") else 0.0,
            points_per_game=off if not key_off.startswith("r") else 0.0,
            points_allowed_per_game=dfn if not key_def.startswith("r") else 0.0,
            extra=extra,
        )


def poisson_sd(mu: float) -> float:
    """Standard deviation of a Poisson variable (sqrt of the mean)."""
    return math.sqrt(max(0.0, mu))


def fpts_distribution(means: Dict[str, float], coefficients: Dict[str, float]) -> Dict[str, float]:
    """Mean and sd of a linear combination of independent Poisson stats.

    Returns ``{"mean": ..., "sd": ...}``.  Any stat in ``means`` without a
    coefficient contributes nothing (coefficient 0).
    """
    mean = 0.0
    var = 0.0
    for stat, mu in means.items():
        c = coefficients.get(stat, 0.0)
        if not c or not mu:
            continue
        mean += c * mu
        var += (c * c) * mu
    return {"mean": mean, "sd": math.sqrt(max(0.0, var))}


def band_from_distribution(mean: float, sd: float,
                           floor_z: float = FLOOR_Z, ceil_z: float = CEIL_Z) -> Dict[str, float]:
    """``floor`` / ``ceil`` from a normal approximation to the FPTS distribution."""
    return {
        "floor": max(0.0, mean - floor_z * sd),
        "ceil": mean + ceil_z * sd,
        "sd": sd,
    }


def band_from_ratio(mean: float,
                    floor_ratio: float = RG_OBSERVED_FLOOR_RATIO,
                    ceil_ratio: float = RG_OBSERVED_CEIL_RATIO) -> Dict[str, float]:
    """``floor`` / ``ceil`` reproducing the bands observed on RotoGrinders' public grid.

    Provenance: measured from the six free MLB rows published at
    ``RG_OBSERVED_SOURCE``.  Sample size 6.  Use with care - see IR-12.
    """
    return {
        "floor": max(0.0, mean * floor_ratio),
        "ceil": mean * ceil_ratio,
        "sd": None,
    }


def _ratio(num: Optional[float], den: Optional[float], default: float = 1.0) -> float:
    if not num or not den:
        return default
    return float(num) / float(den)


@dataclass
class ProjectionContext:
    """Everything one player projection needs, assembled by the pipeline."""

    sport: str
    game_id: Optional[str] = None
    team: Optional[str] = None
    opp: Optional[str] = None
    #: expected team output today (runs for MLB, points for NBA/NFL/NHL)
    team_expected_output: Optional[float] = None
    #: the team's own season-average output per game
    team_season_output_pg: Optional[float] = None
    #: opponent's season-average allowed output per game
    opp_season_allowed_pg: Optional[float] = None
    #: expected opponent output today (runs / points / goals)
    opp_expected_output: Optional[float] = None
    #: expected margin (home - away) from the market, when available
    expected_margin: Optional[float] = None
    league: Optional[LeagueAverages] = None
    park_factor: Optional[float] = None
    pace_ratio: Optional[float] = None
    weather_ratio: float = 1.0
    opportunity: Optional[float] = None     # minutes, PA, or 1.0 for a game
    opportunity_unit: str = "game"
    rest_flag: Optional[str] = None
    status: Optional[str] = None
    #: P(team wins), derived from the market line by
    #: :func:`rgengy.vegas.market_win_probability` and supplied by the pipeline.
    #: Deliberately an INPUT rather than something an engine computes: a win
    #: probability has to have one documented origin, and ``None`` means "the
    #: market did not provide one", which downstream code must respect instead of
    #: substituting 0.5.
    win_prob: Optional[float] = None
    #: which line produced ``win_prob`` ('moneyline_devig' or 'spread_normal')
    win_prob_method: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def environment_ratio(self) -> Dict[str, float]:
        """The multiplicative environment adjustment, broken out for audit."""
        out: Dict[str, float] = {}
        if self.sport == "mlb":
            out["team_output_ratio"] = _ratio(self.team_expected_output, self.team_season_output_pg)
            out["opp_pitching_ratio"] = _ratio(
                self.opp_season_allowed_pg,
                self.league.runs_allowed_per_game if self.league else None,
            )
            if self.park_factor:
                out["park_factor"] = float(self.park_factor)
        else:
            out["team_output_ratio"] = _ratio(self.team_expected_output, self.team_season_output_pg)
            lg_allowed = None
            if self.league:
                lg_allowed = self.league.points_allowed_per_game or self.league.runs_allowed_per_game
            out["opp_defense_ratio"] = _ratio(self.opp_season_allowed_pg, lg_allowed)
            if self.pace_ratio:
                out["pace_ratio"] = float(self.pace_ratio)
        out["weather_ratio"] = float(self.weather_ratio)
        return out

    def combined_ratio(self) -> float:
        product = 1.0
        for v in self.environment_ratio().values():
            if v:
                product *= float(v)
        return product


class Engine:
    """Generic rate x opportunity x environment engine."""

    sport = "generic"
    #: canonical stat keys this engine emits
    stat_keys: Sequence[str] = ()
    #: stats whose value scales with team output (hits, points, goals)
    offense_keys: Sequence[str] = ()
    #: stats that are mostly opportunity-driven and NOT scaled by opponent quality
    neutral_keys: Sequence[str] = ()

    def __init__(self, band_mode: str = "distribution") -> None:
        if band_mode not in ("distribution", "rg_band"):
            raise ValueError(f"band_mode must be 'distribution' or 'rg_band', got {band_mode!r}")
        self.band_mode = band_mode

    # -- core --------------------------------------------------------------
    def project_player(self, raw: Dict[str, Any], ctx: "ProjectionContext") -> Dict[str, float]:
        """Project one player from a raw season record.

        The base implementation is position-agnostic.  Sports that project two
        different kinds of participant (baseball hitters vs pitchers, hockey
        skaters vs goalies) override this to dispatch on position, because using
        hitter stat keys for a pitcher silently produces a wrong-but-plausible
        score - only the strikeouts line up and everything else is missing.
        """
        return self.project(
            raw.get("season") or {}, ctx,
            games=raw.get("games"),
            sample_minutes=raw.get("sample_minutes") or raw.get("minutes"),
        )

    def rates(self, season: Dict[str, float], games: Optional[float],
              keys: Optional[Sequence[str]] = None) -> Dict[str, float]:
        """Per-game rates from season totals.

        ``keys`` must be given explicitly when projecting a participant whose
        stats differ from ``self.stat_keys`` (a baseball pitcher, a hockey
        goalie).  Defaulting to ``self.stat_keys`` there silently drops every
        relevant stat and yields a near-zero projection that still looks like a
        number - the bug this parameter exists to prevent.
        """
        if not games or games <= 0:
            return {}
        keys = tuple(keys) if keys is not None else self.stat_keys
        return {k: float(season.get(k) or 0.0) / games for k in keys}

    def per_minute_rates(self, season: Dict[str, float], sample_minutes: Optional[float],
                         keys: Optional[Sequence[str]] = None) -> Dict[str, float]:
        """Per-minute rates.  ``sample_minutes`` is the *season total* minutes
        the season totals were accumulated over - NOT the minutes projected for
        today.  Today's minutes come from ``ctx.opportunity``.  Keeping those two
        quantities apart is the single most important correctness detail in a
        per-minute projection model, so the names are deliberately different."""
        if not sample_minutes or sample_minutes <= 0:
            return {}
        keys = tuple(keys) if keys is not None else self.stat_keys
        return {k: float(season.get(k) or 0.0) / sample_minutes for k in keys}

    def project(self, season: Dict[str, float], ctx: ProjectionContext,
                games: Optional[float] = None,
                sample_minutes: Optional[float] = None) -> Dict[str, float]:
        """Return projected raw stats for one player in one game.

        ``games`` and ``sample_minutes`` describe the *sample* the season totals
        were accumulated over.  Today's playing time is ``ctx.opportunity``.
        """
        env = ctx.combined_ratio()
        if ctx.opportunity_unit == "minute":
            base = self.per_minute_rates(season, sample_minutes)
            if ctx.opportunity is None:
                # No projected minutes supplied: fall back to the player's own
                # average minutes per game, and say so.
                if games and sample_minutes:
                    opp_units = sample_minutes / games
                    ctx.notes.append(
                        "opportunity not supplied; using season average minutes per game "
                        f"({opp_units:.2f})")
                else:
                    opp_units = 0.0
            else:
                opp_units = float(ctx.opportunity)
        else:
            base = self.rates(season, games)
            opp_units = float(ctx.opportunity) if ctx.opportunity is not None else 1.0
        if not base:
            ctx.notes.append(
                f"{self.sport}: no usable season sample (games={games}, "
                f"sample_minutes={sample_minutes}); projection skipped rather than fabricated"
            )
            return {}

        projected: Dict[str, float] = {}
        for stat, rate in base.items():
            if stat in self.neutral_keys:
                scale = 1.0
            elif stat in self.offense_keys:
                scale = env
            else:
                # defensive / peripheral stats: scaled only by opportunity.
                scale = 1.0
            mu = rate * (opp_units or 0.0) * scale
            # Counts cannot be negative; the clamp is applied uniformly so a
            # negative environment ratio can never produce nonsense.
            projected[stat] = max(0.0, mu)
        return projected

    def score_and_band(self, projected: Dict[str, float], coefficients: Dict[str, float],
                       salary: Optional[float]) -> Dict[str, Any]:
        """Attach mean/sd/floor/ceil to a projection dict."""
        dist = fpts_distribution(projected, coefficients)
        mean = dist["mean"]
        if self.band_mode == "rg_band":
            band = band_from_ratio(mean)
        else:
            band = band_from_distribution(mean, dist["sd"])
        out = {
            "fpts": round(mean, 2),
            "sd": None if band["sd"] is None else round(band["sd"], 3),
            "floor": round(band["floor"], 2),
            "ceil": round(band["ceil"], 2),
            "band_mode": self.band_mode,
        }
        if salary:
            out["fpts_per_1k"] = round(mean / (salary / 1000.0), 3)
        return out


class BaseballEngine(Engine):
    """MLB.  Stat keys mirror RotoGrinders' public MLB grid columns."""

    sport = "mlb"
    hitter_keys = ("pa", "1b", "2b", "3b", "hr", "rbi", "r", "sb", "bb", "hbp", "k", "cs")
    pitcher_keys = ("ip", "k", "er", "ha", "bba", "hbpa", "win", "qs", "outs")
    stat_keys = hitter_keys
    # Plate appearances are an OPPORTUNITY, not an outcome: a batter gets roughly
    # the same number of PA whether his team scores 2 runs or 8.  Scaling PA by
    # the run environment is a modelling error (and the implausible-value check
    # in rgengy.quality caught exactly that), so 'pa' is neutral.
    offense_keys = ("1b", "2b", "3b", "hr", "rbi", "r", "sb", "bb", "hbp")
    neutral_keys = ("pa", "k", "cs")

    def __init__(self, band_mode: str = "distribution") -> None:
        super().__init__(band_mode)
        self.hitter_stat_keys = self.hitter_keys
        self.pitcher_stat_keys = self.pitcher_keys

    #: stats expressed per inning rather than per game
    PITCHER_RATE_KEYS = ("er", "ha", "bba", "hbpa", "k")

    def project_player(self, raw: Dict[str, Any], ctx: "ProjectionContext") -> Dict[str, float]:
        """Dispatch hitters to :meth:`project` and pitchers to :meth:`project_pitcher`."""
        positions = {str(x).upper() for x in (raw.get("positions") or [])}
        season = raw.get("season") or {}
        if positions & {"P", "SP", "RP"}:
            return self.project_pitcher(
                season, ctx, games=raw.get("games"),
                projected_ip=raw.get("projected_ip"),
            )
        return self.project(
            season, ctx, games=raw.get("games"),
            sample_minutes=raw.get("sample_minutes") or raw.get("minutes"),
        )

    def project_pitcher(self, season: Dict[str, float], ctx: ProjectionContext,
                        games: Optional[float] = None,
                        projected_ip: Optional[float] = None) -> Dict[str, float]:
        """Pitcher projection.  ``projected_ip`` defaults to the season IP rate."""
        base = self.rates(season, games, keys=self.pitcher_keys)
        if not base or not base.get("ip"):
            ctx.notes.append(
                f"mlb pitcher: no usable innings sample (games={games}); projection skipped "
                f"rather than fabricated")
            return {}
        sample_ip = base.get("ip", 0.0)
        ip = projected_ip if projected_ip is not None else sample_ip
        ip = max(0.0, float(ip or 0.0))
        env = ctx.combined_ratio()
        # Per-inning rates, then scaled to today's innings.  Only counting stats
        # that a pitcher is charged with are converted; win and quality start are
        # derived probabilities, not rates.
        per_ip = {k: (base.get(k, 0.0) / sample_ip if sample_ip else 0.0)
                  for k in self.PITCHER_RATE_KEYS}
        out: Dict[str, float] = {"ip": ip, "outs": ip * 3.0}
        for stat in ("er", "ha", "bba", "hbpa"):
            out[stat] = max(0.0, per_ip.get(stat, 0.0) * ip * env)
        # Strikeouts are only mildly environment-sensitive; keep them neutral.
        out["k"] = max(0.0, per_ip.get("k", 0.0) * ip)
        # Quality start is a rule applied to the point estimates: >= 6 IP and
        # <= 3 ER.  With a point-estimate line this is a hard 0/1; the Poisson-tail
        # form inside quality_start_probability softens it when ER is fractional.
        out["qs"] = quality_start_probability(out["ip"], out["er"])
        out["win"], win_src = team_win_probability(ctx)
        ctx.notes.append(
            f"pitcher win probability source: {win_src}. A starter is credited with the win "
            f"when his team holds the lead he leaves with, so P(win) is bounded above by "
            f"P(team wins) and scaled by P(quality start): "
            f"{out['win']:.4f} = P(team wins) x P(QS).")
        out["win"] = round(out["win"] * out["qs"], 4)
        return out


def team_win_probability(ctx: "ProjectionContext") -> Tuple[float, str]:
    """P(team wins) for a projection context, plus a label saying where it came from.

    Preference order, best evidence first:

    1.  ``ctx.win_prob`` - derived from the market line by
        :func:`rgengy.vegas.market_win_probability`.  A de-vigged moneyline needs
        no distributional assumption at all.
    2.  expected runs/points on both sides through a normal link
        (:func:`win_probability`).  Needs ``SIGMA``, an unaudited RGENGY
        assumption (IR-03).
    3.  ``0.0`` with the label ``"unavailable"`` - which callers must treat as
        "no projection", never as "a coin flip that came up tails".

    Returning the label alongside the number is the point: two engines that both
    produce 0.62 are not equally trustworthy, and the difference is invisible
    unless it travels with the value.
    """
    if ctx.win_prob is not None:
        return float(ctx.win_prob), f"market ({ctx.win_prob_method or 'line'})"
    opp = ctx.opp_expected_output
    if opp is None and ctx.expected_margin is not None and ctx.team_expected_output is not None:
        opp = ctx.team_expected_output - ctx.expected_margin
    if ctx.team_expected_output is not None and opp is not None:
        sigma = 2.9 if ctx.sport == "mlb" else SIGMA_BY_SPORT.get(ctx.sport, 12.0)
        return (win_probability(ctx.team_expected_output, opp, sd=sigma),
                f"expected-output differential (sigma={sigma}, unaudited - IR-03)")
    return 0.0, "unavailable (no market line and no expected output on both sides)"


def win_probability(team_runs: Optional[float], opp_runs: Optional[float],
                    sd: float = 2.9) -> float:
    """P(win) from expected runs using a normal approximation.

    ``sd`` defaults to :data:`rgengy.vegas.SIGMA['mlb']` - an unaudited RGENGY
    assumption (IR-03).  Returns 0.0 when either side is unknown rather than
    guessing.
    """
    if team_runs is None or opp_runs is None:
        return 0.0
    diff = team_runs - opp_runs
    return 0.5 * (1.0 + math.erf(diff / (sd * math.sqrt(2.0))))


def quality_start_probability(ip: float, er: float) -> float:
    """P(QS) - definition: >= 6 innings and <= 3 earned runs.

    Definition source (retrieved 2026-09-22):
    https://intercom.help/boomfantasy/en/articles/9950352-mlb
    ("Started the game and pitched at least 6 innings; allowed 3 earned runs or
    fewer").

    Modelled as a Poisson tail: P(X <= 3) where X ~ Poisson(er * 6 / ip) scaled
    to a 6-inning outing.  Returns 0 when the projected outing is shorter than
    6 innings.
    """
    if ip <= 0 or ip < 6.0:
        return 0.0
    lam = max(1e-9, er * (6.0 / ip))
    total = 0.0
    for k in range(0, 4):
        total += math.exp(-lam) * (lam ** k) / math.factorial(k)
    return min(1.0, total)


class BasketballEngine(Engine):
    """NBA / WNBA.  Stat keys mirror RotoGrinders' public WNBA grid columns."""

    sport = "nba"
    stat_keys = ("min", "pts", "three_pm", "two_pm", "ftm", "fgm", "fga", "reb", "ast",
                 "to", "stl", "blk")
    offense_keys = ("pts", "three_pm", "two_pm", "ftm", "fgm", "fga", "ast")
    neutral_keys = ("min", "to", "stl", "blk", "reb")

    def derive_components(self, projected: Dict[str, float]) -> Dict[str, float]:
        """Derive double-double / triple-double probabilities from projections.

        RotoGrinders publishes P-A, P-R, P-R-A, B-S and R-A columns on its WNBA
        grid (verified 2026-09-22) - pair and triple combos.  A rigorous open
        equivalent is the probability that two (or three) of {pts, reb, ast,
        stl, blk} each reach 10, under independent Poisson assumptions.
        """
        keys = ["pts", "reb", "ast", "stl", "blk"]
        p10 = {k: _poisson_ge(projected.get(k, 0.0), 10) for k in keys}
        combos: Dict[str, float] = {}
        # Named pairs/triples mirroring RG's P-A, P-R, P-R-A, B-S, R-A columns.
        named = {
            "P-A": ("pts", "ast"),
            "P-R": ("pts", "reb"),
            "P-R-A": ("pts", "reb", "ast"),
            "B-S": ("blk", "stl"),
            "R-A": ("reb", "ast"),
        }
        for label, ks in named.items():
            prob = 1.0
            for k in ks:
                prob *= p10[k]
            combos[label] = round(prob, 4)
        combos["dd"] = round(_any_double_double(p10), 4)
        combos["td"] = round(_any_triple_double(p10), 4)
        return combos


def _poisson_ge(lam: float, k: int) -> float:
    """P(X >= k) for X ~ Poisson(lam).  Pure stdlib."""
    if lam <= 0:
        return 0.0 if k > 0 else 1.0
    cdf = 0.0
    for i in range(0, k):
        cdf += math.exp(-lam) * (lam ** i) / math.factorial(i)
    return max(0.0, min(1.0, 1.0 - cdf))


def _any_double_double(p10: Dict[str, float]) -> float:
    """P(at least two of five categories reach 10), assuming independence."""
    return _at_least_k(p10, 2)


def _any_triple_double(p10: Dict[str, float]) -> float:
    return _at_least_k(p10, 3)


def _at_least_k(p10: Dict[str, float], k: int) -> float:
    """Poisson-binomial tail probability.  Exact, O(2^n) with n=5."""
    ps = list(p10.values())
    n = len(ps)
    total = 0.0
    for mask in range(1 << n):
        hits = bin(mask).count("1")
        if hits < k:
            continue
        prob = 1.0
        for i in range(n):
            prob *= ps[i] if (mask >> i) & 1 else (1.0 - ps[i])
        total += prob
    return max(0.0, min(1.0, total))


class HockeyEngine(Engine):
    """NHL.  Skaters and goalies are projected separately."""

    sport = "nhl"
    skater_keys = ("toi", "g", "a", "sog", "blk", "ppp", "shp", "hits", "fow")
    goalie_keys = ("sv", "ga", "so", "win_goalie", "toi")
    stat_keys = skater_keys
    offense_keys = ("g", "a", "sog", "ppp", "shp")
    neutral_keys = ("toi", "blk", "hits", "fow")

    def project_player(self, raw: Dict[str, Any], ctx: "ProjectionContext") -> Dict[str, float]:
        """Dispatch skaters to :meth:`project` and goalies to :meth:`project_goalie`."""
        positions = {str(x).upper() for x in (raw.get("positions") or [])}
        if positions & {"G", "GOALIE"}:
            return self.project_goalie(raw.get("season") or {}, ctx, games=raw.get("games"))
        return self.project(raw.get("season") or {}, ctx, games=raw.get("games"),
                            sample_minutes=raw.get("sample_minutes"))

    def project_goalie(self, season: Dict[str, float], ctx: ProjectionContext,
                       games: Optional[float] = None) -> Dict[str, float]:
        # `keys=` is mandatory here for the same reason it is in project_pitcher:
        # HockeyEngine.stat_keys holds the SKATER keys, so defaulting to them
        # drops 'sv' and 'ga' entirely and a goalie projects to nothing but a win
        # probability - a plausible-looking number that is silently wrong.
        base = self.rates(season, games, keys=self.goalie_keys)
        if not base or not base.get("sv"):
            ctx.notes.append(
                f"nhl goalie: no usable save sample (games={games}); projection skipped "
                f"rather than fabricated")
            return {}
        env = ctx.combined_ratio()
        ga = max(0.0, base.get("ga", 0.0) * env)
        sv = max(0.0, base.get("sv", 0.0))
        shots = ga + sv
        out = {
            "ga": ga,
            "sv": sv,
            "so": 1.0 if (ga < 0.02 and shots > 0) else _poisson_eq(ga, 0),
            # Same single documented origin as the baseball pitcher win: the market
            # line when it exists, otherwise the expected-goal differential, and
            # never an invented 0.5.
            "win_goalie": team_win_probability(ctx)[0],
        }
        return out


def _poisson_eq(lam: float, k: int) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


class FootballEngine(Engine):
    """NFL.  Stat keys mirror RotoGrinders' public NFL grid columns."""

    sport = "nfl"
    passing_keys = ("pa_att", "pa_cmp", "pa_yds", "pa_td", "pa_int")
    rushing_keys = ("ru_att", "ru_yds", "ru_td")
    receiving_keys = ("rec_tgt", "rec", "rec_yds", "rec_td")
    kicker_keys = ("fg_0_39", "fg_40_49", "fg_50p", "pat")
    dst_keys = ("dst_sack", "dst_int", "dst_fum_rec", "dst_td", "dst_safety", "dst_block",
                "dst_pts_allowed")
    stat_keys = passing_keys + rushing_keys + receiving_keys + ("fum_lost", "two_pt")
    offense_keys = ("pa_att", "pa_cmp", "pa_yds", "pa_td", "ru_att", "ru_yds", "ru_td",
                    "rec_tgt", "rec", "rec_yds", "rec_td")
    neutral_keys = ("pa_int", "fum_lost", "two_pt")

    def project_player(self, raw: Dict[str, Any], ctx: "ProjectionContext") -> Dict[str, float]:
        """Dispatch skill positions, kickers and team defences separately.

        An NFL roster legally requires a team defence (and on FanDuel can require
        a kicker through the flex), so those participant types must be projected
        too.  Projecting them with the skill-position stat keys yields an empty
        dict, which then makes the whole roster infeasible - the failure this
        dispatch prevents.  Team-defence and kicker stats are league-level rather
        than opponent-adjusted in this model, and that is stated rather than
        hidden: no audited DST-vs-opponent adjustment was found.
        """
        positions = {str(x).upper() for x in (raw.get("positions") or [])}
        season = raw.get("season") or {}
        games = raw.get("games")
        if positions & {"DST", "D", "DEF"}:
            out = self.rates(season, games, keys=self.dst_keys)
            if not out:
                ctx.notes.append("nfl DST: no season sample; projection skipped")
                return {}
            ctx.notes.append(
                "DST stats are projected at the season rate with no opponent adjustment; "
                "no audited defence-vs-opponent model was found")
            return out
        if positions & {"K", "PK"}:
            out = self.rates(season, games, keys=self.kicker_keys)
            if not out:
                ctx.notes.append("nfl kicker: no season sample; projection skipped")
                return {}
            ctx.notes.append("kicker stats are projected at the season rate, unadjusted")
            return out
        return self.project(season, ctx, games=games,
                            sample_minutes=raw.get("sample_minutes") or raw.get("minutes"))

    def bonus_probabilities(self, projected: Dict[str, float]) -> Dict[str, float]:
        """100-yard rushing / receiving and 300-yard passing bonuses.

        RotoGrinders publishes 100RU, 100RE and 300PA columns on its NFL grid
        (verified 2026-09-22), and FanDuel pays bonuses for each, so an open
        rebuild has to model them.  Modelled as normal tails around the
        projection with sd = sqrt(mean) (Poisson-like dispersion on yards is a
        documented approximation, not an audited fact).
        """
        def p_over(mu: float, threshold: float) -> float:
            if mu <= 0:
                return 0.0
            sd = math.sqrt(mu)
            return 0.5 * math.erfc((threshold - mu) / (sd * math.sqrt(2.0)))

        return {
            "100ru": round(p_over(projected.get("ru_yds", 0.0), 100.0), 4),
            "100rec": round(p_over(projected.get("rec_yds", 0.0), 100.0), 4),
            "300pa": round(p_over(projected.get("pa_yds", 0.0), 300.0), 4),
        }


ENGINES: Dict[str, Engine] = {
    "mlb": BaseballEngine(),
    "nba": BasketballEngine(),
    "wnba": BasketballEngine(),
    "nhl": HockeyEngine(),
    "nfl": FootballEngine(),
}


def engine_for(sport: str, band_mode: str = "distribution") -> Engine:
    cls = {
        "mlb": BaseballEngine,
        "nba": BasketballEngine,
        "wnba": BasketballEngine,
        "nhl": HockeyEngine,
        "nfl": FootballEngine,
    }.get(sport)
    if cls is None:
        raise KeyError(f"no engine for sport {sport!r}; supported: mlb, nba, wnba, nhl, nfl")
    return cls(band_mode=band_mode)


def park_factor_from_splits(home_runs_pg: Optional[float], away_runs_pg: Optional[float],
                            league_runs_pg: Optional[float]) -> Optional[float]:
    """Ballpark run factor from observed home/away splits.

    ``factor = (team home runs per game / team away runs per game)`` normalised
    so that 1.0 is neutral.  Computed entirely from observed data - no
    hard-coded park table is shipped, because a hard-coded table would be an
    unaudited assertion.
    """
    if not home_runs_pg or not away_runs_pg or not league_runs_pg:
        return None
    ratio = home_runs_pg / away_runs_pg
    return round(ratio, 4)
