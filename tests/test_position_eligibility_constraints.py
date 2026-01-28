from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import create_decision_variables


def test_positional_selection_decision_variables_are_only_created_for_eligible_positions() -> None:
    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=1)}

    # Player eligible for DEF only.
    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=1.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1}, rounds=rounds, team_rules=rules)
    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    # Eligible tuples exist.
    assert (1, Position.DEF, 1) in dvs.y_onfield
    assert (1, Position.DEF, 1) in dvs.y_bench

    # Ineligible tuples are not created at all.
    assert (1, Position.MID, 1) not in dvs.y_onfield
    assert (1, Position.RUC, 1) not in dvs.y_onfield
    assert (1, Position.FWD, 1) not in dvs.y_onfield

    assert (1, Position.MID, 1) not in dvs.y_bench
    assert (1, Position.RUC, 1) not in dvs.y_bench
    assert (1, Position.FWD, 1) not in dvs.y_bench
