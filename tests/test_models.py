"""Domain-model, roster-provenance and run-report tests.

A roster template that is wrong is worse than a projection that is wrong: it
produces lineups the operator would reject outright.  So these tests pin the
templates to their documented sources rather than to what merely runs.
"""
import sys, unittest
import helpers  # noqa: F401
sys.path.insert(0, helpers.REPO)

from rgengy import models, quality
from rgengy.pipeline import (RunResult, StageResult, STAGE_COMPLETE, STAGE_DEGRADED,
                             STAGE_UNAVAILABLE)

ALL_TEMPLATES = sorted(models.ROSTER_PROVENANCE)


class TestPlayerValue(unittest.TestCase):
    """Player.value() is the RotoGrinders 'value' heuristic: FPTS per $1,000."""

    def _p(self, **kw):
        kw.setdefault("player_id", "p1")
        kw.setdefault("name", "Player One")
        kw.setdefault("positions", ["P"])
        return helpers.make_player(**kw)

    def test_value_is_fpts_per_thousand(self):
        self.assertAlmostEqual(self._p(fpts=25.0, salary=5000).value("draftkings"), 5.0)

    def test_value_is_zero_when_the_salary_is_unknown(self):
        """Documented behaviour: value() is total, so an unknown salary yields 0.0.

        The grid never shows that 0.0 - pipeline._resolve() and attach_ownership()
        both substitute None so an unpriceable player reads as unvalued, not worthless.
        """
        self.assertEqual(self._p(fpts=25.0, salary=None).value("draftkings"), 0.0)
        self.assertEqual(self._p(fpts=25.0, salary=0).value("draftkings"), 0.0)

    def test_value_is_zero_when_there_is_no_projection_for_the_site(self):
        self.assertEqual(self._p(fpts=None, salary=5000).value("draftkings"), 0.0)

    def test_higher_value_means_more_points_per_dollar(self):
        cheap = self._p(player_id="c", name="Cheap", fpts=10.0, salary=3000)
        dear = self._p(player_id="d", name="Dear", fpts=10.0, salary=6000)
        self.assertGreater(cheap.value("draftkings"), dear.value("draftkings"))

    def test_negative_projection_still_returns_a_negative_value(self):
        self.assertLess(self._p(fpts=-2.0, salary=4000).value("draftkings"), 0.0)

    def test_site_is_honoured(self):
        p = self._p(fpts=10.0, salary=5000, site="fanduel")
        self.assertAlmostEqual(p.value("fanduel"), 2.0)
        self.assertEqual(p.value("draftkings"), 0.0, "no DK projection was supplied")


class TestRosterProvenance(unittest.TestCase):
    def test_every_template_carries_a_salary_cap_and_a_verification_status(self):
        for key in ALL_TEMPLATES:
            entry = models.ROSTER_PROVENANCE[key]
            self.assertIn("sources", entry, f"{key}: no sources key at all")
            self.assertTrue(entry.get("salary_cap"), f"{key}: no salary cap")
            self.assertTrue(entry.get("verification_status"), f"{key}: no verification status")

    def test_templates_without_a_source_are_marked_unaudited_and_say_so(self):
        """IR-22: a template we could not verify must never look verified."""
        for key in ALL_TEMPLATES:
            entry = models.ROSTER_PROVENANCE[key]
            if not entry["sources"]:
                self.assertEqual(entry["verification_status"], "not-audited", key)
                self.assertIn("UNCONFIRMED", entry.get("note") or "", key)

    def test_no_template_claims_more_confidence_than_it_has(self):
        for key in ALL_TEMPLATES:
            entry = models.ROSTER_PROVENANCE[key]
            self.assertIn(entry["verification_status"],
                          {"multi-source-consistent", "single-source", "disputed", "not-audited"},
                          key)
            if entry["verification_status"] == "multi-source-consistent":
                self.assertGreaterEqual(len(entry["sources"]), 2, key)

    def test_disputed_templates_are_flagged(self):
        self.assertEqual(models.ROSTER_PROVENANCE["nfl:fanduel"]["verification_status"],
                         "disputed", "IR-16: fanscout.pro contradicts RG on the FD NFL FLEX")

    def test_default_roster_is_derivable_for_every_template(self):
        for key in ALL_TEMPLATES:
            sport, site = key.split(":")
            tmpl = models.default_roster(sport, site)
            self.assertEqual(sum(r.count for r in tmpl["slots"]), tmpl["n_players"], key)

    def test_default_roster_rejects_unknown_combinations(self):
        with self.assertRaises(KeyError):
            models.default_roster("cricket", "draftkings")

    def test_unaudited_templates_say_so_in_their_note(self):
        for key in ALL_TEMPLATES:
            tmpl = models.default_roster(*key.split(":"))
            if tmpl["verification_status"] == "not-audited":
                self.assertIn("UNCONFIRMED", tmpl.get("note") or "", key)

    def test_salary_caps_match_operator_documents(self):
        self.assertEqual(models.default_roster("mlb", "draftkings")["salary_cap"], 50000)
        self.assertEqual(models.default_roster("nfl", "draftkings")["salary_cap"], 50000)
        self.assertEqual(models.default_roster("nfl", "fanduel")["salary_cap"], 60000)

    def test_draftkings_nfl_is_nine_slots_with_no_kicker(self):
        slots = models.default_roster("nfl", "draftkings")["slots"]
        self.assertEqual(sum(s.count for s in slots), 9)
        self.assertFalse(any("K" in s.eligible for s in slots),
                         "DK classic NFL has no kicker slot (operator scoring page)")

    def test_fanduel_nfl_includes_a_kicker(self):
        slots = models.default_roster("nfl", "fanduel")["slots"]
        self.assertTrue(any("K" in s.eligible for s in slots))
        self.assertEqual(sum(s.count for s in slots), 9)

    def test_draftkings_mlb_uses_a_combined_c_1b_slot(self):
        """Observed on the live DK MLB slate: C and 1B share one slot, not two."""
        slots = models.default_roster("mlb", "draftkings")["slots"]
        self.assertTrue(any(set(s.eligible) >= {"C", "1B"} for s in slots))
        self.assertFalse(any(s.eligible == ["C"] for s in slots))

    def test_draftkings_mlb_starts_two_pitchers(self):
        slots = models.default_roster("mlb", "draftkings")["slots"]
        self.assertEqual(next(s.count for s in slots if "P" in s.eligible), 2)

    def test_slot_counts_are_positive_integers(self):
        for key in ALL_TEMPLATES:
            for rule in models.default_roster(*key.split(":"))["slots"]:
                self.assertGreaterEqual(rule.count, 1, f"{key}/{rule.label}")
                self.assertTrue(rule.eligible, f"{key}/{rule.label} has no eligible positions")


class TestGridSchema(unittest.TestCase):
    def test_grid_columns_match_the_observed_counts(self):
        self.assertEqual(len(models.RG_GRID_COLUMNS["mlb"]), 49)
        self.assertEqual(len(models.RG_GRID_COLUMNS["nfl"]), 38)
        self.assertEqual(len(models.RG_GRID_COLUMNS["wnba"]), 33)

    def test_schemas_are_uppercase_and_unique(self):
        for sport, cols in models.RG_GRID_COLUMNS.items():
            self.assertEqual(len(cols), len(set(cols)), f"{sport}: duplicate column")
            self.assertTrue(all(c == c.upper() for c in cols), f"{sport}: lower-case column")

    def test_nba_and_nhl_grids_are_not_claimed(self):
        """IR-22: never present a grid schema we have not actually observed."""
        self.assertNotIn("nba", models.RG_GRID_COLUMNS)
        self.assertNotIn("nhl", models.RG_GRID_COLUMNS)


class TestRunResult(unittest.TestCase):
    _DEFAULT_STAGES = object()          # sentinel: an empty list is a real case

    def _result(self, stages=_DEFAULT_STAGES, findings=()):
        report = quality.QualityReport()
        for f in findings:
            report.add(f)
        if stages is self._DEFAULT_STAGES:
            stages = [StageResult("slate", STAGE_COMPLETE)]
        return RunResult(sport="mlb", date="2026-09-22", site="draftkings",
                         stages=stages,
                         slate=None, report=report,
                         fetch_summary={"mlb_games": {"rows": 30}}, warnings=["w"])

    def test_to_dict_round_trips_the_important_fields(self):
        d = self._result().to_dict()
        for k in ("sport", "date", "site", "overall_status", "generated_at",
                  "stages", "warnings", "fetch_summary", "quality"):
            self.assertIn(k, d, k)

    def test_no_stages_means_unavailable_not_complete(self):
        self.assertEqual(self._result(stages=[]).overall_status, STAGE_UNAVAILABLE)

    def test_status_is_the_worst_of_its_stages(self):
        stages = [StageResult("slate", STAGE_COMPLETE), StageResult("project", STAGE_DEGRADED)]
        self.assertEqual(self._result(stages).overall_status, STAGE_DEGRADED)
        stages.append(StageResult("optimise", STAGE_UNAVAILABLE))
        self.assertEqual(self._result(stages).overall_status, STAGE_UNAVAILABLE)

    def test_has_critical_reflects_the_findings(self):
        f = quality.Finding("check_endpoint_failures", "critical", "feed down", entity="x")
        self.assertTrue(self._result(findings=[f]).report.has_critical)
        self.assertFalse(self._result().report.has_critical)

    def test_slate_is_omitted_from_the_dict_when_absent(self):
        self.assertNotIn("slate", self._result().to_dict())


if __name__ == "__main__":
    unittest.main(verbosity=2)
