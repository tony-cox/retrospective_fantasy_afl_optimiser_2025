from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import _add_position_eligibility_constraints, create_decision_variables


def test_add_position_eligibility_constraints_adds_expected_constraint_names() -> None:
    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=1)}

    # Player eligible for DEF only
    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=1.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1}, rounds=rounds, team_rules=rules)
    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_position_eligibility_constraints(problem, data, dvs)

    # For MID/RUC/FWD the player is ineligible, so constraints should force those vars to 0.
    assert "elig_onfield_1_MID_1" in problem.constraints
    assert "elig_onfield_1_RUC_1" in problem.constraints
    assert "elig_onfield_1_FWD_1" in problem.constraints

    assert "elig_bench_1_MID_1" in problem.constraints
    assert "elig_bench_1_RUC_1" in problem.constraints
    assert "elig_bench_1_FWD_1" in problem.constraints

    # No constraint needed for eligible position
    assert "elig_onfield_1_DEF_1" not in problem.constraints
    assert "elig_bench_1_DEF_1" not in problem.constraints
