"""Projected ownership (pOWN).

What RotoGrinders does
----------------------
RotoGrinders publishes a pOWN% column on every projection grid and documents how
THE BAT X ownership projections are built
(https://rotogrinders.com/grids/the-bat-ownership-projections-beta-faq-3771773,
retrieved 2026-09-22):

* gradient-boosted trees (XGBoost) trained on **historical DraftKings ownership
  data** plus several hundred explanatory variables;
* tailored to DraftKings mid-stakes multi-entry tournaments (the $15 Relay
  Throw) on the main slate;
* fully automated - "there is no direct manual component";
* known weakness: rain/postponement risk is not fully accounted for;
* refreshes on the same five-minute loop as the projections.

What RGENGY can honestly do
---------------------------
Historical per-contest ownership is **not** available from any free official
feed, so the trained-model approach cannot be reproduced.  Instead RGENGY
implements a *choice model*: a softmax over player value.  This is a standard,
transparent formulation and it has one free parameter, ``beta``, which is:

* set to a documented default (``DEFAULT_BETA``) that is **explicitly
  uncalibrated** - flagged as IR-13;
* fit-able by :func:`calibrate_beta` the moment real ownership data is supplied
  (for example the ownership published by an operator after a contest settles).

The output is always labelled with its calibration status so nobody mistakes an
uncalibrated number for a measured one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

#: Softmax sensitivity.  RGENGY default, NOT fitted to data (IR-13).
#: beta is expressed per unit of ``value`` (FPTS per $1000 of salary).
DEFAULT_BETA = 0.35

#: Ownership is capped so a single player can never be projected at 100%.
MAX_POWN = 0.95


@dataclass(frozen=True)
class OwnershipModel:
    """A configured, and possibly calibrated, ownership model."""

    beta: float
    calibrated: bool
    n_calibration_points: int
    value_key: str
    rmse: Optional[float] = None
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "beta": self.beta,
            "calibrated": self.calibrated,
            "n_calibration_points": self.n_calibration_points,
            "value_key": self.value_key,
            "rmse": self.rmse,
            "note": self.note or (
                "beta is an uncalibrated RGENGY default; pOWN values from this model "
                "must not be compared directly to RotoGrinders' trained pOWN"
                if not self.calibrated else
                f"beta fitted by grid search on {self.n_calibration_points} observed ownership points"
            ),
        }


def default_model(value_key: str = "value") -> OwnershipModel:
    return OwnershipModel(beta=DEFAULT_BETA, calibrated=False,
                          n_calibration_points=0, value_key=value_key)


def _softmax(values: Sequence[float], beta: float) -> List[float]:
    if not values:
        return []
    scaled = [beta * v for v in values]
    m = max(scaled)
    exps = [math.exp(s - m) for s in scaled]
    total = sum(exps)
    if total <= 0:
        return [1.0 / len(values)] * len(values)
    return [e / total for e in exps]


def project_ownership(values: Sequence[float], model: Optional[OwnershipModel] = None,
                      weights: Optional[Sequence[float]] = None) -> List[float]:
    """Project ownership shares that sum to 1.0 (capped at ``MAX_POWN``).

    ``values`` is the per-player ``value`` used by the choice model - by default
    FPTS per $1000 of salary, because that is the quantity DFS players actually
    sort on.  ``weights`` optionally scales a player's share to represent a
    smaller slate field or a known site bias; it defaults to uniform.
    """
    model = model or default_model()
    n = len(values)
    if n == 0:
        return []
    if n == 1:
        # A one-player "slate" cannot sum to 1.0 without breaching the cap, and
        # claiming 100% ownership of the field for a single player is the exact
        # error MAX_POWN exists to prevent.  The cap wins over normalisation.
        return [MAX_POWN]
    w = list(weights) if weights else [1.0] * n
    if len(w) != n:
        raise ValueError("weights must align with values")
    shares = _softmax(list(values), model.beta)
    shares = [s * wi for s, wi in zip(shares, w)]
    total = sum(shares)
    if total <= 0:
        shares = [1.0 / n] * n
        total = 1.0
    out = [s / total for s in shares]
    return _apply_cap(out)


def _apply_cap(shares: List[float], cap: float = MAX_POWN,
               max_rounds: int = 64) -> List[float]:
    """Redistribute any share above ``cap`` to the players still below it.

    Capping and then re-normalising by the new total does NOT work: dividing
    every share by a sum that the cap pushed below 1.0 scales them all back up,
    so the capped player ends up above the cap again.  With a dominant value the
    previous implementation returned 1.0 - i.e. 100% projected ownership for one
    player, which is exactly what MAX_POWN exists to forbid, and it also
    corrupted ``leverage`` and the simulated field built from pOWN.

    This is water-filling: pin the over-cap players, then spread the freed mass
    over the rest in proportion to their shares, repeating because spreading can
    push another player over the cap.  It terminates because each round pins at
    least one more player, and it preserves both invariants - nothing exceeds
    the cap, and the shares still sum to 1.0 whenever at least one player is
    left free to absorb the mass.
    """
    out = list(shares)
    n = len(out)
    if n == 0:
        return out
    pinned: set = set()
    for _ in range(max_rounds):
        over = [i for i in range(n) if i not in pinned and out[i] > cap + 1e-12]
        if not over:
            break
        for i in over:
            out[i] = cap
            pinned.add(i)
        free = [i for i in range(n) if i not in pinned]
        if not free:
            break                                   # everyone is at the cap; 1.0 is unreachable
        budget = max(0.0, 1.0 - cap * len(pinned))
        denom = sum(out[i] for i in free)
        if denom <= 0 or budget <= 0:
            each = budget / len(free) if budget > 0 else 0.0
            for i in free:
                out[i] = each
            break
        factor = budget / denom
        for i in free:
            out[i] *= factor
    rounded = [round(o, 6) for o in out]
    # Rounding each share independently leaves a residual of up to n*5e-7, which
    # is far inside the 0.02 normalisation tolerance but sloppy for an audit
    # artefact.  Park it on the largest share that is not at the cap, so the
    # published shares sum to exactly 1.0 without ever breaching MAX_POWN.
    residual = round(1.0 - sum(rounded), 6)
    if residual and abs(residual) <= 1e-4:
        room = [i for i in range(len(rounded)) if rounded[i] + residual <= cap + 1e-12]
        if room:
            target = max(room, key=lambda i: (rounded[i], -i))
            rounded[target] = round(rounded[target] + residual, 6)
    return rounded


def calibrate_beta(values: Sequence[float], observed: Sequence[float],
                   grid: Optional[Iterable[float]] = None,
                   value_key: str = "value") -> OwnershipModel:
    """Fit ``beta`` to observed ownership by 1-D grid search (least squares).

    Deliberately simple and fully deterministic: no optimiser dependency, no
    random restarts, reproducible to the last digit.  Returns a model marked
    ``calibrated=True`` together with the achieved RMSE.
    """
    if len(values) != len(observed):
        raise ValueError("values and observed must be the same length")
    if len(values) < 3:
        raise ValueError("need at least 3 observations to fit beta")
    grid = list(grid) if grid is not None else [round(0.02 * i, 4) for i in range(0, 251)]
    best_beta, best_rmse = None, None
    for beta in grid:
        model = OwnershipModel(beta=beta, calibrated=False, n_calibration_points=0,
                               value_key=value_key)
        pred = project_ownership(values, model)
        rmse = math.sqrt(sum((p - o) ** 2 for p, o in zip(pred, observed)) / len(observed))
        if best_rmse is None or rmse < best_rmse:
            best_beta, best_rmse = beta, rmse
    return OwnershipModel(beta=best_beta, calibrated=True,
                          n_calibration_points=len(observed), value_key=value_key,
                          rmse=round(best_rmse, 6))


def leverage(pown: float, projected_fpts: float, field_avg_fpts: float,
             field_size: int) -> float:
    """Value share minus ownership share - RGENGY's own ``LEV`` analogue.

    RotoGrinders publishes a ``LEV`` column (verified on the public MLB grid,
    2026-09-22, where it was 9 for every one of the six free rows) but does not
    publish its formula, so RGENGY does not claim to reproduce it.  This is
    RGENGY's own definition and is labelled as such everywhere it is surfaced.

    Both terms are SHARES of the field, so the subtraction is dimensionally
    coherent and the result sums to roughly zero across a slate:

        value share       = (projected_fpts / field_avg_fpts) / field_size
        ownership share   = pown

    Positive means the player is projected to a larger share of slate production
    than the share of the field that owns him - the classic GPP leverage read.
    An earlier revision of this function subtracted ``pown`` from an unnormalised
    ``projected/field_avg`` ratio, which mixed a ratio with a probability and was
    not interpretable; ``field_size`` is now required so the ratio can be turned
    into a share.
    """
    if field_avg_fpts <= 0 or field_size <= 0:
        return 0.0
    value_share = (projected_fpts / field_avg_fpts) / field_size
    return round(value_share - pown, 6)


def smash_probability(fpts_mean: float, fpts_sd: Optional[float], threshold: float) -> Optional[float]:
    """P(player exceeds ``threshold`` fantasy points).

    RotoGrinders publishes a SMASH column (verified 2026-09-22) without a
    published definition.  RGENGY defines it as the upper-tail probability at a
    caller-supplied threshold, using a normal approximation.  The threshold is
    never invented here - the caller must supply it.
    """
    if fpts_sd is None or fpts_sd <= 0:
        return None
    z = (threshold - fpts_mean) / fpts_sd
    return round(0.5 * math.erfc(z / math.sqrt(2.0)), 4)
