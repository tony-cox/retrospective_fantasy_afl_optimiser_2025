from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import add_constraints, add_objective, create_decision_variables


def test_minimal_model_solves_and_picks_best_scored_and_captain() -> None:
    # Simplest bounded model:
    # - exactly 1 on-field DEF, no bench, no utility
    # - exactly 1 scored player per round
    # - exactly 1 captain per round and captain must be scored
    # This should pick the best-scoring player as both scored and captain.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=1)}

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=7.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("min_model", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    # Solve with the default CBC solver (bundled with PuLP in many installs).
    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # Best player should be selected on-field DEF, scored, and captain.
    assert dvs.y_onfield[(1, Position.DEF, 1)].value() == 1
    assert dvs.scored[(1, 1)].value() == 1
    assert dvs.captain[(1, 1)].value() == 1

    assert dvs.y_onfield[(2, Position.DEF, 1)].value() == 0
    assert dvs.scored[(2, 1)].value() == 0
    assert dvs.captain[(2, 1)].value() == 0

    # Objective should reflect doubling via captaincy: 10 (scored) + 10 (captain bonus)
    assert pulp.value(problem.objective) == 20.0


def test_minimal_model_with_three_players_select_two_picks_best_two_and_best_captain() -> None:
    rules = TeamStructureRules(
        on_field_required={Position.DEF: 2, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=2)}

    # Scores: p1 best, p2 second, p3 worst
    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=8.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p3 = Player(player_id=3, first_name="C", last_name="C")
    p3.by_round[1] = PlayerRoundInfo(round_number=1, score=1.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2, 3: p3}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("min_model_3", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # Pick the best 2 of 3 on-field
    assert dvs.y_onfield[(1, Position.DEF, 1)].value() == 1
    assert dvs.y_onfield[(2, Position.DEF, 1)].value() == 1
    assert dvs.y_onfield[(3, Position.DEF, 1)].value() == 0

    # Scored should be the same two (since counted_onfield_players=2)
    assert dvs.scored[(1, 1)].value() == 1
    assert dvs.scored[(2, 1)].value() == 1
    assert dvs.scored[(3, 1)].value() == 0

    # Captain should be the best overall (p1)
    assert dvs.captain[(1, 1)].value() == 1
    assert dvs.captain[(2, 1)].value() == 0
    assert dvs.captain[(3, 1)].value() == 0

    # Objective: (10+8) + captain bonus 10 = 28
    assert pulp.value(problem.objective) == 28.0
