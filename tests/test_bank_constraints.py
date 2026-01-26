from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import (
    _add_bank_balance_recurrence_constraints,
    _add_initial_bank_balance_constraints,
    create_decision_variables,
)


def _rules_with_one_onfield_def_and_zero_else(salary_cap: float) -> TeamStructureRules:
    return TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=salary_cap,
        utility_bench_count=0,
    )


def test_add_initial_bank_balance_constraints_adds_constraint_and_coefficients() -> None:
    rules = _rules_with_one_onfield_def_and_zero_else(salary_cap=100.0)

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=1)}

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=30.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=40.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_initial_bank_balance_constraints(problem, data, dvs)

    assert "bank_initial_round_1" in problem.constraints

    cons = problem.constraints["bank_initial_round_1"]

    # bank_1 == salary_cap - 30*x_1_1 - 40*x_2_1
    assert cons.get(dvs.bank[1], 0.0) == 1
    assert cons.get(dvs.x_selected[(1, 1)], 0.0) == 30.0
    assert cons.get(dvs.x_selected[(2, 1)], 0.0) == 40.0

    # RHS constant stored as -constant in PuLP constraint representation
    # For equality:  bank_1 + 30*x1 + 40*x2 - salary_cap == 0
    assert cons.constant == -100.0


def test_add_bank_balance_recurrence_constraints_adds_constraint_and_coefficients() -> None:
    rules = _rules_with_one_onfield_def_and_zero_else(salary_cap=0.0)

    rounds = {
        1: Round(number=1, max_trades=2, counted_onfield_players=1),
        2: Round(number=2, max_trades=2, counted_onfield_players=1),
    }

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=10.0, eligible_positions=frozenset({Position.DEF}))
    p1.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=11.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=20.0, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=22.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_bank_balance_recurrence_constraints(problem, data, dvs)

    assert "bank_recurrence_2" in problem.constraints

    cons = problem.constraints["bank_recurrence_2"]

    # bank_2 == bank_1 + 11*out_1_2 + 22*out_2_2 - 11*in_1_2 - 22*in_2_2
    assert cons.get(dvs.bank[2], 0.0) == 1
    assert cons.get(dvs.bank[1], 0.0) == -1

    assert cons.get(dvs.traded_out[(1, 2)], 0.0) == -11.0
    assert cons.get(dvs.traded_out[(2, 2)], 0.0) == -22.0

    assert cons.get(dvs.traded_in[(1, 2)], 0.0) == 11.0
    assert cons.get(dvs.traded_in[(2, 2)], 0.0) == 22.0
