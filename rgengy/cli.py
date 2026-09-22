"""Command-line interface.

    python3 -m rgengy.cli sources                     list every endpoint with its verification status
    python3 -m rgengy.cli probe --endpoint nws.point  fetch one endpoint and print the real key paths
    python3 -m rgengy.cli verify                      re-check every endpoint, write verification.json
    python3 -m rgengy.cli scoring --sport mlb         print the scoring audit for a sport
    python3 -m rgengy.cli run --sport mlb --date ...  full pipeline -> JSON artefacts
    python3 -m rgengy.cli demo                        end-to-end run on a clearly-labelled synthetic slate

``demo`` exists because the sandbox and CI may not have network access to the
sports feeds.  It proves the optimiser, simulator, ownership model and quality
checks work end to end.  Its input is generated in-process, is labelled
``SYNTHETIC`` in every artefact, and is never presented as real data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from rgengy import __version__, pipeline, scoring, sources
from rgengy.http import FetchLog, FetchError, get_json


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _emit(obj: Any, out: Optional[Path] = None, indent: int = 2) -> None:
    text = json.dumps(obj, indent=indent, default=str)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text)


def _walk_keys(obj: Any, prefix: str = "", depth: int = 0, max_depth: int = 4,
               limit_per_level: int = 40) -> List[str]:
    """Flatten a JSON payload into dotted key paths, for schema discovery."""
    out: List[str] = []
    if depth > max_depth:
        return out
    if isinstance(obj, dict):
        for i, (k, v) in enumerate(obj.items()):
            if i >= limit_per_level:
                out.append(f"{prefix}...(+{len(obj) - i} more keys)")
                break
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                out.append(path)
                out.extend(_walk_keys(v, path, depth + 1, max_depth, limit_per_level))
            else:
                out.append(f"{path} = {v!r}")
    elif isinstance(obj, list):
        if obj:
            out.extend(_walk_keys(obj[0], f"{prefix}[0]", depth + 1, max_depth, limit_per_level))
        else:
            out.append(f"{prefix} = [] (empty)")
    return out


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_sources(args: argparse.Namespace) -> int:
    rows = sources.registry_rows()
    if args.json:
        _emit({"audit_date": sources.AUDIT_DATE, "summary": sources.verification_summary(),
               "endpoints": rows}, args.out)
        return 0
    summary = sources.verification_summary()
    print(f"RGENGY data-source registry  (audit date {summary['audit_date']})")
    print(f"  {summary['total_endpoints']} endpoints | "
          f"{summary['official']} official | {summary['unofficial']} unofficial | "
          f"{summary['requires_auth']} requiring auth")
    print("  status:", ", ".join(f"{k}={v}" for k, v in sorted(summary["by_status"].items())))
    print()
    for r in rows:
        flag = "OFFICIAL " if r["official"] else "unofficial"
        print(f"  [{r['verification_status']:<13}] {flag} {r['key']}")
        print(f"      {r['name']}")
        print(f"      {r['url_template']}")
        if r["docs_url"]:
            print(f"      docs: {r['docs_url']}")
        if r["terms_url"]:
            print(f"      terms: {r['terms_url']}")
        if r["replaces"]:
            print(f"      replaces: {', '.join(r['replaces'])}")
        print(f"      auth: {r['auth']}   verified: {r['verified_on'] or 'not verified'}")
        print()
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    """Fetch one endpoint live and print the real key paths.

    This is the anti-hallucination tool: instead of asserting a response shape,
    run ``probe`` and read what the endpoint actually returned.
    """
    ep = sources.get(args.endpoint)
    url = ep.url(**dict(kv.split("=", 1) for kv in (args.param or [])))
    log = FetchLog()
    print(f"probing {ep.key}\n  {url}\n  provider: {ep.provider} (official={ep.official})")
    try:
        data, prov = get_json(url, log=log, use_cache=not args.no_cache)
    except FetchError as exc:
        print(f"\nFAILED: {exc}", file=sys.stderr)
        return 2
    print(f"  status: {prov.status}  elapsed: {prov.elapsed_ms}ms  cached: {prov.from_cache}")
    print(f"\nkey paths (depth<={args.depth}):")
    for line in _walk_keys(data, max_depth=args.depth):
        print(f"  {line}")
    if args.out:
        _emit({"endpoint": ep.key, "url": url, "provenance": prov.to_dict(),
               "key_paths": _walk_keys(data, max_depth=args.depth),
               "sample": data if args.save_sample else None}, args.out)
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Re-check every registered endpoint and write a verification report."""
    log = FetchLog()
    results: List[Dict[str, Any]] = []
    for ep in sources.ENDPOINTS:
        url = _example_url(ep, args.date)
        record: Dict[str, Any] = {
            "key": ep.key, "name": ep.name, "url_tested": url,
            "provider": ep.provider, "official": ep.official,
            "declared_status": ep.verification_status,
        }
        if args.skip_reference and ep.key.startswith("rg."):
            record.update({"observed_status": "skipped",
                           "note": "reference-only endpoint; not fetched by --skip-reference"})
            results.append(record)
            continue
        try:
            _data, prov = get_json(url, log=log, use_cache=False)
            record.update({"observed_status": prov.status, "fetched_at": prov.fetched_at,
                           "elapsed_ms": prov.elapsed_ms, "ok": prov.ok})
        except FetchError as exc:
            record.update({"observed_status": exc.status, "ok": False, "error": str(exc.reason)})
        except Exception as exc:  # non-JSON reference endpoint (robots.txt, sitemaps.xml)
            record.update({"observed_status": None, "ok": False,
                           "error": f"{type(exc).__name__}: {exc}"})
        results.append(record)

    ok = sum(1 for r in results if r.get("ok"))
    report = {
        "tool": "rgengy verify",
        "version": __version__,
        "date": args.date,
        "endpoints_tested": len(results),
        "endpoints_ok": ok,
        "endpoints_failed": len(results) - ok,
        "results": results,
    }
    _emit(report, args.out)
    if not args.out:
        pass
    print(f"\n{ok}/{len(results)} endpoints reachable", file=sys.stderr)
    return 0 if ok == len(results) else 1


def _example_url(ep: sources.Endpoint, date: str) -> str:
    """Fill an endpoint's template with plausible example parameters."""
    defaults: Dict[str, Dict[str, str]] = {
        "mlb.schedule": {"date": date},
        "mlb.schedule_plain": {"date": date},
        "mlb.team_stats": {"team_id": "147", "group": "hitting", "season": "2026"},
        "mlb.player_stats": {"person_id": "607074", "group": "pitching", "season": "2026"},
        "mlb.venue": {"venue_id": "3313"},
        "nws.point": {"lat": "33.4484", "lon": "-112.0740"},
        "nws.gridpoint": {"grid_id": "PSR", "grid_x": "159", "grid_y": "58"},
        "nhl.scoreboard": {"date": date},
        "nhl.club_schedule": {"club": "TOR", "season": "20262027"},
        "nhl.player_landing": {"player_id": "8478483"},
        "espn.scoreboard": {"sport_path": "football/nfl"},
        "espn.odds": {"sport": "football", "league": "nfl", "event_id": "401872932",
                      "competition_id": "401872932"},
        "nba.cdn_scoreboard": {},
        "rg.public_grid": {"sport": "mlb"},
        "rg.robots": {},
        "rg.sitemaps": {},
    }
    params = defaults.get(ep.key, {})
    try:
        return ep.url(**params)
    except KeyError:
        return ep.url_template


def cmd_scoring(args: argparse.Namespace) -> int:
    if args.json:
        _emit(scoring.audit(), args.out)
        return 0
    audit = scoring.audit()
    print(f"scoring tables: {len(audit['tables'])} | "
          f"disputed values: {audit['disputed_total']} | "
          f"operator-confirmed values: {audit['operator_confirmed_total']}")
    print()
    for t in audit["tables"]:
        if args.sport and not t["key"].startswith(args.sport + ":"):
            continue
        flag = "" if not t["disputed"] else f"  DISPUTED: {', '.join(t['disputed'])}"
        print(f"  {t['key']:<20} {t['n_values']:>3} values{flag}")
    print()
    print("NOTE: 0 values are operator-confirmed. Every operator scoring page sits inside a")
    print("      logged-in app, so all tables are built from secondary sources. See")
    print("      docs/09-irregularities.md and docs/10-roadmap-and-limitations.md (L-02).")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    log = FetchLog()
    players_raw = None
    if args.players:
        players_raw = json.loads(Path(args.players).read_text(encoding="utf-8"))
        if isinstance(players_raw, dict):
            players_raw = players_raw.get("players")
    league = None
    if args.league:
        raw = json.loads(Path(args.league).read_text(encoding="utf-8"))
        from rgengy.engines import LeagueAverages
        league = LeagueAverages(**{k: v for k, v in raw.items() if k in LeagueAverages.__annotations__})

    result = pipeline.run(
        sport=args.sport, date=args.date, site=args.site,
        players_raw=players_raw, league=league,
        n_lineups=args.lineups, n_sims=args.sims, field_size=args.field_size,
        sharp_fraction=args.sharp_fraction,
        enable_weather=not args.no_weather, band_mode=args.band_mode,
        use_cache=not args.no_cache, log=log,
    )
    paths = pipeline.write_artefacts(result, Path(args.out))
    print(f"\noverall status: {result.overall_status}")
    for s in result.stages:
        print(f"  {s.name:<14} {s.status:<12} {s.counts or ''}")
        if s.reason:
            print(f"      reason: {s.reason}")
    if result.report:
        counts = result.report.by_severity()
        print(f"\nquality findings: {counts}")
        for f in result.report.findings[: args.max_findings]:
            print(f"  [{f.severity}] {f.check}: {f.message}")
    print()
    for p in paths:
        print(f"wrote {p}")
    return 0 if not result.report.has_critical else 1


def cmd_demo(args: argparse.Namespace) -> int:
    """End-to-end run on a synthetic slate.  Labelled SYNTHETIC everywhere."""
    import random

    rng = random.Random(args.seed)
    sport = args.sport
    site = args.site
    n_teams = 8
    teams = [f"T{i:02d}" for i in range(n_teams)]

    # Synthetic games with a sport-appropriate market line so the implied-total
    # path is exercised.  Using one total range for every sport silently inflates
    # every projection through the run/point environment ratio, so the ranges
    # below are per-sport and are stated in the demo output.
    from rgengy.models import Game, Odds
    market_ranges = {
        "mlb": {"spread": (-1.5, 1.5), "total": (7.5, 10.5)},
        "nfl": {"spread": (-10.5, 10.5), "total": (40.5, 52.5)},
        "nba": {"spread": (-12.5, 12.5), "total": (210.5, 238.5)},
        "wnba": {"spread": (-12.5, 12.5), "total": (150.5, 178.5)},
        "nhl": {"spread": (-1.5, 1.5), "total": (5.0, 7.0)},
    }
    mr = market_ranges.get(sport, market_ranges["nba"])
    games: List[Game] = []
    for i in range(n_teams // 2):
        home, away = teams[i * 2], teams[i * 2 + 1]
        spread = round(rng.uniform(*mr["spread"]), 1)
        total = round(rng.uniform(*mr["total"]), 1)
        games.append(Game(
            sport=sport, game_id=f"demo-{i}", starts_utc=f"{args.date}T23:00:00Z",
            home_team=home, away_team=away, venue=f"Demo Arena {i}",
            status="Scheduled",
            odds=Odds(provider="SYNTHETIC", spread=spread, over_under=total,
                      home_ml=int(round(-110 - spread * 10)), away_ml=int(round(-110 + spread * 10)),
                      source="synthetic demo input"),
        ))

    # Synthetic players with season totals that are internally consistent.
    # One entry per roster-eligible position group.  Every group required by the
    # site's roster template must appear here, or the optimizer correctly reports
    # the roster infeasible - which is what happened for NHL and for the NFL
    # defence slot before this table was completed.
    pos_by_sport = {
        "nba": (["PG"], ["SG"], ["SF"], ["PF"], ["C"]),
        "wnba": (["PG"], ["SG"], ["SF"], ["PF"], ["C"]),
        "mlb": (["P"], ["C"], ["1B"], ["2B"], ["3B"], ["SS"], ["OF"]),
        "nfl": (["QB"], ["RB"], ["WR"], ["TE"], ["K"], ["DST"]),
        "nhl": (["C"], ["LW"], ["RW"], ["D"], ["G"]),
    }
    position_groups = pos_by_sport.get(sport, pos_by_sport["nba"])
    # Season-average team output per game, per sport, used as the denominator of
    # the environment ratio.
    season_output = {
        "mlb": (4.0, 5.5), "nfl": (18.0, 28.0), "nba": (105.0, 120.0),
        "wnba": (74.0, 90.0), "nhl": (2.6, 3.6),
    }.get(sport, (105.0, 120.0))
    # Games played in a season differ by an order of magnitude between sports, and
    # using an NBA-length sample for the NFL deflates every per-game rate.
    games_range = {
        "mlb": (110, 150), "nba": (55, 78), "wnba": (30, 40), "nfl": (12, 17), "nhl": (60, 82),
    }.get(sport, (55, 78))

    players_raw: List[Dict[str, Any]] = []
    pid = 0
    for team in teams:
        team_output = round(rng.uniform(*season_output), 2)
        opp_allowed = round(rng.uniform(*season_output), 2)
        for gi, positions in enumerate(position_groups):
            count = 3 if positions[0] in ("OF", "WR", "RB") else 2
            for _ in range(count):
                pid += 1
                mpg = round(rng.uniform(18.0, 36.0), 1) if sport in ("nba", "wnba") else None
                games_played = rng.randint(*games_range)
                # season total minutes (the sample); only basketball uses it
                minutes = round(mpg * games_played, 1) if mpg else None
                salary = float(3000 + 100 * rng.randint(0, 60))
                rates = None
                if sport in ("nba", "wnba"):
                    # Calibrate to RotoGrinders' published salary/value heuristic.
                    from rgengy import scoring as _scoring
                    target = _demo_target_fpts(salary, site)
                    rates = _basketball_rates(positions[0], rng)
                    coeff = _scoring.load(sport, site).points
                    per_min = sum(float(coeff.get(k, 0.0)) * v for k, v in rates.items())
                    rates["fpts_per_minute"] = per_min
                    rates["target_fpts"] = target
                season = _synthetic_season(
                    sport, positions[0], minutes, games_played, rng, rates=rates)
                players_raw.append({
                    "player_id": f"demo-{pid}",
                    "name": f"Demo Player {pid}",
                    "team": team,
                    "positions": positions,
                    "salary": salary,
                    "games": games_played,
                    "sample_minutes": minutes,
                    "season": season,
                    # opportunity = projected playing time for THIS game
                    "opportunity": mpg if sport in ("nba", "wnba") else 1.0,
                    "opportunity_unit": "minute" if sport in ("nba", "wnba") else "game",
                    "team_output_pg": team_output,
                    "opp_allowed_pg": opp_allowed,
                })

    from rgengy.engines import LeagueAverages
    lg_mid = round((season_output[0] + season_output[1]) / 2.0, 3)
    league = LeagueAverages(n_teams=n_teams, points_per_game=lg_mid, points_allowed_per_game=lg_mid,
                            runs_scored_per_game=lg_mid, runs_allowed_per_game=lg_mid)

    result = pipeline.run(
        sport=sport, date=args.date, site=site, games=games,
        players_raw=players_raw, league=league,
        n_lineups=args.lineups, n_sims=args.sims, field_size=args.field_size,
        sharp_fraction=args.sharp_fraction,
        enable_weather=False, band_mode=args.band_mode, use_cache=False, log=FetchLog(),
    )
    # Stamp every artefact as synthetic.  This must never be ambiguous.
    payload = result.to_dict()
    payload["SYNTHETIC"] = True
    payload["synthetic_notice"] = (
        "Every number in this artefact was generated by `rgengy demo` from an in-process "
        "seeded PRNG. There is no real player, team, salary, market line or game in this "
        "file. It exists to prove the optimiser, simulator, ownership model and quality "
        "checks work end to end without network access. It must never be used for a real "
        "contest or presented as real data."
    )
    payload["seed"] = args.seed
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"demo-{sport}-{site}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Also emit the grid-shaped view, stamped SYNTHETIC, so the demo exercises the
    # same artefact contract the real pipeline and the site consume.
    grid_payload = pipeline.grid_rows(result)
    grid_payload["SYNTHETIC"] = True
    grid_payload["synthetic_notice"] = payload["synthetic_notice"]
    grid_path = out / f"demo-{sport}-{site}.grid.json"
    grid_path.write_text(json.dumps(grid_payload, indent=2) + "\n", encoding="utf-8")

    print("SYNTHETIC DEMO - no real data in this run")
    print(f"  synthetic market ranges: spread {mr['spread']}, total {mr['total']}")
    print(f"  synthetic season output per game: {season_output}\n")
    print(f"overall status: {result.overall_status}")
    for s in result.stages:
        print(f"  {s.name:<14} {s.status:<12} {s.counts or ''}")
    if result.report:
        print(f"\nquality findings: {result.report.by_severity()}")
    if result.slate and result.slate.lineups:
        top = result.slate.lineups[0]
        print(f"\nbest lineup: {top['projected_points']} pts, "
              f"salary {top['salary_used']}/{top['salary_cap']}, exact={top['exact']}")
        for p in top["players"]:
            print(f"    {p['name']:<18} {p['positions']} ${int(p['salary']):>5}  {p['fpts']:.2f}")
    sim = payload["slate"]["meta"].get("simulation") or {}
    for r in (sim.get("results") or [])[:3]:
        print(f"  sim {r['label']}: mean={r['simulated_mean']} cash={r['cash_rate']:.1%} "
              f"top10={r['top10_rate']:.1%} roi={r['roi']:+.1%}")
    print(f"\nwrote {path}")
    print(f"wrote {grid_path}")
    print(f"  grid columns: {grid_payload['n_filled']} filled, "
          f"{grid_payload['n_unfilled']} left null (never invented)")
    return 0


def _demo_target_fpts(salary: float, site: str) -> Optional[float]:
    """Target fantasy points for a demo basketball player, from RG's own heuristic.

    RotoGrinders' FanDuel NBA strategy guide
    (https://rotogrinders.com/articles/fanduel-nba-strategy-239702, retrieved
    2026-09-22) states: "you normally want 5x a player's salary for most guys.
    That means if a particular player costs $6,000, he should score in the
    neighborhood of 30 points to be considered of value.  Elite players really
    only need to hit 4x their salary to be valuable, while bargain bin players
    should be closer to 6X."

    That is a published, checkable relationship between salary and projected
    fantasy points, so the synthetic demo is calibrated to it instead of drawing
    statlines that happen to make everyone a superstar.  Returns ``None`` for
    sports where no equivalent benchmark was retrieved - in that case the demo
    does NOT invent one.
    """
    thousands = salary / 1000.0
    # 4x at the top of the salary range, 6x at the bottom, ~5x in the middle.
    ratio = 6.0 - 2.0 * min(1.0, max(0.0, (salary - 3500.0) / 6500.0))
    return round(thousands * ratio, 2)


def _basketball_rates(position: str, rng: "random.Random") -> Dict[str, float]:
    """Per-minute production rates for a synthetic basketball player.

    Distributions are league-plausible rather than uniform-and-independent: a
    player who scores 30 also does not average 12 rebounds, 9 assists, 2 steals
    and 2.5 blocks, which is what the first draft of this generator produced and
    why its lineups scored ~57 fantasy points per player instead of ~35.
    """
    guard = position in ("PG", "SG", "G")
    big = position in ("C", "PF", "F")
    pts = rng.uniform(0.28, 0.80)
    reb = rng.uniform(0.06, 0.16) if guard else rng.uniform(0.14, 0.38)
    ast = rng.uniform(0.10, 0.26) if guard else rng.uniform(0.02, 0.14)
    stl = rng.uniform(0.006, 0.030)
    blk = rng.uniform(0.015, 0.075) if big else rng.uniform(0.002, 0.020)
    to = rng.uniform(0.045, 0.110)
    threes = pts * rng.uniform(0.10, 0.28)          # 3PM made per minute
    twos = (pts - 3.0 * threes) * rng.uniform(0.30, 0.42)
    ftm = max(0.0, pts - 3.0 * threes - 2.0 * twos)
    fgm = twos + threes
    return {
        "pts": pts, "reb": reb, "ast": ast, "stl": stl, "blk": blk, "to": to,
        "three_pm": threes, "two_pm": twos, "ftm": ftm, "fgm": fgm,
        "fga": fgm / rng.uniform(0.40, 0.55),
    }


def _synthetic_season(sport: str, position: str, minutes: Optional[float], games: int,
                      rng: "random.Random",
                      rates: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """Synthetic season totals for one demo player.

    ``minutes`` is the season total of minutes played and is only meaningful for
    basketball; it is ``None`` for every other sport.  An unknown sport raises
    rather than falling through to another sport's template, because silently
    generating defence stats for a hockey centre is worse than failing.
    """
    if sport in ("nba", "wnba"):
        if not minutes:
            raise ValueError(f"{sport} demo players need season minutes")
        # Built from per-minute RATES, then scaled by minutes.  RotoGrinders' own
        # NBA guide says "One of the easiest ways to project NBA players is by
        # looking at minutes. There's a very strong correlation between minutes on
        # the floor and fantasy points", so minutes is the lever here too.  The
        # caller passes the player's target fantasy points (see _demo_target_fpts)
        # so that the resulting value ratio matches the benchmark RotoGrinders
        # publishes: ~5x salary for most players, 4x for elite, 6x for bargain bin.
        rates = dict(rates) if rates else _basketball_rates(position, rng)
        per_min = rates.get("fpts_per_minute", 0.0)
        mpg = minutes / max(1, games)
        target = rates.pop("target_fpts", None)
        rates.pop("fpts_per_minute", None)
        MIN_MPG, MAX_MPG = 8.0, 42.0
        if target and per_min > 0:
            mpg = target / per_min
            if mpg > MAX_MPG:
                # 42 minutes is already an outlier night; rather than let the
                # player miss the value target, scale production up to what 42
                # minutes would deliver.  The alternative is silently breaking
                # the salary/value relationship the demo is calibrated to.
                scale = target / (per_min * MAX_MPG)
                rates = {k: v * scale for k, v in rates.items()}
                mpg = MAX_MPG
            elif mpg < MIN_MPG:
                scale = target / (per_min * MIN_MPG)
                rates = {k: v * scale for k, v in rates.items()}
                mpg = MIN_MPG
        season = {"min": round(mpg * games, 1)}
        for stat, rate in rates.items():
            season[stat] = round(rate * mpg * games, 1)
        return season
    if sport == "mlb":
        if position == "P":
            ip = rng.uniform(4.0, 7.0) * games
            return {"ip": round(ip, 1), "k": round(rng.uniform(5, 11) * games, 1),
                    "er": round(rng.uniform(1, 5) * games, 1), "ha": round(rng.uniform(3, 9) * games, 1),
                    "bba": round(rng.uniform(1, 4) * games, 1), "hbpa": round(rng.uniform(0, 1) * games, 1),
                    "win": round(rng.uniform(0.2, 0.7) * games, 2)}
        pa = rng.uniform(3.5, 5.0) * games
        return {"pa": round(pa, 1), "1b": round(pa * rng.uniform(0.12, 0.20), 2),
                "2b": round(pa * rng.uniform(0.04, 0.08), 2), "3b": round(pa * rng.uniform(0.005, 0.02), 2),
                "hr": round(pa * rng.uniform(0.02, 0.07), 2), "rbi": round(pa * rng.uniform(0.08, 0.16), 2),
                "r": round(pa * rng.uniform(0.09, 0.18), 2), "sb": round(pa * rng.uniform(0.0, 0.04), 2),
                "bb": round(pa * rng.uniform(0.05, 0.14), 2), "hbp": round(pa * rng.uniform(0.0, 0.02), 2),
                "k": round(pa * rng.uniform(0.12, 0.30), 2), "cs": round(pa * rng.uniform(0.0, 0.01), 2)}
    if sport == "nhl":
        # Per-game rates are league-plausible: an NHL skater averages roughly
        # 0.3 goals, 0.5 assists and 2.5 shots on goal, and a goalie faces about
        # 31 shots.  A goalie's season 'win' total is derived by the engine, so it
        # is not supplied here.
        if position == "G":
            return {"toi": 58.0 * games, "sv": round(28.0 * games, 1),
                    "ga": round(2.9 * games, 1), "so": round(0.10 * games, 2)}
        g_pg = round(rng.uniform(0.15, 0.65), 3) * games
        a_pg = round(rng.uniform(0.20, 0.95), 3) * games
        return {"toi": round(rng.uniform(12.0, 24.0) * games, 1),
                "g": round(g_pg, 1), "a": round(a_pg, 1),
                "sog": round(rng.uniform(1.2, 4.5) * games, 1),
                "blk": round(rng.uniform(0.4, 2.6) * games * (1.8 if position == "D" else 0.7), 1),
                "ppp": round(rng.uniform(0.05, 0.45) * games, 2),
                "shp": round(rng.uniform(0.0, 0.06) * games, 2),
                "hits": round(rng.uniform(1.0, 6.0) * games, 1),
                "fow": round(rng.uniform(2.0, 14.0) * games * (1.0 if position == "C" else 0.1), 1)}

    # nfl
    if position == "QB":
        return {"pa_att": 32.0 * games, "pa_cmp": 21.0 * games, "pa_yds": 245.0 * games,
                "pa_td": 1.8 * games, "pa_int": 0.8 * games, "ru_att": 3.0 * games,
                "ru_yds": 15.0 * games, "ru_td": 0.25 * games}
    if position == "RB":
        return {"ru_att": 15.0 * games, "ru_yds": 68.0 * games, "ru_td": 0.5 * games,
                "rec_tgt": 3.5 * games, "rec": 2.7 * games, "rec_yds": 22.0 * games,
                "rec_td": 0.1 * games}
    if position == "WR":
        return {"rec_tgt": 7.5 * games, "rec": 4.6 * games, "rec_yds": 62.0 * games,
                "rec_td": 0.4 * games, "ru_att": 0.3 * games, "ru_yds": 2.0 * games}
    if position == "TE":
        return {"rec_tgt": 5.0 * games, "rec": 3.3 * games, "rec_yds": 36.0 * games,
                "rec_td": 0.25 * games}
    if position == "K":
        return {"fg_0_39": 1.0 * games, "fg_40_49": 0.6 * games, "fg_50p": 0.3 * games,
                "pat": 2.2 * games}
    if sport != "nfl":
        # Never fall through to the NFL defence template for an unrecognised
        # sport: that silently produces defence stats for a hockey centre.
        raise ValueError(f"no synthetic season generator for sport {sport!r}")
    return {"dst_sack": 2.4 * games, "dst_int": 0.9 * games, "dst_fum_rec": 0.6 * games,
            "dst_td": 0.15 * games}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rgengy", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"rgengy {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("sources", help="list every registered endpoint with its verification status")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out", type=Path)
    s.set_defaults(func=cmd_sources)

    s = sub.add_parser("probe", help="fetch one endpoint live and print its real key paths")
    s.add_argument("--endpoint", required=True, choices=[e.key for e in sources.ENDPOINTS])
    s.add_argument("--param", action="append", help="key=value template parameter (repeatable)")
    s.add_argument("--depth", type=int, default=3)
    s.add_argument("--no-cache", action="store_true")
    s.add_argument("--save-sample", action="store_true")
    s.add_argument("--out", type=Path)
    s.set_defaults(func=cmd_probe)

    s = sub.add_parser("verify", help="re-check every registered endpoint")
    s.add_argument("--date", default="2026-09-22")
    s.add_argument("--out", type=Path)
    s.add_argument("--skip-reference", action="store_true",
                   help="do not fetch the rotogrinders.com reference endpoints")
    s.set_defaults(func=cmd_verify)

    s = sub.add_parser("scoring", help="print the scoring-table audit")
    s.add_argument("--sport")
    s.add_argument("--json", action="store_true")
    s.add_argument("--out", type=Path)
    s.set_defaults(func=cmd_scoring)

    s = sub.add_parser("run", help="run the full pipeline for a sport/date/site")
    s.add_argument("--sport", required=True,
                   choices=["mlb", "nba", "wnba", "nhl", "nfl"])
    s.add_argument("--date", required=True)
    s.add_argument("--site", default="draftkings", choices=["draftkings", "fanduel", "yahoo"])
    s.add_argument("--players", type=Path, help="JSON file of per-player season inputs")
    s.add_argument("--league", type=Path, help="JSON file of league averages")
    s.add_argument("--out", type=Path, default=Path("data/runs"))
    s.add_argument("--lineups", type=int, default=5)
    s.add_argument("--sims", type=int, default=500)
    s.add_argument("--field-size", type=int, default=200)
    s.add_argument("--sharp-fraction", type=float, default=0.5,
                   help="fraction of the simulated field built by the optimiser (rest is "
                        "ownership-proportional sampling)")
    s.add_argument("--band-mode", default="distribution", choices=["distribution", "rg_band"])
    s.add_argument("--no-weather", action="store_true")
    s.add_argument("--no-cache", action="store_true")
    s.add_argument("--max-findings", type=int, default=25)
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("demo", help="end-to-end run on a clearly-labelled SYNTHETIC slate")
    s.add_argument("--sport", default="nba", choices=["mlb", "nba", "nfl", "nhl", "wnba"])
    s.add_argument("--site", default="draftkings", choices=["draftkings", "fanduel", "yahoo"])
    s.add_argument("--date", default="2026-09-22")
    s.add_argument("--lineups", type=int, default=5)
    s.add_argument("--sims", type=int, default=300)
    s.add_argument("--field-size", type=int, default=100)
    s.add_argument("--sharp-fraction", type=float, default=0.5)
    s.add_argument("--band-mode", default="distribution", choices=["distribution", "rg_band"])
    s.add_argument("--seed", type=int, default=20260922)
    s.add_argument("--out", type=Path, default=Path("data/demo"))
    s.set_defaults(func=cmd_demo)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
