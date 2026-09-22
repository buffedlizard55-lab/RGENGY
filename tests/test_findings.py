"""Findings-register integrity tests.

The register is the single source of truth for the IR-nn and L-nn ids that the
scoring tables, module docstrings and quality findings all cite.  These tests
keep the two in step: an id cited in code but missing from the register is an
undocumented irregularity, and an id in the register that nothing cites is
dead prose.  Both directions are failures.
"""
import pathlib, re, sys, unittest
import helpers  # noqa: F401
sys.path.insert(0, helpers.REPO)

from rgengy import findings

ROOT = pathlib.Path(helpers.REPO)
SCAN_GLOBS = ("rgengy/*.py", "rgengy/data/scoring/*.json", "scripts/*.py",
              "tests/*.py", "docs/*.md", "README.md", "site/*.html", "site/*.js")
ID_RE = re.compile(r"\b(IR|L)-(\d{2})\b")

#: Files that are rendered FROM a registry rather than written by hand.  Counting
#: them as citations would be circular: docs/09 and site/findings.html are
#: generated from findings.py, so they "cite" every id including the ones declared
#: unused, and docs/03 is generated from the scoring tables.  A citation has to
#: originate somewhere a human wrote it.  Both generators stamp the same marker.
GENERATED_MARKER = "GENERATED FILE - DO NOT EDIT"
NEVER_A_CITATION = {"findings.py", "test_findings.py"}


def _referenced_ids():
    """Every IR-nn / L-nn id cited by a hand-written file, with locations."""
    found = {}
    for glob in SCAN_GLOBS:
        for path in ROOT.glob(glob):
            if path.name in NEVER_A_CITATION:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if GENERATED_MARKER in text[:400]:
                continue
            for m in ID_RE.finditer(text):
                found.setdefault(m.group(0), set()).add(str(path.relative_to(ROOT)))
    return found


def _generated_files():
    out = []
    for glob in SCAN_GLOBS:
        for path in ROOT.glob(glob):
            try:
                if GENERATED_MARKER in path.read_text(encoding="utf-8")[:400]:
                    out.append(path)
            except (UnicodeDecodeError, OSError):
                continue
    return out


class TestRegisterIntegrity(unittest.TestCase):
    def test_the_register_passes_its_own_validation(self):
        self.assertEqual(findings.validate(), [], findings.validate())

    def test_ids_are_unique(self):
        ids = findings.ids()
        self.assertEqual(len(ids), len(set(ids)))

    def test_irregularities_use_IR_and_limitations_use_L(self):
        for f in findings.irregularities():
            self.assertTrue(f.id.startswith("IR-"), f.id)
        for f in findings.limitations():
            self.assertTrue(f.id.startswith("L-"), f.id)

    def test_every_kind_and_status_is_from_the_declared_vocabulary(self):
        for f in findings.FINDINGS:
            self.assertIn(f.kind, findings.KINDS)
            self.assertIn(f.status, findings.STATUSES)
            self.assertIn(f.severity, findings.SEVERITIES)

    def test_every_source_is_an_absolute_url(self):
        for f in findings.FINDINGS:
            for url in f.sources:
                self.assertTrue(url.startswith("http"), f"{f.id}: {url}")

    def test_serialisation_is_json_shaped(self):
        import json
        d = findings.to_dict()
        json.dumps(d)
        self.assertEqual(d["counts"]["total"], len(findings.FINDINGS))
        self.assertEqual(len(d["findings"]), len(findings.FINDINGS))


class TestCrossReferences(unittest.TestCase):
    """Code and register must agree in both directions."""

    def setUp(self):
        self.refs = _referenced_ids()
        self.registered = set(findings.ids())

    def test_every_id_cited_in_the_tree_is_registered(self):
        missing = sorted(set(self.refs) - self.registered)
        self.assertEqual(missing, [], f"cited but not registered: {missing}")

    def test_every_registered_id_is_cited_somewhere_or_declared_unused(self):
        for f in findings.FINDINGS:
            if f.status == "unused-id":
                continue
            self.assertIn(f.id, self.refs,
                          f"{f.id} is registered but nothing in the tree cites it")

    def test_unused_ids_are_genuinely_uncited(self):
        """An id can only be declared unused if nothing actually uses it."""
        for f in findings.FINDINGS:
            if f.status == "unused-id":
                self.assertNotIn(f.id, self.refs,
                                 f"{f.id} is declared unused but is cited in "
                                 f"{sorted(self.refs.get(f.id, ()))}")

    def test_numbering_gaps_are_all_declared(self):
        """A silent gap in the sequence would look like a suppressed finding."""
        for prefix in ("IR", "L"):
            nums = sorted(int(f.id.split("-")[1]) for f in findings.FINDINGS
                          if f.id.startswith(prefix + "-"))
            for gap in range(1, max(nums) + 1):
                if gap not in nums:
                    self.fail(f"{prefix}-{gap:02d} is missing from the register entirely; "
                              f"either register it or declare it unused-id")

    def test_generated_ids_do_not_satisfy_the_citation_requirement(self):
        """A finding justified only by its own rendered document is not justified."""
        from rgengy import findings as F
        for f in F.FINDINGS:
            if f.status == "unused-id":
                continue
            citing = self.refs.get(f.id, set())
            self.assertTrue(citing, f"{f.id} is cited only by generated files")
            self.assertFalse(all(p.startswith("docs/") for p in citing) and not citing,
                             f.id)

    def test_resolved_findings_still_explain_what_changed(self):
        for f in findings.FINDINGS:
            if f.status == "resolved":
                self.assertIn("RESOLVED", f.title, f.id)
                self.assertTrue(f.detail, f.id)


class TestCoverage(unittest.TestCase):
    def test_the_register_covers_every_irregularity_the_audit_found(self):
        ids = set(findings.ids())
        for expected in ("IR-01", "IR-02", "IR-03", "IR-12", "IR-13", "IR-21", "IR-22", "IR-23",
                         "L-02", "L-03", "L-04", "L-05", "L-06"):
            self.assertIn(expected, ids)

    def test_open_findings_are_the_ones_that_constrain_claims(self):
        open_ids = {f.id for f in findings.open_findings()}
        self.assertIn("L-02", open_ids)
        self.assertNotIn("IR-09", open_ids, "IR-09 is resolved")
        self.assertNotIn("IR-17", open_ids, "IR-17 is resolved")

    def test_every_open_finding_states_a_concrete_action(self):
        for f in findings.open_findings():
            self.assertGreater(len(f.action), 60, f"{f.id}: action is not actionable")

    def test_get_raises_for_an_unknown_id(self):
        with self.assertRaises(KeyError):
            findings.get("IR-99")

    def test_generated_files_are_recognised_as_generated(self):
        """The exclusion above depends on this marker staying in the generator."""
        generated = {p.name for p in _generated_files()}
        self.assertTrue({"09-irregularities.md", "03-scoring-verification.md"} <= generated,
                        generated)
        self.assertNotIn("00-index.md", generated, "hand-written docs must not be excluded")

    def test_the_audit_date_matches_the_source_registry(self):
        from rgengy import sources
        self.assertEqual(findings.AUDIT_DATE, sources.AUDIT_DATE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
