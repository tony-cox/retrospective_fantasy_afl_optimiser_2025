"""Domain data model for the Retro Fantasy AFL optimiser.

This module is intentionally *pure*: it defines the core enums and dataclasses
used throughout the project, with no dependency on input file formats.

I/O, parsing, and dataset construction live in :mod:`retro_fantasy.io`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from typing import Dict, FrozenSet, Iterable, Mapping, Optional, Sequence


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


@dataclass
class ModelInputData:
    """Top-level container for all model input data.

    This class is frequently queried by the MILP formulation. To keep the
    formulation code clean (and avoid repeatedly building the same derived
    lists), we provide a set of memoised helpers.
    """

    players: Dict[int, Player]
    rounds: Dict[int, Round]
    team_rules: TeamStructureRules

    def __post_init__(self) -> None:
        if not self.players:
            raise ValueError("ModelInputData.players cannot be empty")
        if not self.rounds:
            raise ValueError("ModelInputData.rounds cannot be empty")

    # --- Core index sets (memoised) ---

    @cached_property
    def player_ids(self) -> Sequence[int]:
        """Sorted player IDs (P)."""

        return tuple(sorted(self.players))

    @cached_property
    def round_numbers(self) -> Sequence[int]:
        """Sorted round numbers (R)."""

        return tuple(sorted(self.rounds))

    @cached_property
    def rounds_excluding_1(self) -> Sequence[int]:
        """Sorted round numbers excluding round 1 (R \\ {1})."""

        return tuple(r for r in self.round_numbers if r != 1)

    @cached_property
    def positions(self) -> Sequence[Position]:
        """The position set K = {DEF, MID, RUC, FWD}."""

        return tuple(Position)

    # --- Common parameter lookups ---

    def score(self, player_id: int, round_number: int) -> float:
        """Known score s[p,r].

        If the player has no data for that round, assume 0.
        """

        player = self.players[player_id]
        info = player.by_round.get(round_number)
        if info is None:
            return 0.0
        return info.score

    def price(self, player_id: int, round_number: int) -> float:
        """Known price c[p,r].

        If the player has no price for that round (i.e. no data), treat them as
        prohibitively expensive by returning the full salary cap.
        """

        player = self.players[player_id]
        info = player.by_round.get(round_number)
        if info is None:
            return float(self.salary_cap)
        return info.price

    def eligible_positions(self, player_id: int, round_number: int) -> FrozenSet[Position]:
        """Eligible positions for player p in round r.

        If the player has no round data, fall back to their original positions.
        This keeps eligibility non-empty and matches how eligibility updates are
        defined (positions are only ever added).
        """

        player = self.players[player_id]
        info = player.by_round.get(round_number)
        if info is None:
            if player.original_positions:
                return player.original_positions
            # Extremely defensive: should never happen because loader enforces non-empty.
            return frozenset({Position.DEF})
        return info.eligible_positions

    def is_eligible(self, player_id: int, position: Position, round_number: int) -> bool:
        """Binary eligibility e[p,k,r] as a bool."""

        return position in self.eligible_positions(player_id, round_number)

    # --- Team structure / round-level rule accessors ---

    @property
    def salary_cap(self) -> float:
        return self.team_rules.salary_cap

    @property
    def utility_bench_count(self) -> int:
        return self.team_rules.utility_bench_count

    def on_field_required(self, position: Position) -> int:
        return int(self.team_rules.on_field_required[position])

    def bench_required(self, position: Position) -> int:
        return int(self.team_rules.bench_required[position])

    def max_trades(self, round_number: int) -> int:
        return int(self.rounds[round_number].max_trades)

    def counted_onfield_players(self, round_number: int) -> int:
        return int(self.rounds[round_number].counted_onfield_players)

    # --- Derived index tuples used frequently by the formulation ---

    @cached_property
    def idx_player_round(self) -> Sequence[tuple[int, int]]:
        """All (p,r) pairs for p in P, r in R."""

        return tuple((p, r) for p in self.player_ids for r in self.round_numbers)

    @cached_property
    def idx_player_round_excluding_1(self) -> Sequence[tuple[int, int]]:
        """All (p,r) pairs for p in P, r in R \\ {1}."""

        return tuple((p, r) for p in self.player_ids for r in self.rounds_excluding_1)

    @cached_property
    def idx_player_position_round(self) -> Sequence[tuple[int, Position, int]]:
        """All (p,k,r) triples for p in P, k in K, r in R."""

        return tuple((p, k, r) for p in self.player_ids for k in self.positions for r in self.round_numbers)

    @cached_property
    def idx_round(self) -> Sequence[int]:
        """All round numbers r in R (sorted)."""

        return self.round_numbers

    @cached_property
    def idx_round_excluding_1(self) -> Sequence[int]:
        """All round numbers r in R \\ {1} (sorted)."""

        return self.rounds_excluding_1

    @cached_property
    def eligibility_map(self) -> Mapping[tuple[int, Position, int], bool]:
        """Eligibility map e[p,k,r] as a boolean mapping.

        Keys are (player_id, position, round_number).
        """

        return {
            (p, k, r): self.is_eligible(p, k, r)
            for p in self.player_ids
            for k in self.positions
            for r in self.round_numbers
        }

    @property
    def on_field_size(self) -> int:
        """Total number of on-field slots implied by rules (typically 22)."""

        return sum(self.team_rules.on_field_required.values())

    @property
    def bench_size(self) -> int:
        """Total number of bench slots implied by rules (bench positions + utility)."""

        return sum(self.team_rules.bench_required.values()) + self.team_rules.utility_bench_count

    @property
    def squad_size(self) -> int:
        """Total squad size implied by rules (on-field + bench)."""

        return self.team_rules.squad_size

    def iter_round_numbers(self) -> Iterable[int]:
        # Backwards-compatible generator-style API.
        return (r for r in self.round_numbers)

    @cached_property
    def idx_eligible_player_position_round(self) -> Sequence[tuple[int, Position, int]]:
        """All (p,k,r) triples where player p is eligible for position k in round r."""

        # Using eligibility_map avoids repeated PlayerRoundInfo lookups.
        # We iterate the existing full index but filter down to eligible only.
        return tuple(
            (p, k, r)
            for (p, k, r) in self.idx_player_position_round
            if self.eligibility_map[(p, k, r)]
        )

