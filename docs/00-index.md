# RGENGY - documentation index

An open, auditable rebuild of the *data quality* behind
[RotoGrinders](https://rotogrinders.com/)' projection system: what it uses, where
that data comes from, what could be verified from official sources, and what could
not.

Audit date **2026-09-22**. Everything in `docs/` is either generated from a
committed registry or is narrative that cites one. No number in these files is
asserted from memory.

---

## Read these first

| doc | what it answers |
| --- | --- |
| [01 - Method](01-method.md) | How the audit was run, and the rules every claim had to satisfy |
| [02 - Data sources](02-data-sources.md) | **Every external input**, with provider, official/unofficial, auth, verification status and links |
| [04 - RotoGrinders findings](04-rg-findings.md) | What was reverse-engineered from the live grid, with the arithmetic |
| [09 - Irregularities](09-irregularities.md) | **Everything wrong, conflicting or unverifiable** that was found |
| [10 - Limitations and remaining work](10-roadmap-and-limitations.md) | What RGENGY cannot do yet, and the prioritised work to close it |

## Reference

| doc | what it covers |
| --- | --- |
| [03 - Scoring verification](03-scoring-verification.md) | All 11 scoring tables: every coefficient, its evidence class and its source URLs |
| [05 - Projection engines](05-projection-engines.md) | Rate x opportunity x environment, bands, win probability |
| [06 - Optimizer and simulator](06-optimizer-and-simulator.md) | Roster construction, exposure, payouts, field simulation |
| [07 - Grid schema](07-grid-schema.md) | RotoGrinders' column set and which columns RGENGY fills, and why not the rest |
| [08 - Quality gates](08-quality-gates.md) | The checks that stop an indefensible number being published |

---

## The headline results

1. **The scoring table is externally validated.** RGENGY's independently sourced
   DraftKings MLB coefficients, applied to RotoGrinders' own published stat
   projections, reproduce RotoGrinders' published FPTS for all six free rows
   within **0.07 FPTS** (0.56% worst case). See [04 §1](04-rg-findings.md).
2. **`FPTS/$` is reproduced exactly.**
   `FPTS/$ == FPTS / (SALARY / 1000)`, max error 0.0036 over six rows - pure 2dp
   display rounding. It is the only RotoGrinders analytic column RGENGY claims to
   reproduce.
3. **16 data endpoints are registered, 14 of them official league feeds**, with a
   verification status each. Zero require an API key. See [02](02-data-sources.md).
4. **29 findings are on the register** - 23 irregularities and 6 limitations, of
   which 6 were defects in RGENGY itself and are now resolved and pinned by tests.
   See [09](09-irregularities.md).
5. **No operator scoring page could be retrieved** (both are inside logged-in
   apps), so *no coefficient is marked `confirmed_by_operator`*. That is limitation
   **L-02** and it is the single largest constraint on this project.

## What RGENGY deliberately does not do

- It does not publish a number under a RotoGrinders column heading unless it can
  show the derivation. Columns it cannot fill are `null` **with a written reason**
  ([07](07-grid-schema.md)).
- It does not invent a win probability. Every one carries the method that produced
  it, and "unavailable" is a legal answer (IR-23).
- It does not drop a player it cannot project. They stay at 0.0, flagged, because
  dropping them turns one missing sample into "no lineup exists" (IR-19).
- It does not apply an unvalidated sensitivity. The weather/air-density adjustment
  is computed exactly and then multiplied by a coefficient of **0** until someone
  fits one (docs/05).

## Running it

```bash
python3 -m rgengy sources            # the endpoint register with verification status
python3 -m rgengy probe              # re-check live endpoint shapes (needs network)
python3 -m rgengy verify             # write verification.json
python3 -m rgengy scoring --sport mlb --site draftkings
python3 -m rgengy run --sport mlb --date 2026-09-22 --site draftkings
python3 -m rgengy demo --sport mlb   # synthetic, stamped SYNTHETIC end to end

python3 -m unittest discover -s tests -t tests      # the full suite
python3 scripts/build_docs.py --check               # docs/site data not stale
```

`data/` is gitignored: every artefact is reproducible from the seeded inputs plus
the committed scoring tables and endpoint registry, and the GitHub Pages workflow
regenerates it on each build so the published site cannot disagree with the code.
