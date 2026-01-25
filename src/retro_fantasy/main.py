from __future__ import annotations

from pathlib import Path
from typing import Dict

from retro_fantasy.data import Player
from retro_fantasy.io import load_players_from_json


def load_players(
    *,
    players_json_path: str | Path,
    position_updates_csv_path: str | Path,
) -> Dict[int, Player]:
    """Load player data for the optimiser."""

    return load_players_from_json(
        players_json_path,
        position_updates_csv=position_updates_csv_path,
    )
