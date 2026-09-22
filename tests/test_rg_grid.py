"""Validation against RotoGrinders' own published numbers.

This is the only test module in the suite whose expectations come from outside
the codebase: every assertion is checked against the six free rows of
RotoGrinders' public MLB grid, transcribed verbatim into
``tests/fixtures/rg_public_mlb_grid_2026-09-22.json``.

If RGENGY's DraftKings MLB scoring table can reproduce RotoGrinders' published
``FPTS`` from RotoGrinders' published stat projections, the table is right.  That
is a real external validation, and it is the strongest evidence available without
a subscription.
"""

from __future__ import annotations

import unittest

from helpers import RG_MLB_GRID, load_fixture

from rgengy import scoring
from rgengy.models import RG_GRID_COLUMNS

import importlib.util
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "analyze_rg_public_grid.py"
_spec = importlib.util.spec_from_file_location("analyze_rg_public_grid", _SCRIPT)
analyze_mod = importlib.util.module_from_spec(_spec)
sys.modules["analyze_rg_public_grid"] = analyze_mod
_spec.loader.exec_module(analyze_mod)


class TestFixtureIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fx = load_fixture(RG_MLB_GRID)

    def test_fixture_records_its_own_provenance(self):
        prov = self.fx["_provenance"]
        for key in ("source_url", "retrieved_utc", "publisher", "retrieval_method",
                    "licence_note"):
            self.assertTrue(prov.get(key), f"_provenance is missing {key}")
        self.assertIn("rotogrinders.com", prov["source_url"])

    def test_column_schema_matches_the_code_constant_exactly(self):
        declared = ["FPTS/$" if c == "FPTS_PER_SALARY" else c for c in self.fx["columns"]]
        self.assertEqual(declared, list(RG_GRID_COLUMNS["mlb"]),
                         "the transcribed header and rgengy.models.RG_GRID_COLUMNS['mlb'] "
                         "have drifted apart; one of them is wrong")

    def test_row_count_matches_the_free_tier(self):
        self.assertEqual(len(self.fx["rows"]), 6)
        self.assertEqual(self.fx["_provenance"]["integrity"]["row_count"], 6)

    def test_every_row_carries_a_player_url_for_manual_review(self):
        for row in self.fx["rows"]:
            self.assertIn("player_url", row, f"{row['PLAYER']} has no player_url")
            self.assertIn("rotogrinders.com/players/", row["player_url"])
            self.assertIn("rg_player_id", row)

    def test_floating_point_artefacts_are_preserved_not_rounded(self):
        """Copying the page means copying its artefacts too."""
        marte = next(r for r in self.fx["rows"] if r["PLAYER"] == "Ketel Marte")
        self.assertEqual(marte["OBFPTS"], 15.172400000000001)

    def test_lawlar_floor_anomaly_is_recorded_and_excluded(self):
        lawlar = next(r for r in self.fx["rows"] if r["PLAYER"] == "Jordan Lawlar")
        self.assertEqual(lawlar["FLOOR"], 0)
        self.assertIn("_anomaly", lawlar,
                      "the zero floor must be flagged in the fixture, not silently kept")


class TestScoringAgainstRotoGrinders(unittest.TestCase):
    """Recompute RG's published FPTS from RG's published stats."""

    @classmethod
    def setUpClass(cls):
        cls.report = analyze_mod.analyze()

    def test_schema_is_identical_to_the_code_constant(self):
        self.assertTrue(self.report["schema"]["identical_to_code_constant"])
        self.assertEqual(self.report["schema"]["fixture_columns"], 49)

    def test_draftkings_mlb_fpts_reproduced_within_tolerance(self):
        sv = self.report["scoring_validation"]
        self.assertTrue(sv["passed"], sv["verdict"])
        self.assertLessEqual(sv["max_abs_delta"], analyze_mod.FPTS_TOLERANCE)

    def test_every_row_is_reproduced_individually(self):
        for row in self.report["scoring_validation"]["rows"]:
            with self.subTest(player=row["player"]):
                self.assertLessEqual(
                    row["abs_delta"], analyze_mod.FPTS_TOLERANCE,
                    f"{row['player']}: RGENGY scored {row['rgengy_fpts']} from RG's own "
                    f"published stats but RG published {row['published_fpts']}")

    def test_worst_case_percentage_error_is_under_one_percent(self):
        worst = max(r["pct_error"] for r in self.report["scoring_validation"]["rows"])
        self.assertLess(worst, 1.0)

    def test_residuals_are_consistent_with_input_rounding(self):
        """The residual is not a wrong coefficient.

        RG publishes FPTS to 2dp and its input stats to 2-3dp.  Recomputing from
        rounded inputs cannot be exact, but the residual must be small in absolute
        terms and must not grow with the size of the stat line.  If a coefficient
        were wrong the error would scale with the stat it multiplies.
        """
        rows = self.report["scoring_validation"]["rows"]
        deltas = [r["delta"] for r in rows]
        self.assertLessEqual(max(abs(d) for d in deltas), 0.10)
        # both signs occur, so this is rounding noise rather than a systematic
        # coefficient error (which would bias every row the same way)
        self.assertTrue(any(d > 0 for d in deltas) and any(d < 0 for d in deltas),
                        "all residuals share a sign, which suggests a systematically "
                        "wrong coefficient rather than input rounding")


class TestPublishedIdentities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze_mod.analyze()

    def test_fpts_per_salary_is_exactly_fpts_over_salary_in_thousands(self):
        ident = self.report["fpts_per_salary_identity"]
        self.assertTrue(ident["confirmed"], ident["verdict"])
        self.assertLessEqual(ident["max_abs_error"], 0.01)

    def test_rgengy_value_metric_uses_the_same_definition(self):
        """Player.value() must match RG's `FPTS/$` or the two are not comparable."""
        from helpers import make_player

        fx = load_fixture(RG_MLB_GRID)
        for row in fx["rows"]:
            with self.subTest(player=row["PLAYER"]):
                p = make_player("x", row["PLAYER"], [row["POS"]], float(row["SALARY"]),
                                fpts=float(row["FPTS"]))
                # RG publishes 2dp; the identity holds to within that rounding.
                self.assertAlmostEqual(p.value("draftkings"),
                                       float(row["FPTS_PER_SALARY"]), delta=0.01)

    def test_the_optimizer_objective_is_raw_points_not_value_per_dollar(self):
        """A distinction worth pinning down explicitly.

        ``Player.value`` is FPTS per $1000 (RG's ``FPTS/$``) and is what the
        ownership model and the ``TOPVAL``-style rankings use.  The knapsack
        objective must instead be RAW projected points, because cost is already
        handled by the salary constraint - optimising value-per-dollar under a
        cap would systematically prefer cheap players and produce a lower-scoring
        legal lineup.
        """
        from rgengy.optimizer import _value
        from helpers import make_player

        cheap = make_player("cheap", "Cheap", ["OF"], 3000.0, fpts=18.0)   # 6.00x
        stud = make_player("stud", "Stud", ["OF"], 6000.0, fpts=30.0)      # 5.00x
        self.assertGreater(cheap.value("draftkings"), stud.value("draftkings"))
        self.assertGreater(_value(stud, "draftkings"), _value(cheap, "draftkings"))
        self.assertEqual(_value(stud, "draftkings"), 30.0)


class TestCalibrationConstants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze_mod.analyze()

    def test_floor_ratio_matches_the_engine_constant(self):
        from rgengy import engines
        self.assertAlmostEqual(
            engines.RG_OBSERVED_FLOOR_RATIO,
            self.report["floor_ratio"]["mean"], places=4,
            msg=("rgengy.engines.RG_OBSERVED_FLOOR_RATIO has drifted from the value "
                 "recomputed from the fixture; re-run scripts/analyze_rg_public_grid.py"))

    def test_ceil_ratio_matches_the_engine_constant(self):
        from rgengy import engines
        self.assertAlmostEqual(
            engines.RG_OBSERVED_CEIL_RATIO,
            self.report["ceil_ratio"]["mean"], places=4)

    def test_floor_sample_excludes_the_anomalous_row(self):
        self.assertEqual(self.report["floor_ratio"]["n"], 5)
        self.assertEqual(len(self.report["floor_ratio"]["excluded"]), 1)
        self.assertEqual(self.report["floor_ratio"]["excluded"][0]["player"], "Jordan Lawlar")

    def test_bands_are_strongly_asymmetric(self):
        """CEIL/FPTS is ~7x FLOOR/FPTS - RG models upside far wider than downside."""
        fr = self.report["floor_ratio"]["mean"]
        cr = self.report["ceil_ratio"]["mean"]
        self.assertGreater(cr / fr, 5.0)

    def test_obfpts_is_not_the_same_metric_as_fpts(self):
        ob = self.report["obfpts"]
        self.assertGreater(ob["min"], 1.05)
        self.assertFalse(ob["definition_known"],
                         "if a definition is ever found, this flag must be flipped and "
                         "the value reproduced rather than left as an observation")

    def test_sample_size_warning_is_always_reported(self):
        self.assertIn("n=", self.report["engine_constants"]["sample_size_warning"])
        self.assertIn("ONE team", self.report["engine_constants"]["sample_size_warning"])


class TestOwnershipObservations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = analyze_mod.analyze()

    def test_pown_sums_to_roughly_the_whole_field(self):
        self.assertAlmostEqual(self.report["ownership"]["pown_sum"], 1.0068, places=4)

    def test_teamown_is_team_level_not_player_level(self):
        self.assertEqual(self.report["ownership"]["teamown_values"], [0.1758])

    def test_prizepicks_column_equals_rg_own_projection(self):
        fx = load_fixture(RG_MLB_GRID)
        for row in fx["rows"]:
            self.assertEqual(row["PRIZEPICKS"], row["FPTS"],
                             f"{row['PLAYER']}: PRIZEPICKS != FPTS")

    def test_underdog_column_differs_from_rg_own_projection(self):
        fx = load_fixture(RG_MLB_GRID)
        differing = [r for r in fx["rows"] if r["UNDERDOG"] != r["FPTS"]]
        self.assertEqual(len(differing), 6)


if __name__ == "__main__":
    unittest.main()
