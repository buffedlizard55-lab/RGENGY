"""Scoring tables: provenance integrity and arithmetic.

These tests are the reason the scoring tables can be trusted at all.  A wrong
coefficient is invisible in the output - it just makes every projection quietly
wrong - so each one is pinned by a hand-computed expectation.
"""

from __future__ import annotations

import unittest

from helpers import REPO  # noqa: F401  (path setup)

from rgengy import scoring
from rgengy.scoring import ScoringTable


class TestAudit(unittest.TestCase):
    def test_every_table_is_structurally_valid(self):
        audit = scoring.audit()
        self.assertEqual(audit["structural_problems"], [],
                         "a scoring value carries an unknown status, a non-numeric value, "
                         "claims agreement without listing sources, or is flagged "
                         "intentionally_zero while non-zero")

    def test_no_table_double_counts_a_representation(self):
        """The bug that inflated every FanDuel NBA projection ~2x (IR-15)."""
        self.assertEqual(scoring.representation_audit(), [],
                         "a table scores an aggregate and its components at once")

    def test_audit_reports_clean(self):
        self.assertTrue(scoring.audit()["clean"])

    def test_available_keys_use_colon_separator(self):
        keys = scoring.available()
        self.assertIn("mlb:draftkings", keys)
        self.assertTrue(all(":" in k for k in keys),
                        "keys must be sport:site so callers can split unambiguously")
        self.assertNotIn("mlb_draftkings", keys)

    def test_expected_coverage(self):
        self.assertEqual(
            sorted(scoring.available()),
            ["mlb:draftkings", "mlb:fanduel", "mlb:yahoo",
             "nba:draftkings", "nba:fanduel",
             "nfl:draftkings", "nfl:fanduel",
             "nhl:draftkings", "nhl:fanduel",
             "wnba:draftkings", "wnba:fanduel"])

    def test_no_value_claims_operator_confirmation(self):
        """Honesty check: nothing was read from an operator's own page."""
        audit = scoring.audit()
        self.assertEqual(audit["operator_confirmed_total"], 0,
                         "no operator scoring page was reachable, so no value may claim "
                         "confirmed_by_operator")

    def test_every_value_has_a_known_status(self):
        for key in scoring.available():
            sport, site = key.split(":")
            for problem in scoring.load(sport, site).validate():
                self.fail(problem)


class TestHandComputedTotals(unittest.TestCase):
    """Pin the arithmetic so a coefficient edit cannot pass silently."""

    def test_draftkings_mlb(self):
        # 2 singles, 1 double, 1 HR, 2 R, 3 RBI, 1 BB  ->  DK MLB
        # 2*3 + 1*5 + 1*10 + 2*2 + 3*2 + 1*2 = 6+5+10+4+6+2 = 33.0
        t = scoring.load("mlb", "draftkings")
        self.assertAlmostEqual(
            t.score({"1b": 2, "2b": 1, "hr": 1, "r": 2, "rbi": 3, "bb": 1}), 33.0)

    def test_fanduel_mlb(self):
        # Same stat line on FanDuel:
        # 2*3 + 1*6 + 1*12 + 2*3.2 + 3*3.5 + 1*3 = 6+6+12+6.4+10.5+3 = 43.9
        t = scoring.load("mlb", "fanduel")
        self.assertAlmostEqual(
            t.score({"1b": 2, "2b": 1, "hr": 1, "r": 2, "rbi": 3, "bb": 1}), 43.9)

    def test_draftkings_mlb_pitcher(self):
        # 6 IP, 8 K, 2 ER, 1 win, 5 hits allowed, 2 BB allowed, 1 HBP allowed
        # 6*2.25 + 8*2 - 2*2 + 1*4 - 5*0.6 - 2*0.6 - 1*0.6
        # = 13.5 + 16 - 4 + 4 - 3 - 1.2 - 0.6 = 24.7
        t = scoring.load("mlb", "draftkings")
        self.assertAlmostEqual(
            t.score({"ip": 6, "k": 8, "er": 2, "win": 1, "ha": 5, "bba": 2, "hbpa": 1}), 24.7)

    def test_fanduel_does_not_double_count_pitcher_innings(self):
        """FanDuel pays 3 per inning; 'outs' must be pinned at 0 (IR-14)."""
        t = scoring.load("mlb", "fanduel")
        self.assertEqual(t.get("ip"), 3.0)
        self.assertEqual(t.get("outs"), 0.0)
        # 6 IP, 8 K, 2 ER, QS, win: 18 + 24 - 6 + 4 + 6 = 46
        self.assertAlmostEqual(
            t.score({"ip": 6, "outs": 18, "k": 8, "er": 2, "qs": 1, "win": 1}), 46.0)

    def test_fanduel_nba_does_not_double_count_points(self):
        t = scoring.load("nba", "fanduel")
        self.assertEqual(t.get("pts"), 1.0)
        self.assertEqual(t.get("two_pm"), 0.0)
        self.assertEqual(t.get("ftm"), 0.0)
        # 30 pts, 8 reb, 6 ast, 2 stl, 1 blk, 3 to, 4 threes (no FD 3PM bonus)
        # 30 + 9.6 + 9 + 6 + 3 - 3 = 54.6
        self.assertAlmostEqual(
            t.score({"pts": 30, "reb": 8, "ast": 6, "stl": 2, "blk": 1, "to": 3,
                     "three_pm": 4, "two_pm": 8, "ftm": 6}), 54.6)

    def test_draftkings_nba_pays_a_threepoint_bonus_on_top_of_points(self):
        """DK's 3PM=0.5 is additive, NOT a decomposition - so it is legal."""
        t = scoring.load("nba", "draftkings")
        # 30 pts, 4 threes, 8 reb, 6 ast, 2 stl, 1 blk, 3 to, DD bonus
        # 30 + 2 + 10 + 9 + 4 + 2 - 1.5 + 1.5 = 57.0
        self.assertAlmostEqual(
            t.score({"pts": 30, "three_pm": 4, "reb": 8, "ast": 6, "stl": 2,
                     "blk": 1, "to": 3, "dd": 1}), 57.0)

    def test_draftkings_nhl_goal_also_counts_as_a_shot(self):
        """Per DraftKings Network: a goal is 8.5 + 1.5 = 10.0."""
        t = scoring.load("nhl", "draftkings")
        self.assertEqual(t.get("g"), 8.5)
        self.assertEqual(t.get("sog"), 1.5)
        self.assertNotIn("sog_goal", t.points,
                         "the removed 'sog_goal' key would double count every goal (IR-14)")
        # The headline fact from DraftKings Network's own worked example
        # ("Center: +8.5 Pts (Goal) +1.5 (Shot on Goal) = 10 Pts"):
        self.assertAlmostEqual(t.score({"g": 1, "sog": 1}), 10.0)

        # 1 goal (which is also one of his 5 shots), 2 assists, 5 SOG, 3 blocks,
        # plus the three threshold bonuses:
        #   8.5 + 7.5 + 10.0 + 3.9 + 3 + 3 + 3 = 38.9
        self.assertAlmostEqual(
            t.score({"g": 1, "a": 2, "sog": 5, "blk": 3, "g3_pts": 1,
                     "g5_sog": 1, "g3_blk": 1}), 38.9)

    def test_draftkings_nfl_has_milestones_and_no_kicker(self):
        t = scoring.load("nfl", "draftkings")
        self.assertEqual(t.get("100ru"), 3.0)
        self.assertEqual(t.get("300pa"), 3.0)
        self.assertEqual(t.get("rec"), 1.0, "DraftKings is full PPR")
        self.assertEqual(t.get("pat"), 0.0, "DK classic has no kicker slot (IR-18)")
        self.assertEqual(t.get("fum_lost"), -1.0)

    def test_fanduel_nfl_is_half_ppr_with_kicker_and_no_milestones(self):
        t = scoring.load("nfl", "fanduel")
        self.assertEqual(t.get("rec"), 0.5)
        self.assertEqual(t.get("pat"), 1.0)
        self.assertEqual(t.get("fg_50p"), 5.0)
        self.assertEqual(t.get("100ru"), 0.0, "FanDuel pays no yardage milestones (IR-18)")
        self.assertEqual(t.get("fum_lost"), -2.0)

    def test_wnba_tables_are_deliberately_empty(self):
        """Limitation L-03: no WNBA source was retrieved, so nothing is asserted."""
        for site in ("draftkings", "fanduel"):
            t = scoring.load("wnba", site)
            self.assertTrue(all(v == 0.0 for v in t.points.values()),
                            f"wnba:{site} must not carry unaudited point values")
            self.assertEqual(len(t.not_audited), len(t.points))


class TestScoringTableApi(unittest.TestCase):
    def test_score_ignores_absent_stats(self):
        t = scoring.load("mlb", "draftkings")
        self.assertEqual(t.score({}), 0.0)

    def test_score_rounds_to_two_decimals(self):
        t = scoring.load("mlb", "draftkings")
        self.assertEqual(t.score({"1b": 1 / 3.0}), round(3.0 / 3.0, 2))

    def test_load_rejects_unknown_table(self):
        with self.assertRaises(FileNotFoundError):
            scoring.load("cricket", "draftkings")

    def test_provenance_rows_expose_status(self):
        rows = scoring.load("mlb", "draftkings").provenance_rows()
        self.assertTrue(all("verification_status" in r for r in rows))
        self.assertTrue(all("sources" in r for r in rows))

    def test_intentionally_zero_is_tracked(self):
        t = scoring.load("nba", "fanduel")
        self.assertIn("two_pm", t.intentionally_zero)
        self.assertIn("ftm", t.intentionally_zero)

    def test_validate_rejects_a_bad_status(self):
        bad = ScoringTable("mlb", "draftkings", {
            "meta": {}, "values": {"hr": {"value": 10.0, "verification_status": "trust-me",
                                          "sources": ["https://example.com"]}}})
        problems = bad.validate()
        self.assertTrue(any("trust-me" in p for p in problems))

    def test_validate_rejects_agreement_without_sources(self):
        bad = ScoringTable("mlb", "draftkings", {
            "meta": {}, "values": {"hr": {"value": 10.0,
                                          "verification_status": "multi-source-consistent",
                                          "sources": []}}})
        self.assertTrue(any("no sources" in p for p in bad.validate()))

    def test_validate_rejects_nonzero_intentionally_zero(self):
        bad = ScoringTable("mlb", "draftkings", {
            "meta": {}, "values": {"hr": {"value": 10.0, "verification_status": "not-applicable",
                                          "sources": [], "intentionally_zero": True}}})
        self.assertTrue(any("intentionally_zero" in p for p in bad.validate()))


if __name__ == "__main__":
    unittest.main()
