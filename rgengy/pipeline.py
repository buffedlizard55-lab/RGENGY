"""End-to-end pipeline: sources -> environment -> projections -> tools -> report.

The pipeline is built around one principle: **it never fabricates a stage**.
Each stage records a status of ``complete``, ``degraded`` or ``unavailable``
together with the reason, and every artefact it writes carries that status.  A
run with no reachable endpoints produces an honest, empty-but-labelled report
rather than plausible-looking numbers.

Stages
------
``slate``       games for the date, from an official or documented feed
``environment`` weather, air density, park factor, implied team totals
``inputs``      per-player season stats (the stage most likely to degrade)
``projections`` rate x opportunity x environment
``scoring``     per-site fantasy points from the audited scoring tables
``ownership``   softmax choice model (uncalibrated by default)
``optimizer``   exact DP lineup solve + diversified multi-lineup set
``simulator``   Monte-Carlo contest simulation
``quality``     irregularity checks over everything above
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from rgengy import (engines, models, ownership, optimizer, quality, scoring,
                    simulator, sources, vegas)
from rgengy.http import FetchLog
from rgengy.models import Game, Player, Slate

STAGE_COMPLETE = "complete"
STAGE_DEGRADED = "degraded"
STAGE_UNAVAILABLE = "unavailable"


@dataclass
class StageResult:
    name: str
    status: str
    reason: Optional[str] = None
    counts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"stage": self.name, "status": self.status, "reason": self.reason,
                "counts": self.counts}


@dataclass
class RunResult:
    sport: str
    date: str
    site: str
    stages: List[StageResult] = field(default_factory=list)
    slate: Optional[Slate] = None
    report: Optional[quality.QualityReport] = None
    fetch_summary: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        if not self.stages:
            return STAGE_UNAVAILABLE
        if any(s.status == STAGE_UNAVAILABLE for s in self.stages):
            return STAGE_UNAVAILABLE
        if any(s.status == STAGE_DEGRADED for s in self.stages):
            return STAGE_DEGRADED
        return STAGE_COMPLETE

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "sport": self.sport,
            "date": self.date,
            "site": self.site,
            "overall_status": self.overall_status,
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stages": [s.to_dict() for s in self.stages],
            "warnings": self.warnings,
            "fetch_summary": self.fetch_summary,
            "quality": self.report.to_dict() if self.report else None,
        }
        if self.slate is not None:
            out["slate"] = self.slate.to_dict()
        return out


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Stage 1: slate
# ---------------------------------------------------------------------------

def build_slate(sport: str, date: str, log: FetchLog,
                use_cache: bool = True) -> tuple:
    """Return ``(games, provenance, warnings, StageResult)``."""
    warnings: List[str] = []
    provenance: List[Dict[str, Any]] = []

    if sport == "mlb":
        games, prov, warns = sources.mlb_games(date, log=log, use_cache=use_cache)
    elif sport == "nhl":
        games, prov, warns = sources.nhl_games(date, log=log, use_cache=use_cache)
    elif sport in sources.ESPN_SPORT_PATHS:
        games, prov, warns = sources.espn_games(sport, date=date, log=log, use_cache=use_cache)
    else:
        return [], [], [f"no slate source implemented for sport {sport!r}"], StageResult(
            "slate", STAGE_UNAVAILABLE, f"sport {sport!r} has no implemented source")

    provenance.extend(prov)
    warnings.extend(warns)
    if not games:
        return games, provenance, warnings, StageResult(
            "slate", STAGE_UNAVAILABLE,
            "no games returned; either an off-day or the feed shape changed - see warnings")
    status = STAGE_DEGRADED if warns else STAGE_COMPLETE
    reason = "; ".join(warns[:3]) if warns else None
    return games, provenance, warnings, StageResult(
        "slate", status, reason, {"games": len(games)})


# ---------------------------------------------------------------------------
# Stage 2: environment
# ---------------------------------------------------------------------------

def attach_environment(games: Sequence[Game], sport: str, log: FetchLog,
                       use_cache: bool = True,
                       enable_weather: bool = True) -> tuple:
    """Attach weather and implied team totals to each game."""
    warnings: List[str] = []
    provenance: List[Dict[str, Any]] = []

    for g in games:
        # --- market -------------------------------------------------------
        odds = g.odds
        it = None
        if odds:
            it = vegas.implied_totals(
                sport, total=odds.over_under, spread=odds.spread,
                home_ml=odds.home_ml, away_ml=odds.away_ml,
            )
        if it is None:
            warnings.append(f"game {g.game_id}: no market line available; implied totals left empty "
                            f"rather than guessed")
        else:
            g.home_implied_total = round(it.home, 3)
            g.away_implied_total = round(it.away, 3)
            g.implied_total_method = it.method
            g.extra["implied_totals"] = it.to_dict()

        # --- weather (outdoor sports only) --------------------------------
        if not enable_weather or sport not in engines.OUTDOOR_SPORTS:
            continue
        lat, lon = g.venue_lat, g.venue_lon
        if lat is None or lon is None:
            warnings.append(
                f"game {g.game_id} ({g.away_team} @ {g.home_team}): venue coordinates unavailable, "
                f"so the NWS weather layer was skipped. RGENGY does not ship a hard-coded coordinate "
                f"table because inventing coordinates would violate the no-hallucination rule."
            )
            continue
        weather, wprov, wwarn = sources.venue_weather(lat, lon, g.starts_utc, log=log,
                                                      use_cache=use_cache)
        provenance.extend(wprov)
        warnings.extend(wwarn)
        if weather is not None:
            g.weather = weather

    status = STAGE_COMPLETE
    n_weather = sum(1 for g in games if g.weather is not None)
    n_market = sum(1 for g in games if g.home_implied_total is not None)
    if n_market == 0 and games:
        status = STAGE_UNAVAILABLE
    elif n_weather == 0 and sport in engines.OUTDOOR_SPORTS and enable_weather:
        status = STAGE_DEGRADED
    elif warnings:
        status = STAGE_DEGRADED
    return provenance, warnings, StageResult(
        "environment", status,
        None if status == STAGE_COMPLETE else ("; ".join(warnings[:3]) if warnings else None),
        {"games_with_market": n_market, "games_with_weather": n_weather, "games": len(games)})


# ---------------------------------------------------------------------------
# Stage 3/4/5: inputs -> projections -> scoring
# ---------------------------------------------------------------------------

def project_players(players_raw: Sequence[Dict[str, Any]], games: Sequence[Game],
                    sport: str, league: Optional[engines.LeagueAverages],
                    site: str, band_mode: str = "distribution") -> tuple:
    """Turn raw player-season records plus game context into projected rows.

    ``players_raw`` entries must carry at least:
    ``player_id``, ``name``, ``team``, ``positions``, ``season`` (totals),
    ``games`` or ``minutes``, and optionally ``salary``, ``status``.
    """
    engine = engines.engine_for(sport, band_mode=band_mode)
    coefficients = scoring.load(sport, site).points
    games_by_team: Dict[str, Game] = {}
    for g in games:
        games_by_team.setdefault(g.home_team, g)
        games_by_team.setdefault(g.away_team, g)

    out: List[Player] = []
    warnings: List[str] = []
    skipped = 0

    for raw in players_raw:
        team = raw.get("team")
        game = games_by_team.get(team)
        opp = None
        ctx_kwargs: Dict[str, Any] = {"sport": sport, "team": team}
        if game is not None:
            ctx_kwargs["game_id"] = game.game_id
            opp = game.away_team if game.home_team == team else game.home_team
            ctx_kwargs["opp"] = opp
            ctx_kwargs["team_expected_output"] = (
                game.home_implied_total if game.home_team == team else game.away_implied_total)
            ctx_kwargs["opp_expected_output"] = (
                game.away_implied_total if game.home_team == team else game.home_implied_total)
            if game.odds:
                ctx_kwargs["expected_margin"] = game.odds.spread
                # One documented origin for every win probability in the system:
                # derived from the market line here, never invented inside an
                # engine.  Returns None when the line carries neither a moneyline
                # pair nor a spread, in which case no win probability is claimed.
                from rgengy.vegas import market_win_probability
                wp = market_win_probability(
                    sport, home_ml=game.odds.home_ml, away_ml=game.odds.away_ml,
                    spread=game.odds.spread,
                    side="home" if game.home_team == team else "away")
                if wp is not None:
                    ctx_kwargs["win_prob"] = wp.prob
                    ctx_kwargs["win_prob_method"] = wp.method
                else:
                    warnings.append(
                        f"{team}: the market line carried neither a moneyline pair nor a "
                        f"spread, so no team win probability is derived (RGENGY does not "
                        f"assume 0.5)")
            if game.weather and game.weather.air_density_kg_m3:
                ctx_kwargs["weather_ratio"] = _weather_ratio(
                    game.weather.air_density_kg_m3, sport)
        ctx_kwargs["league"] = league
        ctx_kwargs["team_season_output_pg"] = raw.get("team_output_pg")
        ctx_kwargs["opp_season_allowed_pg"] = raw.get("opp_allowed_pg")
        ctx_kwargs["park_factor"] = raw.get("park_factor")
        ctx_kwargs["pace_ratio"] = raw.get("pace_ratio")
        ctx_kwargs["status"] = raw.get("status")

        unit = raw.get("opportunity_unit", "minute" if sport in ("nba", "wnba") else "game")
        ctx_kwargs["opportunity_unit"] = unit
        ctx_kwargs["opportunity"] = raw.get("opportunity")

        ctx = engines.ProjectionContext(**ctx_kwargs)
        projected = engine.project_player(raw, ctx)
        if projected and not any(projected.values()):
            # An all-zero projection means the season sample was empty or the
            # opportunity input was missing, so the player is unrankable.  It is
            # reported separately from "no projection at all" because the fix is
            # different, and silently keeping a 0.0 would look like a real bust.
            skipped += 1
            warnings.append(
                f"{raw.get('name') or raw.get('player_id')}: every projected stat is zero "
                f"(empty season sample or missing opportunity input); retained in the pool at "
                f"0.0 {site} points and flagged rather than dropped or invented")
        if not projected:
            # The player is KEPT in the pool with a zero projection rather than
            # dropped.  Dropping them makes any roster slot that only they could
            # fill impossible to satisfy, which silently turns one missing season
            # sample into "no lineup exists for this sport at all".  Keeping them
            # with a flagged zero is both more useful and more honest: the quality
            # report names every player whose projection is zero.
            skipped += 1
            warnings.append(
                f"{raw.get('name') or raw.get('player_id')}: no projection could be produced "
                f"(no usable season sample); retained in the pool at 0.0 {site} points and "
                f"flagged rather than dropped or invented")

        bands = engine.score_and_band(projected or {}, coefficients, raw.get("salary"))
        p = Player(
            sport=sport,
            player_id=str(raw.get("player_id")),
            name=raw.get("name") or str(raw.get("player_id")),
            team=team or "???",
            opp=opp,
            positions=list(raw.get("positions") or []),
            salary=raw.get("salary"),
            site=site,
            game_id=ctx_kwargs.get("game_id"),
            status=raw.get("status"),
            stats={k: v for k, v in (raw.get("season") or {}).items()},
            projected={k: round(v, 4) for k, v in projected.items()},
            fpts={site: bands["fpts"]},
            floor=bands["floor"], ceil=bands["ceil"],
            extra={
                "sd": bands.get("sd"),
                "band_mode": bands.get("band_mode"),
                "fpts_per_1k": bands.get("fpts_per_1k"),
                "environment_ratio": {k: round(v, 4) for k, v in ctx.environment_ratio().items()},
                "engine_notes": list(ctx.notes),
                # The market line for this player's game, so grid columns like
                # SPREAD and O/U are filled from a retrieved number rather than
                # left empty or, worse, inferred.  Absent when no line was found.
                "game_line": ({
                    "spread": game.odds.spread,
                    "over_under": game.odds.over_under,
                    "win_prob": ctx_kwargs.get("win_prob"),
                    "win_prob_method": ctx_kwargs.get("win_prob_method"),
                    "source": "market line retrieved with the slate",
                } if (game is not None and game.odds) else None),
            },
        )
        # Sport-specific derived columns mirroring the RotoGrinders grid.
        if isinstance(engine, engines.BasketballEngine):
            p.extra["combos"] = engine.derive_components(projected)
        if isinstance(engine, engines.FootballEngine):
            p.extra["bonuses"] = engine.bonus_probabilities(projected)
        out.append(p)

    if skipped:
        warnings.append(f"{skipped} player(s) skipped: no usable season sample")
    if not out:
        warnings.append("no players could be projected from the supplied inputs")

    status = STAGE_COMPLETE if out and not skipped else (
        STAGE_UNAVAILABLE if not out else STAGE_DEGRADED)
    stage = StageResult("projections", status,
                        "; ".join(warnings[:3]) if warnings else None,
                        {"players": len(out), "skipped": skipped})
    return out, warnings, stage


def _weather_ratio(air_density: float, sport: str) -> float:
    """Run-scoring adjustment from air density.

    Denser air suppresses flight (fewer home runs, shorter kicks); thinner air
    helps.  RGENGY computes the *ratio* to the ISA standard density exactly
    (:data:`rgengy.vegas.ISA_AIR_DENSITY_KG_M3`), but multiplies it by
    ``WEATHER_AIR_DENSITY_COEFFICIENT``, which defaults to **0** - i.e. the
    adjustment is disabled.  Enabling it would apply a sensitivity that has not
    been validated against data, which would fabricate precision.  Set the
    coefficient explicitly, and document the evidence, to turn it on.
    """
    coeff = engines.WEATHER_AIR_DENSITY_COEFFICIENT
    if not coeff:
        return 1.0
    delta = (air_density - vegas.ISA_AIR_DENSITY_KG_M3) / vegas.ISA_AIR_DENSITY_KG_M3
    # Thinner air (delta < 0) increases scoring, hence the minus sign.
    return 1.0 - coeff * delta


def _roster_known(sport: str, site: str) -> bool:
    """Whether a roster template exists, without raising for an unshipped one."""
    return f"{sport}:{site}" in models.ROSTER_PROVENANCE


#: Smash threshold as a multiple of the projected mean, used only when the caller
#: does not supply one.  RGENGY choice, NOT a RotoGrinders value: RG publishes a
#: SMASH column without defining it, so any threshold here is ours and is labelled
#: as ours wherever it is surfaced.
DEFAULT_SMASH_THRESHOLD_MULTIPLE = 1.5


def attach_ownership(players: Sequence[Player], site: str,
                     model: Optional[ownership.OwnershipModel] = None,
                     smash_multiple: float = DEFAULT_SMASH_THRESHOLD_MULTIPLE) -> tuple:
    """Attach pOWN plus RGENGY's own leverage and smash analytics.

    RotoGrinders' ``FPTS/$`` identity IS reproduced here because it was verified
    exactly against the public grid (``FPTS / (SALARY/1000)``, max error 0.0036
    over six rows - see tests/test_rg_grid.py).  ``LEV``, ``SMASH`` and
    ``TOPVAL`` are NOT reproduced: RotoGrinders publishes those columns without
    defining them, so RGENGY computes its own clearly-labelled equivalents and
    leaves the corresponding grid columns null rather than passing an invented
    number off as theirs.
    """
    model = model or ownership.default_model()
    players = list(players)
    values = [p.value(site) for p in players]
    shares = ownership.project_ownership(values, model)
    fpts_values = [float(p.fpts.get(site) or 0.0) for p in players]
    field_avg = (sum(fpts_values) / len(fpts_values)) if fpts_values else 0.0
    field_size = len(players)
    for p, share in zip(players, shares):
        p.pown = round(share, 6)
        # Stored as None - never 0.0 - when the salary is missing, so a player
        # we cannot value is visibly unvalued instead of looking worthless.
        # This mirrors _resolve("value_per_1k"), which already returns None.
        _pts = p.fpts.get(site)
        p.extra["value_per_1k"] = (round(_pts / (p.salary / 1000.0), 4)
                                   if (p.salary and _pts is not None) else None)
        p.extra["ownership_model"] = model.to_dict()
        p.extra["lev"] = ownership.leverage(share, float(p.fpts.get(site) or 0.0),
                                            field_avg, field_size)
        threshold = smash_multiple * float(p.fpts.get(site) or 0.0)
        p.extra["smash"] = ownership.smash_probability(
            float(p.fpts.get(site) or 0.0), p.extra.get("sd"), threshold)
        p.extra["smash_threshold"] = round(threshold, 3)
    for p in players:
        p.extra["analytics_provenance"] = {
            "FPTS/$": ("reproduced - identity verified exactly against RotoGrinders' public "
                       "MLB grid on 2026-09-22 (max error 0.0036 over 6 rows)"),
            "lev": ("RGENGY definition (value share minus ownership share). RotoGrinders "
                    "publishes a LEV column without a formula; this is NOT a reproduction."),
            "smash": (f"RGENGY definition: P(FPTS > {smash_multiple}x projection) under a normal "
                      "approximation. RotoGrinders publishes a SMASH column without a formula; "
                      "this is NOT a reproduction."),
            "topval": "not computed - RotoGrinders' definition is unpublished (left null)",
            "difference": "not computed - RotoGrinders' definition is unpublished (left null)",
            "obfpts": "not computed - RotoGrinders' definition is unpublished (left null)",
        }
    stage = StageResult(
        "ownership", STAGE_DEGRADED if not model.calibrated else STAGE_COMPLETE,
        None if model.calibrated else
        "beta is an uncalibrated RGENGY default (IR-13); pOWN is a transparent choice model, "
        "not a reproduction of RotoGrinders' gradient-boosted ownership projections",
        {"players": len(players)})
    return list(players), stage


# ---------------------------------------------------------------------------
# Full run
# ---------------------------------------------------------------------------

def run(sport: str, date: str, site: str = "draftkings", *,
        games: Optional[Sequence[Game]] = None,
        players_raw: Optional[Sequence[Dict[str, Any]]] = None,
        league: Optional[engines.LeagueAverages] = None,
        n_lineups: int = 5, n_sims: int = 500, field_size: int = 200,
        sharp_fraction: float = 0.5,
        enable_weather: bool = True, band_mode: str = "distribution",
        use_cache: bool = True, log: Optional[FetchLog] = None) -> RunResult:
    """Execute every stage and return a fully-labelled :class:`RunResult`."""
    log = log if log is not None else FetchLog()
    result = RunResult(sport=sport, date=date, site=site)
    report = quality.QualityReport()
    if sport not in engines.ENGINES:
        # engines.engine_for() raises for an unsupported sport, which is right
        # for a library call but wrong at the top of a run: the caller asked for
        # a report, so return one that says the sport is not implemented rather
        # than an exception with no stages and no quality findings.
        supported = ", ".join(sorted(engines.ENGINES))
        result.stages.append(StageResult(
            "slate", STAGE_UNAVAILABLE,
            f"sport {sport!r} has no projection engine; supported: {supported}"))
        result.warnings.append(
            f"sport {sport!r} is not implemented (supported: {supported}); "
            f"nothing was projected and nothing was invented")
        result.report = report
        result.fetch_summary = log.summary()
        return result
    result.report = report

    if games is not None:
        # Caller supplied the slate (used by `rgengy demo` and by tests).  No
        # network stage is implied, so nothing is claimed as fetched.
        games = list(games)
        prov = []
        result.stages.append(StageResult(
            "slate", STAGE_COMPLETE, "slate supplied by the caller; no feed was fetched",
            {"games": len(games)}))
    else:
        games, prov, warns, stage = build_slate(sport, date, log, use_cache=use_cache)
        result.stages.append(stage)
        result.warnings.extend(warns)

    if games:
        eprov, ewarns, estage = attach_environment(games, sport, log, use_cache=use_cache,
                                                   enable_weather=enable_weather)
        prov.extend(eprov)
        result.warnings.extend(ewarns)
        result.stages.append(estage)
    else:
        result.stages.append(StageResult("environment", STAGE_UNAVAILABLE, "no slate to attach to"))

    # --- inputs -----------------------------------------------------------
    if players_raw is None:
        result.stages.append(StageResult(
            "inputs", STAGE_UNAVAILABLE,
            "no per-player season stats were supplied and RGENGY will not synthesise them. "
            "The MLB/NBA/NHL/NFL player-stat endpoints are listed as 'unverified' in "
            "rgengy/sources.py; run `rgengy probe` to confirm their live shape before enabling "
            "this stage."))
        players: List[Player] = []
    else:
        players, pwarns, pstage = project_players(
            players_raw, games, sport, league, site, band_mode=band_mode)
        result.warnings.extend(pwarns)
        result.stages.append(StageResult(
            "inputs", STAGE_COMPLETE, None, {"players_supplied": len(players_raw)}))
        result.stages.append(pstage)

        _players, ostage = attach_ownership(players, site)
        result.stages.append(ostage)

        table = scoring.load(sport, site)
        coefficients = table.points
        opt = optimizer.optimize_multi(players, sport, site, n_lineups=n_lineups)
        lineups = opt.get("lineups", [])
        # optimizer.infeasible() names EVERY unfilled slot and the reason, which
        # is the only actionable part of the failure.  Dropping it and reporting a
        # bare "no feasible lineup" would send the user back to guesswork, so the
        # detail is carried into both the stage reason and the run warnings.
        why = opt.get("infeasible_reason") or "no feasible lineup could be built"
        unfilled = opt.get("unfilled_slots") or []
        if not lineups:
            detail = why + (f"; unfilled slots: {', '.join(map(str, unfilled))}" if unfilled else "")
            result.warnings.append(
                f"optimizer: {detail} (pool={len(players)} players, "
                f"cap={models.default_roster(sport, site)['salary_cap'] if _roster_known(sport, site) else 'n/a'})")
        else:
            detail = None
        result.stages.append(StageResult(
            "optimizer", STAGE_COMPLETE if lineups else STAGE_UNAVAILABLE,
            detail,
            {"lineups": len(lineups)}))

        if not lineups:
            sim: Dict[str, Any] = {"results": [], "note": "skipped: no lineups"}
            sim_stage_status = STAGE_UNAVAILABLE
        elif not any(v for v in coefficients.values()):
            # Every coefficient in this table is 0 because none of them was ever
            # audited (see the WNBA tables and limitation L-03).  Simulating a
            # contest on an all-zero scoring table returns 100% cash and +100% ROI
            # for a lineup that scores nothing, which is precisely the kind of
            # confident nonsense this pipeline exists to avoid.
            sim = {"results": [], "n_sims": 0,
                   "note": ("skipped: every scoring coefficient for "
                            f"{sport}:{site} is 0.0 because none was audited, so any "
                            "simulated ROI would be meaningless. Fill the scoring table "
                            "from the operator's own page first.")}
            sim_stage_status = STAGE_UNAVAILABLE
        else:
            sim = simulator.simulate_contest(lineups, players, sport, site,
                                             n_sims=n_sims, field_size=field_size,
                                             sharp_fraction=sharp_fraction)
            sim_stage_status = STAGE_COMPLETE if sim.get("results") else STAGE_DEGRADED
        result.stages.append(StageResult(
            "simulator", sim_stage_status,
            None if sim_stage_status == STAGE_COMPLETE else sim.get("note"),
            {"n_sims": sim.get("n_sims", 0)}))

        quality.check_zero_projection(players, site, report)
        quality.check_duplicate_ids(players, report)
        quality.check_implausible_values(players, sport, report)
        quality.check_ownership_normalisation(players, report)
        quality.check_scoring_coverage(players, coefficients, report, scoring_table=table)
        quality.check_representation_double_count(sport, site, report)

    quality.check_stale_provenance(prov, report)
    result.fetch_summary = log.summary()
    quality.check_endpoint_failures(result.fetch_summary, report)

    result.slate = Slate(
        sport=sport, date=date, site=site, games=list(games), players=players,
        lineups=(opt.get("lineups", []) if players_raw is not None else []),
        meta={
            "generated_at": _now_iso(),
            "overall_status": result.overall_status,
            "simulation": (sim if players_raw is not None else {"skipped": True}),
            "scoring_table": {
                "key": f"{sport}:{site}",
                "confirmed_by_operator": scoring.load(sport, site).confirmed_by_operator,
                "disputed_values": scoring.load(sport, site).disputed,
            },
        },
    )
    return result


def write_artefacts(result: RunResult, out_dir: Path) -> List[Path]:
    """Write the JSON artefacts consumed by the GitHub Pages site."""
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = result.to_dict()
    paths = []

    main_path = out_dir / f"{result.sport}-{result.date}-{result.site}.json"
    main_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    paths.append(main_path)

    # A flat, grid-shaped CSV-like view matching RotoGrinders' column order, so
    # the two can be compared column by column.
    grid = out_dir / f"{result.sport}-{result.date}-{result.site}.grid.json"
    grid.write_text(json.dumps(grid_rows(result), indent=2) + "\n", encoding="utf-8")
    paths.append(grid)

    latest = out_dir / "latest.json"
    latest.write_text(json.dumps({
        "sport": result.sport, "date": result.date, "site": result.site,
        "overall_status": result.overall_status,
        "generated_at": payload["generated_at"],
        "artefact": main_path.name,
    }, indent=2) + "\n", encoding="utf-8")
    paths.append(latest)
    return paths


def grid_rows(result: RunResult) -> Dict[str, Any]:
    """Flatten projections into RotoGrinders' published column order.

    Columns RGENGY cannot produce are emitted as ``null`` and listed in
    ``unfilled_columns`` - never as a fabricated value.  This is what makes the
    two products comparable side by side without pretending to parity.
    """
    from rgengy.models import RG_GRID_COLUMNS

    columns = RG_GRID_COLUMNS.get(result.sport)
    slate = result.slate
    rows: List[Dict[str, Any]] = []
    filled = set()
    for p in (slate.players if slate else []):
        row = _row_for(p, result.site, result.sport)
        rows.append(row)
        filled.update(k for k, v in row.items() if v is not None)
    unfilled = [c for c in (columns or []) if c not in filled] if columns else []
    observed = columns is not None
    return {
        "sport": result.sport,
        "date": result.date,
        "site": result.site,
        "rg_column_schema": columns,
        "rg_column_schema_observed": observed,
        "rg_column_schema_source": (
            f"https://rotogrinders.com/projected-stats/{result.sport} (retrieved 2026-09-22)"
            if observed else None),
        "rg_column_schema_note": (
            None if observed else
            f"RotoGrinders' {result.sport.upper()} grid header was NOT transcribed during the "
            f"2026-09-22 audit, so the column set below is RGENGY's own and must not be read as "
            f"a reproduction of RotoGrinders' {result.sport.upper()} schema. Retrieve the header "
            f"from the URL above to make them comparable."),
        "unfilled_columns": unfilled,
        # Two different situations produce a null, and they must not read the
        # same.  A column RGENGY does not map at all carries its documented
        # reason; a column that IS mapped but came back empty on this run means
        # the input data was missing, which is a fetch problem, not a schema one.
        "unfilled_column_reasons": {
            c: (UNMAPPED_COLUMN_REASONS[c] if c in UNMAPPED_COLUMN_REASONS else
                ("mapped, but every row was empty for this run - the input data "
                 "(weather, market line, batting order, status...) was not "
                 "available, so the column is null rather than guessed"
                 if c in (_COLUMN_MAP.get(result.sport) or {}) else
                 "no reason recorded - see IR-22"))
            for c in unfilled
        },
        "n_unfilled": len(unfilled),
        "n_filled": len(filled),
        "n_rows": len(rows),
        "rows": rows,
    }


#: Maps a RotoGrinders grid column name onto an RGENGY player attribute path.
#:
#: Only columns RGENGY can actually compute are mapped.  Every other column in
#: ``RG_GRID_COLUMNS`` is emitted as ``null`` and listed in ``unfilled_columns``,
#: because publishing an invented number under RotoGrinders' column heading would
#: be indistinguishable from having reproduced theirs.  In particular:
#:
#: * ``FPTS/$`` IS mapped - the identity ``FPTS / (SALARY/1000)`` was verified
#:   exactly against the public grid (max error 0.0036 over 6 rows).
#: * ``LEV``, ``SMASH``, ``TOPVAL``, ``DIFFERENCE``, ``OBFPTS``, ``OPTO``,
#:   ``TEAMOWN``, ``BATK``, ``HRRBI``, ``BASES``, ``H``, ``PC`` are NOT mapped -
#:   RotoGrinders publishes those columns without defining them.  RGENGY computes
#:   its own clearly-labelled ``lev`` and ``smash`` in ``extra`` instead.
_COLUMN_MAP: Dict[str, Dict[str, str]] = {
    "mlb": {
        "PLAYER": "name", "SALARY": "salary", "POS": "position", "TEAM": "team", "OPP": "opp",
        "PA": "projected.pa", "1B": "projected.1b", "2B": "projected.2b", "3B": "projected.3b",
        "HR": "projected.hr", "RBI": "projected.rbi", "R": "projected.r", "SB": "projected.sb",
        "BB": "projected.bb", "IP": "projected.ip", "BBA": "projected.bba", "K": "projected.k",
        "W": "projected.win", "ER": "projected.er", "HA": "projected.ha", "HBP": "projected.hbp",
        "QS": "projected.qs",
        "FPTS": "fpts", "FPTS/$": "value_per_1k",
        "FLOOR": "floor", "CEIL": "ceil", "POWN": "pown",
        "WIND": "weather.wind", "TEMP": "weather.temp_f", "TEMPDESC": "weather.desc",
        "ORDER": "batting_order",
    },
    "nfl": {
        "PLAYER": "name", "SALARY": "salary", "POS": "position", "TEAM": "team", "OPP": "opp",
        "INJURY": "status",
        "PAATT": "projected.pa_att", "CMP": "projected.pa_cmp", "PAYDS": "projected.pa_yds",
        "PATD": "projected.pa_td", "INT": "projected.pa_int", "RUATT": "projected.ru_att",
        "RUYDS": "projected.ru_yds", "RUTD": "projected.ru_td", "TAR": "projected.rec_tgt",
        "REC": "projected.rec", "REYDS": "projected.rec_yds", "RETD": "projected.rec_td",
        "100RU": "projected.100ru", "100RE": "projected.100rec", "300PA": "projected.300pa",
        "FPTS": "fpts", "FPTS/$": "value_per_1k",
        "FLOOR": "floor", "CEIL": "ceil", "POWN": "pown",
    },
    "wnba": {
        "PLAYER": "name", "SALARY": "salary", "POS": "position", "TEAM": "team", "OPP": "opp",
        "STATUS": "status",
        # Market-line columns.  Both are retrieved numbers (Game.odds.spread /
        # Game.odds.over_under), not estimates, so they are filled.  TOTAL sits
        # beside them but is deliberately NOT mapped - see UNMAPPED_COLUMN_REASONS.
        "SPREAD": "game_line.spread", "O/U": "game_line.over_under",
        "MINUTES": "projected.min", "PTS": "projected.pts",
        "REB": "projected.reb", "AST": "projected.ast", "3PM": "projected.three_pm",
        "TO": "projected.to", "STL": "projected.stl", "BLK": "projected.blk",
        "FPTS": "fpts", "FPTS/$": "value_per_1k",
        "FLOOR": "floor", "CEIL": "ceil", "POWN": "pown",
    },
    "nhl": {
        "PLAYER": "name", "SALARY": "salary", "POS": "position", "TEAM": "team", "OPP": "opp",
        "G": "projected.g", "A": "projected.a", "SOG": "projected.sog", "BLK": "projected.blk",
        "PPP": "projected.ppp", "SHP": "projected.shp",
        "SV": "projected.sv", "GA": "projected.ga", "SO": "projected.so",
        "FPTS": "fpts", "FPTS/$": "value_per_1k",
        "FLOOR": "floor", "CEIL": "ceil", "POWN": "pown",
    },
}
_COLUMN_MAP["nba"] = dict(_COLUMN_MAP["wnba"])

#: Columns RGENGY deliberately leaves null on the emitted grid, with the reason.
#: Surfaced in the artefact so a reader can tell "we could not determine this"
#: from "we forgot this".
UNMAPPED_COLUMN_REASONS: Dict[str, str] = {
    "OBFPTS": "RotoGrinders publishes OBFPTS at full float precision, ~1.08-1.13x FPTS, with no "
              "published definition (IR-21). Not reproduced.",
    "OPTO": "RotoGrinders' optimiser output. Its objective and constraints are unpublished, so "
            "RGENGY emits its own optimiser result separately instead of under this heading.",
    "SMASH": "Unpublished definition. RGENGY computes its own P(FPTS > 1.5x projection) into "
             "extra['smash'] and labels it as its own (IR-21).",
    "TOPVAL": "Unpublished definition; not reproduced.",
    "TEAMOWN": "Team-level ownership. RotoGrinders' aggregation is unpublished; RGENGY exposes "
               "per-player pOWN only rather than inventing a team roll-up (IR-22).",
    "DIFFERENCE": "Unpublished definition; not reproduced.",
    "LEV": "Unpublished definition. RGENGY computes its own value-share-minus-ownership-share "
           "into extra['lev'] and labels it as its own (IR-21).",
    "BATK": "Unpublished definition; not reproduced.",
    "HRRBI": "Unpublished definition; not reproduced.",
    "BASES": "Consistent with 1B + 2*2B + 3*3B + 4*HR on the six public rows, but that is an "
             "inference, not a published definition, so it is not emitted.",
    "H": "Consistent with 1B + 2B + 3B + HR on the six public rows, but inferred rather than "
         "published, so it is not emitted.",
    "PC": "Empty on all six public rows; meaning undetermined.",
    "OUTS": "Zero for hitters on all six public rows and a pitcher statistic; not emitted for "
            "hitters rather than guessed.",
    "UNDERDOG": "A partner-site projection. RotoGrinders does not publish how it differs from "
                "FPTS (it does differ on all six rows), so it is not reproduced.",
    "PRIZEPICKS": "Equalled FPTS exactly on all six public rows, i.e. RotoGrinders' own "
                  "projection re-published under a partner brand. Not emitted, because RGENGY "
                  "cannot verify that equivalence holds generally (IR-23).",
    "REFTM": "Reference team for a comparison view; a UI affordance rather than a projection.",
    "REFOPP": "Reference opponent for a comparison view; a UI affordance rather than a projection.",
    "PARK": "Ballpark identifier. RGENGY derives a park FACTOR from observed splits "
            "(engines.park_factor_from_splits) rather than shipping a hard-coded park table, and "
            "exposes it in extra['park_factor'].",
    "SLATE": "NFL slate label; a UI grouping rather than a projection.",
    "INJURY": "Mapped for NFL; absent from the other grids.",
    "PP": "Unpublished definition; not reproduced.",
    "UD": "Unpublished definition; not reproduced.",
    "P-A": "Prop-style combined stat with an unpublished definition; not reproduced.",
    "P-R": "Prop-style combined stat with an unpublished definition; not reproduced.",
    "P-R-A": "Prop-style combined stat with an unpublished definition; not reproduced.",
    "B-S": "Prop-style combined stat with an unpublished definition; not reproduced.",
    "R-A": "Prop-style combined stat with an unpublished definition; not reproduced.",
    "POSDRK": "Position rank on DraftKings under an unpublished ranking rule; not reproduced.",
    "POSFAN": "Position rank on FanDuel under an unpublished ranking rule; not reproduced.",
    "RANGE": "Unpublished definition; not reproduced.",
    "KPTS": "Kicker points; the NFL scoring table's DST/kicker tiers are unaudited (L-04).",
    "TOTYD": "Unpublished combination rule; not reproduced.",
    "TEAMNAME": ("Full team name. RGENGY carries the team ABBREVIATION from the league feed and "
                 "has no verified abbreviation-to-name table, so emitting one would be invented "
                 "text in a column that looks like retrieved data."),
    "TOTAL": ("Published immediately after SPREAD and O/U on the WNBA grid with no definition. It "
              "may be RotoGrinders' own projected game total rather than the market line; filling "
              "it with Game.odds.over_under (which is already emitted under O/U) would present an "
              "unverified substitution as their number. Left null. IR-22."),
    "TOTTD": "Unpublished combination rule; not reproduced.",
    "PARUYD": "Unpublished definition; not reproduced.",
    "PARUTD": "Unpublished definition; not reproduced.",
    "RUREYD": "Unpublished definition; not reproduced.",
    "RURETD": "Unpublished definition; not reproduced.",
}


def _resolve(player: Player, path: str, site: str) -> Any:
    if path == "name":
        return player.name
    if path == "salary":
        return player.salary
    if path == "position":
        return "/".join(player.positions) or None
    if path == "team":
        return player.team
    if path == "opp":
        return player.opp
    if path == "status":
        return player.status
    if path == "fpts":
        return player.fpts.get(site)
    if path == "floor":
        return player.floor
    if path == "ceil":
        return player.ceil
    if path == "pown":
        # RotoGrinders renders POWN as a percentage with two decimals (e.g. 23.36%).
        return None if player.pown is None else round(player.pown * 100.0, 2)
    if path == "value_per_1k":
        # FPTS/$ - identity verified exactly against the public grid.
        salary = player.salary
        pts = player.fpts.get(site)
        if not salary or pts is None:
            return None
        return round(pts / (salary / 1000.0), 2)
    if path.startswith("weather."):
        w = player.extra.get("weather") or {}
        return w.get(path.split(".", 1)[1])
    if path == "batting_order":
        return player.extra.get("batting_order")
    if path.startswith("game_line."):
        line = player.extra.get("game_line") or {}
        return line.get(path.split(".", 1)[1])
    if path.startswith("projected."):
        return player.projected.get(path.split(".", 1)[1])
    return None


def _row_for(player: Player, site: str, sport: str) -> Dict[str, Any]:
    """One grid row, keyed in RotoGrinders' own column order.

    Every column of the observed RG schema is present in the returned dict.  The
    ones RGENGY cannot fill are present with the value ``None`` rather than being
    omitted, because an omitted key cannot be diffed against RG's grid: the whole
    point of emitting their schema is to make the two products comparable column
    by column, and a short row silently defeats that.  ``grid_rows`` lists the
    nulls in ``unfilled_columns`` with a reason for each.
    """
    from rgengy.models import RG_GRID_COLUMNS

    mapping = _COLUMN_MAP.get(sport, {})
    # Prefer RG's observed column order; fall back to the mapped keys for a sport
    # whose grid header was never transcribed (nba, nhl).
    columns = RG_GRID_COLUMNS.get(sport) or list(mapping)
    row: Dict[str, Any] = {}
    for column in columns:
        path = mapping.get(column)
        row[column] = _resolve(player, path, site) if path else None
    # Columns RGENGY can derive even where the sport's grid does not list them.
    if "FPTS/$" not in row and player.salary:
        pts = player.fpts.get(site)
        row["FPTS/$"] = round(pts / (player.salary / 1000.0), 2) if pts else None
    return row
