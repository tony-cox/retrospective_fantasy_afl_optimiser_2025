from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import add_objective, create_decision_variables


def _zero_counts_by_position() -> dict[Position, int]:
    return {pos: 0 for pos in Position.__members__.values()}


def test_add_objective_sets_expected_coefficients_for_scored_and_captain() -> None:
    # Two players, one round.
    rules = TeamStructureRules(
        on_field_required=_zero_counts_by_position(),
        bench_required=_zero_counts_by_position(),
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=22)}

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p2 = Player(player_id=2, first_name="B", last_name="B")

    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=0.0, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=7.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)

    # Objective coefficients should be:
    # 10 * scored_1_1 + 7 * scored_2_1 + 10 * captain_1_1 + 7 * captain_2_1
    obj = problem.objective
    assert obj is not None

    assert obj.get(dvs.scored[(1, 1)]) == 10.0
    assert obj.get(dvs.scored[(2, 1)]) == 7.0
    assert obj.get(dvs.captain[(1, 1)]) == 10.0
    assert obj.get(dvs.captain[(2, 1)]) == 7.0


def test_objective_doubles_when_player_is_both_scored_and_captain() -> None:
    rules = TeamStructureRules(
        on_field_required=_zero_counts_by_position(),
        bench_required=_zero_counts_by_position(),
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=22)}

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)

    # Simulate a solution: player is both scored and captain in round 1.
    dvs.scored[(1, 1)].setInitialValue(1)
    dvs.captain[(1, 1)].setInitialValue(1)

    # PuLP doesn't automatically evaluate objective at initial values, but we can
    # temporarily assign varValues to mimic a solved state.
    dvs.scored[(1, 1)].varValue = 1
    dvs.captain[(1, 1)].varValue = 1

    assert pulp.value(problem.objective) == 20.0
