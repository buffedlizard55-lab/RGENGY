"""End-to-end pipeline tests: projection, the RG grid schema, and artefacts.

The organising rule for this file is IR-22 - every column of RotoGrinders' grid
that RGENGY cannot fill must be null AND carry a written reason.  A null with no
reason is indistinguishable from a bug, and a filled column with no source is
indistinguishable from a fabrication, so both directions are tested.
"""
import json, pathlib, sys, tempfile, unittest
import helpers  # noqa: F401
sys.path.insert(0, helpers.REPO)

from rgengy import engines, models, pipeline, quality, scoring, vegas
from rgengy.http import FetchLog
from rgengy.models import Game, Odds, Player, Slate, Weather
from rgengy.pipeline import (STAGE_COMPLETE, STAGE_DEGRADED, STAGE_UNAVAILABLE, RunResult,
                             StageResult, _resolve, _weather_ratio, grid_rows, project_players,
                             run, write_artefacts)

DATE = "2026-09-22"


def _game(home="NYY", away="BOS", *, spread=-150.0, ou=8.5, home_ml=-150, away_ml=130,
          sport="mlb", weather=None):
    return Game(sport=sport, game_id=f"{away}@{home}", starts_utc=f"{DATE}T23:05:00Z",
                home_team=home, away_team=away, home_id=home, away_id=away,
                venue="Yankee Stadium", odds=Odds(provider="test", spread=spread,
                                                  over_under=ou, home_ml=home_ml,
                                                  away_ml=away_ml, source="test"),
                weather=weather, home_implied_total=4.75, away_implied_total=3.75,
                implied_total_method="test")


def _raw(pid, name, team, positions, season, salary=4000, **kw):
    d = {"player_id": pid, "name": name, "team": team, "positions": positions,
         "season": season, "games": 100, "salary": salary}
    d.update(kw)
    return d


HITTER = dict(pa=500.0, h=140.0, doubles=28.0, triples=3.0, hr=25.0, rbi=80.0, r=85.0,
              sb=10.0, bb=55.0, hbp=4.0, k=110.0, cs=2.0)
PITCHER = dict(ip=150.0, k=150.0, ha=140.0, er=55.0, bba=40.0, hbp=5.0, win=10.0, gs=28.0,
               cg=1.0, cgso=0.0, qs=18.0)


def _mlb_raw():
    return [_raw("h1", "Hitter One", "NYY", ["OF"], HITTER, salary=5200),
            _raw("h2", "Hitter Two", "BOS", ["1B"], HITTER, salary=4800),
            _raw("p1", "Pitcher One", "NYY", ["SP"], PITCHER, salary=9500),
            _raw("p2", "Pitcher Two", "BOS", ["SP"], PITCHER, salary=8800)]


def _full_mlb_raw():
    """A pool big enough to satisfy the 10-slot DraftKings MLB roster
    (2 P, C/1B, 2B, 3B, SS, 3 OF, UTIL).  Four players cannot fill ten slots, so
    end-to-end tests that expect a lineup need this rather than ``_mlb_raw``."""
    rows = [_raw(f"p{i}", f"Pitcher {i}", "NYY" if i % 2 else "BOS", ["SP"], PITCHER,
                 salary=7000 - 100 * i) for i in range(1, 5)]
    slots = [("c1", ["C"]), ("b1", ["1B"]), ("b2", ["2B"]), ("b3", ["3B"]), ("s1", ["SS"]),
             ("o1", ["OF"]), ("o2", ["OF"]), ("o3", ["CF"]), ("u1", ["1B", "OF"])]
    for i, (pid, pos) in enumerate(slots):
        rows.append(_raw(pid, f"Batter {i}", "NYY" if i % 2 else "BOS", pos, HITTER,
                         salary=4200 - 100 * i))
    return rows


def _league():
    return engines.LeagueAverages(runs_scored_per_game=4.5, runs_allowed_per_game=4.5,
                                  points_per_game=110.0, points_allowed_per_game=110.0)


class TestColumnMapCompleteness(unittest.TestCase):
    """IR-22: no grid column may be silently dropped."""

    def test_every_observed_column_is_either_mapped_or_explained(self):
        for sport, columns in models.RG_GRID_COLUMNS.items():
            mapping = pipeline._COLUMN_MAP.get(sport, {})
            for col in columns:
                self.assertTrue(col in mapping or col in pipeline.UNMAPPED_COLUMN_REASONS,
                                f"{sport}:{col} is neither mapped nor explained")

    def test_every_explanation_refers_to_a_real_observed_column(self):
        all_columns = {c for cols in models.RG_GRID_COLUMNS.values() for c in cols}
        for reason in pipeline.UNMAPPED_COLUMN_REASONS:
            self.assertIn(reason, all_columns, f"{reason} explains a column that does not exist")

    def test_no_mapped_column_is_absent_from_the_observed_grid(self):
        for sport, mapping in pipeline._COLUMN_MAP.items():
            if sport not in models.RG_GRID_COLUMNS:
                continue          # nba/nhl mappings exist but their grids are unobserved
            for col in mapping:
                self.assertIn(col, models.RG_GRID_COLUMNS[sport], f"{sport}:{col} is an orphan")

    def test_every_explanation_is_a_real_sentence(self):
        for col, reason in pipeline.UNMAPPED_COLUMN_REASONS.items():
            self.assertGreater(len(reason), 25, f"{col}: reason is too thin to act on")
            self.assertTrue(reason.endswith("."), col)

    def test_fpts_dollar_is_mapped_for_every_sport(self):
        """The one RG identity RGENGY verified exactly; it must never be dropped."""
        for sport, mapping in pipeline._COLUMN_MAP.items():
            self.assertEqual(mapping.get("FPTS/$"), "value_per_1k", sport)

    def test_unpublished_rg_columns_are_never_mapped(self):
        for col in ("LEV", "SMASH", "TOPVAL", "DIFFERENCE", "OBFPTS", "OPTO", "TEAMOWN"):
            for sport, mapping in pipeline._COLUMN_MAP.items():
                self.assertNotIn(col, mapping, f"{sport}:{col} has no published definition")


class TestResolve(unittest.TestCase):
    def setUp(self):
        self.p = Player(sport="mlb", player_id="h1", name="Hitter One", team="NYY", opp="BOS",
                        positions=["OF", "1B"], salary=5000, site="draftkings",
                        stats={}, projected={"pa": 4.2, "hr": 0.25},
                        fpts={"draftkings": 12.5}, floor=3.8, ceil=27.5, pown=0.2336)
        self.p.status = "P"
        self.p.extra["batting_order"] = 3
        self.p.extra["weather"] = {"wind": "8 mph out to RF", "temp_f": 72, "desc": "Clear"}
        self.p.extra["game_line"] = {"spread": -1.5, "over_under": 8.5}

    def test_scalar_paths(self):
        self.assertEqual(_resolve(self.p, "name", "draftkings"), "Hitter One")
        self.assertEqual(_resolve(self.p, "salary", "draftkings"), 5000)
        self.assertEqual(_resolve(self.p, "team", "draftkings"), "NYY")
        self.assertEqual(_resolve(self.p, "opp", "draftkings"), "BOS")
        self.assertEqual(_resolve(self.p, "status", "draftkings"), "P")
        self.assertEqual(_resolve(self.p, "floor", "draftkings"), 3.8)
        self.assertEqual(_resolve(self.p, "ceil", "draftkings"), 27.5)

    def test_position_is_slash_joined(self):
        self.assertEqual(_resolve(self.p, "position", "draftkings"), "OF/1B")

    def test_a_player_with_no_position_resolves_to_null_not_empty_string(self):
        self.p.positions = []
        self.assertIsNone(_resolve(self.p, "position", "draftkings"))

    def test_fpts_is_site_specific(self):
        self.assertEqual(_resolve(self.p, "fpts", "draftkings"), 12.5)
        self.assertIsNone(_resolve(self.p, "fpts", "fanduel"))

    def test_pown_is_rendered_as_a_two_dp_percentage(self):
        self.assertEqual(_resolve(self.p, "pown", "draftkings"), 23.36)

    def test_an_absent_pown_stays_null(self):
        self.p.pown = None
        self.assertIsNone(_resolve(self.p, "pown", "draftkings"))

    def test_value_per_1k_matches_the_verified_identity(self):
        self.assertEqual(_resolve(self.p, "value_per_1k", "draftkings"), 2.5)

    def test_value_per_1k_is_null_without_a_salary(self):
        self.p.salary = None
        self.assertIsNone(_resolve(self.p, "value_per_1k", "draftkings"))

    def test_projected_stats_use_a_dotted_path(self):
        self.assertEqual(_resolve(self.p, "projected.pa", "draftkings"), 4.2)
        self.assertIsNone(_resolve(self.p, "projected.nonsense", "draftkings"))

    def test_weather_and_game_line_use_dotted_paths(self):
        self.assertEqual(_resolve(self.p, "weather.temp_f", "draftkings"), 72)
        self.assertEqual(_resolve(self.p, "game_line.spread", "draftkings"), -1.5)
        self.assertEqual(_resolve(self.p, "game_line.over_under", "draftkings"), 8.5)

    def test_a_missing_game_line_resolves_to_null(self):
        self.p.extra["game_line"] = None
        self.assertIsNone(_resolve(self.p, "game_line.spread", "draftkings"))

    def test_an_unknown_path_is_null_rather_than_an_error(self):
        self.assertIsNone(_resolve(self.p, "not_a_real_column", "draftkings"))


class TestWeatherRatio(unittest.TestCase):
    def test_the_adjustment_is_disabled_by_default(self):
        """Applying an unvalidated sensitivity would fabricate precision."""
        self.assertEqual(engines.WEATHER_AIR_DENSITY_COEFFICIENT, 0.0)
        for density in (0.9, vegas.ISA_AIR_DENSITY_KG_M3, 1.4):
            for sport in ("mlb", "nfl", "nba"):
                self.assertEqual(_weather_ratio(density, sport), 1.0)

    def test_enabling_the_coefficient_makes_thin_air_help_scoring(self):
        original = engines.WEATHER_AIR_DENSITY_COEFFICIENT
        try:
            engines.WEATHER_AIR_DENSITY_COEFFICIENT = 1.0
            self.assertGreater(_weather_ratio(1.0, "mlb"), 1.0)     # thinner than ISA
            self.assertLess(_weather_ratio(1.4, "mlb"), 1.0)        # denser than ISA
            self.assertEqual(_weather_ratio(vegas.ISA_AIR_DENSITY_KG_M3, "mlb"), 1.0)
        finally:
            engines.WEATHER_AIR_DENSITY_COEFFICIENT = original


class TestProjectPlayers(unittest.TestCase):
    def setUp(self):
        self.games = [_game()]
        self.players, warns, stage = project_players(
            _mlb_raw(), self.games, "mlb", _league(), "draftkings")
        self.warnings = warns

    def test_every_raw_row_becomes_a_player(self):
        self.assertEqual(len(self.players), 4)
        self.assertEqual([p.player_id for p in self.players], ["h1", "h2", "p1", "p2"])

    def test_opponent_is_taken_from_the_game_not_the_raw_row(self):
        self.assertEqual(self.players[0].opp, "BOS")
        self.assertEqual(self.players[1].opp, "NYY")

    def test_projections_are_nonnegative_and_rounded(self):
        for p in self.players:
            for stat, v in p.projected.items():
                self.assertGreaterEqual(v, 0.0, f"{p.player_id}.{stat} = {v}")
                self.assertEqual(v, round(v, 4))

    def test_fpts_are_scored_with_the_shipped_table(self):
        table = scoring.load("mlb", "draftkings")
        for p in self.players:
            self.assertAlmostEqual(p.fpts["draftkings"], table.score(p.projected), places=2)

    def test_floor_is_below_the_projection_and_ceil_above_it(self):
        for p in self.players:
            if p.fpts["draftkings"] > 0:
                self.assertLess(p.floor, p.fpts["draftkings"])
                self.assertGreater(p.ceil, p.fpts["draftkings"])

    def test_the_environment_ratio_is_recorded_for_audit(self):
        for p in self.players:
            self.assertIn("team_output_ratio", p.extra["environment_ratio"])
            self.assertIn("weather_ratio", p.extra["environment_ratio"])

    def test_the_market_line_is_carried_onto_the_player(self):
        line = self.players[0].extra["game_line"]
        self.assertEqual(line["spread"], -150.0)
        self.assertEqual(line["over_under"], 8.5)

    def test_win_probability_has_one_documented_origin(self):
        """IR-23: derived from the market line in the pipeline, never inside an engine."""
        for p in self.players:
            line = p.extra["game_line"]
            self.assertIsNotNone(line["win_prob"])
            self.assertTrue(line["win_prob_method"])
            self.assertGreater(line["win_prob"], 0.0)
            self.assertLess(line["win_prob"], 1.0)

    def test_the_home_side_is_favoured_when_the_line_says_so(self):
        home = next(p for p in self.players if p.team == "NYY")
        away = next(p for p in self.players if p.team == "BOS")
        self.assertGreater(home.extra["game_line"]["win_prob"],
                           away.extra["game_line"]["win_prob"])

    def test_a_game_with_no_line_claims_no_win_probability(self):
        g = _game(home_ml=None, away_ml=None, spread=None)
        players, warns, _ = project_players(_mlb_raw(), [g], "mlb", _league(), "draftkings")
        self.assertTrue(any("no team win probability" in w for w in warns), warns)
        self.assertIsNone(players[0].extra["game_line"]["win_prob"])

    def test_a_player_with_no_projection_is_kept_at_zero_and_flagged(self):
        """IR-19: dropping them would make an entire roster slot unfillable."""
        raw = _mlb_raw() + [_raw("h3", "No Sample", "NYY", ["OF"], {}, salary=3000)]
        players, warns, _ = project_players(raw, self.games, "mlb", _league(), "draftkings")
        self.assertEqual(len(players), 5)
        ghost = next(p for p in players if p.player_id == "h3")
        self.assertEqual(ghost.fpts["draftkings"], 0.0)
        self.assertTrue(any("No Sample" in w and "retained" in w for w in warns), warns)

    def test_an_empty_slate_produces_no_players_and_no_crash(self):
        players, warns, stage = project_players([], [], "mlb", _league(), "draftkings")
        self.assertEqual(players, [])

    def test_an_all_zero_projection_is_flagged_as_separately_as_an_empty_one(self):
        """A 0.0 that looks like a real bust projection is the dangerous case."""
        raw = _mlb_raw() + [_raw("h3", "No Sample", "NYY", ["OF"], {}, salary=3000)]
        players, warns, _ = project_players(raw, self.games, "mlb", _league(), "draftkings")
        ghost = next(p for p in players if p.player_id == "h3")
        self.assertEqual(ghost.fpts["draftkings"], 0.0)
        self.assertTrue(any("No Sample" in w and "zero" in w for w in warns), warns)

    def test_an_unmapped_raw_team_leaves_the_opponent_null(self):
        raw = [_raw("x1", "Orphan", "TEX", ["OF"], HITTER)]
        players, _, _ = project_players(raw, self.games, "mlb", _league(), "draftkings")
        self.assertIsNone(players[0].opp)
        self.assertIsNone(players[0].extra["game_line"])

    def test_band_mode_is_passed_through_to_the_engine(self):
        players, _, _ = project_players(_mlb_raw(), self.games, "mlb", _league(),
                                        "draftkings", band_mode="rg_band")
        self.assertEqual(players[0].extra["band_mode"], "rg_band")

    def test_an_invalid_band_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            project_players(_mlb_raw(), self.games, "mlb", _league(), "draftkings",
                            band_mode="rg_observed")


class TestGridRows(unittest.TestCase):
    def _result(self, sport="mlb", site="draftkings", players=None):
        slate = Slate(sport=sport, date=DATE, site=site, games=[_game()],
                      players=players if players is not None else [], lineups=[], meta={})
        return RunResult(sport=sport, date=DATE, site=site,
                         stages=[StageResult("project", STAGE_COMPLETE)], slate=slate,
                         report=quality.QualityReport())

    def _filled_result(self):
        players, _, _ = project_players(_mlb_raw(), [_game()], "mlb", _league(), "draftkings")
        players, _ = pipeline.attach_ownership(players, "draftkings")
        return self._result(players=players)

    def test_rows_are_emitted_in_rg_column_order(self):
        g = grid_rows(self._filled_result())
        self.assertEqual(g["rg_column_schema"], models.RG_GRID_COLUMNS["mlb"])
        self.assertEqual(list(g["rows"][0]), models.RG_GRID_COLUMNS["mlb"])

    def test_the_schema_is_marked_observed_only_where_it_was_transcribed(self):
        self.assertTrue(grid_rows(self._filled_result())["rg_column_schema_observed"])
        self.assertIn("rotogrinders.com/projected-stats/mlb",
                      grid_rows(self._filled_result())["rg_column_schema_source"])

    def test_an_unobserved_schema_says_so_and_cites_no_source(self):
        g = grid_rows(self._result(sport="nba"))
        self.assertFalse(g["rg_column_schema_observed"])
        self.assertIsNone(g["rg_column_schema_source"])
        self.assertIn("NOT transcribed", g["rg_column_schema_note"])

    def test_every_unfilled_column_carries_a_reason(self):
        g = grid_rows(self._filled_result())
        self.assertTrue(g["unfilled_columns"])
        for col in g["unfilled_columns"]:
            self.assertTrue(g["unfilled_column_reasons"].get(col), f"{col} has no reason")

    def test_filled_and_unfilled_counts_are_consistent_with_the_schema(self):
        g = grid_rows(self._filled_result())
        self.assertEqual(g["n_filled"] + g["n_unfilled"], len(models.RG_GRID_COLUMNS["mlb"]))
        self.assertEqual(g["n_rows"], 4)

    def test_unfilled_cells_are_null_never_zero(self):
        g = grid_rows(self._filled_result())
        for row in g["rows"]:
            for col in g["unfilled_columns"]:
                self.assertIsNone(row[col], f"{col} was filled with {row[col]!r}")

    def test_an_empty_slate_reports_zero_rows_without_crashing(self):
        g = grid_rows(self._result())
        self.assertEqual(g["n_rows"], 0)
        self.assertEqual(g["n_filled"], 0)
        self.assertEqual(g["unfilled_columns"], models.RG_GRID_COLUMNS["mlb"])

    def test_a_slate_with_no_result_slate_is_still_serialisable(self):
        r = RunResult(sport="mlb", date=DATE, site="draftkings",
                      stages=[StageResult("slate", STAGE_UNAVAILABLE)])
        g = grid_rows(r)
        self.assertEqual(g["n_rows"], 0)
        json.dumps(g)

    def test_the_grid_is_json_serialisable(self):
        json.dumps(grid_rows(self._filled_result()))


class TestEndToEndRun(unittest.TestCase):
    def test_run_produces_a_complete_result_from_supplied_data(self):
        result = run("mlb", DATE, "draftkings", games=[_game()], players_raw=_full_mlb_raw(),
                     league=_league(), n_lineups=2, n_sims=50, field_size=20,
                     enable_weather=False)
        self.assertEqual(result.sport, "mlb")
        self.assertIsNotNone(result.slate)
        self.assertEqual(len(result.slate.players), 13)
        self.assertTrue(result.slate.lineups, "a full pool must produce at least one lineup")
        self.assertIsNotNone(result.report)
        self.assertIn(result.overall_status, (STAGE_COMPLETE, STAGE_DEGRADED))

    def test_every_lineup_respects_the_roster_and_the_salary_cap(self):
        result = run("mlb", DATE, "draftkings", games=[_game()], players_raw=_full_mlb_raw(),
                     league=_league(), n_lineups=3, n_sims=20, field_size=10,
                     enable_weather=False)
        tmpl = models.default_roster("mlb", "draftkings")
        cap, n_slots = tmpl["salary_cap"], tmpl["n_players"]
        self.assertTrue(result.slate.lineups)
        for lineup in result.slate.lineups:
            roster = lineup["players"]
            self.assertTrue(lineup["feasible"])
            self.assertEqual(len(roster), n_slots)
            self.assertEqual(len({p["id"] for p in roster}), n_slots,
                             "a player may not appear twice in one lineup")
            self.assertLessEqual(sum(p["salary"] for p in roster), cap)
            self.assertEqual(lineup["salary_used"], sum(p["salary"] for p in roster))
            self.assertEqual(lineup["salary_cap"], cap)
            self.assertEqual(lineup["salary_remaining"], cap - lineup["salary_used"])
            self.assertAlmostEqual(lineup["projected_points"],
                                   sum(p["fpts"] for p in roster), places=2)
            self.assertEqual(lineup["site"], "draftkings")

    def test_every_roster_slot_is_filled_by_an_eligible_player(self):
        result = run("mlb", DATE, "draftkings", games=[_game()], players_raw=_full_mlb_raw(),
                     league=_league(), n_lineups=1, n_sims=10, field_size=5,
                     enable_weather=False)
        lineup = result.slate.lineups[0]
        tmpl = models.default_roster("mlb", "draftkings")
        self.assertEqual(set(lineup["slots"]), {r.label for r in tmpl["slots"]})
        by_name = {p["name"]: p for p in lineup["players"]}
        seen = []
        for rule in tmpl["slots"]:
            names = lineup["slots"][rule.label]
            self.assertEqual(len(names), rule.count, rule.label)
            for name in names:
                picked = by_name.get(name)
                self.assertIsNotNone(picked, f"slot {rule.label} names {name!r}, "
                                             f"who is not in the roster")
                self.assertTrue(set(rule.eligible) & set(picked["positions"]),
                                f"{name} ({picked['positions']}) is not eligible for "
                                f"{rule.label} ({rule.eligible})")
                seen.append(name)
        self.assertEqual(len(seen), len(set(seen)),
                         f"the same player fills two slots: {seen}")

    def test_a_pool_too_small_to_fill_the_roster_reports_infeasible_not_a_guess(self):
        result = run("mlb", DATE, "draftkings", games=[_game()], players_raw=_mlb_raw(),
                     league=_league(), n_lineups=2, n_sims=20, field_size=10,
                     enable_weather=False)
        self.assertEqual(result.slate.lineups, [])
        stage = next(s for s in result.stages if s.name == "optimizer")
        self.assertEqual(stage.status, STAGE_UNAVAILABLE)
        self.assertTrue(stage.reason and len(stage.reason) > len("no feasible lineup"),
                        "the optimizer's own explanation must reach the stage, not a generic string")
        self.assertTrue(any("optimizer:" in w for w in result.warnings), result.warnings)

    def test_the_infeasibility_warning_names_the_salary_cap(self):
        result = run("mlb", DATE, "draftkings", games=[_game()], players_raw=_mlb_raw(),
                     league=_league(), n_lineups=1, n_sims=10, field_size=5,
                     enable_weather=False)
        self.assertIn("50000", " ".join(result.warnings))

    def test_a_successful_optimisation_adds_no_infeasibility_warning(self):
        result = run("mlb", DATE, "draftkings", games=[_game()], players_raw=_full_mlb_raw(),
                     league=_league(), n_lineups=1, n_sims=10, field_size=5,
                     enable_weather=False)
        self.assertFalse(any("optimizer:" in w for w in result.warnings), result.warnings)
        self.assertEqual(next(s for s in result.stages if s.name == "optimizer").status,
                         STAGE_COMPLETE)

    def test_the_run_is_deterministic_for_a_fixed_seed_input(self):
        kwargs = dict(games=[_game()], players_raw=_full_mlb_raw(), league=_league(),
                      n_lineups=2, n_sims=30, field_size=15, enable_weather=False)
        a = run("mlb", DATE, "draftkings", **kwargs).to_dict()
        b = run("mlb", DATE, "draftkings", **kwargs).to_dict()
        self.assertEqual(a["slate"]["players"], b["slate"]["players"])
        self.assertEqual(a["slate"]["lineups"], b["slate"]["lineups"])

    def test_a_run_without_a_network_still_reports_its_stage_honestly(self):
        """No outbound network in this environment: the slate stage must say so,
        never quietly substitute invented games."""
        log = FetchLog()
        result = run("mlb", DATE, "draftkings", games=[], players_raw=[], league=_league(),
                     log=log, enable_weather=False, use_cache=False)
        statuses = {s.name: s.status for s in result.stages}
        self.assertIn(STAGE_UNAVAILABLE, statuses.values(), statuses)

    def test_quality_checks_run_and_are_recorded(self):
        result = run("mlb", DATE, "draftkings", games=[_game()], players_raw=_mlb_raw(),
                     league=_league(), n_lineups=1, n_sims=20, field_size=10,
                     enable_weather=False)
        for check in ("zero_projection", "duplicate_player_id", "implausible_value",
                      "ownership_normalisation", "scoring_coverage",
                      "representation_double_count"):
            self.assertIn(check, result.report.checks_run)

    def test_the_result_serialises_to_json(self):
        result = run("mlb", DATE, "draftkings", games=[_game()], players_raw=_mlb_raw(),
                     league=_league(), n_lineups=1, n_sims=20, field_size=10,
                     enable_weather=False)
        json.dumps(result.to_dict())

    def test_an_unknown_sport_does_not_produce_a_silent_empty_run(self):
        result = run("curling", DATE, "draftkings", games=[], players_raw=[],
                     league=None, enable_weather=False)
        self.assertIn(STAGE_UNAVAILABLE, [s.status for s in result.stages])


class TestWriteArtefacts(unittest.TestCase):
    def _result(self):
        return run("mlb", DATE, "draftkings", games=[_game()], players_raw=_mlb_raw(),
                   league=_league(), n_lineups=1, n_sims=20, field_size=10,
                   enable_weather=False)

    def test_both_the_run_and_the_grid_are_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_artefacts(self._result(), pathlib.Path(tmp))
            names = sorted(p.name for p in paths)
            self.assertTrue(any(n.endswith(".grid.json") for n in names), names)
            self.assertTrue(any(not n.endswith(".grid.json") and n.endswith(".json")
                                for n in names), names)
            for p in paths:
                self.assertTrue(p.exists())
                json.loads(p.read_text())

    def test_the_grid_artefact_contains_the_rg_column_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            for p in write_artefacts(self._result(), pathlib.Path(tmp)):
                if p.name.endswith(".grid.json"):
                    doc = json.loads(p.read_text())
                    self.assertEqual(doc["rg_column_schema"], models.RG_GRID_COLUMNS["mlb"])
                    self.assertEqual(len(doc["rows"]), 4)
                    for row in doc["rows"]:
                        self.assertEqual(list(row), models.RG_GRID_COLUMNS["mlb"],
                                         "an artefact row must carry RG's full column shape")

    def test_the_output_directory_is_created_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "nested" / "deeper"
            paths = write_artefacts(self._result(), target)
            self.assertTrue(target.is_dir())
            self.assertTrue(all(p.parent == target for p in paths))


if __name__ == "__main__":
    unittest.main(verbosity=2)
