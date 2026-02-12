"""Domain objects for prospective season generation.

This package creates prospective seasons (scores + prices) from projections.
The intent is to export a JSON structure compatible with the retrospective
solver's `players_final.json` format.

This module contains *pure* domain objects only:
- no file parsing (see :mod:`player_price_generator.io`)
- no simulation logic (see :mod:`player_price_generator.simulate`)
- no pricing logic (see :mod:`player_price_generator.pricing`)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Mapping, Optional

from retro_fantasy.data import Position


@dataclass(frozen=True, slots=True)
class Club:
    """AFL club metadata keyed by its fixture code (e.g. COL, STK)."""

    code: str
    fixture_name: str

    early_bye_round: Optional[int]
    mid_season_bye_round: int


@dataclass(frozen=True, slots=True)
class Fixture:
    """A single match fixture."""

    match_number: int
    round_number: int
    home_club: str
    away_club: str


@dataclass(slots=True)
class ProjectedPlayer:
    """A player's projected scoring distribution inputs (low/high/mid)."""

    name: str
    club_code: str
    positions: FrozenSet[Position]
    price: float

    priced_at: Optional[float] = None

    projection_low: float = 0.0
    projection_high: float = 0.0
    projection_mid: float = 0.0

    simulated_scores_by_round: Dict[int, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProspectiveInputData:
    """Full prospective input dataset used to generate simulated seasons."""

    clubs: Mapping[str, Club]
    fixtures: tuple[Fixture, ...]
    projected_players: tuple[ProjectedPlayer, ...]

    @property
    def rounds(self) -> FrozenSet[int]:
        return frozenset({f.round_number for f in self.fixtures})


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Monte Carlo simulation settings."""

    n_sims: int = 1
    seed: Optional[int] = None


@dataclass(frozen=True, slots=True)
class PricingConfig:
    """Pricing model configuration.

    The true AFL Fantasy price-change mechanics are nuanced; we'll start with a
    configurable approximation.
    """

    salary_cap: float
    magic_number: float


# Aliases for algorithm outputs. We'll likely replace these with richer
# dataclasses later.
SimulatedScores = Dict[str, Dict[int, float]]  # player_name -> round -> score
RoundPrices = Dict[str, Dict[int, float]]  # player_name -> round -> price
