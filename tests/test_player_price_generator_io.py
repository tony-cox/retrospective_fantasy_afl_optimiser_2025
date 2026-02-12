from __future__ import annotations

import csv
from pathlib import Path

from player_price_generator.io import (
    _parse_currency,
    load_club_byes_csv,
    load_fixtures_csv,
    load_player_projections_csv,
    load_prospective_input_data,
)
from retro_fantasy.data import Position


def _write_csv(path: Path, *, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def test_parse_currency_parses_dollar_and_commas() -> None:
    assert _parse_currency("$230,000") == 230000.0


def test_load_club_byes_csv_parses_minus_one_as_none(tmp_path: Path) -> None:
    p = tmp_path / "club_byes.csv"
    _write_csv(
        p,
        header=["club", "fixture_name", "ealy_bye_rd", "mid_season_by_rd"],
        rows=[
            ["COL", "Collingwood", "2", "14"],
            ["ESS", "Essendon", "-1", "15"],
        ],
    )

    clubs = load_club_byes_csv(p)

    assert clubs["COL"].fixture_name == "Collingwood"
    assert clubs["COL"].early_bye_round == 2
    assert clubs["ESS"].early_bye_round is None
    assert clubs["ESS"].mid_season_bye_round == 15


def test_load_fixtures_csv_sorts_by_round_then_match_number(tmp_path: Path) -> None:
    p = tmp_path / "fixtures.csv"
    _write_csv(
        p,
        header=["Match Number", "Round Number", "home_club", "away_club"],
        rows=[
            ["2", "1", "COL", "ESS"],
            ["1", "0", "ESS", "COL"],
            ["1", "1", "COL", "ADE"],
        ],
    )

    fixtures = load_fixtures_csv(p)
    assert [(f.round_number, f.match_number) for f in fixtures] == [(0, 1), (1, 1), (1, 2)]


def test_load_player_projections_csv_parses_positions_and_currency(tmp_path: Path) -> None:
    p = tmp_path / "player_projections.csv"
    _write_csv(
        p,
        header=[
            "PLAYER",
            "CLUB",
            "POSITION",
            "PRICE",
            "PRICED AT",
            "2025 AVERAGE",
            "2025 GAMES",
            "early_bye",
            "mid_bye",
            "has_early_bye?",
            "discount",
            "discount_on_most_recent_year",
            "my_projection_low",
            "my_projection_high",
            "my_projection_middle",
        ],
        rows=[
            [
                "Zeke Uwland",
                "GCS",
                "DEF/MID",
                "$346,000",
                "33",
                "0",
                "0",
                "3",
                "12",
                "TRUE",
                "30.00%",
                "30.00%",
                "65",
                "82",
                "74",
            ]
        ],
    )

    players = load_player_projections_csv(p)
    assert len(players) == 1

    pl = players[0]
    assert pl.name == "Zeke Uwland"
    assert pl.club_code == "GCS"
    assert pl.positions == frozenset({Position.DEF, Position.MID})
    assert pl.price == 346000.0
    assert pl.projection_low == 65.0
    assert pl.projection_high == 82.0
    assert pl.projection_mid == 74.0


def test_load_prospective_input_data_integrates_all_three_sources(tmp_path: Path) -> None:
    cb = tmp_path / "club_byes.csv"
    fx = tmp_path / "fixtures.csv"
    pp = tmp_path / "player_projections.csv"

    _write_csv(
        cb,
        header=["club", "fixture_name", "ealy_bye_rd", "mid_season_by_rd"],
        rows=[["COL", "Collingwood", "2", "14"]],
    )
    _write_csv(
        fx,
        header=["Match Number", "Round Number", "home_club", "away_club"],
        rows=[["1", "1", "COL", "ESS"]],
    )
    _write_csv(
        pp,
        header=[
            "PLAYER",
            "CLUB",
            "POSITION",
            "PRICE",
            "PRICED AT",
            "2025 AVERAGE",
            "2025 GAMES",
            "early_bye",
            "mid_bye",
            "has_early_bye?",
            "discount",
            "discount_on_most_recent_year",
            "my_projection_low",
            "my_projection_high",
            "my_projection_middle",
        ],
        rows=[["A Player", "COL", "MID", "$230,000", "21.9", "0", "0", "2", "14", "TRUE", "", "", "50", "60", "55"]],
    )

    data = load_prospective_input_data(
        club_byes_csv=cb,
        fixtures_csv=fx,
        player_projections_csv=pp,
    )

    assert "COL" in data.clubs
    assert len(data.fixtures) == 1
    assert len(data.projected_players) == 1
    assert data.rounds == frozenset({1})
