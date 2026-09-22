"""Ownership model tests.

RotoGrinders' pOWN is gradient-boosted over historical DraftKings ownership data
(https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773),
which is not obtainable from any free feed, so RGENGY implements a transparent
softmax choice model instead.  These tests therefore assert the properties a
choice model MUST have - normalisation, monotonicity, the ownership cap, and an
honest calibration label - rather than pretending to match RG's numbers.
"""
import sys, unittest
import helpers  # noqa: F401
sys.path.insert(0, helpers.REPO)

from rgengy import ownership, pipeline
from rgengy.ownership import (DEFAULT_BETA, MAX_POWN, OwnershipModel, calibrate_beta,
                              default_model, leverage, project_ownership, smash_probability)


class TestModelProvenance(unittest.TestCase):
    def test_default_model_is_explicitly_uncalibrated(self):
        m = default_model()
        self.assertEqual(m.beta, DEFAULT_BETA)
        self.assertFalse(m.calibrated, "IR-13: the default beta must never claim to be fitted")
        self.assertEqual(m.n_calibration_points, 0)
        self.assertIsNone(m.rmse)

    def test_the_uncalibrated_status_survives_serialisation(self):
        d = default_model().to_dict()
        self.assertFalse(d["calibrated"])
        self.assertEqual(d["beta"], DEFAULT_BETA)

    def test_a_calibrated_model_reports_its_sample_size_and_error(self):
        values = [5.0, 4.0, 3.0, 2.0]
        observed = project_ownership(values, OwnershipModel(beta=0.8, calibrated=False,
                                                            n_calibration_points=0, value_key="value"))
        m = calibrate_beta(values, observed)
        self.assertTrue(m.calibrated)
        self.assertEqual(m.n_calibration_points, 4)
        self.assertIsNotNone(m.rmse)
        self.assertAlmostEqual(m.beta, 0.8, places=1)

    def test_calibration_recovers_a_known_beta(self):
        values = [6.0, 5.0, 4.0, 3.0, 2.0, 1.0]
        truth = OwnershipModel(beta=1.20, calibrated=False, n_calibration_points=0,
                               value_key="value")
        m = calibrate_beta(values, project_ownership(values, truth))
        self.assertAlmostEqual(m.beta, 1.20, places=2)
        self.assertLess(m.rmse, 1e-3)

    def test_calibration_is_deterministic(self):
        values, observed = [5.0, 3.0, 1.0], [0.5, 0.3, 0.2]
        self.assertEqual(calibrate_beta(values, observed).to_dict(),
                         calibrate_beta(values, observed).to_dict())

    def test_calibration_refuses_too_few_observations(self):
        with self.assertRaises(ValueError):
            calibrate_beta([1.0, 2.0], [0.5, 0.5])

    def test_calibration_refuses_mismatched_lengths(self):
        with self.assertRaises(ValueError):
            calibrate_beta([1.0, 2.0, 3.0], [0.5, 0.5])

    def test_a_custom_grid_is_honoured(self):
        m = calibrate_beta([5.0, 3.0, 1.0], [0.6, 0.25, 0.15], grid=[0.5, 1.5])
        self.assertIn(m.beta, (0.5, 1.5))


class TestProjection(unittest.TestCase):
    def test_empty_slate_returns_no_shares(self):
        self.assertEqual(project_ownership([]), [])

    def test_shares_sum_to_one(self):
        for values in ([5.0, 4.0, 3.0], [1.0] * 12, [9.0, 1.0, 0.5, 0.25], [3.0, 2.0, 1.0]):
            self.assertAlmostEqual(sum(project_ownership(values)), 1.0, places=5, msg=values)

    def test_a_large_slate_still_normalises_exactly(self):
        self.assertAlmostEqual(sum(project_ownership([float(i) for i in range(300)])), 1.0, places=6)

    def test_equal_values_get_equal_shares(self):
        s = project_ownership([4.0] * 8)
        self.assertEqual(len(set(s)), 1)
        self.assertAlmostEqual(s[0], 1 / 8, places=5)

    def test_ownership_is_monotonic_in_value(self):
        s = project_ownership([1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(s, sorted(s), "a better value must never be projected lower")
        self.assertLess(s[0], s[-1])

    def test_a_zero_value_still_gets_a_nonzero_share(self):
        """A projected-bust player is still owned by someone in a real field."""
        s = project_ownership([5.0, 0.0, 0.0])
        self.assertGreater(min(s), 0.0)

    def test_all_zero_values_fall_back_to_uniform(self):
        s = project_ownership([0.0, 0.0, 0.0])
        self.assertAlmostEqual(s[0], 1 / 3, places=5)

    def test_no_share_ever_exceeds_the_cap(self):
        """Regression: capping then re-normalising by the new total scales every
        share back up, so a dominant player previously came out at 1.0 (100%)."""
        for values in ([100.0, 0.0, 0.0], [50.0, 5.0, 5.0], [30.0, 1.0, 1.0, 1.0],
                       [1e9, 1.0, 1.0], [20.0] + [0.0] * 9):
            s = project_ownership(values)
            self.assertLessEqual(max(s), MAX_POWN + 1e-9, f"cap breached for {values}: {s}")

    def test_capped_mass_is_redistributed_to_the_other_players(self):
        s = project_ownership([100.0, 0.0, 0.0])
        self.assertAlmostEqual(s[0], MAX_POWN, places=5)
        self.assertAlmostEqual(sum(s), 1.0, places=5, msg="freed mass must not be destroyed")
        self.assertAlmostEqual(s[1], s[2], places=6)

    def test_a_single_player_slate_is_capped_rather_than_claimed_at_100_percent(self):
        self.assertEqual(project_ownership([7.0]), [MAX_POWN])

    def test_beta_zero_gives_a_uniform_field(self):
        m = OwnershipModel(beta=0.0, calibrated=False, n_calibration_points=0, value_key="value")
        s = project_ownership([10.0, 1.0, 0.1], m)
        self.assertAlmostEqual(s[0], 1 / 3, places=5)

    def test_a_larger_beta_concentrates_ownership(self):
        flat = OwnershipModel(beta=0.01, calibrated=False, n_calibration_points=0, value_key="v")
        sharp = OwnershipModel(beta=2.0, calibrated=False, n_calibration_points=0, value_key="v")
        values = [6.0, 4.0, 2.0]
        self.assertGreater(project_ownership(values, sharp)[0],
                           project_ownership(values, flat)[0])

    def test_weights_must_align_with_values(self):
        with self.assertRaises(ValueError):
            project_ownership([1.0, 2.0, 3.0], weights=[1.0, 1.0])

    def test_a_weight_of_zero_removes_a_player_from_the_field(self):
        s = project_ownership([5.0, 5.0, 5.0], weights=[1.0, 1.0, 0.0])
        self.assertEqual(s[2], 0.0)
        self.assertAlmostEqual(sum(s), 1.0, places=5)

    def test_weights_scale_shares_and_renormalise(self):
        s = project_ownership([5.0, 5.0], weights=[3.0, 1.0])
        self.assertAlmostEqual(s[0] / s[1], 3.0, places=4)

    def test_all_zero_weights_fall_back_to_uniform_rather_than_dividing_by_zero(self):
        s = project_ownership([5.0, 4.0], weights=[0.0, 0.0])
        self.assertAlmostEqual(sum(s), 1.0, places=5)
        self.assertAlmostEqual(s[0], 0.5, places=5)

    def test_shares_are_bounded_probabilities(self):
        for values in ([5.0, 4.0], [-3.0, 2.0], [1e6, -1e6]):
            for x in project_ownership(values):
                self.assertGreaterEqual(x, 0.0)
                self.assertLessEqual(x, 1.0)

    def test_negative_values_do_not_crash_the_softmax(self):
        s = project_ownership([-5.0, -2.0, 1.0])
        self.assertAlmostEqual(sum(s), 1.0, places=5)
        self.assertEqual(s.index(max(s)), 2)


class TestLeverage(unittest.TestCase):
    def test_leverage_sums_to_about_zero_across_a_slate(self):
        """Both terms are field shares, so the slate-wide total must cancel."""
        fpts = [20.0, 15.0, 10.0, 5.0]
        avg = sum(fpts) / len(fpts)
        shares = project_ownership([f / 4000 * 1000 for f in fpts])
        total = sum(leverage(p, f, avg, len(fpts)) for p, f in zip(shares, fpts))
        self.assertAlmostEqual(total, 0.0, places=4)

    def test_positive_leverage_means_more_production_share_than_ownership_share(self):
        # value share = (20/10)/100 = 0.02, ownership share = 0.01 -> +0.01
        self.assertAlmostEqual(leverage(pown=0.01, projected_fpts=20.0, field_avg_fpts=10.0,
                                        field_size=100), 0.01, places=6)

    def test_leverage_turns_negative_once_ownership_outgrows_the_value_share(self):
        self.assertLess(leverage(pown=0.05, projected_fpts=20.0, field_avg_fpts=10.0,
                                 field_size=100), 0.0)

    def test_negative_leverage_means_a_chalk_play(self):
        self.assertLess(leverage(pown=0.50, projected_fpts=10.0, field_avg_fpts=10.0,
                                 field_size=100), 0.0)

    def test_a_player_exactly_at_his_share_has_no_leverage(self):
        # value share = (10/10)/100 = 0.01
        self.assertAlmostEqual(leverage(0.01, 10.0, 10.0, 100), 0.0, places=6)

    def test_field_size_is_required_for_the_subtraction_to_be_dimensional(self):
        """Regression: without normalising by field size, a ratio was subtracted
        from a probability and the result meant nothing."""
        small = leverage(0.01, 10.0, 10.0, 10)
        large = leverage(0.01, 10.0, 10.0, 1000)
        self.assertGreater(small, large)

    def test_a_degenerate_field_average_returns_zero_not_a_division_error(self):
        self.assertEqual(leverage(0.1, 10.0, 0.0, 100), 0.0)
        self.assertEqual(leverage(0.1, 10.0, -5.0, 100), 0.0)

    def test_a_degenerate_field_size_returns_zero(self):
        self.assertEqual(leverage(0.1, 10.0, 10.0, 0), 0.0)

    def test_leverage_is_rounded_for_output(self):
        v = leverage(0.123456789, 10.0, 10.0, 3)
        self.assertEqual(v, round(v, 6))


class TestSmashProbability(unittest.TestCase):
    def test_a_threshold_at_the_mean_is_a_coin_flip(self):
        self.assertAlmostEqual(smash_probability(20.0, 5.0, 20.0), 0.5, places=4)

    def test_probability_falls_as_the_threshold_rises(self):
        ps = [smash_probability(20.0, 5.0, t) for t in (10.0, 20.0, 30.0, 40.0)]
        self.assertEqual(ps, sorted(ps, reverse=True))

    def test_one_sd_above_the_mean_matches_the_normal_table(self):
        self.assertAlmostEqual(smash_probability(20.0, 5.0, 25.0), 0.1587, places=4)

    def test_a_threshold_below_the_mean_is_more_likely_than_not(self):
        self.assertGreater(smash_probability(20.0, 5.0, 10.0), 0.95)

    def test_an_unknown_spread_returns_none_rather_than_a_guess(self):
        self.assertIsNone(smash_probability(20.0, None, 25.0))

    def test_a_zero_or_negative_spread_returns_none(self):
        self.assertIsNone(smash_probability(20.0, 0.0, 25.0))
        self.assertIsNone(smash_probability(20.0, -1.0, 25.0))

    def test_probability_is_a_bounded_four_dp_number(self):
        for mean, sd, t in ((20.0, 5.0, 0.0), (20.0, 5.0, 200.0), (0.0, 1.0, 0.0)):
            p = smash_probability(mean, sd, t)
            self.assertGreaterEqual(p, 0.0)
            self.assertLessEqual(p, 1.0)
            self.assertEqual(p, round(p, 4))

    def test_a_larger_spread_raises_the_tail_probability(self):
        self.assertGreater(smash_probability(20.0, 10.0, 30.0), smash_probability(20.0, 2.0, 30.0))


class TestPipelineIntegration(unittest.TestCase):
    """attach_ownership() is where the model meets a real slate."""

    def setUp(self):
        self.pool = helpers.mlb_pool(n_per_position=3)
        self.players, self.stage = pipeline.attach_ownership(self.pool, "draftkings")

    def test_every_player_gets_a_share(self):
        self.assertTrue(all(p.pown is not None for p in self.players))
        self.assertAlmostEqual(sum(p.pown for p in self.players), 1.0, places=4)

    def test_the_analytics_are_labelled_with_their_origin(self):
        prov = self.players[0].extra["analytics_provenance"]
        self.assertIn("reproduced", prov["FPTS/$"])
        self.assertIn("NOT a reproduction", prov["lev"])
        self.assertIn("NOT a reproduction", prov["smash"])
        for unpublished in ("topval", "difference", "obfpts"):
            self.assertIn("not computed", prov[unpublished],
                          f"{unpublished} must stay null - RG's definition is unpublished")

    def test_the_model_calibration_status_is_attached_to_every_player(self):
        for p in self.players:
            self.assertIn("calibrated", p.extra["ownership_model"])
            self.assertFalse(p.extra["ownership_model"]["calibrated"])

    def test_value_per_1k_matches_the_verified_identity(self):
        for p in self.players:
            self.assertAlmostEqual(p.extra["value_per_1k"],
                                   round(p.fpts["draftkings"] / (p.salary / 1000.0), 4), places=4)

    def test_a_player_with_no_salary_is_unvalued_not_zero_valued(self):
        self.pool[0].salary = None
        players, _ = pipeline.attach_ownership(self.pool, "draftkings")
        self.assertIsNone(players[0].extra["value_per_1k"],
                          "0.0 would read as 'worthless'; None reads as 'unknown'")

    def test_smash_uses_the_documented_default_threshold(self):
        p = self.players[0]
        self.assertAlmostEqual(p.extra["smash_threshold"],
                               round(pipeline.DEFAULT_SMASH_THRESHOLD_MULTIPLE *
                                     p.fpts["draftkings"], 3), places=3)

    def test_the_stage_is_degraded_while_beta_is_uncalibrated(self):
        self.assertEqual(self.stage.status, pipeline.STAGE_DEGRADED)
        self.assertIn("IR-13", self.stage.reason or "")

    def test_the_stage_is_complete_once_beta_is_fitted(self):
        model = OwnershipModel(beta=0.8, calibrated=True, n_calibration_points=50,
                               value_key="value", rmse=0.01)
        _, stage = pipeline.attach_ownership(self.pool, "draftkings", model=model)
        self.assertEqual(stage.status, pipeline.STAGE_COMPLETE)
        self.assertIsNone(stage.reason)

    def test_ownership_is_monotonic_in_value_on_a_real_pool(self):
        by_value = sorted(self.players, key=lambda p: p.extra["value_per_1k"])
        shares = [p.pown for p in by_value]
        self.assertEqual(shares, sorted(shares))

    def test_an_empty_slate_does_not_crash(self):
        players, stage = pipeline.attach_ownership([], "draftkings")
        self.assertEqual(players, [])
        self.assertEqual(stage.counts["players"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
