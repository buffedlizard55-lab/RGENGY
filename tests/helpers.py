"""Shared helpers for the RGENGY test suite.

Kept deliberately tiny: the tests are the specification, so anything that hides
behind a helper is harder to review.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

FIXTURES = REPO / "tests" / "fixtures"


def load_fixture(name: str) -> Dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


RG_MLB_GRID = "rg_public_mlb_grid_2026-09-22.json"


def make_player(player_id: str, name: str, positions: List[str], salary: float,
                site: str = "draftkings", fpts: Optional[float] = None,
                team: str = "T1", opp: str = "T2",
                projected: Optional[Dict[str, float]] = None,
                floor: Optional[float] = None, ceil: Optional[float] = None,
                pown: Optional[float] = None) -> Any:
    """Build a :class:`rgengy.models.Player` without importing it at module scope."""
    from rgengy.models import Player

    value = fpts if fpts is not None else 0.0
    return Player(
        sport="mlb", player_id=player_id, name=name, team=team, opp=opp,
        positions=list(positions), salary=salary, site=site,
        stats={}, projected=projected or {},
        fpts={site: value},
        floor=floor if floor is not None else value * 0.3,
        ceil=ceil if ceil is not None else value * 2.2,
        pown=pown,
    )


def mlb_pool(n_per_position: int = 3, site: str = "draftkings",
             salary_cap: int = 50000) -> List[Any]:
    """A pool with enough players at every position to fill a legal MLB roster.

    Salaries are spread across the cap so the cap actually binds, and values are
    deliberately NOT monotonic in salary so a greedy solver would fail.
    """
    positions = ["P", "C", "1B", "2B", "3B", "SS", "OF"]
    pool: List[Any] = []
    i = 0
    for pos in positions:
        for j in range(n_per_position):
            i += 1
            salary = 2500 + 700 * ((i * 7) % 9)
            # value deliberately inversely related to salary for some players
            fpts = round(6.0 + ((i * 13) % 17) * 1.3 - (salary / 5000.0), 2)
            pool.append(make_player(f"p{i}", f"Player {i} ({pos})", [pos], float(salary),
                                    site=site, fpts=max(0.5, fpts)))
    return pool
