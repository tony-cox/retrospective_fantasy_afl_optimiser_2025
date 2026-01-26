from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import (
    _add_maximum_team_changes_per_round_constraints,
    _add_trade_indicator_linking_constraints,
    create_decision_variables,
)


def _rules_minimal(salary_cap: float) -> TeamStructureRules:
    return TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=salary_cap,
        utility_bench_count=0,
    )


def _make_two_round_two_player_data(max_trades_round2: int = 2) -> ModelInputData:
    rules = _rules_minimal(salary_cap=0.0)

    rounds = {
        1: Round(number=1, max_trades=2, counted_onfield_players=1),
        2: Round(number=2, max_trades=max_trades_round2, counted_onfield_players=1),
    }

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))
    p1.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    return ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)


def test_trade_indicator_linking_constraints_add_expected_constraint_names() -> None:
    data = _make_two_round_two_player_data()
    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_trade_indicator_linking_constraints(problem, data, dvs)

    # Lower bounds
    assert "trade_link_lb_in_1_2" in problem.constraints
    assert "trade_link_lb_out_1_2" in problem.constraints

    # Upper bounds
    assert "trade_link_ub_in_requires_selected_1_2" in problem.constraints
    assert "trade_link_ub_in_requires_not_prev_1_2" in problem.constraints
    assert "trade_link_ub_out_requires_prev_1_2" in problem.constraints
    assert "trade_link_ub_out_requires_not_selected_1_2" in problem.constraints


def test_maximum_team_changes_constraints_add_expected_constraint_names() -> None:
    data = _make_two_round_two_player_data(max_trades_round2=1)
    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_maximum_team_changes_per_round_constraints(problem, data, dvs)

    assert "max_trades_in_2" in problem.constraints
    assert "max_trades_out_2" in problem.constraints
