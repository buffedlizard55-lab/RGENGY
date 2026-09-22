"""Contest simulator: payout maths, sampling correctness, determinism, honesty."""

from __future__ import annotations

import math
import random
import unittest

from helpers import make_player

from rgengy import simulator
from rgengy.scoring import load


def _pool(sport="mlb", site="draftkings", n=30, seed=3):
    """A pool whose players have real projected stats, not just an FPTS number."""
    rng = random.Random(seed)
    positions = ["P", "C", "1B", "2B", "3B", "SS", "OF"]
    coeff = load(sport, site).points
    hitters = [k for k, v in coeff.items() if v > 0 and k not in ("ip", "k", "win", "qs", "er")]
    pool = []
    for i in range(n):
        pos = positions[i % len(positions)]
        projected = {h: round(rng.uniform(0.05, 1.4), 3) for h in hitters[:8]}
        fpts = round(sum(coeff[h] * v for h, v in projected.items()), 2)
        pool.append(make_player(f"p{i}", f"Player {i}", [pos],
                                float(3000 + 200 * (i % 20)), site=site, fpts=fpts,
                                projected=projected))
    return pool


class TestPayoutStructure(unittest.TestCase):
    def setUp(self):
        self.pay = simulator.PayoutStructure(entry_fee=15.0)

    def test_first_place_gets_the_top_prize_for_that_field_size(self):
        # In a 1000-entry field the winner sits at frac 0.001, which is the 100x
        # bucket; the 200x bucket only exists for fields of 5000+.
        self.assertEqual(self.pay.multiple_for_rank(1, 1000), 100.0)
        self.assertEqual(self.pay.multiple_for_rank(1, 5000), 200.0)
        self.assertEqual(self.pay.multiple_for_rank(1, 1000) * 15.0, 1500.0)

    def test_buckets_are_monotone_in_rank(self):
        multiples = [self.pay.multiple_for_rank(r, 1000) for r in range(1, 1001)]
        for a, b in zip(multiples, multiples[1:]):
            self.assertGreaterEqual(a, b, "a worse finish must never pay more")

    def test_cash_boundary_is_the_widest_bucket(self):
        # 20% cash: rank 200 of 1000 pays, rank 201 does not
        self.assertGreater(self.pay.multiple_for_rank(200, 1000), 0.0)
        self.assertEqual(self.pay.multiple_for_rank(201, 1000), 0.0)
        self.assertAlmostEqual(self.pay.cash_fraction, 0.20)

    def test_small_finish_takes_the_smallest_satisfied_threshold(self):
        """The original bug: the LAST matching bucket won, so 1st place paid 1x."""
        # frac 0.001 -> the 0.1% bucket (100x); the 0.02% bucket needs a 5000+ field
        self.assertEqual(self.pay.multiple_for_rank(1, 1000), 100.0)
        # frac 0.002 -> first threshold satisfied is 0.005 (40x)
        self.assertEqual(self.pay.multiple_for_rank(2, 1000), 40.0)
        self.assertEqual(self.pay.multiple_for_rank(5, 1000), 40.0)
        self.assertEqual(self.pay.multiple_for_rank(6, 1000), 20.0)
        self.assertEqual(self.pay.multiple_for_rank(10, 1000), 20.0)
        self.assertEqual(self.pay.multiple_for_rank(11, 1000), 10.0)
        self.assertEqual(self.pay.multiple_for_rank(20, 1000), 10.0)
        self.assertEqual(self.pay.multiple_for_rank(100, 1000), 2.0)

    def test_bottom_of_the_field_pays_nothing(self):
        self.assertEqual(self.pay.multiple_for_rank(1000, 1000), 0.0)
        self.assertEqual(self.pay.multiple_for_rank(900, 1000), 0.0)

    def test_degenerate_inputs(self):
        self.assertEqual(self.pay.multiple_for_rank(0, 1000), 0.0)
        self.assertEqual(self.pay.multiple_for_rank(1, 0), 0.0)

    def test_tiny_field_still_pays_the_winner(self):
        """A field smaller than every bucket threshold must not pay first place 0."""
        for size in (1, 2, 3, 4):
            with self.subTest(field_size=size):
                self.assertGreater(self.pay.multiple_for_rank(1, size), 0.0)
        self.assertTrue(self.pay.extrapolated_for_small_field)
        # ...while everyone else in that tiny field still gets the threshold rule
        fresh = simulator.PayoutStructure(entry_fee=15.0)
        self.assertEqual(fresh.multiple_for_rank(1, 5), 1.0)   # frac 0.2 -> cash bucket
        self.assertEqual(fresh.multiple_for_rank(5, 5), 0.0)   # last place never cashes
        self.assertFalse(fresh.extrapolated_for_small_field)

    def test_empty_structure_pays_nothing(self):
        empty = simulator.PayoutStructure(entry_fee=15.0, payout_fractions={})
        self.assertEqual(empty.multiple_for_rank(1, 100), 0.0)
        self.assertEqual(empty.cash_fraction, 0.0)


class TestCountGreater(unittest.TestCase):
    def test_binary_search_on_a_descending_list(self):
        desc = [10.0, 8.0, 8.0, 5.0, 1.0]
        self.assertEqual(simulator._count_greater(desc, 9.0), 1)
        self.assertEqual(simulator._count_greater(desc, 8.0), 1)   # strictly greater
        self.assertEqual(simulator._count_greater(desc, 7.9), 3)
        self.assertEqual(simulator._count_greater(desc, 100.0), 0)
        self.assertEqual(simulator._count_greater(desc, -1.0), 5)
        self.assertEqual(simulator._count_greater([], 1.0), 0)


class TestLineupMoments(unittest.TestCase):
    def test_mean_matches_the_scoring_table(self):
        coeff = {"1b": 3.0, "hr": 10.0}
        p = make_player("x", "X", ["1B"], 4000.0, projected={"1b": 1.0, "hr": 0.25})
        mean, sd = simulator.lineup_moments([p], "draftkings", coeff)
        self.assertAlmostEqual(mean, 3.0 + 2.5)
        # var = 3^2*1 + 10^2*0.25 = 9 + 25 = 34
        self.assertAlmostEqual(sd, math.sqrt(34.0))

    def test_unscored_stats_contribute_nothing(self):
        coeff = {"1b": 3.0}
        p = make_player("x", "X", ["1B"], 4000.0, projected={"1b": 1.0, "pa": 5.0})
        mean, _ = simulator.lineup_moments([p], "draftkings", coeff)
        self.assertAlmostEqual(mean, 3.0)

    def test_moments_are_additive_over_players(self):
        coeff = {"1b": 3.0}
        a = make_player("a", "A", ["1B"], 4000.0, projected={"1b": 1.0})
        b = make_player("b", "B", ["1B"], 4000.0, projected={"1b": 2.0})
        m1, s1 = simulator.lineup_moments([a], "draftkings", coeff)
        m2, s2 = simulator.lineup_moments([b], "draftkings", coeff)
        m, _ = simulator.lineup_moments([a, b], "draftkings", coeff)
        self.assertAlmostEqual(m, m1 + m2)
        self.assertAlmostEqual(s1 * s1 + s2 * s2, 3.0 ** 2 * 3.0)


class TestPoissonSampler(unittest.TestCase):
    def test_mean_converges_to_the_projection(self):
        """The sampler must be unbiased or every ROI figure downstream is wrong."""
        coeff = {"1b": 3.0, "hr": 10.0, "sb": 5.0}
        p = make_player("x", "X", ["1B"], 4000.0,
                        projected={"1b": 1.0, "hr": 0.25, "sb": 0.1})
        want = 3.0 * 1.0 + 10.0 * 0.25 + 5.0 * 0.1     # 6.0
        rng = random.Random(2026)
        draws = [simulator.sample_player_fpts(p, "draftkings", coeff, rng)
                 for _ in range(20000)]
        got = sum(draws) / len(draws)
        self.assertAlmostEqual(got, want, delta=0.08)

    def test_variance_matches_the_poisson_sum(self):
        coeff = {"1b": 3.0, "hr": 10.0}
        p = make_player("x", "X", ["1B"], 4000.0, projected={"1b": 1.0, "hr": 0.25})
        rng = random.Random(99)
        draws = [simulator.sample_player_fpts(p, "draftkings", coeff, rng)
                 for _ in range(20000)]
        mean = sum(draws) / len(draws)
        var = sum((d - mean) ** 2 for d in draws) / (len(draws) - 1)
        self.assertAlmostEqual(var, 34.0, delta=1.5)

    def test_large_lambda_uses_the_normal_approximation(self):
        coeff = {"1b": 1.0}
        p = make_player("x", "X", ["1B"], 4000.0, projected={"1b": 5000.0})
        rng = random.Random(5)
        draws = [simulator.sample_player_fpts(p, "draftkings", coeff, rng) for _ in range(400)]
        self.assertAlmostEqual(sum(draws) / len(draws), 5000.0, delta=120.0)

    def test_zero_and_negative_means_draw_nothing(self):
        coeff = {"1b": 3.0}
        rng = random.Random(1)
        for projected in ({}, {"1b": 0.0}, {"1b": -5.0}):
            p = make_player("x", "X", ["1B"], 4000.0, projected=projected)
            self.assertEqual(simulator.sample_player_fpts(p, "draftkings", coeff, rng), 0.0)


class TestFieldConstruction(unittest.TestCase):
    def test_sharp_fraction_controls_the_mix(self):
        pool = _pool(n=40)
        out = simulator.build_field(pool, "mlb", "draftkings", field_size=20,
                                    sharp_fraction=0.5, seed=1)
        self.assertEqual(out["n_sharp"] + out["n_casual"], len(out["lineups"]))
        self.assertLessEqual(len(out["lineups"]), 20)
        self.assertGreater(out["n_sharp"], 0)
        self.assertGreater(out["n_casual"], 0)

    def test_all_sharp_field_is_better_than_all_casual(self):
        """A proportional-sampling field is far weaker than an optimised one.

        This is why the mixture exists: an all-casual field produces absurd cash
        rates, and an all-sharp field produces none.
        """
        pool = _pool(n=40)
        sharp = simulator.build_field(pool, "mlb", "draftkings", field_size=12,
                                      sharp_fraction=1.0, seed=1)
        casual = simulator.build_field(pool, "mlb", "draftkings", field_size=12,
                                       sharp_fraction=0.0, seed=1)
        coeff = load("mlb", "draftkings").points
        def mean_lineup(build):
            vals = [simulator.lineup_moments(r, "draftkings", coeff)[0]
                    for r in build["lineups"]]
            return sum(vals) / len(vals)
        self.assertGreater(mean_lineup(sharp), mean_lineup(casual))

    def test_field_lineups_are_legal_rosters(self):
        from rgengy.models import default_roster
        pool = _pool(n=40)
        out = simulator.build_field(pool, "mlb", "draftkings", field_size=10,
                                    sharp_fraction=0.5, seed=2)
        template = default_roster("mlb", "draftkings")["slots"]
        for roster in out["lineups"]:
            self.assertEqual(len(roster), sum(r.count for r in template))
            self.assertEqual(len({p.player_id for p in roster}), len(roster),
                             "a field entry rostered the same player twice")

    def test_deterministic_for_a_seed(self):
        pool = _pool(n=30)
        a = simulator.build_field(pool, "mlb", "draftkings", 10, seed=42)
        b = simulator.build_field(pool, "mlb", "draftkings", 10, seed=42)
        self.assertEqual([[p.player_id for p in r] for r in a["lineups"]],
                         [[p.player_id for p in r] for r in b["lineups"]])

    def test_bad_sharp_fraction_raises(self):
        with self.assertRaises(ValueError):
            simulator.build_field(_pool(n=10), "mlb", "draftkings", 5, sharp_fraction=1.5)


class TestSimulateContest(unittest.TestCase):
    def _lineups(self, pool, n=3):
        from rgengy import optimizer
        return optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=n,
                                        flex_candidates=4,
                                        max_flex_enumerations=60)["lineups"]

    def test_passing_the_whole_result_dict_is_rejected_with_a_clear_message(self):
        from rgengy import optimizer
        pool = _pool(n=30)
        result = optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=2,
                                          flex_candidates=4, max_flex_enumerations=40)
        with self.assertRaises(TypeError) as ctx:
            simulator.simulate_contest(result, pool, "mlb", "draftkings",
                                       n_sims=5, field_size=5)
        self.assertIn("result['lineups']", str(ctx.exception))

    def test_malformed_lineup_entry_is_rejected(self):
        pool = _pool(n=20)
        with self.assertRaises(TypeError):
            simulator.simulate_contest(["not-a-lineup"], pool, "mlb", "draftkings",
                                       n_sims=5, field_size=5)

    def test_reports_every_expected_field(self):
        pool = _pool(n=40)
        out = simulator.simulate_contest(self._lineups(pool), pool, "mlb", "draftkings",
                                         n_sims=40, field_size=12, seed=1)
        for key in ("n_sims", "field_size", "field_sharp", "field_casual", "entry_fee",
                    "payout_structure", "seed", "results", "assumptions", "field_winners"):
            self.assertIn(key, out)
        for r in out["results"]:
            for key in ("label", "projected_points", "simulated_mean", "simulated_sd",
                        "cash_rate", "top10_rate", "top1_rate", "mean_rank_pct", "roi"):
                self.assertIn(key, r)

    def test_rates_are_probabilities(self):
        pool = _pool(n=40)
        out = simulator.simulate_contest(self._lineups(pool), pool, "mlb", "draftkings",
                                         n_sims=60, field_size=12, seed=1)
        for r in out["results"]:
            for key in ("cash_rate", "top10_rate", "top1_rate", "mean_rank_pct"):
                self.assertGreaterEqual(r[key], 0.0)
                self.assertLessEqual(r[key], 1.0)
            self.assertGreaterEqual(r["cash_rate"], r["top10_rate"])
            self.assertGreaterEqual(r["top10_rate"], r["top1_rate"])

    def test_deterministic_for_a_seed(self):
        pool = _pool(n=40)
        lus = self._lineups(pool)
        a = simulator.simulate_contest(lus, pool, "mlb", "draftkings", n_sims=30,
                                       field_size=10, seed=7)
        b = simulator.simulate_contest(lus, pool, "mlb", "draftkings", n_sims=30,
                                       field_size=10, seed=7)
        self.assertEqual(a["results"], b["results"])

    def test_different_seeds_differ(self):
        pool = _pool(n=40)
        lus = self._lineups(pool)
        a = simulator.simulate_contest(lus, pool, "mlb", "draftkings", n_sims=60,
                                       field_size=12, seed=7)
        b = simulator.simulate_contest(lus, pool, "mlb", "draftkings", n_sims=60,
                                       field_size=12, seed=8)
        self.assertNotEqual(a["results"], b["results"])

    def test_all_sharp_field_pushes_cash_rate_towards_the_payout_bucket(self):
        """Internal-consistency check on the whole model.

        Against a field of equally-optimised lineups a user lineup has no edge, so
        its cash rate must converge to the payout structure's cash bucket (20%)
        and its ROI must go negative.  Against an all-casual field it would be far
        higher.  If this relationship inverts, the field model is broken.
        """
        # A large pool is required: with ~40 players the salary-capped optimum is
        # almost unique, so an "all-sharp" field collapses onto the user's own
        # roster and the comparison becomes meaningless.
        pool = _pool(n=140, seed=17)
        lus = self._lineups(pool, n=1)
        sharp = simulator.simulate_contest(lus, pool, "mlb", "draftkings", n_sims=300,
                                           field_size=40, sharp_fraction=1.0, seed=11)
        casual = simulator.simulate_contest(lus, pool, "mlb", "draftkings", n_sims=300,
                                            field_size=40, sharp_fraction=0.0, seed=11)
        self.assertTrue(sharp["results"] and casual["results"],
                        sharp.get("note") or casual.get("note"))
        self.assertGreater(casual["results"][0]["cash_rate"],
                           sharp["results"][0]["cash_rate"])
        self.assertLess(sharp["results"][0]["roi"], casual["results"][0]["roi"])

    def test_simulated_mean_tracks_the_projection(self):
        pool = _pool(n=40)
        lus = self._lineups(pool, n=1)
        out = simulator.simulate_contest(lus, pool, "mlb", "draftkings", n_sims=400,
                                         field_size=10, seed=5, user_mode="poisson")
        r = out["results"][0]
        self.assertAlmostEqual(r["simulated_mean"], r["projected_points"], delta=4.0)

    def test_normal_and_poisson_modes_agree_on_the_mean(self):
        pool = _pool(n=40)
        lus = self._lineups(pool, n=1)
        kw = dict(n_sims=400, field_size=10, seed=5)
        a = simulator.simulate_contest(lus, pool, "mlb", "draftkings",
                                       user_mode="poisson", **kw)["results"][0]
        b = simulator.simulate_contest(lus, pool, "mlb", "draftkings",
                                       user_mode="normal", **kw)["results"][0]
        self.assertAlmostEqual(a["simulated_mean"], b["simulated_mean"], delta=4.0)
        self.assertAlmostEqual(a["simulated_sd"], b["simulated_sd"], delta=4.0)

    def test_bad_mode_raises(self):
        pool = _pool(n=40)
        with self.assertRaises(ValueError):
            simulator.simulate_contest(self._lineups(pool, 1), pool, "mlb", "draftkings",
                                       n_sims=5, field_size=5, user_mode="quantum")

    def test_no_lineups_is_reported_not_crashed(self):
        out = simulator.simulate_contest([], _pool(n=10), "mlb", "draftkings",
                                         n_sims=5, field_size=5)
        self.assertEqual(out["results"], [])
        self.assertIn("no lineups", out["note"])

    def test_assumptions_are_stated_in_the_output(self):
        pool = _pool(n=30)
        out = simulator.simulate_contest(self._lineups(pool, 1), pool, "mlb", "draftkings",
                                         n_sims=10, field_size=8, seed=1)
        joined = " ".join(out["assumptions"]).lower()
        self.assertIn("poisson", joined)
        self.assertIn("payout structure", joined)
        self.assertIn("not", joined)      # the correlation caveat must be present

    def test_payout_structure_is_not_claimed_to_be_an_operators(self):
        pool = _pool(n=30)
        out = simulator.simulate_contest(self._lineups(pool, 1), pool, "mlb", "draftkings",
                                         n_sims=10, field_size=8, seed=1)
        self.assertTrue(any("generic" in a for a in out["assumptions"]),
                        "the output must say the payout shape is RGENGY's own")


if __name__ == "__main__":
    unittest.main()
