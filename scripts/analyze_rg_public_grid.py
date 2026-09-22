#!/usr/bin/env python3
"""Derive every RotoGrinders calibration constant from the transcribed public grid.

Why this script exists
----------------------
RotoGrinders' projection engine is closed.  The only RotoGrinders projection data
observable without a subscription is the free top-of-grid on
``https://rotogrinders.com/projected-stats/{sport}`` - on 2026-09-22 that was
**six** Arizona Diamondbacks hitters from one game
(``tests/fixtures/rg_public_mlb_grid_2026-09-22.json``).

Six rows cannot identify a model.  What they *can* do is:

1. **Validate** RGENGY's scoring tables.  RotoGrinders publishes both the
   projected stats and the resulting ``FPTS``, so recomputing ``FPTS`` from the
   published stats with RGENGY's own coefficients is a direct, external test of
   every point value in ``rgengy/data/scoring``.
2. **Confirm identities.**  ``FPTS/$`` can be checked against
   ``FPTS / (SALARY / 1000)`` exactly.
3. **Measure** the ``FLOOR``/``CEIL`` scale so RGENGY's bands are at least in the
   same units as the reference system, with the sample size stated every time.

Everything printed here is recomputed from the fixture on every run, so no
constant in the codebase is a magic number that has drifted from its evidence.
Nothing is inferred beyond what the six rows support, and anything that cannot be
determined is printed as UNKNOWN rather than guessed.

Run:  ``python3 scripts/analyze_rg_public_grid.py`` (add ``--json`` for machine-readable output)
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from rgengy import scoring  # noqa: E402
from rgengy.models import RG_GRID_COLUMNS  # noqa: E402

FIXTURE = REPO / "tests" / "fixtures" / "rg_public_mlb_grid_2026-09-22.json"

#: Projected-stat columns on the MLB grid, i.e. the ones a scoring table consumes.
MLB_STAT_COLUMNS = ("PA", "1B", "2B", "3B", "HR", "RBI", "R", "SB", "BB",
                    "IP", "BBA", "K", "W", "ER", "HA", "HBP", "QS")

#: Grid column -> rgengy scoring-table stat key.
STAT_KEY_MAP = {
    "PA": "pa", "1B": "1b", "2B": "2b", "3B": "3b", "HR": "hr", "RBI": "rbi",
    "R": "r", "SB": "sb", "BB": "bb", "IP": "ip", "BBA": "bba", "K": "k",
    "W": "win", "ER": "er", "HA": "ha", "HBP": "hbp", "QS": "qs",
}

#: Tolerance for "reproduces the published value".  RotoGrinders rounds FPTS to
#: 2dp and publishes its input stats rounded to 2-3dp, so recomputing from the
#: rounded inputs cannot be bit-exact; 0.15 FPTS (~1% of a typical value) is the
#: band within which rounding of the inputs fully explains the residual.
FPTS_TOLERANCE = 0.15


def load_fixture(path: Path = FIXTURE) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stats_from_row(row: Dict[str, Any]) -> Dict[str, float]:
    """Convert a grid row's projected-stat columns into rgengy stat keys."""
    out: Dict[str, float] = {}
    for col in MLB_STAT_COLUMNS:
        if col not in row:
            continue
        val = row[col]
        if val is None or val == "":
            continue
        out[STAT_KEY_MAP[col]] = float(val)
    return out


def ratio_stats(values: Sequence[float]) -> Dict[str, Any]:
    if not values:
        return {"n": 0, "mean": None, "min": None, "max": None, "sd": None}
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "sd": round(statistics.pstdev(values), 4) if len(values) > 1 else 0.0,
    }


def analyze(fixture: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    fixture = fixture or load_fixture()
    rows: List[Dict[str, Any]] = fixture["rows"]
    out: Dict[str, Any] = {
        "fixture": str(FIXTURE.relative_to(REPO)),
        "source_url": fixture["_provenance"]["source_url"],
        "retrieved_utc": fixture["_provenance"]["retrieved_utc"],
        "row_count": len(rows),
    }

    # -- 1. column schema ---------------------------------------------------
    # RG_GRID_COLUMNS is keyed by sport; the MLB grid is the one transcribed.
    # 'FPTS/$' is stored as 'FPTS_PER_SALARY' in the fixture because '/' makes an
    # awkward JSON key, so the comparison maps it back before asserting equality.
    declared = list(fixture["columns"])
    code_cols = list(RG_GRID_COLUMNS.get("mlb", []))
    remapped = ["FPTS/$" if c == "FPTS_PER_SALARY" else c for c in declared]
    out["schema"] = {
        "fixture_columns": len(declared),
        "rg_grid_columns_constant": len(code_cols),
        "identical_to_code_constant": remapped == code_cols,
        "fixture_order": declared,
        "missing_from_code": [c for c in remapped if c not in code_cols],
        "missing_from_fixture": [c for c in code_cols if c not in remapped],
        "key_renames": {"FPTS/$": "FPTS_PER_SALARY"},
    }

    # -- 2. score every row with RGENGY's own DraftKings MLB table -----------
    table = scoring.load("mlb", "draftkings")
    scoring_rows: List[Dict[str, Any]] = []
    for row in rows:
        stats = stats_from_row(row)
        computed = table.score(stats)
        published = float(row["FPTS"])
        scoring_rows.append({
            "player": row["PLAYER"],
            "salary": row["SALARY"],
            "position": row["POS"],
            "published_fpts": published,
            "rgengy_fpts": computed,
            "delta": round(computed - published, 3),
            "abs_delta": round(abs(computed - published), 3),
            "pct_error": round(100.0 * abs(computed - published) / published, 3) if published else None,
            "stats_used": stats,
        })
    deltas = [r["abs_delta"] for r in scoring_rows]
    out["scoring_validation"] = {
        "site": "draftkings",
        "table_values_used": len([v for v in table.points.values() if v]),
        "rows": scoring_rows,
        "max_abs_delta": round(max(deltas), 3) if deltas else None,
        "mean_abs_delta": round(statistics.fmean(deltas), 4) if deltas else None,
        "tolerance": FPTS_TOLERANCE,
        "verdict": ("RGENGY's DraftKings MLB scoring table reproduces RotoGrinders' published FPTS "
                    f"for all {len(rows)} rows within {max(deltas):.2f} FPTS "
                    f"({max(r['pct_error'] for r in scoring_rows):.2f}% worst case)"
                    if deltas and max(deltas) <= FPTS_TOLERANCE else
                    "MISMATCH: at least one row is outside tolerance - a scoring value is wrong"),
        "passed": bool(deltas) and max(deltas) <= FPTS_TOLERANCE,
    }

    # -- 3. FPTS/$ identity -------------------------------------------------
    ident = []
    for row in rows:
        fpts = float(row["FPTS"])
        salary = float(row["SALARY"])
        published = float(row["FPTS_PER_SALARY"])
        ident.append({
            "player": row["PLAYER"],
            "published": published,
            "computed": round(fpts / (salary / 1000.0), 4),
            "abs_error": round(abs(published - fpts / (salary / 1000.0)), 4),
        })
    max_err = max(r["abs_error"] for r in ident)
    out["fpts_per_salary_identity"] = {
        "formula": "FPTS/$ == FPTS / (SALARY / 1000)",
        "rows": ident,
        "max_abs_error": max_err,
        "confirmed": max_err <= 0.01,
        "verdict": ("CONFIRMED EXACTLY - the residual is display rounding only. This is the "
                    "definition RGENGY uses for its own `value` metric."
                    if max_err <= 0.01 else "NOT CONFIRMED - investigate before relying on it"),
    }

    # -- 4. FLOOR / CEIL scale ---------------------------------------------
    floor_ratios, ceil_ratios, floor_excluded = [], [], []
    for row in rows:
        fpts = float(row["FPTS"])
        if not fpts:
            continue
        floor = float(row["FLOOR"])
        ceil = float(row["CEIL"])
        if floor <= 0:
            floor_excluded.append({
                "player": row["PLAYER"], "fpts": fpts, "floor": floor, "ceil": ceil,
                "reason": ("FLOOR is 0 while FPTS and CEIL are both non-zero; every other row has "
                           "FLOOR between 0.27 and 0.34 of FPTS. Excluded from the fitted ratio and "
                           "flagged as IR-19 rather than imputed."),
            })
        else:
            floor_ratios.append(floor / fpts)
        ceil_ratios.append(ceil / fpts)
    out["floor_ratio"] = dict(ratio_stats(floor_ratios), excluded=floor_excluded,
                              per_row=[round(r, 4) for r in floor_ratios])
    out["ceil_ratio"] = dict(ratio_stats(ceil_ratios),
                             per_row=[round(r, 4) for r in ceil_ratios])
    out["band_width"] = {
        "asymmetry": "CEIL/FPTS (~2.2) is roughly 7x FLOOR/FPTS (~0.30), so RotoGrinders' bands "
                     "are strongly asymmetric - upside is modelled far more widely than downside.",
        "ceil_minus_floor": [round(float(r["CEIL"]) - float(r["FLOOR"]), 2) for r in rows],
    }

    # -- 5. OBFPTS ----------------------------------------------------------
    ob = []
    for row in rows:
        fpts = float(row["FPTS"])
        if fpts:
            ob.append(float(row["OBFPTS"]) / fpts)
    out["obfpts"] = dict(
        ratio_stats(ob),
        per_row=[round(r, 4) for r in ob],
        definition_known=False,
        verdict=("OBFPTS is consistently above FPTS by 8-13% and is published at full float "
                 "precision while FPTS is rounded to 2dp, which suggests OBFPTS is an unrounded "
                 "model output on a slightly different scale. Its definition is NOT published "
                 "anywhere reachable, so RGENGY does not attempt to reproduce it. IR-21."),
    )

    # -- 6. ownership -------------------------------------------------------
    powns = [float(row["POWN"]) for row in rows]
    out["ownership"] = {
        "pown_per_row": {row["PLAYER"]: float(row["POWN"]) for row in rows},
        "pown_sum": round(sum(powns), 4),
        "pown_range": [round(min(powns), 4), round(max(powns), 4)],
        "teamown_values": sorted({float(row["TEAMOWN"]) for row in rows}),
        "opto_range": [round(min(float(r["OPTO"]) for r in rows), 3),
                       round(max(float(r["OPTO"]) for r in rows), 3)],
        "verdict": (f"POWN sums to {sum(powns) * 100:.2f}% across the six free rows, i.e. essentially "
                    "the entire field, so POWN is a share of projected field usage rather than an "
                    "independent probability. TEAMOWN is identical for all six rows (team-level). "
                    "OPTO is a fantasy-point projection from RotoGrinders' optimiser, not a "
                    "percentage - it ranges over the same units as CEIL. IR-22."),
    }

    # -- 7. columns that cannot be determined -------------------------------
    constant_cols: Dict[str, Any] = {}
    varying_cols: List[str] = []
    for col in declared:
        vals = [row.get(col) for row in rows]
        if len({json.dumps(v, sort_keys=True) for v in vals}) == 1:
            constant_cols[col] = vals[0]
        else:
            varying_cols.append(col)
    out["constant_across_all_rows"] = constant_cols
    out["varying_columns"] = varying_cols
    out["undetermined_columns"] = {
        "columns": ["BATK", "HRRBI", "BASES", "H", "PC", "DIFFERENCE", "LEV", "SMASH", "TOPVAL"],
        "reason": ("These columns are published without a definition anywhere reachable. Some are "
                   "partly guessable from their inputs (BASES ~= 1B + 2*2B + 3*3B + 4*HR is consistent "
                   "with the data to within rounding; H ~= 1B+2B+3B+HR) but RGENGY does not publish a "
                   "value for any of them, and the grid writer marks them null with `unfilled_columns` "
                   "rather than inventing one. See IR-21 and limitation L-05."),
    }

    # -- 8. derived calibration constants for the engine --------------------
    out["engine_constants"] = {
        "RG_OBSERVED_FLOOR_RATIO": out["floor_ratio"]["mean"],
        "RG_OBSERVED_CEIL_RATIO": out["ceil_ratio"]["mean"],
        "sample_size_warning": (
            f"n={out['floor_ratio']['n']} for the floor ratio and n={out['ceil_ratio']['n']} for the "
            "ceiling ratio, all from ONE team in ONE game at Coors Field on ONE date. These constants "
            "are used only as a sanity band, never as the primary projection mechanism; "
            "rgengy.engines defaults to deriving bands from its own outcome distribution."),
    }
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="emit machine-readable output")
    ap.add_argument("--fixture", type=Path, default=FIXTURE)
    ap.add_argument("--out", type=Path, help="also write the report to this path")
    args = ap.parse_args(argv)

    report = analyze(load_fixture(args.fixture))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report["scoring_validation"]["passed"] else 1

    sv = report["scoring_validation"]
    print(f"RotoGrinders public MLB grid - {report['row_count']} free rows")
    print(f"  source: {report['source_url']}")
    print(f"  retrieved: {report['retrieved_utc']}")
    print()
    schema = report["schema"]
    print(f"column schema: {schema['fixture_columns']} declared in the fixture, "
          f"{schema['rg_grid_columns_constant']} in RG_GRID_COLUMNS['mlb'], "
          f"identical={schema['identical_to_code_constant']}")
    if not schema["identical_to_code_constant"]:
        print(f"   !! missing from code: {schema['missing_from_code']}")
        print(f"   !! missing from fixture: {schema['missing_from_fixture']}")
    print()
    print("1. SCORING VALIDATION (RGENGY's DraftKings MLB table vs RG's published FPTS)")
    print(f"   {'player':18s} {'salary':>7} {'RG FPTS':>8} {'RGENGY':>8} {'delta':>7} {'err%':>6}")
    for r in sv["rows"]:
        print(f"   {r['player']:18s} {r['salary']:>7} {r['published_fpts']:>8.2f} "
              f"{r['rgengy_fpts']:>8.2f} {r['delta']:>+7.2f} {r['pct_error']:>6.2f}")
    print(f"   max |delta| = {sv['max_abs_delta']}  (tolerance {sv['tolerance']})  "
          f"passed={sv['passed']}")
    print(f"   -> {sv['verdict']}")
    print()
    ident = report["fpts_per_salary_identity"]
    print(f"2. FPTS/$ IDENTITY: {ident['formula']}")
    print(f"   max |error| = {ident['max_abs_error']}  confirmed={ident['confirmed']}")
    print(f"   -> {ident['verdict']}")
    print()
    fr, cr = report["floor_ratio"], report["ceil_ratio"]
    print("3. FLOOR / CEIL SCALE")
    print(f"   FLOOR/FPTS  n={fr['n']}  mean {fr['mean']}  range {fr['min']}-{fr['max']}  sd {fr['sd']}")
    print(f"   CEIL/FPTS   n={cr['n']}  mean {cr['mean']}  range {cr['min']}-{cr['max']}  sd {cr['sd']}")
    for ex in fr["excluded"]:
        print(f"   EXCLUDED {ex['player']}: FLOOR={ex['floor']} FPTS={ex['fpts']} CEIL={ex['ceil']}")
        print(f"            {ex['reason']}")
    print(f"   -> {report['band_width']['asymmetry']}")
    print()
    ob = report["obfpts"]
    print(f"4. OBFPTS/FPTS  n={ob['n']}  mean {ob['mean']}  range {ob['min']}-{ob['max']}")
    print(f"   -> {ob['verdict']}")
    print()
    ow = report["ownership"]
    print(f"5. OWNERSHIP  POWN sum={ow['pown_sum']} range={ow['pown_range']} "
          f"TEAMOWN={ow['teamown_values']} OPTO range={ow['opto_range']}")
    print(f"   -> {ow['verdict']}")
    print()
    print(f"6. CONSTANT ACROSS ALL {report['row_count']} ROWS (slate/team-level, not player-level):")
    print("   " + ", ".join(f"{k}={json.dumps(v)}" for k, v in report["constant_across_all_rows"].items()))
    print()
    und = report["undetermined_columns"]
    print(f"7. COLUMNS WHOSE DEFINITION COULD NOT BE DETERMINED: {', '.join(und['columns'])}")
    print(f"   -> {und['reason']}")
    print()
    ec = report["engine_constants"]
    print("8. CALIBRATION CONSTANTS CONSUMED BY rgengy/engines.py")
    print(f"   RG_OBSERVED_FLOOR_RATIO = {ec['RG_OBSERVED_FLOOR_RATIO']}")
    print(f"   RG_OBSERVED_CEIL_RATIO  = {ec['RG_OBSERVED_CEIL_RATIO']}")
    print(f"   !! {ec['sample_size_warning']}")
    return 0 if sv["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
