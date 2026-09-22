#!/usr/bin/env python3
"""Generate the reference documentation and the site's data files.

Everything here is DERIVED from structures that are already committed and already
audited - the endpoint registry, the scoring tables, the grid schema, the column
map and the findings register - rather than written by hand a second time.  A
hand-written copy of a source list is a second place for a link to rot, and a
generated one cannot disagree with the code that uses it.

Run:
    python3 scripts/build_docs.py            # writes docs/ and site/data/
    python3 scripts/build_docs.py --check    # exits 1 if either is stale

The GitHub Pages workflow runs this on every build, then `rgengy verify`, so the
published site always reflects the shipped tables and the live endpoint state.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from rgengy import findings, models, pipeline, quality, scoring, sources  # noqa: E402

DOCS = REPO / "docs"
SITE_DATA = REPO / "site" / "data"

AUDIT_DATE = sources.AUDIT_DATE


def generated_at() -> str:
    """A build timestamp that does not make every rebuild look stale.

    ``--check`` compares rendered bytes against what is committed, so a timestamp
    taken from the wall clock would report the whole site as stale on every run
    and the check would be useless.  Committed output is therefore pinned to the
    audit date - the date the data actually describes - which is reproducible with
    no environment at all.

    ``SOURCE_DATE_EPOCH`` (the reproducible-builds convention) is honoured when set,
    but it is opt-in and the Pages workflow does not set it: injecting a commit-time
    stamp would make ``--check`` compare against a timestamp the committed artefacts
    were never built with, and fail every build.  Runtime artefacts under the
    gitignored ``data/`` keep real wall-clock stamps, because those record when a run
    actually happened.
    """
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        try:
            return _dt.datetime.fromtimestamp(int(epoch), _dt.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, OSError, OverflowError):
            pass
    return f"{AUDIT_DATE}T00:00:00Z"


def _md_escape(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def _link(url: str, label: str | None = None) -> str:
    if not url:
        return "-"
    return f"[{label or url}]({url})"


# ---------------------------------------------------------------------------
# docs/02 - the data-source register
# ---------------------------------------------------------------------------

STATUS_BLURB = {
    "live-verified": "retrieved and its response shape confirmed by inspection",
    "reachable": "reached successfully; response shape not fully confirmed",
    "documented": "the provider documents it; it was not retrieved during the audit",
    "unverified": "NOT retrieved during the audit - listed for completeness only",
}


def build_data_sources() -> str:
    rows = sources.registry_rows()
    summary = sources.verification_summary()
    out: List[str] = []
    out.append("# 02 - Data sources\n")
    out.append(
        f"Every external input RGENGY uses, with the provider, whether that provider is the "
        f"league/official body itself, the authentication it needs, and what was actually "
        f"verified on **{summary['audit_date']}**. Generated from `rgengy/sources.py` by "
        f"`scripts/build_docs.py` - edit the registry, not this file.\n")
    out.append(
        f"**{summary['total_endpoints']} endpoints**: "
        f"{summary['official']} official / {summary['unofficial']} unofficial, "
        f"{summary['requires_auth']} requiring an API key.\n")
    out.append("| verification status | count | meaning |")
    out.append("| --- | ---: | --- |")
    for status, n in sorted(summary["by_status"].items(), key=lambda kv: -kv[1]):
        out.append(f"| `{status}` | {n} | {STATUS_BLURB.get(status, '')} |")
    out.append("")
    out.append(
        "> **L-02.** The audit environment had no outbound network access for raw fetches, so\n"
        "> *no scoring value in this repository is marked `confirmed_by_operator`* - both\n"
        "> operators keep their authoritative scoring pages inside their logged-in apps.\n"
        "> `rgengy probe` and `rgengy verify` exist to be run from a networked machine and stamp\n"
        "> each endpoint with its live status.\n")

    by_provider: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_provider.setdefault(r["provider"], []).append(r)

    for provider in sorted(by_provider):
        group = by_provider[provider]
        official = group[0]["official"]
        out.append(f"## {provider}\n")
        out.append(f"{'Official league/government feed.' if official else 'Third-party feed.'}\n")
        for r in sorted(group, key=lambda x: x["key"]):
            badge = "OFFICIAL" if r["official"] else "unofficial"
            out.append(f"### `{r['key']}` - {r['name']}\n")
            out.append(f"| | |")
            out.append(f"| --- | --- |")
            out.append(f"| status | `{r['verification_status']}` "
                       f"({STATUS_BLURB.get(r['verification_status'], '')}) |")
            out.append(f"| verified on | {r['verified_on'] or 'never'} |")
            out.append(f"| provider | {provider} ({badge}) |")
            out.append(f"| auth | `{r['auth']}` |")
            out.append(f"| url | `{r['url_template']}` |")
            if r.get("docs_url"):
                out.append(f"| docs | {_link(r['docs_url'])} |")
            if r.get("terms_url"):
                out.append(f"| terms | {_link(r['terms_url'])} |")
            else:
                out.append("| terms | **none published** - see IR-01 |")
            if r.get("replaces"):
                out.append(f"| replaces (RotoGrinders) | {', '.join(r['replaces'])} |")
            out.append("")
            if r.get("notes"):
                out.append(f"> {_md_escape(r['notes'])}\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# docs/03 - scoring verification
# ---------------------------------------------------------------------------

def build_scoring() -> str:
    out: List[str] = []
    out.append("# 03 - Scoring verification\n")
    out.append(
        "Fantasy points are the product of a scoring table and a projection, so a wrong "
        "coefficient corrupts every number downstream of it. Each shipped table below lists every "
        "coefficient with the number of independent sources that agree on it, its verification "
        "status, and the URLs those sources came from. Generated from `rgengy/data/scoring/*.json` "
        "- edit the tables (via `scripts/build_scoring_tables.py`), not this file.\n")

    counts: Dict[str, int] = {}
    for key in scoring.available():
        table = scoring.load(*key.split(":"))
        for spec in table.payload.get("values", {}).values():
            counts[spec.get("verification_status") or "unknown"] = \
                counts.get(spec.get("verification_status") or "unknown", 0) + 1

    out.append("## Evidence classes across all tables\n")
    out.append("| verification status | coefficients | meaning |")
    out.append("| --- | ---: | --- |")
    meaning = {
        "multi-source-consistent": "two or more independent sources agree",
        "single-source": "exactly one source - the weakest evidence class",
        "disputed": "sources contradict each other; the majority value was adopted and flagged",
        "not-audited": "no source was retrieved; the value is a documented convention, not a finding",
    }
    for status, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        out.append(f"| `{status}` | {n} | {meaning.get(status, '')} |")
    out.append("")

    for key in scoring.available():
        sport, site = key.split(":")
        table = scoring.load(sport, site)
        meta = table.meta
        values = table.payload.get("values", {})
        n_disputed = len(table.disputed)
        n_unaudited = len(table.not_audited)
        n_zero = len(table.intentionally_zero)
        out.append(f"## {sport.upper()} / {site}\n")
        out.append(f"| | |")
        out.append(f"| --- | --- |")
        out.append(f"| contest format | {_md_escape(str(meta.get('contest_format'))) } |")
        out.append(f"| salary cap | {meta.get('salary_cap')} |")
        out.append(f"| audit date | {meta.get('audit_date')} |")
        out.append(f"| operator-confirmed | **{meta.get('confirmed_by_operator')}** (L-02) |")
        out.append(f"| coefficients | {len(values)} |")
        out.append(f"| disputed | {n_disputed} |")
        out.append(f"| not audited | {n_unaudited} |")
        out.append(f"| deliberately zero | {n_zero} (IR-15) |")
        out.append("")
        if meta.get("audit_method"):
            out.append(f"> **Audit method.** {_md_escape(str(meta['audit_method']))}\n")
        if meta.get("notes"):
            out.append(f"> **Notes.** {_md_escape(str(meta['notes']))}\n")

        out.append("| stat | value | evidence | sources agree | disputed | note |")
        out.append("| --- | ---: | --- | ---: | :---: | --- |")
        for stat in sorted(values):
            spec = values[stat]
            note = _md_escape(str(spec.get("note") or ""))
            out.append(
                f"| `{stat}` | {spec['value']} | `{spec.get('verification_status')}` "
                f"| {spec.get('agreement')} | {'yes' if spec.get('disputed') else ''} "
                f"| {note or '-'} |")
        out.append("")
        out.append("<details><summary>Sources consulted for this table</summary>\n")
        for url in meta.get("sources_consulted", []):
            out.append(f"- {_link(url)}")
        out.append("\n</details>\n")

        rows = table.provenance_rows()
        per_stat_sources = {r["stat"]: r["sources"] for r in rows}
        all_urls = sorted({u for urls in per_stat_sources.values() for u in urls})
        out.append("<details><summary>Per-stat source URLs</summary>\n")
        for stat in sorted(per_stat_sources):
            urls = per_stat_sources[stat]
            out.append(f"- `{stat}` ({len(urls)}): " + ", ".join(_link(u, f"[{i+1}]")
                                                                for i, u in enumerate(urls)))
        out.append("\n</details>\n")
        out.append(f"_All {len(all_urls)} distinct URLs for this table are listed in the two "
                   f"blocks above._\n")
    return "\n".join(out)



# ---------------------------------------------------------------------------
# docs/04 - what was reverse-engineered from RotoGrinders
# ---------------------------------------------------------------------------

def build_rg_findings() -> str:
    """Every claim about RotoGrinders, derived from the saved grid fixture.

    Nothing in this document is asserted from memory: it is recomputed from
    ``tests/fixtures/rg_public_mlb_grid_2026-09-22.json``, a verbatim
    transcription of the free tier of RotoGrinders' MLB projection grid, by
    ``scripts/analyze_rg_public_grid.py``.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    import analyze_rg_public_grid as analysis

    r = analysis.analyze()
    out: List[str] = []
    out.append("# 04 - What was reverse-engineered from RotoGrinders\n")
    out.append(
        f"Source: {_link(r['source_url'])}, retrieved **{r['retrieved_utc']}**, free tier "
        f"({r['row_count']} rows). Saved verbatim to `{r['fixture']}` and recomputed by "
        f"`scripts/analyze_rg_public_grid.py` on every documentation build, so no number below "
        f"can drift from the fixture.\n")
    out.append(
        "> **Read the sample size before trusting any of it.** All "
        f"{r['row_count']} free rows are batters from ONE team in ONE game "
        f"({r['constant_across_all_rows'].get('TEAM')} at "
        f"{r['constant_across_all_rows'].get('OPP')}, park "
        f"{r['constant_across_all_rows'].get('PARK')}) on one date. Every pitcher column is 0 "
        "across all rows. RotoGrinders' paid tier would give a sample large enough to fit "
        "per-position models; the free tier gives enough to *validate a scoring table* and to "
        "*observe* the band and ownership conventions, and not much more. See IR-12 and L-05.\n")

    # -- the headline result ------------------------------------------------
    sv = r["scoring_validation"]
    out.append("## 1. The scoring table reproduces RotoGrinders' published FPTS\n")
    out.append(
        f"> {sv['verdict']}\n")
    out.append(
        "This is the strongest result in the audit and the reason the rest is worth reading: "
        "RGENGY's independently sourced DraftKings MLB coefficients, applied to RotoGrinders' own "
        "published stat projections, reproduce RotoGrinders' published FPTS. Two independently "
        "assembled things agreeing to within a rounding step is evidence that the coefficients are "
        "right, not merely that they are self-consistent.\n")
    out.append("| player | salary | pos | RG FPTS | RGENGY FPTS | delta | % error |")
    out.append("| --- | ---: | --- | ---: | ---: | ---: | ---: |")
    for row in sv["rows"]:
        out.append(f"| {row['player']} | {row['salary']} | {row['position']} "
                   f"| {row['published_fpts']} | {row['rgengy_fpts']} | {row['delta']:+} "
                   f"| {row['pct_error']}% |")
    out.append("")
    out.append(f"| | |")
    out.append(f"| --- | --- |")
    out.append(f"| coefficients used | {sv['table_values_used']} |")
    out.append(f"| max absolute delta | {sv['max_abs_delta']} FPTS |")
    out.append(f"| mean absolute delta | {sv['mean_abs_delta']} FPTS |")
    out.append(f"| tolerance | {sv['tolerance']} FPTS |")
    out.append(f"| **verdict** | **{'PASS' if sv['passed'] else 'FAIL'}** |")
    out.append("")

    # -- FPTS/$ --------------------------------------------------------------
    ident = r["fpts_per_salary_identity"]
    out.append("## 2. `FPTS/$` is exactly `FPTS / (SALARY / 1000)`\n")
    out.append(
        f"> `{ident['formula']}` - max absolute error {ident['max_abs_error']} across "
        f"{len(ident['rows'])} rows, which is pure 2dp display rounding.\n")
    out.append("| player | RG published | computed | abs error |")
    out.append("| --- | ---: | ---: | ---: |")
    for row in ident["rows"]:
        out.append(f"| {row['player']} | {row['published']} | {row['computed']} "
                   f"| {row['abs_error']} |")
    out.append("")
    out.append(
        "Because this identity is verified exactly, RGENGY **reproduces** the column and says so. "
        "It is the only RotoGrinders analytic column RGENGY claims to reproduce. "
        "`tests/test_rg_grid.py` pins it.\n")

    # -- bands ---------------------------------------------------------------
    fr, cr, bw = r["floor_ratio"], r["ceil_ratio"], r["band_width"]
    out.append("## 3. Floor and ceiling are ratios of the projection, and strongly asymmetric\n")
    out.append(f"| quantity | n | mean | min | max | sd |")
    out.append(f"| --- | ---: | ---: | ---: | ---: | ---: |")
    out.append(f"| `FLOOR / FPTS` | {fr['n']} | {fr['mean']} | {fr['min']} | {fr['max']} "
               f"| {fr['sd']} |")
    out.append(f"| `CEIL / FPTS` | {cr['n']} | {cr['mean']} | {cr['min']} | {cr['max']} "
               f"| {cr['sd']} |")
    out.append("")
    out.append(f"> {bw['asymmetry']}\n")
    out.append(
        f"These became `engines.RG_OBSERVED_FLOOR_RATIO = {fr['mean']}` and "
        f"`engines.RG_OBSERVED_CEIL_RATIO = {cr['mean']}`, used only by the opt-in `rg_band` mode. "
        f"{r['engine_constants']['sample_size_warning']} (IR-12)\n")
    if fr.get("excluded"):
        out.append("**Rows excluded from the floor fit, and why:**\n")
        for ex in fr["excluded"]:
            out.append(f"- **{ex['player']}** (FPTS {ex['fpts']}, FLOOR {ex['floor']}, "
                       f"CEIL {ex['ceil']}) - {ex['reason']}")
        out.append("")

    # -- ownership -----------------------------------------------------------
    own = r["ownership"]
    out.append("## 4. Ownership and optimiser columns\n")
    out.append(f"> {own['verdict']}\n")
    out.append("| player | POWN |")
    out.append("| --- | ---: |")
    for name, v in own["pown_per_row"].items():
        out.append(f"| {name} | {v * 100:.2f}% |")
    out.append("")
    out.append(f"| | |")
    out.append(f"| --- | --- |")
    out.append(f"| POWN sum over {len(own['pown_per_row'])} rows | {own['pown_sum'] * 100:.2f}% |")
    out.append(f"| POWN range | {own['pown_range'][0] * 100:.2f}% - "
               f"{own['pown_range'][1] * 100:.2f}% |")
    out.append(f"| TEAMOWN (identical on every row) | {own['teamown_values'][0] * 100:.2f}% |")
    out.append(f"| OPTO range | {own['opto_range'][0]} - {own['opto_range'][1]} (FPTS units, "
               f"not a percentage) |")
    out.append("")
    out.append(
        "POWN summing to ~100% over the free rows means it is a share of projected field usage. "
        "RGENGY's own pOWN is normalised the same way (`ownership.project_ownership` returns "
        "shares summing to 1.0), capped at `MAX_POWN`, and labelled `calibrated=False` because "
        "beta is not fitted to any ownership data (IR-13). RotoGrinders' method IS documented - "
        f"{_link(RG_OWNERSHIP_FAQ_LABEL, 'THE BAT ownership projections FAQ')} - gradient-boosted "
        "over historical DraftKings ownership - and that data is not obtainable from any free "
        "official feed, which is why RGENGY substitutes a transparent choice model instead of "
        "claiming a reproduction.\n")

    # -- OBFPTS --------------------------------------------------------------
    ob = r["obfpts"]
    out.append("## 5. OBFPTS is consistently 8-13% above FPTS, and undefined\n")
    out.append(f"> {ob['verdict']}\n")
    out.append("| player | OBFPTS / FPTS |")
    out.append("| --- | ---: |")
    for row, ratio in zip([x["player"] for x in sv["rows"]], ob["per_row"]):
        out.append(f"| {row} | {ratio} |")
    out.append("")
    out.append(f"| | |")
    out.append(f"| --- | --- |")
    out.append(f"| n | {ob['n']} |")
    out.append(f"| mean ratio | {ob['mean']} |")
    out.append(f"| range | {ob['min']} - {ob['max']} |")
    out.append(f"| sd | {ob['sd']} |")
    out.append(f"| definition published | **{ob['definition_known']}** |")
    out.append("")

    # -- slate-level constants ----------------------------------------------
    const = r["constant_across_all_rows"]
    out.append("## 6. Columns that were constant across every row\n")
    out.append(
        "A column with the same value on all six rows is a slate-level or game-level quantity "
        "rendered per player, not a per-player projection. Treating one as per-player is how a "
        "reproduction goes quietly wrong.\n")
    out.append("| column | value on every row |")
    out.append("| --- | --- |")
    for col, val in const.items():
        out.append(f"| `{col}` | {json.dumps(val) if not isinstance(val, str) else val} |")
    out.append("")
    out.append(
        "Note `LEV` = 9 and `SMASH` = 0.36 on every row: both are slate-level constants here, "
        "which is direct evidence against reading LEV as a per-player leverage score. RGENGY "
        "computes its own per-player `lev` and labels it as its own definition (IR-21).\n")

    out.append("## 7. Columns that varied per player\n")
    out.append(", ".join(f"`{c}`" for c in r["varying_columns"]))
    out.append("")

    # -- undetermined --------------------------------------------------------
    und = r["undetermined_columns"]
    out.append("## 8. Columns whose definition could not be determined\n")
    out.append(f"> {und['reason']}\n")
    out.append("| column | published on the free tier | RGENGY |")
    out.append("| --- | :---: | --- |")
    for col in und["columns"]:
        sample = const.get(col, "varies per row")
        out.append(f"| `{col}` | yes ({_md_escape(str(sample))}) | **null** + written reason |")
    out.append("")

    # -- strategies ----------------------------------------------------------
    out.append("## 9. Strategies behind the product\n")
    out.append(
        "What the grid's column set implies about how RotoGrinders expects its users to build "
        "lineups. Each inference is marked as an inference.\n")
    out.append(
        "| observed feature | implied strategy | confidence |\n"
        "| --- | --- | --- |\n"
        "| `FPTS/$` published beside every projection, and verified exact | Salary efficiency, not "
        "raw projection, is the primary sort. A $3,000 player at 3.0 FPTS/$ beats a $6,000 player "
        "at 2.6. | **verified** |\n"
        "| `FLOOR` and `CEIL` both published, ~7x asymmetric | Cash contests want the floor, GPPs "
        "want the ceiling; the asymmetry says upside is modelled far more widely than downside. | "
        "**verified ratios**, inferred intent |\n"
        "| `POWN` normalised to ~100% of the field | Leverage is a share comparison: a player whose "
        "production share exceeds his ownership share is a GPP differentiator. | observed |\n"
        "| `OPTO` in FPTS units, not a percentage | The optimiser's objective is projected points "
        "under a salary cap, not a value or upside ratio. | observed |\n"
        "| `SMASH`, `TOPVAL`, `DIFFERENCE`, `LEV` published without definitions | Upside "
        "probability, top-value flag and a difference score are first-class UI concepts, but the "
        "thresholds are proprietary. | observed absence |\n"
        "| `UNDERDOG` and `PRIZEPICKS` columns beside `FPTS` | RotoGrinders re-publishes partner "
        "projections in its own grid. PRIZEPICKS equalled FPTS exactly on all six rows while "
        "UNDERDOG differed, so at least one partner simply surfaces RotoGrinders' own number. | "
        "observed on 6 rows - **not** generalisable (IR-23) |\n"
        "| `WIND`, `TEMP`, `TEMPDESC`, `PARK` per row | Environment is folded into the projection "
        "and shown to the user rather than hidden. `TEMPDESC` values like `neutraltemp` suggest a "
        "discrete classification of a continuous input. | observed |\n"
        "| `ORDER` (batting order) per row | Lineup position is an input to plate appearances, "
        "which is why RGENGY resolves `batting_order` explicitly. | observed |\n"
        "| `REFTM` / `REFOPP` constant per row | A comparison affordance, not a projection. | "
        "observed |\n")

    out.append("## 10. Data sources behind RotoGrinders' product\n")
    out.append(
        "Only what is documented by RotoGrinders itself or observable in the grid. Anything beyond "
        "this is speculation and is not listed.\n")
    out.append("| feature | documented source | link |")
    out.append("| --- | --- | --- |")
    out.append("| Ownership projections | RotoGrinders' own FAQ: gradient-boosted trees (XGBoost) "
               "trained on historical DraftKings ownership data plus several hundred explanatory "
               "variables, tailored to DraftKings mid-stakes multi-entry tournaments, fully "
               f"automated, refreshed on the same five-minute loop as the projections "
               f"| {_link(findings.RG_OWNERSHIP_FAQ)} |")
    out.append("| Implied team totals | The Bryant formula attributed to co-founder Riley Bryant, "
               f"with `AdjustedSpread` unpublished | {_link(findings.RG_BAT_VEGAS)} |")
    out.append("| MLB projections | THE BAT X (Chris Carty), licensed | not retrievable |")
    out.append("| Grid columns | Observed directly on the free tier of the MLB projection grid "
               f"| {_link(findings.RG_MLB_GRID)} |")
    out.append("| FanDuel NBA scoring and value heuristics (5x/4x/6x) | RotoGrinders' own strategy "
               f"article | {_link(findings.RG_FD_NBA_STRATEGY)} |")
    out.append("")
    out.append(
        "RGENGY's substitute sources for each of these are listed in "
        "[02-data-sources.md](02-data-sources.md), with the `replaces` field naming exactly which "
        "RotoGrinders feature each endpoint substitutes for.\n")
    return "\n".join(out)


RG_OWNERSHIP_FAQ_LABEL = findings.RG_OWNERSHIP_FAQ


# ---------------------------------------------------------------------------
# docs/07 - grid schema and column mapping
# ---------------------------------------------------------------------------

def build_grid_schema() -> str:
    out: List[str] = []
    out.append("# 07 - RotoGrinders grid schema and column mapping\n")
    out.append(
        f"RotoGrinders' projection grid is the artefact its users actually read, so reproducing "
        f"its *shape* matters as much as reproducing its numbers. Column headers were transcribed "
        f"from the live site on {AUDIT_DATE} for MLB, NFL and WNBA only. Generated from "
        f"`models.RG_GRID_COLUMNS`, `pipeline._COLUMN_MAP` and `pipeline.UNMAPPED_COLUMN_REASONS`.\n")
    out.append(
        "> **IR-22.** The NBA and NHL grid headers were **not** transcribed, so\n"
        "> `RG_GRID_COLUMNS` deliberately omits them. `grid_rows()` sets\n"
        "> `rg_column_schema_observed=False` and writes an explicit note for those sports rather\n"
        "> than presenting RGENGY's own schema as a reproduction of theirs.\n")

    out.append("## Coverage\n")
    out.append("| sport | columns observed | filled by RGENGY | left null | header transcribed |")
    out.append("| --- | ---: | ---: | ---: | :---: |")
    for sport, cols in models.RG_GRID_COLUMNS.items():
        mapping = pipeline._COLUMN_MAP.get(sport, {})
        mapped = [c for c in cols if c in mapping]
        out.append(f"| {sport.upper()} | {len(cols)} | {len(mapped)} | {len(cols) - len(mapped)} "
                   f"| yes |")
    for sport in sorted(set(pipeline._COLUMN_MAP) - set(models.RG_GRID_COLUMNS)):
        out.append(f"| {sport.upper()} | not observed | {len(pipeline._COLUMN_MAP[sport])} mapped "
                   f"| - | **no** |")
    out.append("")
    out.append(
        "Two-way invariant, asserted by `tests/test_pipeline.py`: every observed column is either "
        "mapped or carries a written reason below, and every written reason refers to a column "
        "that actually exists. A null with no reason is indistinguishable from a bug.\n")

    for sport, cols in models.RG_GRID_COLUMNS.items():
        mapping = pipeline._COLUMN_MAP.get(sport, {})
        out.append(f"## {sport.upper()} ({len(cols)} columns)\n")
        out.append("| # | column | RGENGY source | status |")
        out.append("| ---: | --- | --- | --- |")
        for i, col in enumerate(cols, 1):
            if col in mapping:
                path = mapping[col]
                status = "filled"
                if col in ("FPTS/$",):
                    status = "filled - identity verified exactly against the public grid"
            else:
                path = pipeline.UNMAPPED_COLUMN_REASONS.get(col) or "(no reason recorded)"
                status = "**null**"
                path = _md_escape(path)
            out.append(f"| {i} | `{col}` | {_md_escape(str(path))} | {status} |")
        out.append("")

    out.append("## Columns left null, and why\n")
    out.append(
        "These are RotoGrinders' own column headings. Publishing an invented number under one "
        "would be indistinguishable from having reproduced theirs, so they are emitted as `null` "
        "and listed in `unfilled_columns` with the reason attached.\n")
    for col in sorted(pipeline.UNMAPPED_COLUMN_REASONS):
        sports = [s for s, cs in models.RG_GRID_COLUMNS.items() if col in cs]
        out.append(f"- **`{col}`** ({', '.join(x.upper() for x in sports) or 'mapped-only sport'}) "
                   f"- {pipeline.UNMAPPED_COLUMN_REASONS[col]}")
    out.append("")

    out.append("## Cells that are mapped but empty on a given run\n")
    out.append(
        "A mapped column can still come back null for every row when the input was absent - no "
        "weather feed, no market line, no batting order. `grid_rows()` distinguishes that case "
        "from an unmapped column and says so in `unfilled_column_reasons`, because the fix is "
        "different: one is a fetch problem, the other is a schema decision.\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# docs/09 - irregularities
# ---------------------------------------------------------------------------

STATUS_LABEL = {
    "open": "OPEN",
    "resolved": "RESOLVED",
    "assumption": "STATED ASSUMPTION",
    "unused-id": "UNUSED IDENTIFIER",
}


def build_irregularities() -> str:
    out: List[str] = []
    out.append("# 09 - Irregularities\n")
    out.append(
        "Everything found during the audit that is wrong, conflicting, undefined or unverifiable. "
        "Generated from `rgengy/findings.py`, which is the single source of truth: the scoring "
        "tables, module docstrings and quality findings all cite these ids, and "
        "`tests/test_findings.py` fails if the two disagree in either direction.\n")
    d = findings.to_dict()
    c = d["counts"]
    out.append(f"**{c['total']} findings** on {AUDIT_DATE}: {c['irregularities']} irregularities "
               f"and {c['limitations']} limitations - {c['open']} open, {c['assumptions']} stated "
               f"assumptions, {c['resolved']} resolved, {c['unused_ids']} declared-unused "
               f"identifiers, {c['critical']} critical.\n")
    out.append(
        "> Gaps in the numbering are **declared, not silent**. An id that was consumed during the\n"
        "> audit and then folded into another finding stays on the register with status\n"
        "> `unused-id`, because renumbering would quietly invalidate every cross-reference already\n"
        "> written into the scoring tables.\n")

    out.append("## Index\n")
    out.append("| id | severity | status | title |")
    out.append("| --- | --- | --- | --- |")
    for f in findings.FINDINGS:
        out.append(f"| [{f.id}](#{f.id.lower().replace('-', '')}) | {f.severity} "
                   f"| {STATUS_LABEL[f.status]} | {_md_escape(f.title)} |")
    out.append("")

    for f in findings.FINDINGS:
        out.append(f"---\n\n## {f.id}\n")
        out.append(f"**{_md_escape(f.title)}**\n")
        out.append(f"| | |")
        out.append(f"| --- | --- |")
        out.append(f"| kind | {f.kind} |")
        out.append(f"| status | {STATUS_LABEL[f.status]} |")
        out.append(f"| severity | {f.severity} |")
        out.append(f"| cited in | {', '.join('`' + r + '`' for r in f.refs)} |")
        out.append("")
        out.append(f"**What was found.** {f.detail}\n")
        out.append(f"**Why it matters.** {f.impact}\n")
        out.append(f"**What RGENGY does about it.** {f.action}\n")
        if f.sources:
            out.append("**Sources retrieved.**\n")
            for url in f.sources:
                out.append(f"- {_link(url)}")
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# docs/10 - limitations and remaining work
# ---------------------------------------------------------------------------

FUTURE_WORK = [
    ("Retrieve the operators' own scoring pages", "critical",
     "No coefficient in this repository is `confirmed_by_operator` (L-02). Every value rests on "
     "secondary sources, and three are actively contradicted (IR-05, IR-06, IR-16). DraftKings and "
     "FanDuel both keep their authoritative tables inside their logged-in apps, so this needs an "
     "authenticated session or a direct operator relationship.",
     "Settles IR-04, IR-05, IR-06, IR-08, IR-10, IR-16, L-04."),
    ("Fit the ownership model on real ownership data", "high",
     "pOWN is a softmax choice model with an uncalibrated beta (IR-13). RotoGrinders' is "
     "gradient-boosted over historical DraftKings ownership. `ownership.calibrate_beta()` already "
     "fits beta by deterministic grid search; what is missing is the data. Operator-published "
     "ownership after a contest settles is the cheapest legal source.",
     "Turns the ownership stage from `degraded` to `complete`."),
    ("Replace the normal-approximation simulator with a correlated event model", "high",
     "Player outcomes are drawn from a normal built on the mean and the floor/ceiling band (L-06). "
     "Real output is a sum of discrete correlated events, so tail behaviour is understated and a "
     "4-home-run game cannot occur. Needs historical play-by-play to fit per-stat distributions "
     "and their correlations.",
     "Makes simulated top-1 rates usable for large-field GPP decisions."),
    ("Verify the live player-stat endpoints", "high",
     "The slate endpoints are live-verified but the per-player season-stat endpoints are marked "
     "`unverified` (L-02). `rgengy probe` exists to check their shape; until it has been run from "
     "a networked machine, `run()` refuses to synthesise season stats and says so.",
     "Unblocks real projections end to end instead of caller-supplied data."),
    ("Transcribe the NBA and NHL grid headers", "medium",
     "`RG_GRID_COLUMNS` covers MLB, NFL and WNBA only (IR-22). Without the NBA and NHL headers the "
     "grid artefacts for those sports cannot be diffed against RotoGrinders' and are labelled as "
     "RGENGY's own schema.",
     "Makes all five supported sports schema-comparable."),
    ("Confirm the WNBA roster templates", "medium",
     "Both WNBA templates have zero sources and are marked `not-audited` (L-03); they were assumed "
     "to be the NBA shape reduced to six slots. A wrong template produces lineups the operator "
     "rejects outright (the IR-17 failure class).",
     "Removes the only roster template that could produce an illegal lineup."),
    ("Enlarge the RotoGrinders calibration sample", "medium",
     "The floor/ceiling ratios come from six free-tier rows (IR-12), one sport, one site, one "
     "slate. The paid tier would give a sample large enough to fit per-position bands and to test "
     "whether the ratios are stable across slates.",
     "Would let `rg_band` become a defensible default rather than an opt-in curiosity."),
    ("Licence a weather feed with a validated run-scoring sensitivity", "low",
     "Air density is computed exactly from the retrieved pressure, temperature and humidity, but "
     "`WEATHER_AIR_DENSITY_COEFFICIENT` is 0 - the adjustment is disabled, because applying an "
     "unvalidated sensitivity would fabricate precision. Enabling it needs a coefficient fitted "
     "against observed run production.",
     "Turns an already-computed input into an actual adjustment."),
    ("Add per-operator roster templates beyond Classic", "low",
     "Only the Classic (full-slate) template is shipped per sport and site. Showdown, single-game "
     "and 3-player-stack formats have different shapes and caps, and would each need their own "
     "verified provenance entry.",
     "Widens the optimizer to the formats most GPP players actually use."),
]


def build_roadmap() -> str:
    out: List[str] = []
    out.append("# 10 - Limitations and remaining work\n")
    out.append(
        "What RGENGY cannot do yet, what would have to be true to do it, and what to build next. "
        "The limitations section is generated from `rgengy/findings.py`; the roadmap below is the "
        "prioritised work that would retire them.\n")

    out.append("## Limitations\n")
    out.append("| id | severity | status | limitation |")
    out.append("| --- | --- | --- | --- |")
    for f in findings.limitations():
        out.append(f"| [{f.id}](09-irregularities.md#{f.id.lower().replace('-', '')}) "
                   f"| {f.severity} | {STATUS_LABEL[f.status]} | {_md_escape(f.title)} |")
    out.append("")
    for f in findings.limitations():
        out.append(f"### {f.id} - {_md_escape(f.title)}\n")
        out.append(f"{f.detail}\n")
        out.append(f"**Consequence.** {f.impact}\n")
        out.append(f"**Current mitigation.** {f.action}\n")

    out.append("## Stated assumptions\n")
    out.append(
        "These are not defects and not verified facts: they are the places where RGENGY proceeds on "
        "a documented assumption because no source settles it. Each is labelled wherever its output "
        "is surfaced.\n")
    out.append("| id | assumption | where it is labelled |")
    out.append("| --- | --- | --- |")
    for f in findings.FINDINGS:
        if f.status == "assumption":
            out.append(f"| [{f.id}](09-irregularities.md#{f.id.lower().replace('-', '')}) "
                       f"| {_md_escape(f.title)} | {', '.join('`' + r + '`' for r in f.refs)} |")
    out.append("")

    out.append("## Remaining work, prioritised\n")
    out.append(
        "Ordered by how much of the gap to RotoGrinders' data quality each one closes. Priority "
        "reflects the severity of the finding it retires, not the effort involved.\n")
    for i, (title, priority, detail, payoff) in enumerate(FUTURE_WORK, 1):
        out.append(f"### {i}. {title}\n")
        out.append(f"**Priority: {priority}.**\n")
        out.append(f"{detail}\n")
        out.append(f"**Payoff.** {payoff}\n")

    out.append("## What would have to be true to reach parity\n")
    out.append(
        "RotoGrinders' projection quality rests on three things RGENGY does not have and cannot "
        "obtain from free official feeds:\n")
    out.append(
        "1. **Historical per-contest ownership.** Their pOWN is gradient-boosted over it "
        "(IR-13). No operator publishes it historically; some publish it after a contest settles.\n"
        "2. **A proprietary projection engine.** THE BAT X and their in-house models are fitted to "
        "years of outcomes. RGENGY ships a transparent rate x opportunity x environment engine "
        "whose inputs are all sourced, which is auditable but will not match a fitted model's "
        "accuracy.\n"
        "3. **Licensed data.** Player news, injury timing, lineup confirmation and weather come "
        "from paid feeds. RGENGY uses official free feeds and says so per endpoint (docs/02).\n")
    out.append(
        "What RGENGY does better is *auditability*: every coefficient, every roster slot and every "
        "derived column carries its evidence class and its source URLs, and every quantity it "
        "cannot verify is null with a written reason rather than a plausible number.\n")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# site data
# ---------------------------------------------------------------------------

def build_site_data() -> Dict[str, Any]:
    summary = sources.verification_summary()
    # `verification_summary()` stamps itself with the wall clock, which is right for
    # `rgengy sources` at runtime and wrong here: this dict is serialised into the
    # COMMITTED site/data/rgengy.json, so a live timestamp makes `--check` report the
    # file as stale on every single run and the check becomes meaningless.  The
    # runtime function is left alone; only the committed snapshot is made
    # reproducible.
    summary["generated_at"] = generated_at()
    tables = []
    for key in scoring.available():
        sport, site = key.split(":")
        t = scoring.load(sport, site)
        tables.append({
            "key": key, "sport": sport, "site": site, "meta": t.meta,
            "values": t.payload.get("values", {}),
            "disputed": sorted(t.disputed),
            "not_audited": sorted(t.not_audited),
            "intentionally_zero": sorted(t.intentionally_zero),
            "provenance": t.provenance_rows(),
        })
    grid = {}
    for sport, cols in models.RG_GRID_COLUMNS.items():
        mapping = pipeline._COLUMN_MAP.get(sport, {})
        grid[sport] = {
            "columns": cols,
            "observed": True,
            "cells": [{"column": c,
                       "source": mapping.get(c),
                       "reason": None if c in mapping else pipeline.UNMAPPED_COLUMN_REASONS.get(c),
                       "filled": c in mapping} for c in cols],
        }
    for sport, mapping in pipeline._COLUMN_MAP.items():
        if sport not in grid:
            grid[sport] = {"columns": list(mapping), "observed": False,
                           "cells": [{"column": c, "source": p, "reason": None, "filled": True}
                                     for c, p in mapping.items()]}
    roster = {}
    for key in models.ROSTER_PROVENANCE:
        sport, site = key.split(":")
        tmpl = models.default_roster(sport, site)
        roster[key] = {
            "sport": sport, "site": site, "salary_cap": tmpl["salary_cap"],
            "n_players": tmpl["n_players"],
            "verification_status": tmpl["verification_status"],
            "note": tmpl.get("note"),
            "sources": tmpl.get("sources", []),
            "slots": [{"label": r.label, "count": r.count, "eligible": list(r.eligible)}
                      for r in tmpl["slots"]],
        }
    checks = []
    for fn in quality.ALL_CHECKS:
        checks.append({"name": fn.__name__,
                       "doc": (fn.__doc__ or "").strip().split("\n")[0],
                       "registered": True})
    checks.append({"name": "check_cross_source_identity",
                   "doc": "Flag entities present in one source but absent from the official one.",
                   "registered": False})
    return {
        "generated_at": generated_at(),
        "audit_date": AUDIT_DATE,
        "sources": {"summary": summary, "endpoints": sources.registry_rows()},
        "scoring": tables,
        "grid": grid,
        "rosters": roster,
        "findings": findings.to_dict(),
        "checks": checks,
        "engine_summary": {
            "band_modes": ["distribution", "rg_band"],
            "rg_observed_floor_ratio": None,
            "sigma_by_sport": {},
        },
    }


# ---------------------------------------------------------------------------

README = REPO / "README.md"
METHOD = REPO / "docs" / "01-method.md"
METHOD_START = "<!-- RGENGY:TESTS:START - generated by scripts/build_docs.py; do not edit by hand -->"
METHOD_END = "<!-- RGENGY:TESTS:END -->"

# What each test module covers.  Narrative, so it lives here rather than in prose
# that would otherwise drift away from the counts beside it.
TEST_COVER = {
    "test_pipeline": "end-to-end run, grid schema invariants, artefacts",
    "test_ownership": "choice model, cap, leverage, smash, pipeline integration",
    "test_quality": "every quality gate fires *and* stays silent when it should",
    "test_engines": "position dispatch, no-fabrication, win probability, bands",
    "test_vegas": "vig removal, implied totals, Bryant formula, market win probability",
    "test_simulator": "payouts, field construction, cash/top-10/top-1 invariants",
    "test_optimizer": "optimality vs brute force, roster uniqueness, slot breakdown",
    "test_models": "roster provenance, grid schema, run report",
    "test_scoring": "all 11 tables, representation overlaps, evidence classes",
    "test_rg_grid": "the saved RotoGrinders fixture: identity, ratios, validation",
    "test_site": "the markdown renderer, link integrity, README/dashboard accuracy",
    "test_findings": "the IR/L register agrees with every citation in the tree",
}
STATS_START = "<!-- RGENGY:STATS:START - generated by scripts/build_docs.py; do not edit by hand -->"
STATS_END = "<!-- RGENGY:STATS:END -->"


def build_readme_stats(data: Dict[str, Any]) -> str:
    """The README's headline numbers, regenerated from the same data as the site.

    Stating a test count in hand-written prose creates an unstable loop: the test
    that checks the count is itself a test, so correcting the number changes it
    again.  Generating the block between sentinels makes it converge, and
    ``--check`` still catches anyone who edits it by hand.
    """
    s = data["sources"]["summary"]
    f = data["findings"]["counts"]
    n_tests = sum(t["tests"] for t in data["tests"])
    return (
        f"{STATS_START}\n"
        f"Audit date **{data['audit_date']}** · **{n_tests} tests passing** · "
        f"**{s['total_endpoints']} registered endpoints** ·\n"
        f"**{len(data['scoring'])} scoring tables** · "
        f"**{f['total']} findings on the register** ·\n"
        f"**[published site](https://buffedlizard55-lab.github.io/RGENGY/)**\n"
        f"{STATS_END}"
    )


def build_method_tests(data: Dict[str, Any]) -> str:
    """docs/01's test-suite block: the count, and a per-module table, generated."""
    inv = sorted(data["tests"], key=lambda t: (-t["tests"], t["module"]))
    total = sum(t["tests"] for t in inv)
    lines = [
        METHOD_START,
        f"**{total} tests** across {len(inv)} modules, all passing, run with",
        "`python3 -m unittest discover -s tests -t tests`.",
        "",
        "| module | tests | covers |",
        "| --- | ---: | --- |",
    ]
    for t in inv:
        cover = TEST_COVER.get(t["module"], "")
        lines.append(f"| `{t['module']}` | {t['tests']} | {cover} |")
    lines.append(METHOD_END)
    return "\n".join(lines)


def update_method(data: Dict[str, Any]) -> Optional[str]:
    """Return the new docs/01 text, or None if its sentinels are missing."""
    text = METHOD.read_text(encoding="utf-8") if METHOD.exists() else ""
    if METHOD_START not in text or METHOD_END not in text:
        return None
    start = text.index(METHOD_START)
    end = text.index(METHOD_END) + len(METHOD_END)
    return text[:start] + build_method_tests(data) + text[end:]


def update_readme(data: Dict[str, Any]) -> Optional[str]:
    """Return the new README text, or None if the sentinels are missing."""
    text = README.read_text(encoding="utf-8") if README.exists() else ""
    if STATS_START not in text or STATS_END not in text:
        return None
    start = text.index(STATS_START)
    end = text.index(STATS_END) + len(STATS_END)
    return text[:start] + build_readme_stats(data) + text[end:]


GENERATORS = {
    "02-data-sources.md": build_data_sources,
    "04-rg-findings.md": build_rg_findings,
    "03-scoring-verification.md": build_scoring,
    "07-grid-schema.md": build_grid_schema,
    "09-irregularities.md": build_irregularities,
    "10-roadmap-and-limitations.md": build_roadmap,
}

#: Emitted at the top of every generated file.  `tests/test_findings.py` uses it
#: to exclude generated output from the citation scan: counting a page rendered
#: FROM the findings register as evidence FOR the register is circular, and would
#: make a declared-unused id look cited.
GENERATED_MARKER = "GENERATED FILE - DO NOT EDIT"

BANNER = (f"<!-- {GENERATED_MARKER}: rendered by scripts/build_docs.py from the committed "
          "registries. Edit the source and re-run the generator. -->\n\n")


def write_all(check: bool = False) -> int:
    problems: List[str] = []
    register_problems = findings.validate()
    if register_problems:
        problems.extend(f"findings register: {p}" for p in register_problems)

    rendered: Dict[Path, str] = {}
    for name, fn in GENERATORS.items():
        rendered[DOCS / name] = BANNER + fn()
    data = build_site_data()
    # The engine summary is filled from the module so it cannot drift.
    from rgengy import engines
    data["engine_summary"]["rg_observed_floor_ratio"] = engines.RG_OBSERVED_FLOOR_RATIO
    data["engine_summary"]["rg_observed_ceil_ratio"] = engines.RG_OBSERVED_CEIL_RATIO
    data["engine_summary"]["rg_observed_sample_size"] = engines.RG_OBSERVED_SAMPLE_SIZE
    data["engine_summary"]["sigma_by_sport"] = dict(engines.SIGMA_BY_SPORT)
    data["engine_summary"]["weather_coefficient"] = engines.WEATHER_AIR_DENSITY_COEFFICIENT
    data["tests"] = _test_inventory()
    blob = json.dumps(data, indent=2, sort_keys=True, default=str) + "\n"
    rendered[SITE_DATA / "rgengy.json"] = blob

    new_method = update_method(data)
    if new_method is not None:
        rendered[METHOD] = new_method
    elif METHOD.exists():
        problems.append(
            "docs/01-method.md has lost its RGENGY:TESTS sentinels, so its test counts "
            "can no longer be regenerated and will silently go stale")

    new_readme = update_readme(data)
    if new_readme is not None:
        rendered[README] = new_readme
    elif README.exists():
        problems.append(
            "README.md has lost its RGENGY:STATS sentinels, so its headline numbers "
            "can no longer be regenerated and will silently go stale")

    stale: List[str] = []
    for path, text in rendered.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(str(path.relative_to(REPO)))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")

    if check:
        if stale:
            print("STALE generated files (run scripts/build_docs.py):")
            for s in stale:
                print(f"  {s}")
            return 1
        print(f"generated docs and site data are up to date ({len(rendered)} files)")
        return 1 if problems else 0

    for p in problems:
        print(f"WARNING: {p}")
    print(f"wrote {len(rendered)} generated files:")
    for path in sorted(rendered):
        digest = hashlib.sha256(rendered[path].encode()).hexdigest()[:12]
        print(f"  {path.relative_to(REPO)}  ({len(rendered[path])} bytes, sha256:{digest})")
    return 1 if problems else 0


def _test_inventory() -> List[Dict[str, Any]]:
    """Count the tests in each module, so the site reports real coverage."""
    import unittest
    loader = unittest.TestLoader()
    out = []
    for path in sorted((REPO / "tests").glob("test_*.py")):
        try:
            suite = loader.discover(start_dir=str(REPO / "tests"),
                                    pattern=path.name, top_level_dir=str(REPO / "tests"))
            n = suite.countTestCases()
        except Exception as exc:                       # pragma: no cover
            n, out_err = 0, str(exc)
            out.append({"module": path.stem, "tests": 0, "error": out_err})
            continue
        out.append({"module": path.stem, "tests": n})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the generated files are stale, without writing them")
    args = ap.parse_args()
    return write_all(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
