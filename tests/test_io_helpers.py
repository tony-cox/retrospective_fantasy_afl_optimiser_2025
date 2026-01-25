from __future__ import annotations

import pytest

from retro_fantasy.data import Position
from retro_fantasy.io import (
    parse_position_str,
    parse_positions_from_codes,
    validate_update_names,
)


def test_parse_position_str_variants() -> None:
    assert parse_position_str("def") == Position.DEF
    assert parse_position_str("MID") == Position.MID
    assert parse_position_str("ruck") == Position.RUC
    assert parse_position_str("RUC") == Position.RUC

    with pytest.raises(ValueError):
        parse_position_str("WING")


def test_parse_positions_from_codes_default_map() -> None:
    assert parse_positions_from_codes([1, 2]) == frozenset({Position.DEF, Position.MID})

    with pytest.raises(ValueError):
        parse_positions_from_codes([999])


def test_validate_update_names_does_not_raise_when_all_names_present() -> None:
    validate_update_names(
        update_names={"A B"},
        json_names={"A B", "C D"},
        source_label="position_updates_csv",
    )


def test_validate_update_names_raises_and_includes_source_and_name() -> None:
    with pytest.raises(ValueError) as ei:
        validate_update_names(
            update_names={"A B"},
            json_names={"C D"},
            source_label="position_updates_csv",
            close_match_cutoff=0.0,
            close_match_n=1,
        )

    msg = str(ei.value)
    assert "Source: position_updates_csv" in msg
    assert "A B" in msg
