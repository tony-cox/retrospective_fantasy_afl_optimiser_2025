from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import formulate_problem


def test_missing_price_round_disallows_trading_player_in_or_out() -> None:
    # Two rounds so we can trade, one trade allowed.
    rounds = {
        1: Round(number=1, max_trades=0, counted_onfield_players=1),
        2: Round(number=2, max_trades=1, counted_onfield_players=1),
    }

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=1_000_000,
        utility_bench_count=0,
    )

    # Player 1 is on the starting team but has *no data* (no price) in round 2.
    p1 = Player(player_id=1, first_name="P", last_name="One", original_positions=frozenset({Position.DEF}))
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10, price=100, eligible_positions=frozenset({Position.DEF}))

    # Player 2 can be selected in round 2.
    p2 = Player(player_id=2, first_name="P", last_name="Two", original_positions=frozenset({Position.DEF}))
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=0, price=100, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[2] = PlayerRoundInfo(round_number=2, score=10, price=100, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem, dvs = formulate_problem(data)

    # Force round-1 selection of player 1.
    problem += dvs.x_selected[(1, 1)] == 1
    problem += dvs.x_selected[(2, 1)] == 0

    # In round 2, force selection of player 2 (implies player 1 must be traded out).
    # Under the new rule, this must be infeasible because player 1 has no price in round 2,
    # so trading out in round 2 is not allowed.
    problem += dvs.x_selected[(1, 2)] == 0
    problem += dvs.x_selected[(2, 2)] == 1

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))

    assert pulp.LpStatus[status] in {"Infeasible", "Undefined"}


def test_missing_price_round_allows_player_to_remain_without_triggering_trade() -> None:
    rounds = {
        1: Round(number=1, max_trades=0, counted_onfield_players=1),
        2: Round(number=2, max_trades=1, counted_onfield_players=1),
    }

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=1_000_000,
        utility_bench_count=0,
    )

    p1 = Player(player_id=1, first_name="P", last_name="One", original_positions=frozenset({Position.DEF}))
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10, price=100, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="P", last_name="Two", original_positions=frozenset({Position.DEF}))
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=0, price=100, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[2] = PlayerRoundInfo(round_number=2, score=10, price=100, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)
    problem, dvs = formulate_problem(data)

    # Force player 1 to remain selected in round 2.
    problem += dvs.x_selected[(1, 1)] == 1
    problem += dvs.x_selected[(1, 2)] == 1

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # No trades should happen for player 1 in r=2.
    assert pulp.value(dvs.traded_in[(1, 2)]) == 0
    assert pulp.value(dvs.traded_out[(1, 2)]) == 0
