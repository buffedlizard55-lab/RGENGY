"""Quality-gate tests.

These are the checks that stop RGENGY publishing a number it cannot defend.
Each test asserts both that the check FIRES on bad input and that it stays
SILENT on good input - a check that always fires is as useless as one that
never does, because the report becomes noise nobody reads.
"""
import datetime as _dt
import sys, unittest
import helpers  # noqa: F401
sys.path.insert(0, helpers.REPO)

from rgengy import quality, scoring
from rgengy.quality import Finding, QualityReport

MLB_TABLE = scoring.load("mlb", "draftkings")
MLB_COEFFS = MLB_TABLE.points


_N = [0]


def _p(**kw):
    """make_player with every required argument defaulted."""
    _N[0] += 1
    kw.setdefault("player_id", f"q{_N[0]}")
    kw.setdefault("name", f"Player {_N[0]}")
    kw.setdefault("positions", ["P"])
    kw.setdefault("salary", 4000)
    kw.setdefault("fpts", 10.0)
    return helpers.make_player(**kw)


def _report():
    return QualityReport()


def _findings(report, check=None, severity=None):
    out = [f for f in report.findings
           if (check is None or f.check == check) and (severity is None or f.severity == severity)]
    return out


class TestReportMechanics(unittest.TestCase):
    def test_by_severity_always_lists_every_severity(self):
        r = _report()
        r.add(Finding("c", "warning", "m"))
        self.assertEqual(r.by_severity(), {"info": 0, "warning": 1, "critical": 0})

    def test_unknown_severity_is_rejected(self):
        with self.assertRaises(ValueError):
            _report().add(Finding("c", "catastrophic", "m"))

    def test_by_check_groups_counts(self):
        r = _report()
        r.add(Finding("a", "info", "1"))
        r.add(Finding("a", "info", "2"))
        r.add(Finding("b", "warning", "3"))
        self.assertEqual(r.by_check(), {"a": 2, "b": 1})

    def test_extend_adds_all(self):
        r = _report()
        r.extend([Finding("a", "info", "1"), Finding("b", "info", "2")])
        self.assertEqual(len(r.findings), 2)

    def test_to_dict_is_json_shaped_and_carries_the_review_action(self):
        r = _report()
        r.add(Finding("a", "critical", "boom", entity="p1", review_action="look here"))
        d = r.to_dict()
        self.assertTrue(d["has_critical"])
        self.assertEqual(d["findings"][0]["review_action"], "look here")
        import json
        json.dumps(d)          # must be serialisable, or the artefact cannot be written

    def test_every_finding_tells_a_human_what_to_do(self):
        """An irregularity with no review action cannot be actioned."""
        for key in scoring.available():
            sport, site = key.split(":")
            r = _report()
            quality.check_representation_double_count(sport, site, r)
            for f in _findings(r):
                self.assertTrue(f.review_action, f"{key}: no review_action")


class TestZeroProjection(unittest.TestCase):
    def test_fires_for_a_paid_player_with_no_projection(self):
        r = _report()
        quality.check_zero_projection([_p(fpts=None, salary=4000)], "draftkings", r)
        self.assertEqual(len(_findings(r, "zero_projection")), 1)

    def test_fires_for_a_paid_player_projected_at_zero(self):
        r = _report()
        quality.check_zero_projection([_p(fpts=0.0, salary=4000)], "draftkings", r)
        self.assertEqual(len(_findings(r, "zero_projection")), 1)

    def test_silent_for_a_player_with_no_salary(self):
        """A free-agent row with no salary and no projection is not a defect."""
        r = _report()
        quality.check_zero_projection([_p(fpts=None, salary=None)], "draftkings", r)
        self.assertEqual(_findings(r, "zero_projection"), [])

    def test_silent_for_a_normal_projection(self):
        r = _report()
        pool = helpers.mlb_pool(n_per_position=2)
        quality.check_zero_projection(pool, "draftkings", r)
        self.assertEqual(_findings(r, "zero_projection"), [])

    def test_the_check_is_recorded_even_when_it_finds_nothing(self):
        r = _report()
        quality.check_zero_projection([], "draftkings", r)
        self.assertIn("zero_projection", r.checks_run)


class TestDuplicateIds(unittest.TestCase):
    def test_fires_when_the_same_id_appears_twice(self):
        r = _report()
        ps = [_p(player_id="dup", name="A", positions=["P"], salary=4000),
              _p(player_id="dup", name="B", positions=["P"], salary=4100)]
        quality.check_duplicate_ids(ps, r)
        f = _findings(r, "duplicate_player_id")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "critical")

    def test_silent_for_distinct_ids(self):
        r = _report()
        quality.check_duplicate_ids(helpers.mlb_pool(n_per_position=2), r)
        self.assertEqual(_findings(r, "duplicate_player_id"), [])


class TestImplausibleValues(unittest.TestCase):
    def test_negative_count_stat_is_critical(self):
        r = _report()
        p = _p(projected={"h": -1.0})
        quality.check_implausible_values([p], "mlb", r)
        self.assertEqual(len(_findings(r, "implausible_value", "critical")), 1)

    def test_negative_run_prevention_stats_are_allowed(self):
        """ER/GA are subtractions in the scoring table; a negative input is a sign error, not
        an impossibility, but these keys are explicitly exempted so we do not cry wolf."""
        r = _report()
        p = _p(projected={"er": -0.5, "ga": -1.0})
        quality.check_implausible_values([p], "mlb", r)
        self.assertEqual(_findings(r, "implausible_value", "critical"), [])

    def test_plate_appearances_above_the_sanity_bound_warn(self):
        r = _report()
        p = _p(projected={"pa": quality.MAX_MLB_PA + 1})
        quality.check_implausible_values([p], "mlb", r)
        self.assertEqual(len(_findings(r, "implausible_value", "warning")), 1)

    def test_plate_appearances_at_the_bound_do_not_warn(self):
        r = _report()
        p = _p(projected={"pa": quality.MAX_MLB_PA})
        quality.check_implausible_values([p], "mlb", r)
        self.assertEqual(_findings(r, "implausible_value", "warning"), [])

    def test_negative_salary_is_critical(self):
        r = _report()
        quality.check_implausible_values([_p(salary=-100)], "mlb", r)
        self.assertTrue(any("negative salary" in f.message for f in _findings(r)))

    def test_hockey_and_basketball_have_their_own_opportunity_bounds(self):
        r = _report()
        quality.check_implausible_values(
            [_p(projected={"toi": quality.MAX_HOCKEY_TOI + 5})], "nhl", r)
        self.assertEqual(len(_findings(r, "implausible_value", "warning")), 1)
        r2 = _report()
        quality.check_implausible_values(
            [_p(projected={"min": quality.MAX_BASKETBALL_MINUTES + 5})], "nba", r2)
        self.assertEqual(len(_findings(r2, "implausible_value", "warning")), 1)

    def test_unknown_sport_does_not_crash(self):
        r = _report()
        quality.check_implausible_values([_p(projected={"pa": 99})], "curling", r)
        self.assertEqual(_findings(r, "implausible_value", "warning"), [])


class TestStaleProvenance(unittest.TestCase):
    def _prov(self, hours_ago):
        ts = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=hours_ago)
        return [{"source": "mlb_statsapi", "fetched_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ")}]

    def test_fires_for_input_older_than_the_staleness_window(self):
        r = _report()
        quality.check_stale_provenance(self._prov(quality.STALE_AFTER_HOURS + 2), r)
        self.assertEqual(len(_findings(r, "stale_provenance")), 1)

    def test_silent_for_a_fresh_input(self):
        r = _report()
        quality.check_stale_provenance(self._prov(1), r)
        self.assertEqual(_findings(r, "stale_provenance"), [])

    def test_a_network_row_with_no_timestamp_is_flagged_not_assumed_fresh(self):
        """Freshness we cannot verify is reported, not quietly taken on trust."""
        for row in ({"url": "https://a.example/x"},
                    {"endpoint": "mlb_games", "status": 200}):
            r = _report()
            quality.check_stale_provenance([row], r)
            self.assertEqual(len(_findings(r, "stale_provenance")), 1, row)

    def test_a_static_row_with_no_timestamp_is_out_of_scope(self):
        """Scoring-table provenance carries audit_date, not fetched_at; not a fetch."""
        r = _report()
        quality.check_stale_provenance([{"source": "scoring", "stat": "hr", "value": 10.0}], r)
        self.assertEqual(_findings(r, "stale_provenance"), [])

    def test_an_unparseable_timestamp_is_flagged_not_crashed_on(self):
        r = _report()
        quality.check_stale_provenance([{"source": "x", "fetched_at": "not-a-date"}], r)
        self.assertEqual(len(_findings(r, "stale_provenance")), 1)


class TestEndpointFailures(unittest.TestCase):
    def test_one_finding_per_distinct_url(self):
        """Retries must not multiply a single dead endpoint into several defects."""
        r = _report()
        summary = {"failures": [
            {"url": "https://a.example/x", "error": "timeout", "attempt": 1},
            {"url": "https://a.example/x", "error": "timeout", "attempt": 2},
            {"url": "https://b.example/y", "error": "404", "attempt": 1},
        ]}
        quality.check_endpoint_failures(summary, r)
        f = _findings(r, "endpoint_failure")
        self.assertEqual(len(f), 2)
        self.assertTrue(all(x.severity == "critical" for x in f))
        self.assertIn("2 attempts", next(x.message for x in f if "a.example" in x.entity))

    def test_silent_when_nothing_failed(self):
        r = _report()
        quality.check_endpoint_failures({"failures": []}, r)
        self.assertEqual(_findings(r, "endpoint_failure"), [])
        quality.check_endpoint_failures({}, r)
        self.assertEqual(_findings(r, "endpoint_failure"), [])

    def test_a_failure_with_no_url_is_still_reported(self):
        r = _report()
        quality.check_endpoint_failures({"failures": [{"error": "boom"}]}, r)
        self.assertEqual(len(_findings(r, "endpoint_failure")), 1)


class TestCrossSourceIdentity(unittest.TestCase):
    def test_matching_rows_produce_no_finding(self):
        r = _report()
        rows = [{"id": "1", "name": "Aaron Judge"}, {"id": "2", "name": "Shohei Ohtani"}]
        quality.check_cross_source_identity(rows, list(rows), r)
        self.assertEqual(_findings(r), [])

    def test_a_projection_row_the_official_feed_does_not_have_is_flagged(self):
        """primary = official feed, secondary = the projection source being reconciled."""
        r = _report()
        official = [{"id": "1", "name": "Aaron Judge"}]
        projected = [{"id": "1", "name": "Aaron Judge"},
                     {"id": "9", "name": "Frank Gore", "team": "BUF"}]
        quality.check_cross_source_identity(official, projected, r, label="identity")
        f = _findings(r, "identity")
        self.assertEqual(len(f), 1)
        self.assertIn("Frank Gore", f[0].message)

    def test_the_check_catches_the_stale_roster_join_class_of_error(self):
        r = _report()
        quality.check_cross_source_identity(
            [{"name": "Josh Allen"}], [{"name": "Josh Allen Jr."}, {"name": "Josh Allen III"}], r)
        self.assertEqual(_findings(r), [], "generational suffixes must not create phantom mismatches")

    def test_a_row_with_no_name_is_skipped_not_flagged(self):
        r = _report()
        quality.check_cross_source_identity([{"name": "A"}], [{"team": "BUF"}, {"name": ""}], r)
        self.assertEqual(_findings(r), [])

    def test_a_custom_label_is_used_as_the_check_name(self):
        r = _report()
        quality.check_cross_source_identity([{"id": "1", "name": "X"}], [], r, label="my_label")
        self.assertTrue(all(f.check == "my_label" for f in _findings(r)))


class TestOwnershipNormalisation(unittest.TestCase):
    def test_shares_summing_to_one_are_silent(self):
        r = _report()
        ps = helpers.mlb_pool(n_per_position=2)
        for i, p in enumerate(ps):
            p.pown = 1.0 / len(ps)
        quality.check_ownership_normalisation(ps, r)
        self.assertEqual(_findings(r, "ownership_normalisation"), [])

    def test_shares_that_do_not_sum_to_one_warn(self):
        r = _report()
        ps = helpers.mlb_pool(n_per_position=2)
        for p in ps:
            p.pown = 0.5                    # deliberately over-normalised
        quality.check_ownership_normalisation(ps, r)
        self.assertEqual(len(_findings(r, "ownership_normalisation")), 1)

    def test_an_all_zero_slate_is_not_flagged(self):
        """No ownership data at all is 'absent', which is different from 'wrong'."""
        r = _report()
        quality.check_ownership_normalisation(helpers.mlb_pool(n_per_position=2), r)
        self.assertEqual(_findings(r, "ownership_normalisation"), [])


class TestScoringCoverage(unittest.TestCase):
    def test_every_stat_dk_mlb_projects_is_scored(self):
        """The mlb:draftkings table was validated against RG's own FPTS to 0.07."""
        r = _report()
        stats = {"pa": 4.0, "h": 1.0, "2b": 0.2, "hr": 0.1, "rbi": 0.5, "r": 0.5,
                 "sb": 0.05, "bb": 0.4, "hbp": 0.05, "k": 1.0, "cs": 0.01}
        quality.check_scoring_coverage([_p(projected=stats)],
                                       MLB_COEFFS, r, scoring_table=MLB_TABLE)
        self.assertEqual(_findings(r, "scoring_coverage", "warning"), [],
                         [f.message for f in _findings(r, "scoring_coverage")])

    def test_a_projected_stat_with_no_coefficient_is_reported_as_info(self):
        r = _report()
        quality.check_scoring_coverage([_p(projected={"batk": 3.0})],
                                       MLB_COEFFS, r, scoring_table=MLB_TABLE)
        f = _findings(r, "scoring_coverage", "info")
        self.assertTrue(any("batk" in str(x.value) for x in f))

    def test_an_unaudited_zero_on_a_projected_stat_is_a_warning(self):
        """This is the defect class that silently understates FPTS."""
        table = scoring.load("nfl", "draftkings")
        key = "dst_sack"
        self.assertIn(key, table.not_audited)
        coeffs = dict(table.points)
        coeffs[key] = 0.0
        r = _report()
        quality.check_scoring_coverage([_p(projected={key: 1.0})], coeffs, r, scoring_table=table)
        f = _findings(r, "scoring_coverage", "warning")
        self.assertTrue(f, "an unaudited zero on a projected stat must warn")
        self.assertIn("unaudited", f[0].message)
        self.assertIn(key, str(f[0].value))

    def test_a_deliberate_zero_is_informational_not_a_gap(self):
        """A key pinned at 0 because another key carries the production is IR-15, not a defect."""
        table = scoring.load("nfl", "draftkings")
        key = "fg_0_39"
        self.assertIn(key, table.intentionally_zero)
        self.assertNotIn(key, table.not_audited)
        coeffs = dict(table.points)
        coeffs[key] = 0.0
        r = _report()
        quality.check_scoring_coverage([_p(projected={key: 1.0})], coeffs, r, scoring_table=table)
        msgs = [f.message for f in _findings(r, "scoring_coverage")]
        self.assertFalse(any("unaudited" in m for m in msgs), msgs)
        self.assertTrue(any("deliberately scored at zero" in m for m in msgs), msgs)

    def test_the_two_kinds_of_zero_are_told_apart_on_the_same_table(self):
        table = scoring.load("nfl", "draftkings")
        coeffs = dict(table.points)
        coeffs["fg_0_39"] = 0.0
        coeffs["dst_sack"] = 0.0
        r = _report()
        quality.check_scoring_coverage(
            [_p(projected={"fg_0_39": 1.0, "dst_sack": 1.0})], coeffs, r, scoring_table=table)
        msgs = " | ".join(f.message for f in _findings(r, "scoring_coverage"))
        self.assertIn("dst_sack", msgs)
        self.assertNotIn("fg_0_39", next(f.message for f in _findings(r, "scoring_coverage",
                                                                      "warning")
                                         if "unaudited" in f.message))

    def test_without_a_table_the_blunt_fallback_still_warns(self):
        r = _report()
        quality.check_scoring_coverage([_p(projected={"h": 1.0})],
                                       {"h": 0.0}, r, scoring_table=None)
        self.assertEqual(len(_findings(r, "scoring_coverage", "warning")), 1)


class TestRepresentationDoubleCount(unittest.TestCase):
    def test_no_shipped_table_double_counts(self):
        for key in scoring.available():
            sport, site = key.split(":")
            r = _report()
            quality.check_representation_double_count(sport, site, r)
            self.assertEqual(_findings(r, severity="critical"), [],
                             f"{key} double-counts: {[f.message for f in _findings(r)]}")
            self.assertEqual(_findings(r, "representation_double_count"), [],
                             f"{key} produced an unexpected finding")

    def test_an_unshipped_configuration_is_not_reported_as_clean(self):
        """'No findings' and 'never checked' must not look the same in a report."""
        r = _report()
        quality.check_representation_double_count("curling", "draftkings", r)
        f = _findings(r, "representation_double_count")
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].severity, "warning")
        self.assertIn("not been audited", f[0].message)

    def test_the_check_is_recorded_even_for_an_unshipped_configuration(self):
        r = _report()
        quality.check_representation_double_count("curling", "draftkings", r)
        self.assertIn("representation_double_count", r.checks_run)


class TestCheckRegistry(unittest.TestCase):
    def test_every_registered_check_is_exercised_by_this_file(self):
        covered = {
            "check_zero_projection", "check_duplicate_ids", "check_implausible_values",
            "check_stale_provenance", "check_endpoint_failures",
            "check_ownership_normalisation", "check_scoring_coverage",
            "check_representation_double_count",
        }
        self.assertEqual({f.__name__ for f in quality.ALL_CHECKS}, covered,
                         "a quality check was added or removed without a test")

    def test_cross_source_identity_is_deliberately_not_in_the_default_registry(self):
        """It needs two feeds, so the pipeline calls it explicitly rather than by default."""
        self.assertNotIn(quality.check_cross_source_identity, quality.ALL_CHECKS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
