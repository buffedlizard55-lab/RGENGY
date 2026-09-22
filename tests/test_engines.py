"""Projection engines: dispatch, environment scaling, and the refusal to fabricate."""

from __future__ import annotations

import unittest

from helpers import REPO  # noqa: F401

from rgengy import engines
from rgengy.engines import (BaseballEngine, BasketballEngine, FootballEngine, HockeyEngine,
                            LeagueAverages, ProjectionContext, band_from_distribution,
                            band_from_ratio, engine_for, fpts_distribution,
                            park_factor_from_splits, quality_start_probability,
                            team_win_probability, win_probability)

LEAGUE = LeagueAverages(n_teams=30, runs_scored_per_game=4.5, runs_allowed_per_game=4.5,
                        points_per_game=112.0, points_allowed_per_game=112.0)


def ctx(**kw):
    kw.setdefault("league", LEAGUE)
    return ProjectionContext(**kw)


class TestEngineRegistry(unittest.TestCase):
    def test_every_covered_sport_has_an_engine(self):
        for sport in ("mlb", "nba", "wnba", "nhl", "nfl"):
            self.assertIsNotNone(engine_for(sport))

    def test_unknown_sport_raises_rather_than_defaulting(self):
        with self.assertRaises(KeyError):
            engine_for("curling")

    def test_band_mode_selects_the_banding_rule(self):
        self.assertEqual(engine_for("mlb", band_mode="distribution").band_mode, "distribution")
        self.assertEqual(engine_for("mlb", band_mode="rg_band").band_mode, "rg_band")

    def test_wnba_reuses_the_basketball_engine(self):
        self.assertIsInstance(engine_for("wnba"), BasketballEngine)


class TestPositionDispatch(unittest.TestCase):
    """The bug class: projecting a pitcher with hitter stat keys."""

    def test_pitcher_uses_pitcher_keys(self):
        e = BaseballEngine()
        season = {"ip": 100.0, "k": 120.0, "er": 40.0, "ha": 95.0, "bba": 30.0, "hbpa": 5.0}
        out = e.project_player({"positions": ["P"], "season": season, "games": 20},
                               ctx(sport="mlb", team_expected_output=4.5,
                                   opp_expected_output=4.5, win_prob=0.5))
        self.assertGreater(out["ip"], 0.0)
        self.assertGreater(out["k"], 0.0)
        self.assertIn("er", out)
        self.assertNotIn("hr", out, "a pitcher must not be projected with hitter keys")
        self.assertNotIn("1b", out)

    def test_hitter_uses_hitter_keys(self):
        e = BaseballEngine()
        season = {"pa": 600.0, "1b": 90.0, "2b": 30.0, "hr": 25.0, "rbi": 80.0,
                  "r": 75.0, "bb": 60.0, "sb": 10.0}
        out = e.project_player({"positions": ["OF"], "season": season, "games": 150},
                               ctx(sport="mlb", team_expected_output=4.5,
                                   opp_expected_output=4.5))
        self.assertGreater(out["hr"], 0.0)
        self.assertGreater(out["pa"], 0.0)
        self.assertNotIn("ip", out, "a hitter must not be projected with pitcher keys")
        self.assertNotIn("er", out)
        self.assertNotIn("win", out)

    def test_goalie_uses_goalie_keys(self):
        e = HockeyEngine()
        season = {"sv": 1200.0, "ga": 100.0, "so": 3.0, "toi": 2400.0}
        out = e.project_player({"positions": ["G"], "season": season, "games": 40},
                               ctx(sport="nhl", team_expected_output=3.0,
                                   team_season_output_pg=3.0, opp_expected_output=2.5,
                                   win_prob=0.55, win_prob_method="moneyline_devig"))
        # 1200 saves / 40 games = 30 per game
        self.assertAlmostEqual(out["sv"], 30.0, places=6)
        self.assertGreater(out["ga"], 0.0)
        self.assertAlmostEqual(out["win_goalie"], 0.55)
        self.assertNotIn("g", out, "a goalie must not be projected with skater keys")

    def test_goalie_without_a_save_sample_is_skipped_not_zeroed(self):
        e = HockeyEngine()
        c = ctx(sport="nhl")
        out = e.project_player({"positions": ["G"], "season": {"ga": 40.0}, "games": 20}, c)
        self.assertEqual(out, {})
        self.assertTrue(any("save sample" in n for n in c.notes))

    def test_skater_uses_skater_keys(self):
        e = HockeyEngine()
        season = {"g": 30.0, "a": 40.0, "sog": 200.0, "blk": 60.0, "toi": 1200.0}
        out = e.project_player({"positions": ["C"], "season": season, "games": 70},
                               ctx(sport="nhl", team_expected_output=3.0,
                                   opp_expected_output=3.0))
        self.assertGreater(out["g"], 0.0)
        self.assertNotIn("sv", out)

    def test_nfl_defence_and_kicker_are_projected(self):
        """The bug that made every NFL roster infeasible."""
        e = FootballEngine()
        dst = e.project_player({"positions": ["DST"], "games": 16,
                                "season": {"dst_sack": 40.0, "dst_int": 14.0,
                                           "dst_fum_rec": 10.0, "dst_td": 2.0}},
                               ctx(sport="nfl"))
        self.assertGreater(dst["dst_sack"], 0.0)
        self.assertNotIn("pa_yds", dst)
        k = e.project_player({"positions": ["K"], "games": 16,
                              "season": {"fg_0_39": 12.0, "fg_40_49": 8.0, "fg_50p": 3.0,
                                         "pat": 30.0}}, ctx(sport="nfl"))
        self.assertGreater(k["pat"], 0.0)
        self.assertNotIn("ru_yds", k)


class TestNoFabrication(unittest.TestCase):
    def test_empty_season_sample_returns_nothing(self):
        e = BaseballEngine()
        c = ctx(sport="mlb")
        self.assertEqual(e.project_player({"positions": ["OF"], "season": {}, "games": 0}, c), {})
        self.assertTrue(c.notes, "the engine must record WHY it produced nothing")

    def test_zero_games_returns_nothing(self):
        e = BaseballEngine()
        self.assertEqual(e.project({"hr": 10.0}, ctx(sport="mlb"), games=0), {})

    def test_pitcher_without_innings_returns_nothing(self):
        e = BaseballEngine()
        c = ctx(sport="mlb")
        out = e.project_player({"positions": ["P"], "games": 10, "season": {"k": 50.0}}, c)
        self.assertEqual(out, {})
        self.assertTrue(any("innings" in n for n in c.notes))

    def test_basketball_without_minutes_returns_nothing(self):
        e = BasketballEngine()
        c = ctx(sport="nba", opportunity_unit="minute")
        self.assertEqual(e.project_player({"positions": ["PG"], "season": {"pts": 500.0}}, c), {})

    def test_win_probability_is_never_invented(self):
        c = ctx(sport="mlb")
        prob, source = team_win_probability(c)
        self.assertEqual(prob, 0.0)
        self.assertIn("unavailable", source)

    def test_weather_adjustment_is_disabled_by_default(self):
        self.assertEqual(engines.WEATHER_AIR_DENSITY_COEFFICIENT, 0.0)


class TestWinProbability(unittest.TestCase):
    def test_market_is_preferred_over_the_differential_model(self):
        c = ctx(sport="mlb", win_prob=0.71, win_prob_method="moneyline_devig",
                team_expected_output=5.0, opp_expected_output=4.9)
        prob, source = team_win_probability(c)
        self.assertEqual(prob, 0.71)
        self.assertIn("market", source)

    def test_differential_model_is_the_fallback_and_says_so(self):
        c = ctx(sport="mlb", team_expected_output=6.0, opp_expected_output=3.0)
        prob, source = team_win_probability(c)
        self.assertGreater(prob, 0.5)
        self.assertIn("IR-03", source)

    def test_margin_can_stand_in_for_the_opponent(self):
        c = ctx(sport="mlb", team_expected_output=5.0, expected_margin=1.0)
        prob, _ = team_win_probability(c)
        self.assertAlmostEqual(prob, win_probability(5.0, 4.0), places=9)

    def test_even_game_is_a_coin_flip(self):
        self.assertAlmostEqual(win_probability(4.5, 4.5), 0.5, places=9)

    def test_monotone_in_run_differential(self):
        seq = [win_probability(4.5 + d, 4.5) for d in (-2, -1, 0, 1, 2)]
        self.assertEqual(seq, sorted(seq))

    def test_missing_side_is_zero_not_a_guess(self):
        self.assertEqual(win_probability(None, 4.0), 0.0)
        self.assertEqual(win_probability(4.0, None), 0.0)


class TestEnvironmentScaling(unittest.TestCase):
    def test_plate_appearances_are_not_scaled_by_the_run_environment(self):
        """PA is an opportunity, not an outcome (caught by the quality checks)."""
        e = BaseballEngine()
        self.assertIn("pa", e.neutral_keys)
        self.assertNotIn("pa", e.offense_keys)
        season = {"pa": 600.0, "1b": 90.0, "2b": 30.0, "hr": 25.0, "rbi": 80.0,
                  "r": 75.0, "bb": 60.0, "sb": 10.0}
        cold = e.project(season, ctx(sport="mlb", team_expected_output=3.0,
                                     team_season_output_pg=4.5,
                                     opp_season_allowed_pg=4.5), games=150)
        hot = e.project(season, ctx(sport="mlb", team_expected_output=7.0,
                                    team_season_output_pg=4.5,
                                    opp_season_allowed_pg=4.5), games=150)
        self.assertAlmostEqual(cold["pa"], hot["pa"], places=6)
        self.assertGreater(hot["hr"], cold["hr"])

    def test_higher_expected_output_raises_run_production(self):
        e = BaseballEngine()
        season = {"pa": 600.0, "1b": 90.0, "2b": 30.0, "hr": 25.0, "rbi": 80.0,
                  "r": 75.0, "bb": 60.0, "sb": 10.0}
        low = e.project(season, ctx(sport="mlb", team_expected_output=3.5,
                                    team_season_output_pg=4.5,
                                    opp_season_allowed_pg=4.5), games=150)
        high = e.project(season, ctx(sport="mlb", team_expected_output=6.0,
                                     team_season_output_pg=4.5,
                                     opp_season_allowed_pg=3.5), games=150)
        self.assertGreater(high["r"], low["r"])
        self.assertGreater(high["hr"], low["hr"])

    def test_basketball_minutes_are_the_opportunity_not_the_sample(self):
        """sample_minutes is the season total; ctx.opportunity is today's minutes."""
        e = BasketballEngine()
        season = {"pts": 1500.0, "reb": 500.0, "ast": 300.0, "stl": 100.0,
                  "blk": 50.0, "to": 200.0, "three_pm": 150.0}
        c = ctx(sport="nba", opportunity_unit="minute", opportunity=30.0,
                team_expected_output=112.0, opp_expected_output=112.0)
        out = e.project(season, c, games=75, sample_minutes=2250.0)
        # 1500 pts / 2250 min = 0.667 per min, x 30 min = 20 points
        self.assertAlmostEqual(out["pts"], 20.0, places=6)

    def test_missing_opportunity_falls_back_to_the_season_average_and_says_so(self):
        e = BasketballEngine()
        season = {"pts": 1500.0, "reb": 500.0, "ast": 300.0, "stl": 100.0,
                  "blk": 50.0, "to": 200.0, "three_pm": 150.0}
        c = ctx(sport="nba", opportunity_unit="minute", opportunity=None,
                team_expected_output=112.0, opp_expected_output=112.0)
        out = e.project(season, c, games=75, sample_minutes=2250.0)
        self.assertAlmostEqual(out["pts"], 1500.0 / 75.0, places=6)
        self.assertTrue(any("opportunity not supplied" in n for n in c.notes))

    def test_park_factor_is_neutral_when_splits_are_even(self):
        self.assertAlmostEqual(park_factor_from_splits(4.5, 4.5, 4.5), 1.0, places=6)

    def test_park_factor_is_above_one_for_a_hitter_friendly_split(self):
        self.assertGreater(park_factor_from_splits(5.5, 3.5, 4.5), 1.0)

    def test_park_factor_needs_data(self):
        self.assertIsNone(park_factor_from_splits(None, 4.0, 4.5))
        self.assertIsNone(park_factor_from_splits(5.0, 0.0, 4.5))


class TestDistributionsAndBands(unittest.TestCase):
    def test_fpts_distribution_is_exact_for_a_poisson_sum(self):
        d = fpts_distribution({"1b": 1.0, "hr": 0.25}, {"1b": 3.0, "hr": 10.0})
        self.assertAlmostEqual(d["mean"], 5.5)
        self.assertAlmostEqual(d["sd"], (9.0 + 25.0) ** 0.5)

    def test_unscored_stats_contribute_no_variance(self):
        d = fpts_distribution({"1b": 1.0, "pa": 5.0}, {"1b": 3.0})
        self.assertAlmostEqual(d["mean"], 3.0)
        self.assertAlmostEqual(d["sd"], 3.0)

    def test_distribution_band_is_wider_above_than_below(self):
        b = band_from_distribution(20.0, 8.0)
        self.assertAlmostEqual(b["floor"], 20.0 - engines.FLOOR_Z * 8.0)
        self.assertAlmostEqual(b["ceil"], 20.0 + engines.CEIL_Z * 8.0)
        self.assertGreater(b["ceil"] - 20.0, 20.0 - b["floor"])

    def test_floor_is_clamped_at_zero(self):
        self.assertEqual(band_from_distribution(2.0, 10.0)["floor"], 0.0)

    def test_rg_band_uses_the_observed_ratios(self):
        b = band_from_ratio(13.48)
        self.assertAlmostEqual(b["floor"], 13.48 * engines.RG_OBSERVED_FLOOR_RATIO, places=6)
        self.assertAlmostEqual(b["ceil"], 13.48 * engines.RG_OBSERVED_CEIL_RATIO, places=6)

    def test_rg_band_constants_match_the_fixture(self):
        # IR-25: the floor ratio is the mean over the FIVE rows with a non-zero
        # floor (one row published FLOOR=0 and is excluded, documented); the
        # ceiling is the all-rows mean over six.
        self.assertAlmostEqual(engines.RG_OBSERVED_FLOOR_RATIO, 0.30296, places=5)
        self.assertEqual(engines.RG_OBSERVED_FLOOR_SAMPLE_SIZE, 5)
        self.assertAlmostEqual(engines.RG_OBSERVED_CEIL_RATIO, 2.2229, places=4)
        self.assertEqual(engines.RG_OBSERVED_CEIL_SAMPLE_SIZE, 6)
        self.assertEqual(engines.RG_OBSERVED_SAMPLE_SIZE, 6)
        self.assertIn("rotogrinders.com", engines.RG_OBSERVED_SOURCE)

    def test_rg_band_constants_recompute_from_the_fixture(self):
        """The provenance chain fixture -> constant must reproduce (IR-25)."""
        import json
        from pathlib import Path
        fixture = Path(__file__).parent / "fixtures" / "rg_public_mlb_grid_2026-09-22.json"
        rows = json.loads(fixture.read_text())["rows"]
        fr = [float(r["FLOOR"]) / float(r["FPTS"]) for r in rows
              if float(r["FPTS"]) and float(r["FLOOR"]) > 0]
        cr = [float(r["CEIL"]) / float(r["FPTS"]) for r in rows if float(r["FPTS"])]
        self.assertEqual(len(fr), engines.RG_OBSERVED_FLOOR_SAMPLE_SIZE)
        self.assertEqual(len(cr), engines.RG_OBSERVED_CEIL_SAMPLE_SIZE)
        self.assertAlmostEqual(sum(fr) / len(fr), engines.RG_OBSERVED_FLOOR_RATIO, places=4)
        self.assertAlmostEqual(sum(cr) / len(cr), engines.RG_OBSERVED_CEIL_RATIO, places=4)
        # The all-rows floor mean is also pinned so the exclusion stays visible.
        all_fr = [float(r["FLOOR"]) / float(r["FPTS"]) for r in rows if float(r["FPTS"])]
        self.assertLess(sum(all_fr) / len(all_fr), engines.RG_OBSERVED_FLOOR_RATIO,
                        "zero-floor rows lower the mean; if this flips, the exclusion "
                        "rule or the fixture changed")

    def test_rg_band_reproduces_the_public_grid_row(self):
        """Ketel Marte: RG published FPTS 13.48, FLOOR 4.02, CEIL 29.63."""
        b = band_from_ratio(13.48)
        self.assertAlmostEqual(b["floor"], 4.02, delta=0.10)
        self.assertAlmostEqual(b["ceil"], 29.63, delta=0.35)


class TestQualityStart(unittest.TestCase):
    def test_definition_is_six_ip_and_three_er(self):
        self.assertGreater(quality_start_probability(6.0, 2.0), 0.5)
        self.assertEqual(quality_start_probability(5.0, 2.0), 0.0,
                         "fewer than 6 innings can never be a quality start")
        self.assertAlmostEqual(quality_start_probability(6.0, 0.0), 1.0)

    def test_monotone_decreasing_in_earned_runs(self):
        seq = [quality_start_probability(7.0, er) for er in (0, 1, 2, 3, 5)]
        self.assertEqual(seq, sorted(seq, reverse=True))

    def test_no_innings_is_zero(self):
        self.assertEqual(quality_start_probability(0.0, 0.0), 0.0)


class TestScoreAndBand(unittest.TestCase):
    def test_attaches_mean_sd_floor_ceil_and_value(self):
        e = engine_for("mlb")
        coeff = {"1b": 3.0, "hr": 10.0}
        out = e.score_and_band({"1b": 1.0, "hr": 0.25}, coeff, salary=5200.0)
        self.assertAlmostEqual(out["fpts"], 5.5)
        self.assertGreater(out["sd"], 0.0)
        self.assertLessEqual(out["floor"], out["fpts"])
        self.assertGreaterEqual(out["ceil"], out["fpts"])
        self.assertAlmostEqual(out["fpts_per_1k"], 5.5 / 5.2, places=3)

    def test_missing_salary_does_not_crash(self):
        e = engine_for("mlb")
        out = e.score_and_band({"1b": 1.0}, {"1b": 3.0}, salary=None)
        self.assertEqual(out["fpts"], 3.0)

    def test_rg_band_mode_switches_the_rule(self):
        e = engine_for("mlb", band_mode="rg_band")
        out = e.score_and_band({"1b": 1.0}, {"1b": 3.0}, salary=3000.0)
        self.assertEqual(out["band_mode"], "rg_band")
        self.assertAlmostEqual(out["floor"], 3.0 * engines.RG_OBSERVED_FLOOR_RATIO, places=2)


if __name__ == "__main__":
    unittest.main()
