from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import (
    _add_bank_balance_recurrence_constraints,
    _add_initial_bank_balance_constraints,
    create_decision_variables,
)


def test_bank_balance_constraints_two_rounds_respect_recurrence_when_trades_fixed() -> None:
    # This is a pure bank-balance integration test.
    # We fix x_selected and traded_in/traded_out via explicit constraints, then
    # check the bank variables are forced to the expected values.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=100.0,
        utility_bench_count=0,
    )

    rounds = {
        1: Round(number=1, max_trades=2, counted_onfield_players=0),
        2: Round(number=2, max_trades=2, counted_onfield_players=0),
    }

    # Two players, priced differently in round 1 vs round 2.
    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=30.0, eligible_positions=frozenset({Position.DEF}))
    p1.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=35.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=50.0, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[2] = PlayerRoundInfo(round_number=2, score=0.0, price=55.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("bank_integration", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_initial_bank_balance_constraints(problem, data, dvs)
    _add_bank_balance_recurrence_constraints(problem, data, dvs)

    # Fix starting squad in round 1: select only player 1.
    problem += dvs.x_selected[(1, 1)] == 1
    problem += dvs.x_selected[(2, 1)] == 0

    # Fix trades for round 2: trade out player 1, trade in player 2.
    problem += dvs.traded_out[(1, 2)] == 1
    problem += dvs.traded_in[(2, 2)] == 1
    problem += dvs.traded_in[(1, 2)] == 0
    problem += dvs.traded_out[(2, 2)] == 0

    # No requirements for x_selected in round 2 here (trade linking not implemented yet).

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # bank_1 = 100 - 30 = 70
    assert dvs.bank[1].value() == 70.0

    # bank_2 = bank_1 + price_out(round2) - price_in(round2)
    #        = 70 + 35 - 55 = 50
    assert dvs.bank[2].value() == 50.0
