"""The canonical register of irregularities (IR-nn) and limitations (L-nn).

Everything RGENGY could not verify from an official source, every conflict
between sources, and every assumption it had to make is recorded here exactly
once.  ``docs/09-irregularities.md``, ``docs/10-roadmap-and-limitations.md`` and
the published site are all GENERATED from this module, so the prose can never
drift away from the code that cites it - ``rgengy verify`` and
``tests/test_findings.py`` both fail if a code reference names an id that is not
registered here, or if a registered id is referenced nowhere.

Conventions
-----------
``kind``
    ``"irregularity"`` for something observed in the wild that is wrong,
    conflicting or undefined; ``"limitation"`` for something RGENGY itself cannot
    yet do.
``status``
    ``open``            - unresolved, and the affected number is labelled or excluded.
    ``resolved``        - was a defect in RGENGY or in this audit, now fixed; kept
                          on the register because the fix changed a published value.
    ``assumption``      - RGENGY proceeds on a stated, unaudited assumption.
    ``unused-id``       - the identifier is deliberately not used.  Retiring an id
                          silently would make every cross-reference in older notes
                          ambiguous, so gaps in the numbering are declared.

Every entry carries ``sources`` (URLs actually retrieved during the audit, or an
empty list where the finding is internal to RGENGY) and ``refs`` (the modules
that cite it).  An entry with no evidence and no reference is a bug in this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

AUDIT_DATE = "2026-09-22"

#: RotoGrinders pages retrieved during the audit.
RG_MLB_GRID = "https://rotogrinders.com/projected-stats/mlb?site=draftkings"
RG_BAT_VEGAS = "https://rotogrinders.com/articles/the-bat-vs-vegas-2016-results-1873096"
RG_OWNERSHIP_FAQ = "https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773"
RG_FD_NBA_STRATEGY = "https://rotogrinders.com/articles/fanduel-nba-strategy-239702"


@dataclass(frozen=True)
class Finding:
    """One irregularity or limitation, with its evidence and its consequences."""

    id: str
    kind: str                       # "irregularity" | "limitation"
    title: str
    status: str                     # "open" | "resolved" | "assumption" | "unused-id"
    detail: str
    impact: str
    action: str
    severity: str = "warning"       # "info" | "warning" | "critical"
    sources: Sequence[str] = ()
    refs: Sequence[str] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "kind": self.kind, "title": self.title, "status": self.status,
            "severity": self.severity, "detail": self.detail, "impact": self.impact,
            "action": self.action, "sources": list(self.sources), "refs": list(self.refs),
        }


FINDINGS: List[Finding] = [
    # ------------------------------------------------------------------ IR-01
    Finding(
        id="IR-01", kind="irregularity", severity="warning", status="open",
        title="ESPN's site API is undocumented and publishes no terms of use",
        detail=(
            "The slate, score, venue and odds data for NFL, NBA, NHL and WNBA comes from "
            "https://site.api.espn.com/apis/site/v2/sports/{sport}/scoreboard. It was retrieved "
            f"live on {AUDIT_DATE} (HTTP 200) and its field names were confirmed by inspection, "
            "but ESPN publishes no documentation and no terms for it. It is an internal feed for "
            "espn.com, not a product."),
        impact=(
            "The feed can change shape or be withdrawn without notice, and continued use is a "
            "compliance risk for any published or commercial deployment."),
        action=(
            "The endpoint is marked official=False with a terms_url of null in the registry, so "
            "every artefact that used it says so. Replace it with a licensed provider before any "
            "commercial use. `rgengy probe` re-checks the live shape."),
        sources=["https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
                 "https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c"],
        refs=["rgengy/sources.py"]),

    # ------------------------------------------------------------------ IR-02
    Finding(
        id="IR-02", kind="irregularity", severity="warning", status="open",
        title="RotoGrinders publishes the Bryant formula but not its AdjustedSpread input",
        detail=(
            "RotoGrinders attributes this implied-team-total formula to co-founder Riley Bryant: "
            "(TotalPoints / 2) - (Spread * (100 / (AdjustedSpread + 100))) / 2. The derivation of "
            "`AdjustedSpread` is not published anywhere on the site."),
        impact=(
            "The formula cannot be reproduced end to end from published information alone. Any "
            "number produced by guessing AdjustedSpread would look exactly like a reproduction "
            "and would not be one."),
        action=(
            "`vegas.bryant_published()` transcribes the formula verbatim and takes "
            "`adjusted_spread` as a REQUIRED argument, so it raises rather than invents one. It "
            "is shipped for inspection, not as the default path; `vegas.implied_totals()` is the "
            "default and documents its own method."),
        sources=[RG_BAT_VEGAS],
        refs=["rgengy/vegas.py"]),

    # ------------------------------------------------------------------ IR-03
    Finding(
        id="IR-03", kind="irregularity", severity="warning", status="assumption",
        title="The score-distribution sigmas used to turn a margin into a win probability are unaudited",
        detail=(
            "Where no market line exists, a team win probability is derived from the expected "
            "output differential divided by a per-sport sigma (`engines.SIGMA_BY_SPORT`). Those "
            "sigmas are conventional values, not fitted to data, and none is confirmed by an "
            "official source."),
        impact=(
            "Derived win probabilities are sensitive to sigma. The NFL value of 13.5 is known to "
            "understate heavy favourites, so a moneyline-derived probability should be preferred "
            "wherever one exists."),
        action=(
            "The preference order is enforced in one place (`engines.team_win_probability`): "
            "market line first, differential second, and the method actually used is written into "
            "the projection note and into the artefact. No win probability is ever emitted without "
            "its origin."),
        sources=[],
        refs=["rgengy/engines.py", "rgengy/pipeline.py"]),

    # ------------------------------------------------------------------ IR-04
    Finding(
        id="IR-04", kind="irregularity", severity="info", status="open",
        title="DraftKings MLB caught-stealing (-2) is reported by only one source",
        detail=(
            "Only RotoWire lists Caught Stealing = -2 for DraftKings MLB. The 2026 "
            "fantasyteamadvice calculator and the DraftKings/FanDuel comparison tables omit it "
            "entirely, which is not the same as contradicting it."),
        impact="A hitter's FPTS may be overstated by up to 2 points per caught stealing.",
        action=(
            "The value is shipped as `verification_status: single-source`, `disputed: true`, "
            "`agreement: 1`, so `rgengy scoring` and the site both show it as the weakest "
            "evidence class on the table."),
        sources=["https://www.rotowire.com/baseball/article/fantasy-101-how-to-win-on-draftkings-basic-strategy-23444"],
        refs=["rgengy/data/scoring/mlb_draftkings.json"]),

    # ------------------------------------------------------------------ IR-05
    Finding(
        id="IR-05", kind="irregularity", severity="warning", status="open",
        title="DraftKings MLB quality-start bonus is directly contradicted between sources",
        detail=(
            "sportsfanfocus and dailyfantasysports101 both show DraftKings Quality Start = 0 (no "
            "bonus); runpuresports lists +4 under its DraftKings heading. This is a genuine "
            "contradiction, not an omission."),
        impact=(
            "A starting pitcher's FPTS is understated by 4.0 if runpuresports is right. That is "
            "large relative to a pitcher's typical projection and would change roster selection."),
        action=(
            "Set to 0.0 (the two-source majority) and marked `disputed: true`. Resolving it needs "
            "DraftKings' own scoring page, which is inside the logged-in app and could not be "
            "retrieved. `rgengy scoring` prints the conflict next to the value."),
        sources=["https://sportsfanfocus.com/draftkings-yahoo-fanduel-mlb-scoring/",
                 "https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/",
                 "https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/"],
        refs=["rgengy/data/scoring/mlb_draftkings.json"]),

    # ------------------------------------------------------------------ IR-06
    Finding(
        id="IR-06", kind="irregularity", severity="info", status="open",
        title="FanDuel MLB earned-run penalty is -3 in three sources and -1 in one",
        detail=(
            "Three independent sources give FanDuel MLB Earned Run = -3. runpuresports gives -1. "
            "The majority value was adopted."),
        impact=(
            "If the outlier is correct, FanDuel pitcher FPTS is understated by 2.0 per earned run "
            "- a material error over a 5-run outing."),
        action=(
            "Shipped as -3.0 with the conflict recorded in the value's note and surfaced by "
            "`rgengy scoring`. Needs FanDuel's own scoring page to settle."),
        sources=["https://runpuresports.com/the-ultimate-guide-to-mlb-dfs-winning-strategies-for-draftkings-and-fanduel/"],
        refs=["rgengy/data/scoring/mlb_fanduel.json"]),

    # ------------------------------------------------------------------ IR-07
    Finding(
        id="IR-07", kind="irregularity", severity="info", status="unused-id",
        title="Identifier IR-07 is deliberately unused",
        detail=(
            "No finding in this register, in the scoring tables, or anywhere in the source tree "
            "cites IR-07. The id was consumed during the audit by an item that was resolved "
            "before the register was written and then folded into IR-05 and IR-06, which cover the "
            "same class of problem (single-source and contradicted scoring values)."),
        impact=(
            "A gap in the numbering. Left undeclared it would invite the assumption that a "
            "finding had been suppressed."),
        action=(
            "Declared here rather than renumbered: renumbering would silently invalidate every "
            "IR-nn cross-reference already written into the scoring tables and module docstrings."),
        sources=[],
        refs=["rgengy/findings.py"]),

    # ------------------------------------------------------------------ IR-08
    Finding(
        id="IR-08", kind="irregularity", severity="info", status="open",
        title="FanDuel NBA double-double and triple-double bonuses are unconfirmed",
        detail=(
            "Neither RotoGrinders' own FanDuel NBA strategy article nor dfsbuild's comparison "
            "table lists a FanDuel double-double or triple-double bonus, but FanDuel has "
            "historically scored them. Absence from two secondary sources is not evidence of "
            "absence from the operator's rules."),
        impact=(
            "A player reaching a double-double may be understated. Both keys are shipped at 0.0, "
            "which is the conservative direction - it never overstates a projection."),
        action=(
            "Both keys are marked `disputed: true` with the ambiguity stated in their notes, and "
            "`quality.check_scoring_coverage` reports them as a coverage question rather than "
            "letting the zero pass silently."),
        sources=[RG_FD_NBA_STRATEGY],
        refs=["rgengy/data/scoring/nba_fanduel.json", "scripts/build_scoring_tables.py"]),

    # ------------------------------------------------------------------ IR-09
    Finding(
        id="IR-09", kind="irregularity", severity="info", status="resolved",
        title="RESOLVED: DraftKings NHL goal value was missing",
        detail=(
            "Pass 1 had no sourced value for a DraftKings NHL goal. DraftKings' own published "
            "NHL DFS 101 article states goal = 10.0, which is an operator document rather than a "
            "secondary summary."),
        impact="Resolved. The value is now operator-sourced.",
        action=(
            "Adopted 10.0 from dknetwork.draftkings.com and recorded the operator URL in the "
            "value's source list. This is one of the few values in the register backed by the "
            "operator itself."),
        sources=["https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101"],
        refs=["rgengy/data/scoring/nhl_draftkings.json", "scripts/build_scoring_tables.py"]),

    # ------------------------------------------------------------------ IR-10
    Finding(
        id="IR-10", kind="irregularity", severity="warning", status="open",
        title="FanDuel NHL scoring rests on a single document, and FanDuel also scores +/-",
        detail=(
            "The FanDuel NHL table is sourced from exactly one document (ftnfantasy). FanDuel "
            "additionally scores plus/minus, which DraftKings does not."),
        impact=(
            "`nhl:fanduel` is marked `single-source`, the weakest evidence class. The plus/minus "
            "key is shipped as `not-audited` with a 0.0 coefficient, so FanDuel goalie and skater "
            "FPTS is understated by an unknown amount."),
        action=(
            "`quality.check_scoring_coverage` escalates an unaudited zero on a stat that is "
            "actually projected to a warning, so the understatement surfaces in every run report "
            "instead of hiding inside a total."),
        sources=["https://ftnfantasy.com/nhl/the-basics-of-dfs-fantasy-hockey"],
        refs=["rgengy/data/scoring/nhl_fanduel.json", "rgengy/quality.py"]),

    # ------------------------------------------------------------------ IR-11
    Finding(
        id="IR-11", kind="irregularity", severity="warning", status="open",
        title="Yahoo MLB scoring is sourced from a single 2019 document",
        detail=(
            "`mlb:yahoo` rests on one document published in 2019. RotoGrinders does offer a Yahoo "
            "projection view, but its scoring values are behind the subscription and could not be "
            "retrieved."),
        impact=(
            "Yahoo's scoring may have changed in the intervening seasons. Every Yahoo number "
            "RGENGY publishes is older than the audit by up to seven years."),
        action=(
            "The table's meta records the single-source status and the document's age, and the "
            "site shows Yahoo last. Yahoo is not used for any validated comparison."),
        sources=[],
        refs=["rgengy/data/scoring/mlb_yahoo.json", "scripts/build_scoring_tables.py"]),

    # ------------------------------------------------------------------ IR-12
    Finding(
        id="IR-12", kind="irregularity", severity="warning", status="assumption",
        title="RotoGrinders' floor/ceiling ratios are calibrated on six rows",
        detail=(
            "The free tier of RotoGrinders' MLB projection grid exposes six rows. From those, "
            "FLOOR/FPTS averaged 0.3030 and CEIL/FPTS averaged 2.2229, giving "
            "`RG_OBSERVED_FLOOR_RATIO` and `RG_OBSERVED_CEIL_RATIO`."),
        impact=(
            "n=6 is far too small to treat as a distribution. The ratios also come from one sport, "
            "one site and one slate, and only hitters and pitchers in whatever proportion those "
            "six rows happened to contain."),
        action=(
            "The sample size is stored next to the constants (`RG_OBSERVED_SAMPLE_SIZE = 6`) and "
            "printed wherever the rg_band mode is used. `rg_band` is opt-in; the default band "
            "comes from RGENGY's own distribution model, not from these ratios."),
        sources=[RG_MLB_GRID],
        refs=["rgengy/engines.py", "scripts/analyze_rg_public_grid.py"]),

    # ------------------------------------------------------------------ IR-13
    Finding(
        id="IR-13", kind="irregularity", severity="warning", status="assumption",
        title="The ownership model's beta is an uncalibrated default",
        detail=(
            "RotoGrinders' pOWN is gradient-boosted (XGBoost) over historical DraftKings ownership "
            "plus several hundred explanatory variables, trained on mid-stakes multi-entry "
            "tournaments. Historical per-contest ownership is not available from any free official "
            "feed, so that model cannot be reproduced. RGENGY substitutes a softmax choice model "
            "over player value with one parameter, beta, defaulted to 0.35."),
        impact=(
            "pOWN is a transparent modelling choice, not a measurement. Its absolute level is "
            "arbitrary; only its ordering is meaningful."),
        action=(
            "`default_model()` returns `calibrated=False`, the ownership stage reports "
            "`degraded` with this id in the reason, and `calibrate_beta()` fits beta by "
            "deterministic grid search the moment real ownership data is supplied."),
        sources=[RG_OWNERSHIP_FAQ],
        refs=["rgengy/ownership.py", "rgengy/pipeline.py"]),

    # ------------------------------------------------------------------ IR-14
    Finding(
        id="IR-14", kind="irregularity", severity="info", status="resolved",
        title="RESOLVED: DraftKings NHL was double-counting goals via shots-on-goal",
        detail=(
            "A goal is also a shot on goal. Pass 1 scored a goal under both `g` and `sog`, which "
            "counted the same event twice."),
        impact="Resolved. Goaler and skater FPTS were overstated before the fix.",
        action=(
            "The overlap is now declared in `scoring.REPRESENTATION_SETS` so "
            "`quality.check_representation_double_count` fails the run loudly if any shipped table "
            "reintroduces it. The redundant key is pinned to 0.0 and marked "
            "`intentionally_zero` so the coverage check reports it as deliberate, not as a gap."),
        sources=["https://dknetwork.draftkings.com/2025-09-30/nhl-daily-fantasy-101"],
        refs=["rgengy/scoring.py", "rgengy/quality.py", "scripts/build_scoring_tables.py"]),

    # ------------------------------------------------------------------ IR-15
    Finding(
        id="IR-15", kind="irregularity", severity="info", status="resolved",
        title="RESOLVED: representation overlaps let one event satisfy two scoring keys",
        detail=(
            "Several stat families are nested - a hit is also a single/double/triple/homer, a "
            "shot on goal is also a goal, a strikeout is also an out. Scoring both keys counts "
            "the production twice."),
        impact=(
            "Silent FPTS inflation, which is worse than a visible error because the total still "
            "looks plausible."),
        action=(
            "`scoring.REPRESENTATION_SETS` declares every overlap; "
            "`scoring.representation_audit()` and `check_representation_double_count()` run on "
            "every configuration at every run and raise a critical finding if any table scores "
            "two members of a set simultaneously. tests/test_quality.py asserts all 11 shipped "
            "tables are clean."),
        sources=[],
        refs=["rgengy/scoring.py", "rgengy/quality.py"]),

    # ------------------------------------------------------------------ IR-16
    Finding(
        id="IR-16", kind="irregularity", severity="warning", status="open",
        title="FanDuel NFL and DraftKings NBA flex eligibility is disputed between sources",
        detail=(
            "fanscout.pro and RotoGrinders disagree on the FanDuel NBA roster shape, and two 2026 "
            "sources disagree on which positions the FanDuel NFL FLEX accepts. `nfl:fanduel` is "
            "therefore marked `disputed`."),
        impact=(
            "A roster template that is wrong produces lineups the operator rejects outright - a "
            "hard failure, not a scoring error."),
        action=(
            "Both templates carry `verification_status: disputed` with the conflicting sources "
            "listed, and `models.default_roster()` returns that status in its output so no caller "
            "can miss it. tests/test_models.py pins the disputed flag so it cannot be quietly "
            "upgraded to 'consistent'."),
        sources=["https://fanscout.pro/nba-fanduel-optimizer", RG_FD_NBA_STRATEGY],
        refs=["rgengy/models.py", "rgengy/data/scoring/nfl_fanduel.json"]),

    # ------------------------------------------------------------------ IR-17
    Finding(
        id="IR-17", kind="irregularity", severity="critical", status="resolved",
        title="RESOLVED: roster templates that produced illegal lineups",
        detail=(
            "Pass 1 listed separate C and 1B slots for DraftKings MLB, requiring 11 players where "
            "the operator's classic roster combines them into one C/1B slot for 10. Similar "
            "off-by-one errors affected the NHL and NBA templates (a shape with 2 UTILs is not a "
            "legal DraftKings NHL roster)."),
        impact=(
            "Every lineup produced was illegal and would have been rejected at submission. This is "
            "the highest-severity class of defect in the project because it is invisible in the "
            "projection output."),
        action=(
            "Templates were corrected against the operators' published rosters, and "
            "`models.default_roster()` now self-checks that the slot counts sum to the documented "
            "player count and raises if they do not. tests/test_models.py and "
            "tests/test_optimizer.py assert the exact slot shape per sport and site, including the "
            "combined C/1B slot and the absence of a DraftKings NFL kicker."),
        sources=["https://www.dailyfantasysports101.com/draftkings-vs-fanduel-fantasy-baseball-scoring-differences/",
                 "https://www.sportsbettingdime.com/news/nfl/nfl-dfs-week-2-lineup"],
        refs=["rgengy/models.py", "tests/test_models.py"]),

    # ------------------------------------------------------------------ IR-18
    Finding(
        id="IR-18", kind="irregularity", severity="warning", status="resolved",
        title="RESOLVED: NFL 100/300-yard bonuses were attributed to the wrong operator",
        detail=(
            "Pass 1 applied the 100-yard rushing, 100-yard receiving and 300-yard passing bonuses "
            "to both operators. DraftKings scores them (3.0); FanDuel does not. A 2026 source "
            "states the reverse of what pass 1 assumed."),
        impact=(
            "FanDuel NFL FPTS was overstated by up to 3.0 per qualifying player, which is enough "
            "to reorder a slate."),
        action=(
            "The bonuses are 3.0 on `nfl:draftkings` and 0.0 on `nfl:fanduel`, with the conflict "
            "and its resolution recorded in the table notes. This difference is the documented "
            "basis of the DraftKings/FanDuel NFL scoring divergence."),
        sources=["https://fantasyfootballers.org/featured/draftkings-vs-fanduel/",
                 "https://fantasyteamadvisors.com/nfl-dfs-strategy/",
                 "https://occupyfantasy.com/daily-fantasy-football-strategy-draftkings-fanduel-dfs/"],
        refs=["rgengy/data/scoring/nfl_draftkings.json", "rgengy/data/scoring/nfl_fanduel.json",
              "scripts/build_scoring_tables.py"]),

    # ------------------------------------------------------------------ IR-19
    Finding(
        id="IR-19", kind="irregularity", severity="warning", status="resolved",
        title="RESOLVED: players with no usable sample were silently dropped",
        detail=(
            "Pass 1 removed any player for whom no projection could be produced. On RotoGrinders' "
            "own public grid the same situation is visible as a row published with no projection."),
        impact=(
            "Dropping a player makes any roster slot that only they could fill impossible to "
            "satisfy, which silently converts one missing season sample into 'no lineup exists for "
            "this sport at all'. The failure is reported at the optimizer, far from its cause."),
        action=(
            "Players are retained at 0.0 with a run warning naming them, and an all-zero "
            "projection is flagged separately from an empty one because the fixes differ. "
            "`quality.check_zero_projection` reports every paid player with no projection in the "
            "run report."),
        sources=[RG_MLB_GRID],
        refs=["rgengy/pipeline.py", "rgengy/quality.py", "scripts/analyze_rg_public_grid.py"]),

    # ------------------------------------------------------------------ IR-20
    Finding(
        id="IR-20", kind="irregularity", severity="info", status="unused-id",
        title="Identifier IR-20 is deliberately unused",
        detail=(
            "No finding in this register, in the scoring tables, or anywhere in the source tree "
            "cites IR-20. The id was consumed during pass 2 by a simulator payout issue that was "
            "fixed outright and is now covered by tests/test_simulator.py rather than by an open "
            "finding."),
        impact="A gap in the numbering, declared rather than silently renumbered.",
        action=(
            "Declared here. IR-21 to IR-23 were assigned after this gap opened and renumbering "
            "them would invalidate references already written into pipeline.py."),
        sources=[],
        refs=["rgengy/findings.py"]),

    # ------------------------------------------------------------------ IR-21
    Finding(
        id="IR-21", kind="irregularity", severity="warning", status="open",
        title="RotoGrinders publishes OBFPTS, SMASH, LEV, TOPVAL and DIFFERENCE without definitions",
        detail=(
            f"The free tier of the MLB projection grid (retrieved {AUDIT_DATE}) exposes these "
            "columns with values but no formula. Observed: OBFPTS is published at full float "
            "precision at roughly 1.08-1.13x FPTS; LEV was 9 for all six free rows, i.e. a "
            "slate-level constant rather than a per-player quantity; OPTO is expressed in FPTS "
            "units, not as a percentage."),
        impact=(
            "These are the columns most likely to be mistaken for reproduced features. Guessing a "
            "formula would produce numbers that look like RotoGrinders' and are not."),
        action=(
            "RGENGY leaves OBFPTS, TOPVAL, DIFFERENCE and OPTO null and computes its OWN clearly "
            "labelled `lev` (value share minus ownership share) and `smash` (P(FPTS > 1.5x "
            "projection)) into `extra`. `attach_ownership` writes an `analytics_provenance` block "
            "onto every player stating, per column, whether it is reproduced, RGENGY's own, or not "
            "computed - and tests/test_ownership.py asserts that block exists and says the right "
            "thing for each column."),
        sources=[RG_MLB_GRID],
        refs=["rgengy/pipeline.py", "rgengy/ownership.py", "scripts/analyze_rg_public_grid.py"]),

    # ------------------------------------------------------------------ IR-22
    Finding(
        id="IR-22", kind="irregularity", severity="warning", status="open",
        title="RotoGrinders' grid schema was only transcribed for three sports",
        detail=(
            f"Column headers were transcribed from the live site on {AUDIT_DATE} for MLB (49 "
            "columns), NFL (38) and WNBA (33). The NBA and NHL grid headers were NOT transcribed, "
            "so `models.RG_GRID_COLUMNS` deliberately omits them. TEAMOWN is a team-level roll-up "
            "whose aggregation RotoGrinders does not publish, and the WNBA TOTAL column sits "
            "beside SPREAD and O/U with no definition."),
        impact=(
            "Emitting an NBA or NHL grid under RotoGrinders' column headings would present "
            "RGENGY's own schema as a reproduction of theirs. Omitting a column silently would "
            "make the artefact impossible to diff against their grid."),
        action=(
            "`grid_rows()` sets `rg_column_schema_observed=False` and writes an explicit note for "
            "NBA/NHL. Every observed column is either mapped or listed in `unfilled_columns` with "
            "a written reason in `UNMAPPED_COLUMN_REASONS`, and every row carries the full column "
            "shape with nulls rather than omitting keys. tests/test_pipeline.py asserts the "
            "two-way invariant: no column without a mapping or a reason, and no reason without a "
            "column."),
        sources=[RG_MLB_GRID],
        refs=["rgengy/models.py", "rgengy/pipeline.py", "tests/test_pipeline.py"]),

    # ------------------------------------------------------------------ IR-23
    Finding(
        id="IR-23", kind="irregularity", severity="warning", status="open",
        title="Team win probability had two competing origins, and PRIZEPICKS equals FPTS only on six rows",
        detail=(
            "Two issues in the same class. (1) A win probability was being derived inside the "
            "projection engines as well as from the market line in the pipeline, so the same "
            "quantity could come from two places with different values. (2) On the six free MLB "
            "grid rows the PRIZEPICKS column equalled RotoGrinders' FPTS exactly, while UNDERDOG "
            "differed; that equivalence cannot be verified as a general rule from six rows."),
        impact=(
            "A pitcher's win projection and a goalie's win projection would silently disagree with "
            "the market line shown beside them. Claiming PRIZEPICKS == FPTS generally would be an "
            "unverified extrapolation presented as a finding."),
        action=(
            "All win probabilities now come from one function, `engines.team_win_probability()`, "
            "with a fixed preference order (market line, then expected-output differential, then "
            "0.0 with the source labelled 'unavailable'). It returns the source label alongside "
            "the probability and that label is written into the projection notes and the artefact. "
            "No engine may invent 0.5. PRIZEPICKS is left null with the six-row observation "
            "recorded rather than generalised."),
        sources=[RG_MLB_GRID],
        refs=["rgengy/engines.py", "rgengy/pipeline.py", "tests/test_engines.py"]),

    # ------------------------------------------------------------------- L-01
    Finding(
        id="L-01", kind="limitation", severity="info", status="unused-id",
        title="Identifier L-01 is deliberately unused",
        detail=(
            "No limitation in this register or in the source tree cites L-01. The id was consumed "
            "during the audit by the absence of any outbound network access in the build "
            "environment, which turned out to be an environment property rather than a limitation "
            "of the system, and is documented in the README instead."),
        impact="A gap in the numbering, declared rather than silently renumbered.",
        action="Declared here so the L-nn sequence can be read as complete.",
        sources=[],
        refs=["rgengy/findings.py"]),

    # ------------------------------------------------------------------- L-02
    Finding(
        id="L-02", kind="limitation", severity="critical", status="open",
        title="No outbound network access in the build environment",
        detail=(
            "Raw HTTPS fetches from this workspace fail with a TLS/SSL EOF error. The pages "
            "retrieved during the audit were read through a proxy that can reach "
            "rotogrinders.com; fanduel.com is additionally geo-blocked, and both operators keep "
            "their authoritative scoring pages inside their logged-in apps."),
        impact=(
            "No scoring value in this repository is marked `confirmed_by_operator`, because no "
            "operator scoring page could be retrieved. Every value rests on secondary sources. The "
            "live feeds cannot be exercised here, so the pipeline is tested against synthetic and "
            "cached inputs and the slate stage honestly reports `unavailable` rather than "
            "substituting invented games."),
        action=(
            "`rgengy probe` and `rgengy verify` exist to be run from a networked machine; they "
            "stamp each endpoint with its live status and write verification.json. The GitHub "
            "Pages workflow runs them on every build so the published site reflects the live "
            "state rather than the audit state. `data/` is gitignored and regenerated."),
        sources=["https://help.fanduel.com/", "https://www.draftkings.com/"],
        refs=["rgengy/cli.py", "rgengy/sources.py", ".github/workflows/pages.yml"]),

    # ------------------------------------------------------------------- L-03
    Finding(
        id="L-03", kind="limitation", severity="warning", status="open",
        title="The WNBA roster templates are unconfirmed",
        detail=(
            "No source for the WNBA roster shape was retrieved during the audit. The templates "
            "were treated as the NBA shape reduced to six slots."),
        impact=(
            "A WNBA lineup built from these templates may be rejected by the operator. Both "
            "`wnba:draftkings` and `wnba:fanduel` have zero sources and are marked `not-audited`."),
        action=(
            "`models.default_roster()` returns the `not-audited` status and a note beginning "
            "UNCONFIRMED for both, and tests/test_models.py asserts that any template with no "
            "sources must be marked `not-audited` and must say UNCONFIRMED - so the templates "
            "cannot be quietly upgraded without a source being added."),
        sources=[],
        refs=["rgengy/models.py", "tests/test_models.py"]),

    # ------------------------------------------------------------------- L-04
    Finding(
        id="L-04", kind="limitation", severity="warning", status="open",
        title="NFL team-defence and kicker scoring tiers were never retrieved",
        detail=(
            "DraftKings team-defence scoring was not retrieved from any source during the audit. "
            "The shipped values follow the long-standing convention (points allowed and yardage "
            "tiers, sacks, turnovers, defensive touchdowns) but are marked `not-audited`."),
        impact=(
            "DST and KPTS projections carry an unknown error. The NFL grid's KPTS column is left "
            "null rather than filled from unaudited tiers."),
        action=(
            "The seven `dst_*` keys are `not-audited` in both NFL tables, so "
            "`quality.check_scoring_coverage` escalates them to a warning whenever a DST is "
            "actually projected. Under `--strict` the pipeline excludes unaudited coefficients "
            "from published totals."),
        sources=["https://www.draftkings.com/"],
        refs=["rgengy/data/scoring/nfl_draftkings.json", "rgengy/pipeline.py", "rgengy/quality.py"]),

    # ------------------------------------------------------------------- L-05
    Finding(
        id="L-05", kind="limitation", severity="warning", status="open",
        title="RotoGrinders' paywalled features could not be inspected at all",
        detail=(
            "The subscription tier - the full projection grid beyond six rows, the optimizer, "
            "ownership projections, THE BAT X projections, contest simulation and the partner-site "
            "columns (UNDERDOG, PRIZEPICKS) - is not retrievable without an account."),
        impact=(
            "Every claim about those features rests on the free tier, on RotoGrinders' own "
            "published articles, or on nothing at all. Where nothing was available, RGENGY "
            "implements its own documented equivalent and says so."),
        action=(
            "The rebuild is explicit about which is which. `analytics_provenance` labels each "
            "column reproduced / RGENGY-own / not computed; the site carries the same three-way "
            "split; and no paywalled quantity is emitted under RotoGrinders' column heading "
            "without that label."),
        sources=[RG_MLB_GRID, RG_OWNERSHIP_FAQ, RG_BAT_VEGAS],
        refs=["rgengy/pipeline.py", "scripts/analyze_rg_public_grid.py"]),

    # ------------------------------------------------------------------- L-06
    Finding(
        id="L-06", kind="limitation", severity="warning", status="open",
        title="Player outcomes are simulated from a normal approximation, not a per-stat model",
        detail=(
            "`simulator.sample_player_fpts` draws each player's score from a normal distribution "
            "built on the projected mean and a standard deviation derived from the floor/ceiling "
            "band. Real fantasy output is a sum of discrete, correlated events (a hit is also a "
            "run and an RBI; a pitcher's innings correlate with his strikeouts)."),
        impact=(
            "Tail behaviour is understated: a normal draw cannot produce a 4-home-run game, so "
            "simulated top-1 rates are conservative and the cash/top-10/top-1 ordering is "
            "preserved but the magnitudes are not trustworthy for large-field GPPs. The band is "
            "also over-dispersed relative to a true event model."),
        action=(
            "Documented in the simulator module docstring and surfaced in every simulation result. "
            "Replacing it needs a per-stat correlated event model, which needs the historical "
            "play-by-play data listed as future work in docs/10."),
        sources=[],
        refs=["rgengy/simulator.py"]),
]


BY_ID: Dict[str, Finding] = {f.id: f for f in FINDINGS}

KINDS = ("irregularity", "limitation")
STATUSES = ("open", "resolved", "assumption", "unused-id")
SEVERITIES = ("info", "warning", "critical")


def irregularities() -> List[Finding]:
    return [f for f in FINDINGS if f.kind == "irregularity"]


def limitations() -> List[Finding]:
    return [f for f in FINDINGS if f.kind == "limitation"]


def open_findings() -> List[Finding]:
    """Findings that still constrain what RGENGY can claim."""
    return [f for f in FINDINGS if f.status in ("open", "assumption")]


def ids() -> List[str]:
    return [f.id for f in FINDINGS]


def get(fid: str) -> Finding:
    if fid not in BY_ID:
        raise KeyError(f"unknown finding {fid!r}; registered: {ids()}")
    return BY_ID[fid]


def validate() -> List[str]:
    """Self-check the register.  Returns a list of problems, empty when clean."""
    problems: List[str] = []
    seen: set = set()
    for f in FINDINGS:
        if f.id in seen:
            problems.append(f"{f.id} is registered twice")
        seen.add(f.id)
        if f.kind not in KINDS:
            problems.append(f"{f.id}: unknown kind {f.kind!r}")
        if f.status not in STATUSES:
            problems.append(f"{f.id}: unknown status {f.status!r}")
        if f.severity not in SEVERITIES:
            problems.append(f"{f.id}: unknown severity {f.severity!r}")
        if not f.title or not f.title[0].isupper():
            problems.append(f"{f.id}: title must be a capitalised sentence fragment")
        for attr in ("detail", "impact", "action"):
            if len(getattr(f, attr)) < 40:
                problems.append(f"{f.id}: {attr} is too thin to act on")
        if not f.refs:
            problems.append(f"{f.id}: no refs - a finding nothing cites cannot be traced")
        if f.status != "unused-id" and not f.action:
            problems.append(f"{f.id}: no action")
    for prefix, kind in (("IR-", "irregularity"), ("L-", "limitation")):
        for f in FINDINGS:
            if f.id.startswith(prefix) and f.kind != kind:
                problems.append(f"{f.id}: id prefix says {kind} but kind is {f.kind!r}")
    return problems


def to_dict() -> Dict[str, Any]:
    return {
        "audit_date": AUDIT_DATE,
        "counts": {
            "total": len(FINDINGS),
            "irregularities": len(irregularities()),
            "limitations": len(limitations()),
            "open": len([f for f in FINDINGS if f.status == "open"]),
            "assumptions": len([f for f in FINDINGS if f.status == "assumption"]),
            "resolved": len([f for f in FINDINGS if f.status == "resolved"]),
            "unused_ids": len([f for f in FINDINGS if f.status == "unused-id"]),
            "critical": len([f for f in FINDINGS if f.severity == "critical"]),
        },
        "findings": [f.to_dict() for f in FINDINGS],
    }
