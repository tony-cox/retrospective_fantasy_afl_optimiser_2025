from __future__ import annotations

import pulp

from retro_fantasy.data import Player, PlayerRoundInfo, Position, TeamStructureRules
from retro_fantasy.formulation import formulate_problem
from retro_fantasy.main import build_default_rounds, build_model_input_data


def test_formulate_and_solve_end_to_end_from_model_input_data() -> None:
    # Tiny end-to-end smoke test for main/formulation integration.
    # 1 round, require 1 DEF onfield, no bench and no utility.

    team_rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=1_000.0,
        utility_bench_count=0,
    )

    rounds = build_default_rounds(round_numbers=[1], default_max_trades=0, counted_onfield_players_default=1)

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=100.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=5.0, price=100.0, eligible_positions=frozenset({Position.DEF}))

    data = build_model_input_data(players={1: p1, 2: p2}, team_rules=team_rules, rounds=rounds)

    problem, _decision_variables = formulate_problem(data)
    status_code = problem.solve(pulp.PULP_CBC_CMD(msg=False))

    assert pulp.LpStatus[status_code] == "Optimal"


def test_build_default_rounds_assigns_three_trades_to_bye_rounds() -> None:
    rounds = build_default_rounds(round_numbers=[1, 12, 17], trade_rounds_with_three=(12,), default_max_trades=2)
    assert rounds[1].max_trades == 2
    assert rounds[12].max_trades == 3
    assert rounds[17].max_trades == 2
