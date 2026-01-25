import pytest

from retro_fantasy.data import (
    ModelInputData,
    Player,
    PlayerRoundInfo,
    Position,
    Round,
    TeamStructureRules,
)


def _zero_counts_by_position() -> dict[Position, int]:
    # Using __members__.values() keeps type-checkers happy for str-backed Enums.
    return {pos: 0 for pos in Position.__members__.values()}


def test_round_raises_when_number_is_less_than_1() -> None:
    with pytest.raises(ValueError):
        Round(number=0, max_trades=2, counted_onfield_players=22)


def test_round_raises_when_max_trades_is_negative() -> None:
    with pytest.raises(ValueError):
        Round(number=1, max_trades=-1, counted_onfield_players=22)


def test_round_raises_when_counted_onfield_players_is_negative() -> None:
    with pytest.raises(ValueError):
        Round(number=1, max_trades=2, counted_onfield_players=-1)


def test_player_round_info_raises_when_price_is_negative() -> None:
    with pytest.raises(ValueError):
        PlayerRoundInfo(round_number=1, score=100, price=-1, eligible_positions=frozenset({Position.MID}))


def test_player_round_info_raises_when_eligible_positions_is_empty() -> None:
    with pytest.raises(ValueError):
        PlayerRoundInfo(round_number=1, score=100, price=500, eligible_positions=frozenset())


def test_player_raises_when_player_id_is_not_positive() -> None:
    with pytest.raises(ValueError):
        Player(player_id=0, first_name="A", last_name="B")


def test_player_name_property_returns_first_and_last_name() -> None:
    p = Player(player_id=1, first_name="Nick", last_name="Daicos")
    assert p.name == "Nick Daicos"


def test_player_get_round_returns_round_info_when_present() -> None:
    p = Player(player_id=1, first_name="Nick", last_name="Daicos")
    p.by_round[1] = PlayerRoundInfo(
        round_number=1,
        score=10,
        price=100,
        eligible_positions=frozenset({Position.MID}),
    )
    assert p.get_round(1).score == 10


def test_player_get_round_raises_key_error_when_round_missing() -> None:
    p = Player(player_id=1, first_name="Nick", last_name="Daicos")
    with pytest.raises(KeyError):
        p.get_round(2)


def test_team_structure_rules_squad_size_counts_utility_only_when_all_other_counts_zero() -> None:
    base_on = _zero_counts_by_position()
    base_bench = _zero_counts_by_position()

    rules = TeamStructureRules(
        on_field_required=base_on,
        bench_required=base_bench,
        salary_cap=100.0,
        utility_bench_count=1,
    )

    assert rules.squad_size == 1


def test_team_structure_rules_raises_when_salary_cap_is_negative() -> None:
    base_on = _zero_counts_by_position()
    base_bench = _zero_counts_by_position()

    with pytest.raises(ValueError):
        TeamStructureRules(
            on_field_required=base_on,
            bench_required=base_bench,
            salary_cap=-1,
            utility_bench_count=1,
        )


def test_team_structure_rules_raises_when_on_field_required_missing_a_position() -> None:
    base_bench = _zero_counts_by_position()
    bad_on = {Position.DEF: 1, Position.MID: 1, Position.RUC: 1}

    with pytest.raises(ValueError):
        TeamStructureRules(
            on_field_required=bad_on,
            bench_required=base_bench,
            salary_cap=100,
            utility_bench_count=1,
        )


def test_model_input_data_raises_when_players_empty() -> None:
    rules = TeamStructureRules(
        on_field_required=_zero_counts_by_position(),
        bench_required=_zero_counts_by_position(),
        salary_cap=100,
        utility_bench_count=0,
    )

    with pytest.raises(ValueError):
        ModelInputData(players={}, rounds={1: Round(1, 2, 22)}, team_rules=rules)


def test_model_input_data_raises_when_rounds_empty() -> None:
    rules = TeamStructureRules(
        on_field_required=_zero_counts_by_position(),
        bench_required=_zero_counts_by_position(),
        salary_cap=100,
        utility_bench_count=0,
    )

    with pytest.raises(ValueError):
        ModelInputData(players={1: Player(1, "A", "B")}, rounds={}, team_rules=rules)


def test_model_input_data_iter_round_numbers_returns_sorted_round_keys() -> None:
    rules = TeamStructureRules(
        on_field_required=_zero_counts_by_position(),
        bench_required=_zero_counts_by_position(),
        salary_cap=100,
        utility_bench_count=0,
    )

    mid = ModelInputData(
        players={1: Player(1, "A", "B")},
        rounds={2: Round(2, 2, 22), 1: Round(1, 2, 22)},
        team_rules=rules,
    )

    assert list(mid.iter_round_numbers()) == [1, 2]
