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


def read_position_update_csv(path: Path) -> Dict[str, Position]:
    """Read a position update CSV and return name -> added position."""

    updates: Dict[str, Position] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader: csv.DictReader[str] = csv.DictReader(f)
        for row in reader:
            row_map = cast(Mapping[str, Optional[str]], row)
            name = (row_map.get("player") or "").strip()
            add_pos = (row_map.get("add_position") or "").strip()
            if not name or not add_pos:
                continue
            updates[name] = parse_position_str(add_pos)
    return updates


def validate_update_names(
    *,
    update_map: Mapping[str, Position],
    json_names: Iterable[str],
    source_label: str,
    close_match_cutoff: float = 0.6,
    close_match_n: int = 3,
) -> None:
    """Validate that all CSV update names exist in the JSON player set.

    Raises
    ------
    ValueError
        If any names in ``update_map`` aren't present in ``json_names``.
    """

    json_names_set = set(json_names)
    missing_names = sorted(set(update_map.keys()) - json_names_set)
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
    position_update_round_6_csv: str | Path | None = None,
    position_update_round_12_csv: str | Path | None = None,
) -> Dict[int, Player]:
    """Load players from ``players_final.json`` and apply round-based eligibility updates.

    Rules
    -----
    - Players start in round 1 with ``original_positions`` from the JSON.
    - Eligibility is never removed.
    - If a player appears in the round-6 update CSV, their ``add_position`` is
      added from round 6 onward.
    - If a player appears in the round-12 update CSV, their ``add_position`` is
      added from round 12 onward.

    Defensive validation
    --------------------
    We validate that every player name listed in the update CSVs exists in the
    JSON data. If not, we raise with close-match suggestions.
    """

    path = Path(path)
    raw: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    # Optional position updates.
    round6_updates: Dict[str, Position] = {}
    round12_updates: Dict[str, Position] = {}

    if position_update_round_6_csv is not None:
        round6_updates = read_position_update_csv(Path(position_update_round_6_csv))
    if position_update_round_12_csv is not None:
        round12_updates = read_position_update_csv(Path(position_update_round_12_csv))

    # Defensive check: ensure every name in the CSVs appears in the JSON.
    json_names: set[str] = {
        f"{rec.get('first_name', '')} {rec.get('last_name', '')}".strip() for rec in raw
    }

    validate_update_names(
        update_map=round6_updates,
        json_names=json_names,
        source_label="position_update_round_6_csv",
    )
    validate_update_names(
        update_map=round12_updates,
        json_names=json_names,
        source_label="position_update_round_12_csv",
    )

    players: Dict[int, Player] = {}

    for rec in raw:
        pid = int(rec["id"])

        original = parse_positions_from_codes(
            rec.get("original_positions", []) or [],
            code_map=position_code_map,
        )

        player = Player(
            player_id=pid,
            first_name=str(rec.get("first_name", "")),
            last_name=str(rec.get("last_name", "")),
            squad_id=rec.get("squad_id"),
            original_positions=original,
        )

        # Look up added positions by player name (as written in the CSVs).
        add_pos_round6 = round6_updates.get(player.name)
        add_pos_round12 = round12_updates.get(player.name)

        stats: Mapping[str, Any] = rec.get("stats", {}) or {}
        prices: Mapping[str, Any] = stats.get("prices", {}) or {}
        scores: Mapping[str, Any] = stats.get("scores", {}) or {}

        all_round_keys = set(prices.keys()) | set(scores.keys())

        for rk in all_round_keys:
            r = int(rk)
            if r == 0 and not include_round0:
                continue

            eligible_set: set[Position] = set(original)
            if add_pos_round6 is not None and r >= 6:
                eligible_set.add(add_pos_round6)
            if add_pos_round12 is not None and r >= 12:
                eligible_set.add(add_pos_round12)

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
