from __future__ import annotations

import pulp
import pytest

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import (
    _create_bank_balance_decision_variables,
    _create_captain_decision_variables,
    _create_positional_selection_decision_variables,
    _create_scored_decision_variables,
    _create_squad_selection_decision_variables,
    _create_trade_indicator_decision_variables,
    create_decision_variables,
)


def _zero_counts_by_position() -> dict[Position, int]:
    return {pos: 0 for pos in Position.__members__.values()}


def _make_minimal_player(player_id: int, rounds: list[int]) -> Player:
    p = Player(player_id=player_id, first_name=f"P{player_id}", last_name="X")
    for r in rounds:
        p.by_round[r] = PlayerRoundInfo(
            round_number=r,
            score=0.0,
            price=0.0,
            eligible_positions=frozenset({Position.DEF}),
        )
    return p


def _make_minimal_input_data(round_numbers: list[int], player_ids: list[int]) -> ModelInputData:
    rules = TeamStructureRules(
        on_field_required=_zero_counts_by_position(),
        bench_required=_zero_counts_by_position(),
        salary_cap=100.0,
        utility_bench_count=0,
    )
    rounds = {r: Round(number=r, max_trades=2, counted_onfield_players=22) for r in round_numbers}
    players = {pid: _make_minimal_player(pid, round_numbers) for pid in player_ids}
    return ModelInputData(players=players, rounds=rounds, team_rules=rules)


def test_create_squad_selection_decision_variables_keys_and_bounds() -> None:
    data = _make_minimal_input_data(round_numbers=[1, 2], player_ids=[1, 2])
    problem = pulp.LpProblem("t", pulp.LpMaximize)

    x = _create_squad_selection_decision_variables(problem, data)

    assert set(x.keys()) == {(1, 1), (1, 2), (2, 1), (2, 2)}

    v = x[(1, 1)]
    assert v.lowBound == 0
    assert v.upBound == 1
    assert v.cat in (pulp.LpBinary, pulp.LpInteger)


def test_create_trade_indicator_decision_variables_keys() -> None:
    data = _make_minimal_input_data(round_numbers=[1, 2, 3], player_ids=[1])
    problem = pulp.LpProblem("t", pulp.LpMaximize)

    traded_in, traded_out = _create_trade_indicator_decision_variables(problem, data)

    assert set(traded_in.keys()) == {(1, 2), (1, 3)}
    assert set(traded_out.keys()) == {(1, 2), (1, 3)}


def test_create_bank_balance_decision_variables_keys_and_domain() -> None:
    data = _make_minimal_input_data(round_numbers=[1, 2], player_ids=[1])
    problem = pulp.LpProblem("t", pulp.LpMaximize)

    bank = _create_bank_balance_decision_variables(problem, data)

    assert set(bank.keys()) == {1, 2}
    assert bank[1].cat == pulp.LpContinuous
    assert bank[1].lowBound == 0


def test_create_positional_selection_decision_variables_keys() -> None:
    data = _make_minimal_input_data(round_numbers=[1, 2], player_ids=[1])
    problem = pulp.LpProblem("t", pulp.LpMaximize)

    y_on, y_bench, y_util = _create_positional_selection_decision_variables(problem, data)

    # Minimal player is DEF-only in both rounds.
    expected_pkr = {(1, Position.DEF, 1), (1, Position.DEF, 2)}
    assert set(y_on.keys()) == expected_pkr
    assert set(y_bench.keys()) == expected_pkr

    assert set(y_util.keys()) == {(1, 1), (1, 2)}


def test_create_scored_decision_variables_keys() -> None:
    data = _make_minimal_input_data(round_numbers=[1, 2], player_ids=[1, 2])
    problem = pulp.LpProblem("t", pulp.LpMaximize)

    scored = _create_scored_decision_variables(problem, data)

    assert set(scored.keys()) == {(1, 1), (1, 2), (2, 1), (2, 2)}


def test_create_captain_decision_variables_keys() -> None:
    data = _make_minimal_input_data(round_numbers=[1, 2], player_ids=[1, 2])
    problem = pulp.LpProblem("t", pulp.LpMaximize)

    captain = _create_captain_decision_variables(problem, data)

    assert set(captain.keys()) == {(1, 1), (1, 2), (2, 1), (2, 2)}


def test_create_decision_variables_orchestrator_smoke() -> None:
    data = _make_minimal_input_data(round_numbers=[1, 2], player_ids=[1])
    problem = pulp.LpProblem("t", pulp.LpMaximize)

    dvs = create_decision_variables(problem, data)

    # Smoke checks: orchestrator wires fields into the container
    assert len(dvs.x_selected) == 2
    assert len(dvs.bank) == 2

    # Positional vars are eligibility-filtered (player is DEF-only)
    assert len(dvs.y_onfield) == 2
    assert len(dvs.y_bench) == 2


def test_model_input_data_empty_players_raises() -> None:
    rules = TeamStructureRules(
        on_field_required=_zero_counts_by_position(),
        bench_required=_zero_counts_by_position(),
        salary_cap=0.0,
        utility_bench_count=0,
    )
    with pytest.raises(ValueError, match="players cannot be empty"):
        ModelInputData(players={}, rounds={1: Round(number=1, max_trades=2, counted_onfield_players=22)}, team_rules=rules)


def test_model_input_data_empty_rounds_raises() -> None:
    rules = TeamStructureRules(
        on_field_required=_zero_counts_by_position(),
        bench_required=_zero_counts_by_position(),
        salary_cap=0.0,
        utility_bench_count=0,
    )
    p = _make_minimal_player(1, [1])
    with pytest.raises(ValueError, match="rounds cannot be empty"):
        ModelInputData(players={1: p}, rounds={}, team_rules=rules)

