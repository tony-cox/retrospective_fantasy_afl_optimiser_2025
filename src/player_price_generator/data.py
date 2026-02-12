"""Domain objects for prospective season generation.

Notes
-----
These are deliberately *pure* data structures.

- No file parsing (see :mod:`player_price_generator.io`).
- No simulation logic (see :mod:`player_price_generator.simulate`).
- No pricing logic (see :mod:`player_price_generator.pricing`).

Keeping these simple makes it easy to test and reuse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, Mapping, MutableMapping, Optional

from retro_fantasy.data import Position


@dataclass(frozen=True, slots=True)
class PlayerMeta:
    """Metadata required to emit a `players_final.json` compatible record."""

    player_id: int
    first_name: str
    last_name: str
    squad_id: Optional[int]
    original_positions: FrozenSet[Position]

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass(frozen=True, slots=True)
class ProjectionInput:
    """Projection parameters for a single player.

    This is intentionally underspecified. We'll evolve this based on what
    the actual projection files contain.

    The minimal requirement for Monte Carlo is a per-round distribution.
    A common first cut is a per-round mean and standard deviation.
    """

    player_id: int
    # round -> mean score
    mean_by_round: Mapping[int, float]
    # round -> standard deviation (optional; can fall back to a global or heuristic)
    stdev_by_round: Mapping[int, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProjectionDataset:
    """All input projections and metadata needed to produce an output season."""

    players: Mapping[int, PlayerMeta]
    projections: Mapping[int, ProjectionInput]
    rounds: FrozenSet[int]


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Monte Carlo simulation settings."""

    n_sims: int = 1
    seed: Optional[int] = None

    # Placeholder for future config:
    # - distribution: Literal["normal", "student_t", ...]
    # - opponent_adjustments: bool


@dataclass(frozen=True, slots=True)
class PricingConfig:
    """Pricing model configuration.

    The true AFL Fantasy price-change mechanics are nuanced; we'll start with a
    configurable approximation.
    """

    salary_cap: float

    # Placeholder for future config:
    # - rolling_window: int
    # - magic_number: float
    # - floor_price: float


# Aliases for algorithm outputs. We'll likely replace these with richer
# dataclasses later.
SimulatedScores = Dict[int, Dict[int, float]]  # player_id -> round -> score
RoundPrices = Dict[int, Dict[int, float]]  # player_id -> round -> price
