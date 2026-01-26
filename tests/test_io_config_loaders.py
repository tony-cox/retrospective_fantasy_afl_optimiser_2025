from __future__ import annotations

import json
from pathlib import Path

import pytest

from retro_fantasy.data import Position
from retro_fantasy.io import load_rounds_from_json, load_team_rules_from_json


def test_load_team_rules_from_json_happy_path(tmp_path: Path) -> None:
    p = tmp_path / "team_rules.json"
    p.write_text(
        json.dumps(
            {
                "salary_cap": 100.0,
                "utility_bench_count": 1,
                "on_field_required": {"DEF": 1, "MID": 0, "RUC": 0, "FWD": 0},
                "bench_required": {"DEF": 0, "MID": 0, "RUC": 0, "FWD": 0},
            }
        ),
        encoding="utf-8",
    )

    rules = load_team_rules_from_json(p)
    assert rules.salary_cap == 100.0
    assert rules.utility_bench_count == 1
    assert rules.on_field_required[Position.DEF] == 1


def test_load_team_rules_from_json_missing_position_raises(tmp_path: Path) -> None:
    p = tmp_path / "team_rules.json"
    p.write_text(
        json.dumps(
            {
                "salary_cap": 100.0,
                "utility_bench_count": 0,
                "on_field_required": {"DEF": 1, "MID": 0, "RUC": 0},
                "bench_required": {"DEF": 0, "MID": 0, "RUC": 0, "FWD": 0},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_team_rules_from_json(p)


def test_load_rounds_from_json_happy_path(tmp_path: Path) -> None:
    p = tmp_path / "rounds.json"
    p.write_text(
        json.dumps(
            [
                {"number": 1, "max_trades": 2, "counted_onfield_players": 22},
                {"number": 2, "max_trades": 1, "counted_onfield_players": 18},
            ]
        ),
        encoding="utf-8",
    )

    rounds = load_rounds_from_json(p)
    assert set(rounds) == {1, 2}
    assert rounds[1].max_trades == 2
    assert rounds[2].counted_onfield_players == 18


def test_load_rounds_from_json_non_list_raises(tmp_path: Path) -> None:
    p = tmp_path / "rounds.json"
    p.write_text(json.dumps({"number": 1}), encoding="utf-8")

    with pytest.raises(ValueError):
        load_rounds_from_json(p)


def test_load_rounds_from_json_empty_list_raises(tmp_path: Path) -> None:
    p = tmp_path / "rounds.json"
    p.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        load_rounds_from_json(p)
