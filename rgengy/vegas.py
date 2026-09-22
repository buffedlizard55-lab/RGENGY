"""Market mathematics: turning a betting line into expected runs/points.

RotoGrinders' grids publish ``SPREAD``, ``O/U`` and ``TOTAL`` columns and derive
an ``implied team total`` from them.  This module implements that step from
public information.

Three methods are provided, in order of preference:

``moneyline_devig``
    Uses both moneylines.  The vig is removed by normalising implied
    probabilities, the fair win probability is converted to an expected margin
    with a normal-distribution link, and the total is split around that margin.
    Requires a per-sport scoring standard deviation (``SIGMA``).

``spread_total``
    Uses the point spread and the over/under.  Conventional and assumption-free:
    the favourite's implied total is ``total/2 - spread/2`` where ``spread`` is
    the *home* team's spread (negative when the home team is favoured).

``bryant_published``
    A verbatim transcription of the formula RotoGrinders attributes to co-founder
    Riley Bryant in
    https://rotogrinders.com/articles/the-bat-vs-vegas-2016-results-1873096 :

        (TotalPoints / 2) - (Spread * (100 / (AdjustedSpread + 100))) / 2

    RotoGrinders does **not** publish how ``AdjustedSpread`` is derived, so this
    function takes it as an explicit argument and refuses to invent one.  It is
    included so the published formula is reproducible and inspectable, not
    because it is the recommended default.  See IR-02 in
    ``docs/09-irregularities.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Constants.  Everything here is either a published standard or is explicitly
# labelled as an RGENGY assumption that has NOT been validated.
# ---------------------------------------------------------------------------

#: Standard atmosphere (ISA) sea-level air density, kg/m^3.
#: Published value; see https://en.wikipedia.org/wiki/Density_of_air
ISA_AIR_DENSITY_KG_M3 = 1.225

#: Scoring standard deviation used to link a win probability to a point margin.
#: PROVENANCE: RGENGY assumption. These are NOT audited against a dataset and
#: are used only by ``moneyline_devig``. They are exposed here (not buried in a
#: function) so a reviewer can challenge or replace them. FLAGGED as IR-03.
SIGMA: dict = {
    "nfl": 13.5,
    "ncaaf": 18.0,
    "nba": 12.0,
    "wnba": 11.0,
    "mlb": 2.9,
    "nhl": 2.5,
}

#: American-odds conventions.
MONEYLINE_POSITIVE_DIVISOR = 100.0
MONEYLINE_NEGATIVE_DIVISOR = 100.0


@dataclass(frozen=True)
class ImpliedTotals:
    home: float
    away: float
    method: str
    fair_home_win_prob: Optional[float] = None
    expected_margin: Optional[float] = None
    vig_pct: Optional[float] = None
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "home": round(self.home, 3),
            "away": round(self.away, 3),
            "method": self.method,
            "fair_home_win_prob": None if self.fair_home_win_prob is None else round(self.fair_home_win_prob, 4),
            "expected_margin": None if self.expected_margin is None else round(self.expected_margin, 3),
            "vig_pct": None if self.vig_pct is None else round(self.vig_pct, 3),
            "note": self.note,
        }


def american_to_implied(ml: Optional[int]) -> Optional[float]:
    """Convert an American moneyline to an implied probability.

    +150 -> 0.400 ; -200 -> 0.667.  Standard, textbook conversion.
    """
    if ml is None or ml == 0:
        return None
    ml = float(ml)
    if ml > 0:
        return MONEYLINE_POSITIVE_DIVISOR / (ml + MONEYLINE_POSITIVE_DIVISOR)
    return abs(ml) / (abs(ml) + MONEYLINE_NEGATIVE_DIVISOR)


def remove_vig(home_ml: int, away_ml: int) -> Tuple[float, float, float]:
    """Return ``(fair_home_prob, fair_away_prob, vig_pct)``.

    ``vig_pct`` is the overround above 100% before normalisation.
    """
    ph = american_to_implied(home_ml)
    pa = american_to_implied(away_ml)
    if ph is None or pa is None:
        raise ValueError("both moneylines are required to remove vig")
    total = ph + pa
    if total <= 0:
        raise ValueError("implied probabilities must sum to a positive number")
    return ph / total, pa / total, (total - 1.0) * 100.0


@dataclass(frozen=True)
class MarketWinProbability:
    """A team win probability derived from a published betting line.

    ``method`` records *which* line produced it, because the methods carry very
    different assumptions: a de-vigged moneyline needs no distributional
    assumption at all, while a spread-derived probability needs ``SIGMA`` (an
    unaudited RGENGY constant, IR-03).  A caller that does not know which it got
    cannot know how much to trust it.
    """

    prob: float
    side: str
    method: str
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {"prob": round(self.prob, 4), "side": self.side,
                "method": self.method, "note": self.note}


def _norm_cdf(x: float) -> float:
    """Standard normal CDF, pure stdlib."""
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def market_win_probability(sport: str, *, home_ml: Optional[int] = None,
                           away_ml: Optional[int] = None,
                           spread: Optional[float] = None,
                           side: str = "home") -> Optional[MarketWinProbability]:
    """P(``side`` wins) from the market line, or ``None`` when it cannot be derived.

    Preference order:

    1.  **moneyline_devig** - both moneylines are available.  The vig is removed
        by normalising the two implied probabilities.  No distributional
        assumption is required, so this is the strongest evidence available.
    2.  **spread_normal** - only a point spread is available.  The spread is
        treated as the expected margin (``margin = -spread`` for the home team,
        since a negative home spread means the home team is favoured) and
        converted with a normal link using ``SIGMA[sport]``.  ``SIGMA`` is an
        unaudited RGENGY assumption (IR-03), so the returned object says so.

    Returns ``None`` rather than 0.5 when neither is available: a coin flip is a
    number, and publishing one would look like a projection.
    """
    if side not in ("home", "away"):
        raise ValueError(f"side must be 'home' or 'away', got {side!r}")

    if home_ml is not None and away_ml is not None:
        fair_home, fair_away, vig = remove_vig(int(home_ml), int(away_ml))
        prob = fair_home if side == "home" else fair_away
        return MarketWinProbability(
            prob=prob, side=side, method="moneyline_devig",
            note=f"de-vigged from moneylines {home_ml}/{away_ml}; overround was {vig:.2f}%. "
                 f"No distributional assumption is required.")

    if spread is not None:
        sigma = SIGMA.get(sport)
        if not sigma:
            return None
        margin = -float(spread) if side == "home" else float(spread)
        prob = _norm_cdf(margin / sigma)
        return MarketWinProbability(
            prob=prob, side=side, method="spread_normal",
            note=f"derived from spread {spread} with sigma={sigma} for {sport}. "
                 f"SIGMA is an unaudited RGENGY assumption (IR-03), so this probability is "
                 f"weaker evidence than a de-vigged moneyline.")
    return None


def _norm_ppf(p: float) -> float:
    """Inverse standard-normal CDF (probit), pure stdlib.

    Uses the rational approximation published by Peter Acklam
    (https://web.archive.org/web/20151030215612/http://home.online.no/~pjacklam/notes/invnorm/)
    with a maximum absolute error of 1.15e-9, which is far below the precision
    any betting market carries.
    """
    if not (0.0 < p < 1.0):
        raise ValueError(f"probit requires 0 < p < 1, got {p}")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def implied_totals(sport: str, *, total: Optional[float] = None,
                   spread: Optional[float] = None,
                   home_ml: Optional[int] = None,
                   away_ml: Optional[int] = None) -> Optional[ImpliedTotals]:
    """Best available implied team totals for one game.

    ``spread`` is the HOME team's spread (negative = home favoured), matching
    the sign convention ESPN uses in its ``odds[].spread`` field.
    """
    if total is None or total <= 0:
        return None

    if home_ml and away_ml:
        try:
            fair_h, _fair_a, vig = remove_vig(home_ml, away_ml)
            sigma = SIGMA.get(sport)
            if sigma:
                margin = sigma * _norm_ppf(min(max(fair_h, 1e-6), 1 - 1e-6))
                return ImpliedTotals(
                    home=total / 2.0 + margin / 2.0,
                    away=total / 2.0 - margin / 2.0,
                    method="moneyline_devig",
                    fair_home_win_prob=fair_h,
                    expected_margin=margin,
                    vig_pct=vig,
                    note=f"sigma={sigma} is an unaudited RGENGY assumption (IR-03)",
                )
        except (ValueError, ZeroDivisionError):
            pass

    if spread is not None:
        return ImpliedTotals(
            home=total / 2.0 - spread / 2.0,
            away=total / 2.0 + spread / 2.0,
            method="spread_total",
            note="spread is the home team's line; negative = home favoured",
        )

    return ImpliedTotals(
        home=total / 2.0, away=total / 2.0, method="total_only",
        note="no spread or moneyline available; the total is split evenly, which is a "
             "deliberate, documented degradation rather than a guess at an edge",
    )


def bryant_published(total_points: float, spread: float, adjusted_spread: float) -> float:
    """Verbatim transcription of the RotoGrinders-published implied-total formula.

        (TotalPoints / 2) - (Spread * (100 / (AdjustedSpread + 100))) / 2

    Source: https://rotogrinders.com/articles/the-bat-vs-vegas-2016-results-1873096
    (retrieved 2026-09-22), which states the formula is "provided by RotoGrinders
    co-founder Riley Bryant, also used on the RG Lineups Page".

    ``adjusted_spread`` must be supplied by the caller.  RotoGrinders does not
    publish its derivation, so RGENGY will not invent one.
    """
    denom = adjusted_spread + 100.0
    if denom == 0:
        raise ValueError("adjusted_spread must not be -100")
    return (total_points / 2.0) - (spread * (100.0 / denom)) / 2.0


def no_vig_fair_odds(home_ml: int, away_ml: int) -> Tuple[float, float]:
    """De-vigged American odds, returned as ``(home, away)`` in American format."""
    fair_h, fair_a, _vig = remove_vig(home_ml, away_ml)

    def to_american(p: float) -> int:
        if p >= 0.5:
            return int(round(-100.0 * p / (1.0 - p))) if p < 1 else -10000
        return int(round(100.0 * (1.0 - p) / p))

    return to_american(fair_h), to_american(fair_a)


def edge_pct(projected: float, line: float, hit_probability: float) -> float:
    """RotoGrinders' PickLabs 'edge' concept, expressed as a percentage.

    RotoGrinders describes PickLabs as "projecting win probabilities and
    assigning a graded 'edge' for each option"
    (https://rotogrinders.com/articles/introducing-picklabs-the-fastest-and-easiest-way-to-build-slips-for-player-props-dfs-pick-em-4171203).
    On its public pick cards it shows both a hit probability and an edge, e.g.
    "projects to hit 46.04% of the time ... that represents a 3.49% edge"
    (observed on https://rotogrinders.com/ 2026-09-22).

    For a two-way market priced at American odds ``odds``, the fair hit
    probability is ``1 / (1 + decimal - 1)``.  The edge reported by RG is
    consistent with ``(hit_probability - fair_probability)`` expressed in
    percentage points; this function reproduces that relationship and returns
    ``projected hit probability minus the break-even probability implied by the
    price`` in percentage points.
    """
    return round((hit_probability - line) * 100.0, 4)


def breakeven_probability(american_odds: int) -> float:
    """Probability at which a bet at ``american_odds`` has zero expected value."""
    return american_to_implied(american_odds) or 0.0


def expected_value(hit_probability: float, american_odds: int, stake: float = 1.0) -> float:
    """EV of a stake at the given price.  Standard, no assumptions."""
    if american_odds > 0:
        profit = stake * american_odds / 100.0
    else:
        profit = stake * 100.0 / abs(american_odds)
    return hit_probability * profit - (1.0 - hit_probability) * stake
