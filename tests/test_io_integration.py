from __future__ import annotations

import json
from pathlib import Path

import pytest

from retro_fantasy.data import Position
from retro_fantasy.io import load_players_from_json, read_position_updates_csv


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_read_position_updates_csv_parses_and_sorts_and_skips_blanks(tmp_path: Path) -> None:
    csv_path = tmp_path / "position_updates.csv"
    _write_text(
        csv_path,
        "player,initial_position,add_position,round\n"
        "A B,FWD,MID,6\n"
        "A B,FWD,DEF,12\n"
        "\n"
        ",,,\n",
    )

    updates = read_position_updates_csv(csv_path)
    assert updates["A B"] == [(6, Position.MID), (12, Position.DEF)]


def test_load_players_from_json_applies_position_updates_by_round(tmp_path: Path) -> None:
    players_json = [
        {
            "id": 1,
            "first_name": "A",
            "last_name": "B",
            "squad_id": 1,
            "original_positions": [4],
            "stats": {
                "prices": {"1": 100, "6": 120, "12": 140},
                "scores": {"1": 10, "6": 12, "12": 14},
            },
        }
    ]

    json_path = tmp_path / "players_final.json"
    json_path.write_text(json.dumps(players_json), encoding="utf-8")

    updates_csv = tmp_path / "position_updates.csv"
    _write_text(
        updates_csv,
        "player,initial_position,add_position,round\n"
        "A B,FWD,MID,6\n"
        "A B,FWD,DEF,12\n",
    )

    players = load_players_from_json(
        json_path,
        position_updates_csv=updates_csv,
    )

    p1 = players[1]
    assert p1.get_round(1).eligible_positions == frozenset({Position.FWD})
    assert p1.get_round(6).eligible_positions == frozenset({Position.FWD, Position.MID})
    assert p1.get_round(12).eligible_positions == frozenset({Position.FWD, Position.MID, Position.DEF})


def test_load_players_from_json_raises_on_unmatched_update_names(tmp_path: Path) -> None:
    players_json = [
        {
            "id": 1,
            "first_name": "A",
            "last_name": "B",
            "original_positions": [4],
            "stats": {"prices": {"1": 100}, "scores": {"1": 10}},
        }
    ]
    json_path = tmp_path / "players_final.json"
    json_path.write_text(json.dumps(players_json), encoding="utf-8")

    updates_csv = tmp_path / "position_updates.csv"
    _write_text(
        updates_csv,
        "player,initial_position,add_position,round\n"
        "NOT PRESENT,FWD,MID,6\n",
    )

    with pytest.raises(ValueError) as ei:
        load_players_from_json(json_path, position_updates_csv=updates_csv)

    assert "NOT PRESENT" in str(ei.value)
