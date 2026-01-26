"""I/O utilities for building the optimiser's domain objects.

This module owns:
- file format knowledge (JSON, CSV)
- parsing and validation
- construction of domain objects from :mod:`retro_fantasy.data`

Keeping this separate from :mod:`retro_fantasy.data` makes the core model easy
to test and reuse.
"""

from __future__ import annotations

import csv
import difflib
import json
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, Mapping, Optional, cast

from retro_fantasy.data import Player, PlayerRoundInfo, Position, Round, TeamStructureRules


# Pragmatic default mapping for AFL Fantasy position codes found in the JSON.
# If you discover a different mapping, override it when calling the loader.
DEFAULT_POSITION_CODE_MAP: Mapping[int, Position] = {
    1: Position.DEF,
    2: Position.MID,
    3: Position.RUC,
    4: Position.FWD,
}


def parse_position_str(value: str) -> Position:
    """Parse position strings from CSV/UX sources.

    Accepts a couple of common variants:
    - RUCK -> RUC
    - case-insensitive
    """

    v = value.strip().upper()
    if v == "RUCK":
        v = "RUC"

    try:
        return Position(v)
    except ValueError as e:
        raise ValueError(f"Unknown position string: {value!r}") from e


def parse_positions_from_codes(
    codes: Iterable[int],
    *,
    code_map: Mapping[int, Position] = DEFAULT_POSITION_CODE_MAP,
) -> FrozenSet[Position]:
    """Convert numeric position codes to a FrozenSet of :class:`~retro_fantasy.data.Position`."""

    positions: set[Position] = set()
    for c in codes:
        try:
            positions.add(code_map[int(c)])
        except KeyError as e:
            raise ValueError(f"Unknown position code {c}. Provide a code_map override.") from e
    return frozenset(positions)


def read_position_updates_csv(path: Path) -> Dict[str, list[tuple[int, Position]]]:
    """Read position_updates.csv and return name -> list of (effective_round, added_position).

    The file has columns: player, initial_position, add_position, round
    """

    updates: Dict[str, list[tuple[int, Position]]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader: csv.DictReader[str] = csv.DictReader(f)
        for row in reader:
            row_map = cast(Mapping[str, Optional[str]], row)
            name = (row_map.get("player") or "").strip()
            add_pos = (row_map.get("add_position") or "").strip()
            round_str = (row_map.get("round") or "").strip()

            if not name or not add_pos or not round_str:
                continue

            effective_round = int(round_str)
            if effective_round < 1:
                raise ValueError(f"Invalid effective round {effective_round} for player {name!r}")

            updates.setdefault(name, []).append((effective_round, parse_position_str(add_pos)))

    # Keep deterministic order.
    for name in updates:
        updates[name].sort(key=lambda x: x[0])

    return updates


def validate_update_names(
    *,
    update_names: Iterable[str],
    json_names: Iterable[str],
    source_label: str,
    close_match_cutoff: float = 0.6,
    close_match_n: int = 3,
) -> None:
    """Validate that all update CSV player names exist in the JSON player set.

    Raises
    ------
    ValueError
        If any update names aren't present in ``json_names``.
    """

    json_names_set = set(json_names)
    missing_names = sorted(set(update_names) - json_names_set)
    if not missing_names:
        return

    hints: list[str] = []
    for name in missing_names:
        candidates = difflib.get_close_matches(
            name,
            sorted(json_names_set),
            n=close_match_n,
            cutoff=close_match_cutoff,
        )
        if candidates:
            hints.append(f"- {name}  (did you mean: {', '.join(candidates)})")
        else:
            hints.append(f"- {name}")

    raise ValueError(
        "One or more player names in the position update CSV did not match any player name "
        "in players_final.json. Fix spelling/casing so they match exactly.\n"
        f"Source: {source_label}\n"
        "Unmatched names:\n"
        + "\n".join(hints)
    )


def load_players_from_json(
    path: str | Path,
    *,
    position_code_map: Mapping[int, Position] = DEFAULT_POSITION_CODE_MAP,
    include_round0: bool = False,
    position_updates_csv: str | Path | None = None,
    squad_id_filter: FrozenSet[int] | None = None,
) -> Dict[int, Player]:
    """Load players from ``players_final.json`` and apply round-based eligibility updates.

    Parameters
    ----------
    squad_id_filter:
        If provided, only players whose ``squad_id`` is in this set are loaded.
        This is applied during the single pass over the JSON records, so excluded
        players are never instantiated.
    """

    path = Path(path)
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    position_updates: Dict[str, list[tuple[int, Position]]] = {}
    if position_updates_csv is not None:
        position_updates = read_position_updates_csv(Path(position_updates_csv))

    players: Dict[int, Player] = {}

    for rec in raw:
        squad_id = rec.get("squad_id")
        if squad_id_filter is not None:
            if squad_id is None or int(squad_id) not in squad_id_filter:
                continue

        pid = int(rec["id"])

        original = parse_positions_from_codes(
            rec.get("original_positions", []) or [],
            code_map=position_code_map,
        )

        # Some records may have empty original_positions; fall back to 'positions' so
        # we never construct PlayerRoundInfo objects with an empty eligibility set.
        base_positions = original
        if not base_positions:
            base_positions = parse_positions_from_codes(
                rec.get("positions", []) or [],
                code_map=position_code_map,
            )

        player = Player(
            player_id=pid,
            first_name=str(rec.get("first_name", "")),
            last_name=str(rec.get("last_name", "")),
            squad_id=squad_id,
            original_positions=base_positions,
        )

        # Look up added positions by player name (as written in the CSVs).
        player_updates = position_updates.get(player.name, [])

        stats: Mapping[str, Any] = rec.get("stats", {}) or {}
        prices: Mapping[str, Any] = stats.get("prices", {}) or {}
        scores: Mapping[str, Any] = stats.get("scores", {}) or {}

        all_round_keys = set(prices.keys()) | set(scores.keys())

        for rk in all_round_keys:
            r = int(rk)
            if r == 0 and not include_round0:
                continue

            eligible_set: set[Position] = set(base_positions)
            for effective_round, added_pos in player_updates:
                if r >= effective_round:
                    eligible_set.add(added_pos)

            if not eligible_set:
                raise ValueError(
                    f"Player {player.name} (id={player.player_id}) has no eligible positions "
                    f"for round {r}. Check original_positions/positions in JSON and CSV updates."
                )

            price = float(prices.get(rk, 0.0) or 0.0)
            score = float(scores.get(rk, 0.0) or 0.0)

            player.by_round[r] = PlayerRoundInfo(
                round_number=r,
                score=score,
                price=price,
                eligible_positions=frozenset(eligible_set),
            )

        players[pid] = player

    # Validate position update CSV names.
    # If we're loading the full dataset, validate against all JSON names.
    # If we're loading a filtered subset (e.g. a couple of squads for a small model),
    # it's expected that the update CSV contains many names outside the subset, so
    # we intentionally skip this validation.
    if position_updates_csv is not None and squad_id_filter is None:
        json_names: set[str] = {p.name for p in players.values()}
        validate_update_names(
            update_names=position_updates.keys(),
            json_names=json_names,
            source_label="position_updates_csv",
        )

    return players


def load_team_rules_from_json(path: str | Path) -> TeamStructureRules:
    """Load :class:`~retro_fantasy.data.TeamStructureRules` from JSON."""

    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))

    salary_cap = float(raw["salary_cap"])
    utility_bench_count = int(raw.get("utility_bench_count", 0))

    def _parse_counts(obj: Mapping[str, Any], field_name: str) -> Dict[Position, int]:
        counts: Dict[Position, int] = {}
        for pos in Position.__members__.values():
            try:
                counts[pos] = int(obj[pos.value])
            except KeyError as e:
                raise ValueError(f"{field_name} missing key {pos.value!r}") from e
        return counts

    on_field_required = _parse_counts(raw["on_field_required"], "on_field_required")
    bench_required = _parse_counts(raw["bench_required"], "bench_required")

    return TeamStructureRules(
        on_field_required=on_field_required,
        bench_required=bench_required,
        salary_cap=salary_cap,
        utility_bench_count=utility_bench_count,
    )


def load_rounds_from_json(path: str | Path, *, num_rounds: int | None = None) -> Dict[int, Round]:
    """Load rounds from JSON.

    Expected format: a list of objects like:
        {"number": 1, "max_trades": 2, "counted_onfield_players": 22}

    Parameters
    ----------
    num_rounds:
        If provided, only rounds 1..num_rounds (inclusive) are returned.
        Rounds are assumed to start at 1.
    """

    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("rounds.json must be a JSON list")

    if num_rounds is not None and num_rounds < 1:
        raise ValueError("num_rounds must be >= 1")

    rounds: Dict[int, Round] = {}
    for rec in raw:
        if not isinstance(rec, dict):
            continue
        number = int(rec["number"])
        if num_rounds is not None and number > num_rounds:
            continue

        r = Round(
            number=number,
            max_trades=int(rec.get("max_trades", 2)),
            counted_onfield_players=int(rec.get("counted_onfield_players", 22)),
        )
        rounds[r.number] = r

    if not rounds:
        raise ValueError("No rounds loaded from rounds.json")

    # If filtering, ensure we didn't accidentally exclude round 1.
    if num_rounds is not None and 1 not in rounds:
        raise ValueError("rounds.json did not contain round 1, but rounds are required to start from 1")

    return rounds
