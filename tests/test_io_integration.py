from __future__ import annotations

import json
from pathlib import Path

import pytest

from retro_fantasy.data import Position
from retro_fantasy.io import load_players_from_json, read_position_update_csv


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_read_position_update_csv_parses_and_skips_blanks(tmp_path: Path) -> None:
    csv_path = tmp_path / "position_update_round_6.csv"
    _write_text(
        csv_path,
        "player,initial_position,add_position\n"
        "A B,FWD,MID\n"
        "\n"
        ",,\n",
    )

    updates = read_position_update_csv(csv_path)
    assert updates == {"A B": Position.MID}


def test_load_players_from_json_applies_round_updates(tmp_path: Path) -> None:
    # Minimal JSON resembling players_final.json
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
        },
        {
            "id": 2,
            "first_name": "C",
            "last_name": "D",
            "squad_id": 2,
            "original_positions": [1],
            "stats": {
                "prices": {"1": 200, "6": 220, "12": 240},
                "scores": {"1": 20, "6": 22, "12": 24},
            },
        },
    ]

    json_path = tmp_path / "players_final.json"
    json_path.write_text(json.dumps(players_json), encoding="utf-8")

    r6_csv = tmp_path / "position_update_round_6.csv"
    _write_text(r6_csv, "player,initial_position,add_position\nA B,FWD,MID\n")

    r12_csv = tmp_path / "position_update_round_12.csv"
    _write_text(r12_csv, "player,initial_position,add_position\nC D,DEF,MID\n")

    players = load_players_from_json(
        json_path,
        position_update_round_6_csv=r6_csv,
        position_update_round_12_csv=r12_csv,
    )

    p1 = players[1]
    assert p1.get_round(1).eligible_positions == frozenset({Position.FWD})
    assert p1.get_round(6).eligible_positions == frozenset({Position.FWD, Position.MID})
    assert p1.get_round(12).eligible_positions == frozenset({Position.FWD, Position.MID})

    p2 = players[2]
    assert p2.get_round(1).eligible_positions == frozenset({Position.DEF})
    assert p2.get_round(6).eligible_positions == frozenset({Position.DEF})
    assert p2.get_round(12).eligible_positions == frozenset({Position.DEF, Position.MID})


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

    r6_csv = tmp_path / "position_update_round_6.csv"
    _write_text(r6_csv, "player,initial_position,add_position\nNOT PRESENT,FWD,MID\n")

    with pytest.raises(ValueError) as ei:
        load_players_from_json(json_path, position_update_round_6_csv=r6_csv)

    assert "NOT PRESENT" in str(ei.value)
