from __future__ import annotations

import json
from pathlib import Path

import pytest

from player_price_generator.data import PricingConfig, ProjectedPlayer
from player_price_generator.export import build_players_final_records
from player_price_generator.pricing import generate_round_prices
from retro_fantasy.data import Position
from retro_fantasy.io import load_players_from_json


def test_export_build_players_final_records_minimal_schema() -> None:
    players = {
        "A Player": ProjectedPlayer(
            name="A Player",
            club_code="COL",
            positions=frozenset({Position.DEF, Position.MID}),
            price=100.0,
            projection_low=0.0,
            projection_mid=0.0,
            projection_high=0.0,
        ),
        "B Player": ProjectedPlayer(
            name="B Player",
            club_code="STK",
            positions=frozenset({Position.FWD}),
            price=200.0,
            projection_low=0.0,
            projection_mid=0.0,
            projection_high=0.0,
        ),
    }

    simulated_scores = {
        "A Player": {1: 10.0, 2: 11.0},
        "B Player": {1: 20.0},
    }

    prices = generate_round_prices(
        starting_prices_round_1={"A Player": 100.0, "B Player": 200.0},
        simulated_scores=simulated_scores,
        max_round=2,
        config=PricingConfig(salary_cap=0.0, magic_number=1.0),
    )

    records = build_players_final_records(players=players, simulated_scores=simulated_scores, round_prices=prices)
    assert len(records) == 2

    rec = records[0]
    assert set(rec.keys()) == {"id", "first_name", "last_name", "squad_id", "positions", "original_positions", "stats"}
    assert rec["positions"] == rec["original_positions"]
    assert set(rec["stats"].keys()) == {"scores", "prices"}


def test_export_json_can_be_loaded_by_retro_loader(tmp_path: Path) -> None:
    players_by_name = {
        "John Doe": ProjectedPlayer(
            name="John Doe",
            club_code="COL",
            positions=frozenset({Position.DEF}),
            price=123.0,
            projection_low=0.0,
            projection_mid=0.0,
            projection_high=0.0,
        )
    }

    simulated_scores = {"John Doe": {1: 50.0}}
    prices = generate_round_prices(
        starting_prices_round_1={"John Doe": 123.0},
        simulated_scores=simulated_scores,
        max_round=2,
        config=PricingConfig(salary_cap=0.0, magic_number=1.0),
    )

    records = build_players_final_records(players=players_by_name, simulated_scores=simulated_scores, round_prices=prices)

    out_path = tmp_path / "players_final_min.json"
    out_path.write_text(json.dumps(records), encoding="utf-8")

    loaded = load_players_from_json(out_path, include_round0=False)
    assert len(loaded) == 1
    player = next(iter(loaded.values()))
    assert player.name == "John Doe"
    assert player.original_positions == frozenset({Position.DEF})

    # Loader should see our exported per-round numbers.
    assert player.by_round[1].score == pytest.approx(50.0)
    assert player.by_round[1].price == pytest.approx(123.0)
