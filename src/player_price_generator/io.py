"""Input loading helpers for :mod:`player_price_generator`.

This module owns file-format knowledge (currently CSV) for the prospective
season generator.

Input files (repo /data)
------------------------
- club_byes.csv
- fixtures.csv
- player_projections.csv

Only minimal validation is performed here; deeper validation belongs in the
calling code once we know which invariants we want to enforce.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Optional, cast

from retro_fantasy.io import parse_position_str

from .data import Club, Fixture, ProjectedPlayer, ProspectiveInputData


def _none_if_minus_one(value: str) -> Optional[int]:
    v = value.strip()
    if v == "":
        return None
    i = int(v)
    return None if i == -1 else i


def _parse_currency(value: str) -> float:
    """Parse currency-like fields such as "$230,000" to float."""

    v = value.strip().replace("$", "").replace(",", "")
    if v == "":
        return 0.0
    return float(v)


def _parse_optional_float(value: str) -> Optional[float]:
    v = value.strip()
    if v == "":
        return None
    return float(v)


def _parse_positions_field(value: str) -> frozenset:
    """Parse POSITION field from projections, e.g. 'DEF/MID'."""

    parts = [p.strip() for p in value.split("/") if p.strip()]
    if not parts:
        raise ValueError("POSITION field was empty")
    return frozenset(parse_position_str(p) for p in parts)


def load_club_byes_csv(path: str | Path) -> Dict[str, Club]:
    path = Path(path)
    clubs: Dict[str, Club] = {}

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            row = cast(Dict[str, str], raw_row)
            club_code = (row.get("club") or "").strip()
            fixture_name = (row.get("fixture_name") or "").strip()
            if not club_code:
                continue

            early_bye = _none_if_minus_one(row.get("ealy_bye_rd") or "")
            mid_bye_str = (row.get("mid_season_by_rd") or "").strip()
            if mid_bye_str == "":
                raise ValueError(f"mid_season_by_rd missing for club {club_code}")

            clubs[club_code] = Club(
                code=club_code,
                fixture_name=fixture_name,
                early_bye_round=early_bye,
                mid_season_bye_round=int(mid_bye_str),
            )

    if not clubs:
        raise ValueError("No clubs loaded from club_byes.csv")

    return clubs


def load_fixtures_csv(path: str | Path) -> tuple[Fixture, ...]:
    path = Path(path)
    fixtures: list[Fixture] = []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            row = cast(Dict[str, str], raw_row)
            match_number = int((row.get("Match Number") or "0").strip())
            round_number = int((row.get("Round Number") or "0").strip())
            home = (row.get("home_club") or "").strip()
            away = (row.get("away_club") or "").strip()
            if not home or not away:
                continue

            fixtures.append(
                Fixture(
                    match_number=match_number,
                    round_number=round_number,
                    home_club=home,
                    away_club=away,
                )
            )

    if not fixtures:
        raise ValueError("No fixtures loaded from fixtures.csv")

    fixtures.sort(key=lambda x: (x.round_number, x.match_number))
    return tuple(fixtures)


def load_player_projections_csv(path: str | Path) -> tuple[ProjectedPlayer, ...]:
    path = Path(path)
    players: list[ProjectedPlayer] = []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            row = cast(Dict[str, str], raw_row)
            name = (row.get("PLAYER") or "").strip()
            club = (row.get("CLUB") or "").strip()
            pos = (row.get("POSITION") or "").strip()

            if not name or not club or not pos:
                continue

            players.append(
                ProjectedPlayer(
                    name=name,
                    club_code=club,
                    positions=_parse_positions_field(pos),
                    price=_parse_currency(row.get("PRICE") or ""),
                    priced_at=_parse_optional_float(row.get("PRICED AT") or ""),
                    projection_low=float((row.get("my_projection_low") or "0").strip() or 0.0),
                    projection_high=float((row.get("my_projection_high") or "0").strip() or 0.0),
                    projection_mid=float((row.get("my_projection_middle") or "0").strip() or 0.0),
                )
            )

    if not players:
        raise ValueError("No players loaded from player_projections.csv")

    return tuple(players)


def load_prospective_input_data(
    *,
    club_byes_csv: str | Path,
    fixtures_csv: str | Path,
    player_projections_csv: str | Path,
) -> ProspectiveInputData:
    clubs = load_club_byes_csv(club_byes_csv)
    fixtures = load_fixtures_csv(fixtures_csv)
    projected_players = load_player_projections_csv(player_projections_csv)

    return ProspectiveInputData(
        clubs=clubs,
        fixtures=fixtures,
        projected_players=projected_players,
    )
