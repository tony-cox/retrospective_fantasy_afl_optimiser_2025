from __future__ import annotations

import json
from pathlib import Path

import pytest

from retro_fantasy.io import load_rounds_from_json


def test_load_rounds_from_json_num_rounds_filters_to_first_n(tmp_path: Path) -> None:
    p = tmp_path / "rounds.json"
    p.write_text(
        json.dumps(
            [
                {"number": 1, "max_trades": 2, "counted_onfield_players": 22},
                {"number": 2, "max_trades": 1, "counted_onfield_players": 22},
                {"number": 3, "max_trades": 0, "counted_onfield_players": 18},
            ]
        ),
        encoding="utf-8",
    )

    rounds = load_rounds_from_json(p, num_rounds=2)
    assert list(sorted(rounds)) == [1, 2]


def test_load_rounds_from_json_num_rounds_less_than_1_raises(tmp_path: Path) -> None:
    p = tmp_path / "rounds.json"
    p.write_text(json.dumps([{"number": 1, "max_trades": 2, "counted_onfield_players": 22}]), encoding="utf-8")

    with pytest.raises(ValueError):
        load_rounds_from_json(p, num_rounds=0)
