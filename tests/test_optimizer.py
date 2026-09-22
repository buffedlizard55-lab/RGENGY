"""Lineup optimiser: optimality, legality, and honest infeasibility reporting."""

from __future__ import annotations

import itertools
import random
import unittest

from helpers import make_player, mlb_pool

from rgengy import optimizer
from rgengy.models import RosterRule, default_roster


def brute_force(pool, rules, cap, site="draftkings"):
    """Exhaustive reference solver.  Only usable on tiny pools."""
    best_pts, best_roster = -1.0, None
    # total roster size is the sum of the slot COUNTS, not the number of slots
    n = sum(rule.count for rule in rules)
    for combo in itertools.combinations(range(len(pool)), n):
        chosen = [pool[i] for i in combo]
        # every slot must be satisfiable by a distinct chosen player
        remaining = list(chosen)
        ok = True
        for rule in rules:
            need = rule.count
            for cand in list(remaining):
                if need == 0:
                    break
                if any(pos in rule.eligible for pos in cand.positions):
                    remaining.remove(cand)
                    need -= 1
            if need > 0:
                ok = False
                break
        if not ok or remaining:
            continue
        salary = sum(int(p.salary) for p in chosen)
        if salary > cap:
            continue
        pts = sum(float(p.fpts.get(site) or 0.0) for p in chosen)
        if pts > best_pts:
            best_pts, best_roster = pts, sorted(p.player_id for p in chosen)
    return best_pts, best_roster


class TestOptimality(unittest.TestCase):
    def test_matches_brute_force_on_a_small_pool(self):
        """The DP must be exactly optimal, not merely good."""
        rng = random.Random(7)
        rules = [RosterRule("P", 2, ["P"]), RosterRule("C", 1, ["C"]),
                 RosterRule("1B", 1, ["1B"]),
                 RosterRule("UTIL", 1, ["C", "1B", "P"])]
        pool = []
        i = 0
        for pos, n in (("P", 4), ("C", 3), ("1B", 3)):
            for _ in range(n):
                i += 1
                pool.append(make_player(f"p{i}", f"P{i}", [pos],
                                        float(2000 + 500 * rng.randint(0, 8)),
                                        fpts=round(rng.uniform(3, 25), 2)))
        cap = 16000
        want_pts, want_ids = brute_force(pool, rules, cap)
        got = optimizer.optimize(pool, "mlb", "draftkings", salary_cap=cap, rules=rules,
                                 flex_candidates=12, max_flex_enumerations=4000)
        self.assertTrue(got.feasible)
        self.assertAlmostEqual(got.projected_points, want_pts, places=6)
        self.assertEqual(sorted(p.player_id for p in got.players), want_ids)

    def test_salary_cap_is_never_exceeded(self):
        pool = mlb_pool(n_per_position=4)
        res = optimizer.optimize(pool, "mlb", "draftkings")
        self.assertTrue(res.feasible)
        self.assertLessEqual(res.salary_used, res.salary_cap)

    def test_roster_is_legal_for_the_site_template(self):
        for sport, site in (("mlb", "draftkings"), ("mlb", "fanduel"),
                            ("nba", "draftkings"), ("nfl", "draftkings")):
            template = default_roster(sport, site)
            pool = _pool_for(sport, site)
            with self.subTest(sport=sport, site=site):
                res = optimizer.optimize(pool, sport, site, flex_candidates=6,
                                         max_flex_enumerations=600)
                if not res.feasible:
                    self.fail(f"{sport}:{site} infeasible: {res.infeasible_reason}")
                self.assertEqual(len(res.players), template["n_players"])
                self.assertLessEqual(res.salary_used, template["salary_cap"])
                _assert_slots_filled(res.players, template["slots"])


def _pool_for(sport, site, n=4):
    """A pool with enough players at every roster-eligible position."""
    template = default_roster(sport, site)
    positions = sorted({pos for rule in template["slots"] for pos in rule.eligible})
    rng = random.Random(11)
    pool, i = [], 0
    for pos in positions:
        for _ in range(n):
            i += 1
            pool.append(make_player(f"p{i}", f"{pos}{i}", [pos],
                                    float(2000 + 300 * rng.randint(0, 20)),
                                    site=site, fpts=round(rng.uniform(2, 30), 2)))
    return pool


def _assert_slots_filled(players, rules):
    """Every slot must be satisfiable by a distinct player in the roster."""
    remaining = list(players)
    for rule in rules:
        need = rule.count
        for cand in list(remaining):
            if need == 0:
                break
            if any(pos in rule.eligible for pos in cand.positions):
                remaining.remove(cand)
                need -= 1
        if need > 0:
            raise AssertionError(
                f"slot {rule.label} needs {rule.count} of {rule.eligible} but "
                f"{need} could not be filled from the returned roster")
    if remaining:
        raise AssertionError(f"{len(remaining)} rostered players fit no slot: "
                             f"{[p.positions for p in remaining]}")


class TestZeroValuePlayersAreRosterable(unittest.TestCase):
    def test_a_zero_projection_does_not_make_the_roster_infeasible(self):
        """The NFL bug: DST/K projected 0, were filtered out, and no lineup existed."""
        pool = _pool_for("nfl", "draftkings", n=3)
        for p in pool:
            if p.positions[0] in ("DST", "D", "K"):
                p.fpts["draftkings"] = 0.0
        res = optimizer.optimize(pool, "nfl", "draftkings")
        self.assertTrue(res.feasible, res.infeasible_reason)
        self.assertEqual(len(res.players), default_roster("nfl", "draftkings")["n_players"])

    def test_players_with_no_projection_for_the_site_are_dropped(self):
        pool = mlb_pool(n_per_position=3)
        for p in pool:
            p.fpts = {}          # no draftkings entry at all
        res = optimizer.optimize(pool, "mlb", "draftkings")
        self.assertFalse(res.feasible)
        self.assertIn("no player in the pool carries a draftkings projection",
                      res.infeasible_reason)


class TestInfeasibilityReporting(unittest.TestCase):
    def test_missing_position_names_the_slot(self):
        pool = [make_player(f"p{i}", f"P{i}", ["P"], 5000.0, fpts=10.0) for i in range(5)]
        res = optimizer.optimize(pool, "mlb", "draftkings")
        self.assertFalse(res.feasible)
        slots = {g["slot"]: g for g in res.unfilled_slots}
        # DraftKings MLB combines catcher and first base into one C/1B slot, so
        # that is the slot name that must appear (IR-17 correction).
        self.assertIn("C/1B", slots)
        self.assertEqual(slots["C/1B"]["candidates"], 0)
        self.assertEqual(slots["C/1B"]["count"], 1)
        self.assertIn("OF", slots)
        self.assertEqual(slots["OF"]["count"], 3)
        self.assertIn("C/1B", res.infeasible_reason)
        # every unfilled slot reports how many candidates it had
        self.assertTrue(all("candidates" in g for g in res.unfilled_slots))
        # the P slot was fillable, so it must NOT be listed as unfilled
        self.assertNotIn("P", slots)

    def test_impossible_salary_cap_is_reported_not_silently_none(self):
        pool = _pool_for("mlb", "draftkings", n=3)
        res = optimizer.optimize(pool, "mlb", "draftkings", salary_cap=1000)
        self.assertFalse(res.feasible)
        self.assertTrue(res.infeasible_reason)
        self.assertEqual(res.to_dict()["players"], [])

    def test_to_dict_exposes_the_reason(self):
        pool = [make_player("p1", "Solo", ["P"], 5000.0, fpts=10.0)]
        d = optimizer.optimize(pool, "mlb", "draftkings").to_dict()
        self.assertFalse(d["feasible"])
        self.assertIn("infeasible_reason", d)
        self.assertIn("unfilled_slots", d)


class TestBoundReporting(unittest.TestCase):
    def test_flex_truncation_is_declared_never_hidden(self):
        pool = _pool_for("mlb", "draftkings", n=6)
        res = optimizer.optimize(pool, "mlb", "draftkings", flex_candidates=3,
                                 max_flex_enumerations=2)
        if res.feasible:
            self.assertFalse(res.exact)
            self.assertTrue(res.bound_note)
            self.assertIn("enumerat", res.bound_note.lower())

    def test_small_pool_solves_exactly(self):
        rules = [RosterRule("P", 1, ["P"]), RosterRule("C", 1, ["C"])]
        pool = [make_player("p1", "A", ["P"], 3000.0, fpts=10.0),
                make_player("p2", "B", ["P"], 3000.0, fpts=8.0),
                make_player("c1", "C", ["C"], 3000.0, fpts=9.0)]
        res = optimizer.optimize(pool, "mlb", "draftkings", salary_cap=50000, rules=rules)
        self.assertTrue(res.feasible)
        self.assertTrue(res.exact)
        self.assertAlmostEqual(res.projected_points, 19.0)


class TestMultiLineup(unittest.TestCase):
    def test_lineups_are_distinct(self):
        pool = _pool_for("mlb", "draftkings", n=5)
        out = optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=5,
                                       flex_candidates=5, max_flex_enumerations=200)
        self.assertTrue(out.get("feasible", True))
        rosters = [frozenset(p["id"] for p in lu["players"]) for lu in out["lineups"]]
        self.assertEqual(len(set(rosters)), len(rosters))

    def test_first_lineup_is_the_optimum(self):
        pool = _pool_for("mlb", "draftkings", n=4)
        single = optimizer.optimize(pool, "mlb", "draftkings", flex_candidates=5,
                                    max_flex_enumerations=200)
        multi = optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=3,
                                         flex_candidates=5, max_flex_enumerations=200)
        self.assertTrue(multi["lineups"])
        self.assertAlmostEqual(multi["lineups"][0]["projected_points"],
                               single.projected_points, places=6)

    def test_exposure_cap_is_respected(self):
        pool = _pool_for("mlb", "draftkings", n=6)
        out = optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=6,
                                       flex_candidates=5, max_flex_enumerations=200,
                                       max_exposure=0.5)
        counts = {}
        for lu in out["lineups"]:
            for p in lu["players"]:
                counts[p["id"]] = counts.get(p["id"], 0) + 1
        limit = max(1, int(-(-0.5 * len(out["lineups"]) // 1)))
        self.assertTrue(all(c <= limit for c in counts.values()),
                        f"exposure cap breached: {counts} limit {limit}")

    def test_seeded_runs_reproduce_exactly(self):
        pool = _pool_for("mlb", "draftkings", n=5)
        a = optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=4, rng_seed=99,
                                     flex_candidates=5, max_flex_enumerations=200)
        b = optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=4, rng_seed=99,
                                     flex_candidates=5, max_flex_enumerations=200)
        self.assertEqual(a["lineups"], b["lineups"])

    def test_infeasible_multi_reports_the_reason(self):
        pool = [make_player("p1", "Solo", ["P"], 5000.0, fpts=10.0)]
        out = optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=3)
        self.assertEqual(out["lineups"], [])
        self.assertFalse(out["feasible"])
        self.assertTrue(out["unfilled_slots"])

    def test_bad_exposure_raises(self):
        pool = _pool_for("mlb", "draftkings", n=3)
        with self.assertRaises(ValueError):
            optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=2, max_exposure=0.0)


class TestSlotPartition(unittest.TestCase):
    def test_dk_mlb_has_exactly_one_flex_slot(self):
        flex, fixed = optimizer._split_slots(default_roster("mlb", "draftkings")["slots"])
        labels = sorted(default_roster("mlb", "draftkings")["slots"][i].label for i in flex)
        self.assertEqual(labels, ["UTIL"],
                         "a UTIL slot must not cause every positional slot to be "
                         "reclassified as flex - that was a combinatorial explosion")
        self.assertEqual(len(fixed), 6)

    def test_dk_nba_flex_slots(self):
        flex, _ = optimizer._split_slots(default_roster("nba", "draftkings")["slots"])
        labels = sorted(default_roster("nba", "draftkings")["slots"][i].label for i in flex)
        self.assertEqual(labels, ["F", "G", "UTIL"])


class TestRosterUniqueness(unittest.TestCase):
    """A lineup containing the same player twice is rejected by every operator.

    Regression for a real defect: ``_overlap_pairs`` tested whether two slots'
    ELIGIBILITY SETS intersected, so DraftKings MLB ``C/1B`` (C, 1B) and ``OF``
    (OF, LF, CF, RF) were treated as disjoint and solved as independent groups.
    A player listed at both 1B and OF matched both, was picked by both group
    knapsacks, and the published roster carried him twice - with his points
    counted twice.
    """

    def setUp(self):
        # One two-position player, plus enough single-position players that the
        # only reason to double up would be the bug itself.
        self.pool = [
            make_player(player_id="dual", name="Dual Threat", positions=["1B", "OF"],
                        salary=5000, fpts=30.0),
            make_player(player_id="c1", name="Catcher One", positions=["C"], salary=4000, fpts=10.0),
            make_player(player_id="o1", name="Outfield One", positions=["OF"], salary=4000, fpts=12.0),
            make_player(player_id="o2", name="Outfield Two", positions=["OF"], salary=3800, fpts=11.0),
            make_player(player_id="o3", name="Outfield Three", positions=["CF"], salary=3600, fpts=10.0),
            make_player(player_id="b2", name="Second Base", positions=["2B"], salary=3500, fpts=9.0),
            make_player(player_id="b3", name="Third Base", positions=["3B"], salary=3400, fpts=9.0),
            make_player(player_id="s1", name="Shortstop", positions=["SS"], salary=3300, fpts=8.0),
            make_player(player_id="p1", name="Pitcher One", positions=["SP"], salary=8000, fpts=15.0),
            make_player(player_id="p2", name="Pitcher Two", positions=["SP"], salary=7500, fpts=14.0),
            make_player(player_id="p3", name="Pitcher Three", positions=["RP"], salary=5000, fpts=6.0),
        ]
        self.rules = default_roster("mlb", "draftkings")["slots"]

    def test_no_lineup_contains_a_duplicate_player(self):
        res = optimizer.optimize_multi(self.pool, "mlb", "draftkings", n_lineups=6,
                                       rules=self.rules)
        self.assertTrue(res["lineups"], res.get("infeasible_reason"))
        for i, lineup in enumerate(res["lineups"]):
            ids = [p["id"] for p in lineup["players"]]      # optimize_multi returns dicts
            self.assertEqual(len(ids), len(set(ids)), f"lineup {i} doubles up: {ids}")
            self.assertEqual(len(ids), sum(r.count for r in self.rules))

    def test_the_single_optimum_has_no_duplicate(self):
        res = optimizer.optimize(self.pool, "mlb", "draftkings", rules=self.rules)
        self.assertTrue(res.feasible, res.infeasible_reason)
        ids = [p.player_id for p in res.players]
        self.assertEqual(len(ids), len(set(ids)), ids)
        self.assertEqual(len(ids), sum(r.count for r in self.rules))

    def test_projected_points_do_not_count_a_player_twice(self):
        res = optimizer.optimize(self.pool, "mlb", "draftkings", rules=self.rules)
        self.assertAlmostEqual(res.projected_points,
                               sum(p.fpts["draftkings"] for p in res.players), places=6)

    def test_slots_with_disjoint_labels_but_a_shared_player_are_detected(self):
        """The conflict test must look at the pool, not at the slot labels."""
        rules = [RosterRule(label="C/1B", count=1, eligible=["C", "1B"]),
                 RosterRule(label="OF", count=1, eligible=["OF", "LF", "CF", "RF"])]
        self.assertEqual(optimizer._overlap_pairs(rules, [0, 1]), [],
                         "label-only overlap sees these as disjoint")
        self.assertEqual(optimizer._overlap_pairs(rules, [0, 1], self.pool), [(0, 1)],
                         "the dual-position player makes them conflict")

    def test_split_slots_is_pool_aware(self):
        rules = [RosterRule(label="C/1B", count=1, eligible=["C", "1B"]),
                 RosterRule(label="OF", count=1, eligible=["OF", "LF", "CF", "RF"])]
        flex, fixed = optimizer._split_slots(rules)
        self.assertEqual(flex, [], "with no pool there is no evidence of a conflict")
        flex, fixed = optimizer._split_slots(rules, self.pool)
        self.assertEqual(len(flex), 1, "one slot must move to flex to break the conflict")
        self.assertEqual(len(fixed), 1)

    def test_split_slots_stays_label_based_without_a_pool(self):
        """Backwards compatibility: the pool argument is optional."""
        flex, _ = optimizer._split_slots(default_roster("nba", "draftkings")["slots"])
        labels = sorted(default_roster("nba", "draftkings")["slots"][i].label for i in flex)
        self.assertEqual(labels, ["F", "G", "UTIL"])


class TestSlotBreakdown(unittest.TestCase):
    """The slot report must account for every player in the roster."""

    def setUp(self):
        self.pool = _pool_for("mlb", "draftkings", n=8)
        self.rules = default_roster("mlb", "draftkings")["slots"]

    def test_slot_names_cover_the_whole_roster(self):
        """Regression: zip(flex_rules, picked) paired one flex member per RULE, so
        a 3-count OF flex slot reported a single name and the breakdown accounted
        for fewer players than the roster held."""
        res = optimizer.optimize_multi(self.pool, "mlb", "draftkings", n_lineups=4,
                                       rules=self.rules)
        self.assertTrue(res["lineups"], res.get("infeasible_reason"))
        for lineup in res["lineups"]:
            named = [n for v in lineup["slots"].values() for n in v]
            self.assertEqual(len(named), len(lineup["players"]),
                             f"slot breakdown names {len(named)} of "
                             f"{len(lineup['players'])} roster players: {lineup['slots']}")

    def test_every_roster_slot_label_is_present(self):
        res = optimizer.optimize(self.pool, "mlb", "draftkings", rules=self.rules)
        self.assertTrue(res.feasible, res.infeasible_reason)
        self.assertEqual(set(res.slots), {r.label for r in self.rules})

    def test_each_slot_lists_the_right_number_of_players(self):
        res = optimizer.optimize(self.pool, "mlb", "draftkings", rules=self.rules)
        if not res.feasible:
            self.skipTest(res.infeasible_reason)
        for rule in self.rules:
            self.assertEqual(len(res.slots[rule.label]), rule.count, rule.label)

    def test_a_flex_slot_needing_three_players_lists_all_three(self):
        res = optimizer.optimize(self.pool, "mlb", "draftkings", rules=self.rules)
        if not res.feasible:
            self.skipTest(res.infeasible_reason)
        of_count = next(r.count for r in self.rules if r.label == "OF")
        self.assertEqual(len(res.slots["OF"]), of_count)


class TestPublishedRosterInvariants(unittest.TestCase):
    def test_the_salary_cap_is_never_exceeded(self):
        pool = _pool_for("mlb", "draftkings", n=8)
        cap = default_roster("mlb", "draftkings")["salary_cap"]
        res = optimizer.optimize_multi(pool, "mlb", "draftkings", n_lineups=5)
        for lineup in res["lineups"]:
            self.assertLessEqual(lineup["salary_used"], cap)
            self.assertEqual(lineup["salary_used"],
                             sum(int(p["salary"]) for p in lineup["players"]))
            self.assertEqual(lineup["salary_remaining"], cap - lineup["salary_used"])

    def test_the_guard_rejects_a_duplicated_roster(self):
        from rgengy.optimizer import OptimizerResult, _assert_valid_roster
        p = make_player(player_id="x", name="X", positions=["OF"], salary=4000, fpts=10.0)
        bad = OptimizerResult(players=[p, p], projected_points=20.0, salary_used=8000,
                              salary_cap=50000, exact=True)
        with self.assertRaises(RuntimeError) as cm:
            _assert_valid_roster(bad, 50000)
        self.assertIn("same player more than once", str(cm.exception))

    def test_the_guard_rejects_an_over_cap_roster(self):
        from rgengy.optimizer import OptimizerResult, _assert_valid_roster
        p = make_player(player_id="x", name="X", positions=["OF"], salary=4000, fpts=10.0)
        bad = OptimizerResult(players=[p], projected_points=10.0, salary_used=60000,
                              salary_cap=50000, exact=True)
        with self.assertRaises(RuntimeError):
            _assert_valid_roster(bad, 50000)

    def test_the_guard_passes_a_valid_roster(self):
        from rgengy.optimizer import OptimizerResult, _assert_valid_roster
        a = make_player(player_id="a", name="A", positions=["OF"], salary=4000, fpts=10.0)
        b = make_player(player_id="b", name="B", positions=["2B"], salary=3500, fpts=9.0)
        _assert_valid_roster(OptimizerResult(players=[a, b], projected_points=19.0,
                                             salary_used=7500, salary_cap=50000, exact=True),
                             50000)


class TestPerformance(unittest.TestCase):
    def test_realistic_pool_solves_quickly(self):
        import time
        pool = _pool_for("mlb", "draftkings", n=12)   # ~84 players
        t0 = time.time()
        res = optimizer.optimize(pool, "mlb", "draftkings", flex_candidates=8,
                                 max_flex_enumerations=400)
        self.assertLess(time.time() - t0, 20.0)
        self.assertTrue(res.feasible)


if __name__ == "__main__":
    unittest.main()
