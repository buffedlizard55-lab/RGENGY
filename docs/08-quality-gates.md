# 08 - Quality gates

Nine checks run on every pipeline execution. Their job is not to make the numbers
better - it is to stop an indefensible number being published quietly.

`rgengy/quality.py`. Each check appends to a `QualityReport` of `Finding` objects,
and each `Finding` carries a **`review_action`**: what a human should do next. An
irregularity with no review action cannot be actioned, so
`tests/test_quality.py` asserts every emitted finding has one.

---

## Severities

| severity | meaning |
| --- | --- |
| `info` | correct behaviour worth recording, or a question rather than a defect |
| `warning` | the output is usable but degraded; the run continues |
| `critical` | the output must not be trusted; `has_critical` is true and the report says so |

`QualityReport` exposes `by_severity()`, `by_check()`, `has_critical` and
`to_dict()`, and rejects an unknown severity outright rather than bucketing it.
`checks_run` records every check that executed, **including the ones that found
nothing** - a report that lists only failures cannot distinguish "clean" from
"never ran".

## The checks

`ALL_CHECKS` is the registered set, run by `pipeline.run()`:

| check | severity | what it catches |
| --- | --- | --- |
| `check_zero_projection` | warning | a paid player with no projected points, or projected at exactly 0 - they cannot be ranked meaningfully |
| `check_duplicate_ids` | **critical** | the same player id twice, which corrupts ownership normalisation and roster uniqueness |
| `check_implausible_values` | **critical** / warning | a negative count stat (an environment ratio went negative), a negative salary, or an opportunity above a sanity bound |
| `check_stale_provenance` | warning | an input older than `STALE_AFTER_HOURS` (36h), an unparseable timestamp, or a network input with **no timestamp at all** |
| `check_endpoint_failures` | **critical** | an endpoint that returned no data, so every projection downstream of it is degraded |
| `check_ownership_normalisation` | warning | projected ownership that does not sum to ~1.0 across the slate |
| `check_scoring_coverage` | warning / info | a projected stat with no coefficient, or a coefficient of 0 that was never audited - both silently understate FPTS |
| `check_representation_double_count` | **critical** | a scoring table that counts the same production twice |
| `check_cross_source_identity` | warning | a projection row the official feed does not contain. Needs two feeds, so the pipeline calls it explicitly rather than by default |

## Sanity bounds are labelled as ours

| constant | value | applies to |
| --- | ---: | --- |
| `MAX_MLB_PA` | 8.0 | plate appearances (a batter cannot realistically exceed ~7 in 9 innings plus extras) |
| `MAX_MLB_IP` | 12.0 | innings pitched |
| `MAX_BASKETBALL_MINUTES` | 60.0 | `min` for NBA and WNBA |
| `MAX_HOCKEY_TOI` | 45.0 | time on ice |
| `STALE_AFTER_HOURS` | 36 | provenance age |

Exceeding one is a **warning, not an error**, and the review action says so:
"the bound itself is an RGENGY sanity limit, not a league rule." A bound presented
as a rule would be a fabricated constraint.

Negative values are critical for count stats but explicitly exempt for
run-*prevention* keys (`er`, `ga`, `to`, `pa_int`, `fum_lost`), which are
subtractions in the scoring table.

## Telling a deliberate zero from an unaudited zero

This is the distinction the whole coverage check exists for.

A coefficient of 0.0 on a stat that is actually projected means published FPTS
understates the operator's real total. But there are two reasons for a zero, and
they need opposite responses:

- **`intentionally_zero`** - another key already carries that production, so
  scoring both would double-count (IR-15). Example: FanDuel NBA `ftm` and `two_pm`
  against `pts`. Reported as **info**: no action needed.
- **`not_audited`** - no source was ever retrieved for the value. Example: the
  seven `dst_*` keys in both NFL tables (L-04), and FanDuel NHL `plus_minus`
  (IR-10). Reported as **warning**, because the published total is wrong by an
  unknown amount.

`check_scoring_coverage` takes the `ScoringTable` so it can tell them apart. Called
without one it falls back to a single blunt warning, and the review action tells
the caller to pass the table.

## Representation overlaps

`scoring.REPRESENTATION_SETS` declares the five stat families where one real-world
event satisfies two scoring keys - a hit is also a single/double/triple/homer, a
shot on goal is also a goal, a strikeout is also an out. Scoring both counts the
production twice, which inflates FPTS *silently*: the total still looks plausible.

`scoring.representation_audit()` and `check_representation_double_count()` run on
every configuration at every run and raise a **critical** finding if any shipped
table scores two members of a set simultaneously. `tests/test_quality.py` asserts
all 11 shipped tables are clean, so a new table cannot be added with an overlap by
accident.

This caught a real defect: DraftKings NHL was scoring a goal under both `g` and
`sog` (IR-14).

## "No findings" is not the same as "never checked"

`check_representation_double_count("curling", "draftkings")` used to emit nothing,
because there is no scoring table for curling and therefore no audit rows. A report
that reads *clean* for a configuration that was never examined is worse than one
that reads *unknown*. It now emits a warning naming every shipped configuration and
saying plainly that the requested one has had **no invariant checked at all**.

The same rule applies to freshness: a provenance row that looks like a network fetch
but records no `fetched_at` cannot be shown to be fresh, so it is reported rather
than silently skipped. Static scoring-table provenance carries `audit_date` and no
`url`, and is correctly out of scope for a check about fetch times.

## Endpoint failures are grouped by URL

A retried endpoint fails once per attempt. Emitting one critical finding per attempt
made a single dead endpoint look like two separate defects, which sends a reviewer
looking for a second problem that does not exist. Findings are now grouped by URL
with the attempt count preserved in the message, and every distinct error for that
URL is listed.

The review action is explicit about the sandbox case: if there is no outbound
network this is *expected*, and the stage must be reported `unavailable` - never
guessed (L-02).

## Cross-source identity

`check_cross_source_identity(primary, secondary, report)` flags entities present in
the projection source but absent from the official feed. `primary` is the official
feed; `secondary` is the source being reconciled.

This exists because of a class of error observed on RotoGrinders' own public NFL
grid on 2026-09-22, where a row was published for **Frank Gore** against Buffalo.
Gore's NFL career ended years earlier, so a row like that is either an identity
collision in the projection database or a stale roster join. Comparing against the
league's own feed surfaces it without RGENGY having to assert anything about who is
retired - which it is not in a position to do.

Name comparison normalises case, punctuation and generational suffixes
(`Jr`, `Sr`, `II`, `III`, `IV`), so "Josh Allen Jr." does not create a phantom
mismatch against "Josh Allen".

## Where the gates run

```python
quality.check_zero_projection(players, site, report)
quality.check_duplicate_ids(players, report)
quality.check_implausible_values(players, sport, report)
quality.check_ownership_normalisation(players, report)
quality.check_scoring_coverage(players, coefficients, report, scoring_table=table)
quality.check_representation_double_count(sport, site, report)
quality.check_stale_provenance(prov, report)
quality.check_endpoint_failures(result.fetch_summary, report)
```

The report is attached to the `RunResult`, serialised into every artefact, and
drives `overall_status`. `rgengy verify` writes the endpoint half of it to
`verification.json`.
