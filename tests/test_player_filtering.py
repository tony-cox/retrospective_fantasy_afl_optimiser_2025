from __future__ import annotations

import json
from pathlib import Path

from retro_fantasy.io import load_players_from_json


def test_load_players_from_json_squad_id_filter_filters_players(tmp_path: Path) -> None:
    # Minimal JSON: 2 players in different squads.
    players_json = tmp_path / "players.json"
    players_json.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "first_name": "A",
                    "last_name": "One",
                    "squad_id": 40,
                    "original_positions": [1],
                    "stats": {"prices": {"1": 100}, "scores": {"1": 10}},
                },
                {
                    "id": 2,
                    "first_name": "B",
                    "last_name": "Two",
                    "squad_id": 130,
                    "original_positions": [1],
                    "stats": {"prices": {"1": 100}, "scores": {"1": 5}},
                },
            ]
        ),
        encoding="utf-8",
    )

    # Empty updates CSV not needed.
    players = load_players_from_json(players_json, squad_id_filter=frozenset({40}))

    assert set(players.keys()) == {1}
    assert players[1].squad_id == 40
