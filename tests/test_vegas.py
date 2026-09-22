"""Market mathematics: vig removal, implied totals, win probability, edge, EV."""

from __future__ import annotations

import unittest

from helpers import REPO  # noqa: F401

from rgengy import vegas


class TestAmericanOdds(unittest.TestCase):
    def test_positive(self):
        self.assertAlmostEqual(vegas.american_to_implied(150), 0.400)
        self.assertAlmostEqual(vegas.american_to_implied(100), 0.500)

    def test_negative(self):
        self.assertAlmostEqual(vegas.american_to_implied(-200), 2 / 3.0)
        self.assertAlmostEqual(vegas.american_to_implied(-110), 110 / 210.0)

    def test_zero_and_none_are_rejected_not_guessed(self):
        self.assertIsNone(vegas.american_to_implied(0))
        self.assertIsNone(vegas.american_to_implied(None))


class TestRemoveVig(unittest.TestCase):
    def test_symmetric_juice_normalises_to_one(self):
        h, a, vig = vegas.remove_vig(-110, -110)
        self.assertAlmostEqual(h, 0.5)
        self.assertAlmostEqual(a, 0.5)
        self.assertAlmostEqual(vig, (2 * 110 / 210 - 1) * 100, places=6)

    def test_fair_probabilities_sum_to_exactly_one(self):
        for home, away in [(-250, 210), (-110, -110), (135, -165), (-300, 250)]:
            h, a, _ = vegas.remove_vig(home, away)
            with self.subTest(home=home, away=away):
                self.assertAlmostEqual(h + a, 1.0, places=12)
                self.assertGreater(h, 0.0)
                self.assertLess(h, 1.0)

    def test_favourite_keeps_the_higher_fair_probability(self):
        h, a, _ = vegas.remove_vig(-250, 210)
        self.assertGreater(h, a)

    def test_overround_is_positive_for_a_real_book(self):
        _, _, vig = vegas.remove_vig(-110, -110)
        self.assertGreater(vig, 0.0)

    def test_missing_side_raises(self):
        with self.assertRaises(ValueError):
            vegas.remove_vig(0, -110)


class TestImpliedTotals(unittest.TestCase):
    def test_spread_total_is_assumption_free(self):
        # A home spread of -3.5 means the home team is favoured by 3.5, so the
        # home implied total is total/2 + 3.5/2 = 23.75 + 1.75 = 25.50.
        r = vegas.implied_totals("nfl", total=47.5, spread=-3.5)
        self.assertEqual(r.method, "spread_total")
        self.assertAlmostEqual(r.home, 25.5)
        self.assertAlmostEqual(r.away, 22.0)
        self.assertAlmostEqual(r.home + r.away, 47.5)

    def test_positive_home_spread_gives_the_away_team_more(self):
        r = vegas.implied_totals("nfl", total=47.5, spread=3.5)
        self.assertLess(r.home, r.away)
        self.assertAlmostEqual(r.home, 22.0)

    def test_totals_always_sum_to_the_market_total(self):
        for method_kwargs in ({"spread": -3.5}, {"home_ml": -250, "away_ml": 210}, {}):
            r = vegas.implied_totals("mlb", total=8.5, **method_kwargs)
            with self.subTest(method=r.method):
                self.assertAlmostEqual(r.home + r.away, 8.5, places=6)

    def test_moneyline_path_is_preferred_and_reports_its_assumption(self):
        r = vegas.implied_totals("mlb", total=8.5, spread=-1.5, home_ml=-150, away_ml=130)
        self.assertEqual(r.method, "moneyline_devig")
        self.assertIn("unaudited", r.note)
        self.assertIn("IR-03", r.note)
        self.assertIsNotNone(r.fair_home_win_prob)

    def test_favourite_gets_the_larger_implied_total(self):
        r = vegas.implied_totals("nba", total=225.0, home_ml=-300, away_ml=250)
        self.assertGreater(r.home, r.away)

    def test_no_line_splits_evenly_and_says_so(self):
        r = vegas.implied_totals("nhl", total=6.0)
        self.assertEqual(r.method, "total_only")
        self.assertAlmostEqual(r.home, 3.0)
        self.assertIn("documented degradation", r.note)

    def test_missing_total_returns_none(self):
        self.assertIsNone(vegas.implied_totals("mlb", total=None, spread=-1.5))
        self.assertIsNone(vegas.implied_totals("mlb", total=0, spread=-1.5))


class TestMarketWinProbability(unittest.TestCase):
    def test_moneyline_preferred_over_spread(self):
        r = vegas.market_win_probability("mlb", home_ml=-150, away_ml=130, spread=-1.5)
        self.assertEqual(r.method, "moneyline_devig")
        self.assertGreater(r.prob, 0.5)

    def test_devigged_probabilities_are_complementary(self):
        h = vegas.market_win_probability("mlb", home_ml=-150, away_ml=130, side="home")
        a = vegas.market_win_probability("mlb", home_ml=-150, away_ml=130, side="away")
        self.assertAlmostEqual(h.prob + a.prob, 1.0, places=12)

    def test_spread_only_uses_the_normal_link_and_flags_sigma(self):
        r = vegas.market_win_probability("nfl", spread=-7.0, side="home")
        self.assertEqual(r.method, "spread_normal")
        self.assertGreater(r.prob, 0.5)
        self.assertIn("IR-03", r.note)
        # -7 with sigma 13.5 -> Phi(7/13.5) = 0.6980
        self.assertAlmostEqual(r.prob, 0.69795, places=4)

    def test_spread_normal_is_known_to_understate_big_favourites(self):
        """Documents a real calibration gap instead of hiding it.

        For the same game the spread-derived probability and the de-vigged
        moneyline probability disagree, because ``SIGMA`` is an unaudited RGENGY
        assumption (IR-03).  The moneyline needs no distributional assumption, so
        it is preferred - and this test is the evidence for that preference order.
        If SIGMA is ever fitted to data, this gap should close and the assertion
        should be tightened.
        """
        spread_p = vegas.market_win_probability("nfl", spread=-7.0).prob
        ml_p = vegas.market_win_probability("nfl", home_ml=-300, away_ml=250).prob
        self.assertLess(spread_p, ml_p,
                        "the spread/normal link is expected to sit below the de-vigged "
                        "moneyline for a clear favourite; if that has flipped, SIGMA has "
                        "changed and IR-03 needs revisiting")
        self.assertGreater(ml_p - spread_p, 0.01)
        self.assertLess(ml_p - spread_p, 0.15)

    def test_pickem_spread_is_a_coin_flip(self):
        r = vegas.market_win_probability("nba", spread=0.0, side="home")
        self.assertAlmostEqual(r.prob, 0.5, places=9)

    def test_away_side_is_the_complement_under_a_spread(self):
        h = vegas.market_win_probability("nfl", spread=-7.0, side="home")
        a = vegas.market_win_probability("nfl", spread=-7.0, side="away")
        self.assertAlmostEqual(h.prob + a.prob, 1.0, places=9)

    def test_returns_none_rather_than_assuming_a_coin_flip(self):
        """No line at all must not silently become 0.5."""
        self.assertIsNone(vegas.market_win_probability("mlb"))

    def test_unknown_sport_with_only_a_spread_returns_none(self):
        self.assertIsNone(vegas.market_win_probability("darts", spread=-3.0))

    def test_bad_side_raises(self):
        with self.assertRaises(ValueError):
            vegas.market_win_probability("mlb", spread=-1.5, side="neutral")

    def test_to_dict_rounds(self):
        d = vegas.market_win_probability("mlb", home_ml=-150, away_ml=130).to_dict()
        self.assertEqual(set(d), {"prob", "side", "method", "note"})


class TestBryantPublished(unittest.TestCase):
    """The formula RotoGrinders itself publishes (IR-02)."""

    def test_verbatim_formula(self):
        # (8.5/2) - (1.5 * (100/101.5))/2 = 4.25 - 0.7389163 = 3.5110837
        self.assertAlmostEqual(vegas.bryant_published(8.5, 1.5, 1.5), 3.5110837, places=6)

    def test_zero_adjusted_spread_halves_the_spread_adjustment(self):
        # adjusted_spread 0 -> 4.25 - (1.5 * 1)/2 = 3.5
        self.assertAlmostEqual(vegas.bryant_published(8.5, 1.5, 0.0), 3.5)

    def test_requires_the_caller_to_supply_adjusted_spread(self):
        """RG does not publish how AdjustedSpread is derived, so neither do we."""
        import inspect
        sig = inspect.signature(vegas.bryant_published)
        self.assertIs(sig.parameters["adjusted_spread"].default, inspect.Parameter.empty,
                      "adjusted_spread must be a required argument: giving it a default "
                      "would mean inventing RotoGrinders' unpublished derivation")

    def test_rejects_the_singular_denominator(self):
        with self.assertRaises(ValueError):
            vegas.bryant_published(8.5, 1.5, -100.0)


class TestEdgeAndEv(unittest.TestCase):
    def test_edge_is_percentage_points(self):
        # RG's public pick card: "projects to hit 46.04% ... a 3.49% edge"
        self.assertAlmostEqual(vegas.edge_pct(0.0, 0.4255, 0.4604), 3.49, places=2)

    def test_negative_edge_when_the_price_is_short(self):
        self.assertLess(vegas.edge_pct(0.0, 0.50, 0.4604), 0.0)

    def test_breakeven_matches_implied(self):
        self.assertAlmostEqual(vegas.breakeven_probability(-110), 110 / 210.0)

    def test_ev_is_zero_at_the_breakeven_probability(self):
        for odds in (-110, 150, -250, 210):
            p = vegas.breakeven_probability(odds)
            with self.subTest(odds=odds):
                self.assertAlmostEqual(vegas.expected_value(p, odds), 0.0, places=9)

    def test_ev_is_positive_only_above_breakeven(self):
        self.assertGreater(vegas.expected_value(0.60, -110), 0.0)
        self.assertLess(vegas.expected_value(0.45, -110), 0.0)

    def test_ev_scales_with_stake(self):
        self.assertAlmostEqual(vegas.expected_value(0.60, -110, stake=10.0),
                               10.0 * vegas.expected_value(0.60, -110, stake=1.0),
                               places=9)

    def test_no_vig_fair_odds_round_trip(self):
        h, a = vegas.no_vig_fair_odds(-110, -110)
        self.assertEqual((h, a), (-100, -100))


class TestAirDensity(unittest.TestCase):
    def test_isa_constant_is_the_published_value(self):
        self.assertEqual(vegas.ISA_AIR_DENSITY_KG_M3, 1.225)


if __name__ == "__main__":
    unittest.main()
