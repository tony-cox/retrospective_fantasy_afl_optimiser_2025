"""Domain data model for the Retro Fantasy AFL optimiser.

This module is intentionally *pure*: it defines the core enums and dataclasses
used throughout the project, with no dependency on input file formats.

I/O, parsing, and dataset construction live in :mod:`retro_fantasy.io`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, Iterable, Mapping, Optional


class Position(str, Enum):
    """Playing positions used by the optimiser."""

    DEF = "DEF"
    MID = "MID"
    RUC = "RUC"
    FWD = "FWD"


@dataclass(frozen=True, slots=True)
class Round:
    """Round-level parameters."""

    number: int
    max_trades: int
    counted_onfield_players: int

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("Round.number must be >= 1")
        if self.max_trades < 0:
            raise ValueError("Round.max_trades must be >= 0")
        if self.counted_onfield_players < 0:
            raise ValueError("Round.counted_onfield_players must be >= 0")


@dataclass(frozen=True, slots=True)
class PlayerRoundInfo:
    """All player information that varies by round."""

    round_number: int
    score: float
    price: float
    eligible_positions: FrozenSet[Position]

    def __post_init__(self) -> None:
        if self.round_number < 0:
            # allow 0 if a datasource uses 0 (some sources include pre-season)
            raise ValueError("PlayerRoundInfo.round_number must be >= 0")
        if self.price < 0:
            raise ValueError("PlayerRoundInfo.price must be >= 0")
        if not self.eligible_positions:
            raise ValueError("PlayerRoundInfo.eligible_positions must be non-empty")


@dataclass(slots=True)
class Player:
    """A player with round-varying information."""

    player_id: int
    first_name: str
    last_name: str

    # Round number -> info
    by_round: Dict[int, PlayerRoundInfo] = field(default_factory=dict)

    # Optional metadata
    squad_id: Optional[int] = None

    # Positions the player has from the start of the season.
    original_positions: FrozenSet[Position] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.player_id <= 0:
            raise ValueError("Player.player_id must be a positive integer")

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_round(self, round_number: int) -> PlayerRoundInfo:
        try:
            return self.by_round[round_number]
        except KeyError as e:
            raise KeyError(f"No data for player {self.player_id} in round {round_number}") from e


@dataclass(frozen=True, slots=True)
class TeamStructureRules:
    """Season/global team structure rules."""

    on_field_required: Mapping[Position, int]
    bench_required: Mapping[Position, int]
    salary_cap: float
    utility_bench_count: int

    def __post_init__(self) -> None:
        if self.salary_cap < 0:
            raise ValueError("TeamStructureRules.salary_cap must be >= 0")
        if self.utility_bench_count < 0:
            raise ValueError("TeamStructureRules.utility_bench_count must be >= 0")

        for mapping_name, mapping in (
            ("on_field_required", self.on_field_required),
            ("bench_required", self.bench_required),
        ):
            all_positions: set[Position] = set(Position.__members__.values())
            missing: set[Position] = all_positions - set(mapping)
            if missing:
                raise ValueError(f"{mapping_name} missing positions: {sorted(p.value for p in missing)}")
            for pos, count in mapping.items():
                if count < 0:
                    raise ValueError(f"{mapping_name}[{pos.value}] must be >= 0")

    @property
    def squad_size(self) -> int:
        return sum(self.on_field_required.values()) + sum(self.bench_required.values()) + self.utility_bench_count


@dataclass(slots=True)
class ModelInputData:
    """Top-level container for all model input data."""

    players: Dict[int, Player]
    rounds: Dict[int, Round]
    team_rules: TeamStructureRules

    def __post_init__(self) -> None:
        if not self.players:
            raise ValueError("ModelInputData.players cannot be empty")
        if not self.rounds:
            raise ValueError("ModelInputData.rounds cannot be empty")

    def iter_round_numbers(self) -> Iterable[int]:
        return (r for r in sorted(self.rounds))
