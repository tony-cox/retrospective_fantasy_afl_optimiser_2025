from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from retro_fantasy.data import Player
from retro_fantasy.io import load_players_from_json, load_players_from_json_with_warnings


def load_players(
    *,
    players_json_path: str | Path,
    position_updates_csv_path: str | Path,
    strict_update_name_matching: bool = True,
) -> Tuple[Dict[int, Player], list[str]]:
    """Load player data for the optimiser.

    Returns
    -------
    (players, missing_position_update_names)
    """

    if strict_update_name_matching:
        players = load_players_from_json(
            players_json_path,
            position_updates_csv=position_updates_csv_path,
            strict_update_name_matching=True,
        )
        return players, []

    return load_players_from_json_with_warnings(
        players_json_path,
        position_updates_csv=position_updates_csv_path,
    )
