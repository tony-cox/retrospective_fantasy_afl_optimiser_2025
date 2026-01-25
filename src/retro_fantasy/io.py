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

from retro_fantasy.data import Player, PlayerRoundInfo, Position


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
    update_map: Mapping[str, Position],
    json_names: Iterable[str],
    source_label: str,
    close_match_cutoff: float = 0.6,
    close_match_n: int = 3,
    raise_on_missing: bool = True,
) -> list[str]:
    """Validate that all CSV update names exist in the JSON player set.

    Parameters
    ----------
    raise_on_missing:
        If True (default), raise ValueError when any names are unmatched.
        If False, return the list of unmatched names.

    Returns
    -------
    list[str]
        The unmatched names (empty if all matched).
    """

    json_names_set = set(json_names)
    missing_names = sorted(set(update_map.keys()) - json_names_set)
    if not missing_names:
        return []

    if not raise_on_missing:
        return missing_names

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
    strict_update_name_matching: bool = True,
) -> Dict[int, Player]:
    """Load players from ``players_final.json`` and apply round-based eligibility updates.

    Eligibility update file
    -----------------------
    If ``position_updates_csv`` is provided, it is expected to be a CSV with columns:
    ``player, initial_position, add_position, round``.

    Each row indicates that from ``round`` onward, that player's eligible positions
    include both (a) whatever they already had, and (b) the ``add_position``.

    Defensive validation
    --------------------
    We validate that every player name listed in the update CSV exists in the
    JSON data. If not, we raise with close-match suggestions.

    Parameters
    ----------
    strict_update_name_matching:
        If True (default), raise an error if any player names in the update CSVs
        do not match a player name in the JSON.
        If False, print a warning and ignore those update rows.
    """

    path = Path(path)
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    position_updates: Dict[str, list[tuple[int, Position]]] = {}
    if position_updates_csv is not None:
        position_updates = read_position_updates_csv(Path(position_updates_csv))

    json_names: set[str] = {
        f"{rec.get('first_name', '')} {rec.get('last_name', '')}".strip() for rec in raw
    }

    missing_updates = validate_update_names(
        update_map={name: Position.DEF for name in position_updates.keys()},
        json_names=json_names,
        source_label="position_updates_csv",
        raise_on_missing=strict_update_name_matching,
    )

    if not strict_update_name_matching:
        for n in missing_updates:
            position_updates.pop(n, None)

    players: Dict[int, Player] = {}

    for rec in raw:
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
            squad_id=rec.get("squad_id"),
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

    return players


def load_players_from_json_with_warnings(
    path: str | Path,
    *,
    position_code_map: Mapping[int, Position] = DEFAULT_POSITION_CODE_MAP,
    include_round0: bool = False,
    position_updates_csv: str | Path | None = None,
) -> tuple[Dict[int, Player], list[str]]:
    """Like :func:`load_players_from_json`, but returns unmatched-name list.

    This always runs in non-strict mode (unmatched update rows are ignored),
    but returns the unmatched names so callers (e.g. ``run.py``) can log them.
    """

    path = Path(path)
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    position_updates: Dict[str, list[tuple[int, Position]]] = {}
    if position_updates_csv is not None:
        position_updates = read_position_updates_csv(Path(position_updates_csv))

    json_names: set[str] = {
        f"{rec.get('first_name', '')} {rec.get('last_name', '')}".strip() for rec in raw
    }

    # validate_update_names expects Mapping[str, Position]; we just need its key checking.
    fake_map = {name: Position.DEF for name in position_updates.keys()}
    missing = validate_update_names(
        update_map=fake_map,
        json_names=json_names,
        source_label="position_updates_csv",
        raise_on_missing=False,
    )

    players = load_players_from_json(
        path,
        position_code_map=position_code_map,
        include_round0=include_round0,
        position_updates_csv=position_updates_csv,
        strict_update_name_matching=False,
    )

    return players, missing
