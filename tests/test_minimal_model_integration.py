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


def test_minimal_model_two_rounds_team_changes_due_to_scoring() -> None:
    # Two rounds, pick 1 on-field DEF per round, count 1 score per round.
    # Scores are constructed so that the best player in round 1 is different to round 2.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {
        1: Round(number=1, max_trades=2, counted_onfield_players=1),
        2: Round(number=2, max_trades=2, counted_onfield_players=1),
    }

    # p1 best in round 1, p2 best in round 2
    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=0.0, eligible_positions=frozenset({Position.DEF}))
    p1.by_round[2] = PlayerRoundInfo(round_number=2, score=1.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=2.0, price=0.0, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[2] = PlayerRoundInfo(round_number=2, score=9.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p3 = Player(player_id=3, first_name="C", last_name="C")
    p3.by_round[1] = PlayerRoundInfo(round_number=1, score=0.5, price=0.0, eligible_positions=frozenset({Position.DEF}))
    p3.by_round[2] = PlayerRoundInfo(round_number=2, score=0.5, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2, 3: p3}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("min_model_2_rounds", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # Round 1: choose p1
    assert dvs.y_onfield[(1, Position.DEF, 1)].value() == 1
    assert dvs.scored[(1, 1)].value() == 1
    assert dvs.captain[(1, 1)].value() == 1

    assert dvs.y_onfield[(2, Position.DEF, 1)].value() == 0
    assert dvs.scored[(2, 1)].value() == 0
    assert dvs.captain[(2, 1)].value() == 0

    # Round 2: choose p2
    assert dvs.y_onfield[(2, Position.DEF, 2)].value() == 1
    assert dvs.scored[(2, 2)].value() == 1
    assert dvs.captain[(2, 2)].value() == 1

    assert dvs.y_onfield[(1, Position.DEF, 2)].value() == 0
    assert dvs.scored[(1, 2)].value() == 0
    assert dvs.captain[(1, 2)].value() == 0

    # Assert the on-field team changes between rounds
    assert dvs.y_onfield[(1, Position.DEF, 1)].value() != dvs.y_onfield[(1, Position.DEF, 2)].value()
    assert dvs.y_onfield[(2, Position.DEF, 1)].value() != dvs.y_onfield[(2, Position.DEF, 2)].value()

    # Objective: (10 + 9) + (captain bonus 10 + 9) = 38
    assert pulp.value(problem.objective) == 38.0


def test_position_eligibility_prevents_ineligible_player_from_being_selected_in_position() -> None:
    # Need 1 DEF on-field. Player 1 scores highest but is MID-only; player 2 is DEF-only.
    # With eligibility constraints, player 2 must be chosen at DEF.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=1)}

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=100.0, price=0.0, eligible_positions=frozenset({Position.MID}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=1.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("elig_integration", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # Player 1 cannot be placed at DEF due to eligibility
    assert dvs.y_onfield[(1, Position.DEF, 1)].value() == 0

    # Player 2 must fill DEF slot
    assert dvs.y_onfield[(2, Position.DEF, 1)].value() == 1
    assert dvs.scored[(2, 1)].value() == 1
    assert dvs.captain[(2, 1)].value() == 1


def test_dual_position_player_can_fill_either_required_position() -> None:
    # Require 1 DEF and 1 MID on-field. Player 1 is DEF/MID eligible.
    # Player 2 is DEF-only. Player 3 is MID-only.
    # The dual-position player should be used to fill the position where it yields feasibility.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 1, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=2)}

    # Dual position, good score
    p1 = Player(player_id=1, first_name="DPP", last_name="One")
    p1.by_round[1] = PlayerRoundInfo(
        round_number=1,
        score=50.0,
        price=0.0,
        eligible_positions=frozenset({Position.DEF, Position.MID}),
    )

    # Specialists
    p2 = Player(player_id=2, first_name="Def", last_name="Only")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p3 = Player(player_id=3, first_name="Mid", last_name="Only")
    p3.by_round[1] = PlayerRoundInfo(round_number=1, score=9.0, price=0.0, eligible_positions=frozenset({Position.MID}))

    data = ModelInputData(players={1: p1, 2: p2, 3: p3}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("dpp_either", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # Must select exactly 2 on-field players: one DEF and one MID.
    # The DPP player must be selected on-field, in either DEF or MID.
    assert (
        dvs.y_onfield[(1, Position.DEF, 1)].value() + dvs.y_onfield[(1, Position.MID, 1)].value()
    ) == 1

    # Exactly one DEF slot and one MID slot are filled.
    assert (
        dvs.y_onfield[(1, Position.DEF, 1)].value() + dvs.y_onfield[(2, Position.DEF, 1)].value() + dvs.y_onfield[(3, Position.DEF, 1)].value()
    ) == 1
    assert (
        dvs.y_onfield[(1, Position.MID, 1)].value() + dvs.y_onfield[(2, Position.MID, 1)].value() + dvs.y_onfield[(3, Position.MID, 1)].value()
    ) == 1

    # And DPP can't be placed on bench/utility given those are all zero.
    assert dvs.y_utility[(1, 1)].value() == 0


def test_dual_position_player_cannot_be_selected_in_two_positions_same_round() -> None:
    # Require 1 DEF and 1 MID. Only one available player eligible for both (DPP).
    # Since the player can only occupy one slot per round, the problem should be infeasible.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 1, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=1)}

    p1 = Player(player_id=1, first_name="DPP", last_name="Only")
    p1.by_round[1] = PlayerRoundInfo(
        round_number=1,
        score=50.0,
        price=0.0,
        eligible_positions=frozenset({Position.DEF, Position.MID}),
    )

    data = ModelInputData(players={1: p1}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("dpp_not_both", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))

    # With only one player available, you can't fill both a DEF and MID slot.
    assert pulp.LpStatus[status] == "Infeasible"


def test_bench_positional_requirement_selects_expected_bench_player() -> None:
    # Require 1 on-field DEF (so we can have 1 scored player and 1 captain),
    # and also require 1 bench DEF slot.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=1)}

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=1.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("bench_def", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # Exactly one on-field DEF and one bench DEF.
    assert dvs.y_onfield[(1, Position.DEF, 1)].value() + dvs.y_onfield[(2, Position.DEF, 1)].value() == 1
    assert dvs.y_bench[(1, Position.DEF, 1)].value() + dvs.y_bench[(2, Position.DEF, 1)].value() == 1

    # With two DEF-only players and two slots, both players must be selected in exactly one slot each.
    assert dvs.x_selected[(1, 1)].value() == 1
    assert dvs.x_selected[(2, 1)].value() == 1


def test_utility_bench_requirement_selects_exactly_one_utility_player() -> None:
    # Require 1 on-field DEF (so we can have 1 scored player and 1 captain),
    # and also require 1 bench utility slot.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=1,
    )

    rounds = {1: Round(number=1, max_trades=2, counted_onfield_players=1)}

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=1.0, price=0.0, eligible_positions=frozenset({Position.MID}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("bench_util", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # One on-field DEF must be filled.
    assert dvs.y_onfield[(1, Position.DEF, 1)].value() + dvs.y_onfield[(2, Position.DEF, 1)].value() == 1

    # Exactly one utility slot filled.
    util_sum = dvs.y_utility[(1, 1)].value() + dvs.y_utility[(2, 1)].value()
    assert util_sum == 1

    # Ensure no player occupies more than one slot.
    for pid in (1, 2):
        slot_sum = (
            dvs.y_utility[(pid, 1)].value()
            + sum(dvs.y_onfield[(pid, pos, 1)].value() for pos in Position.__members__.values())
            + sum(dvs.y_bench[(pid, pos, 1)].value() for pos in Position.__members__.values())
        )
        assert slot_sum <= 1


def test_trading_allows_team_to_change_across_rounds_with_trade_limit_and_bank_balance() -> None:
    # Two rounds, one on-field DEF each round.
    # Round 1 best scorer is p1, round 2 best scorer is p2.
    # With max_trades=1, the model should trade from p1 -> p2.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=100.0,
        utility_bench_count=0,
    )

    rounds = {
        1: Round(number=1, max_trades=2, counted_onfield_players=1),
        2: Round(number=2, max_trades=1, counted_onfield_players=1),
    }

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=60.0, eligible_positions=frozenset({Position.DEF}))
    p1.by_round[2] = PlayerRoundInfo(round_number=2, score=1.0, price=60.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=2.0, price=60.0, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[2] = PlayerRoundInfo(round_number=2, score=9.0, price=60.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("trade_integration", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # Round 1 select p1
    assert dvs.y_onfield[(1, Position.DEF, 1)].value() == 1
    assert dvs.y_onfield[(2, Position.DEF, 1)].value() == 0

    # Round 2 select p2
    assert dvs.y_onfield[(1, Position.DEF, 2)].value() == 0
    assert dvs.y_onfield[(2, Position.DEF, 2)].value() == 1

    # Trade indicators should reflect a swap in round 2
    assert dvs.traded_out[(1, 2)].value() == 1
    assert dvs.traded_in[(2, 2)].value() == 1
    assert dvs.traded_in[(1, 2)].value() == 0
    assert dvs.traded_out[(2, 2)].value() == 0

    # Bank: start with cap - price(p1,1) = 40
    assert dvs.bank[1].value() == 40.0
    # bank2 = bank1 + 60 (sold p1 at r2) - 60 (bought p2 at r2) = 40
    assert dvs.bank[2].value() == 40.0

    # Objective: (10 + 9) + (captain bonus 10 + 9) = 38
    assert pulp.value(problem.objective) == 38.0


def test_trading_is_limited_to_one_trade_per_round_when_multiple_improving_trades_exist() -> None:
    # 3 rounds, require 2 DEF on-field each round.
    # Start with two mediocre players in round 1 (optimal for round 1).
    # In round 2, there are two better players available; without trade limits you'd swap both.
    # With max_trades=1 in round 2, the model can only swap ONE of them.
    # In round 3, max_trades=1 again, so it can complete the second upgrade.

    rules = TeamStructureRules(
        on_field_required={Position.DEF: 2, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=200.0,
        utility_bench_count=0,
    )

    rounds = {
        1: Round(number=1, max_trades=2, counted_onfield_players=2),
        2: Round(number=2, max_trades=1, counted_onfield_players=2),
        3: Round(number=3, max_trades=1, counted_onfield_players=2),
    }

    # Prices are flat to keep bank effects simple.
    # Round 1 scores favour p1+p2.
    # Round 2 scores heavily favour p3+p4. With only 1 trade allowed, we must keep one of p1/p2.
    # Round 3 continues to favour p3+p4, allowing the second upgrade.

    def _pri(score: float, price: float) -> PlayerRoundInfo:
        return PlayerRoundInfo(round_number=0, score=score, price=price, eligible_positions=frozenset({Position.DEF}))

    p1 = Player(player_id=1, first_name="P1", last_name="")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=90.0, price=50.0, eligible_positions=frozenset({Position.DEF}))
    p1.by_round[2] = PlayerRoundInfo(round_number=2, score=1.0, price=50.0, eligible_positions=frozenset({Position.DEF}))
    p1.by_round[3] = PlayerRoundInfo(round_number=3, score=1.0, price=50.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="P2", last_name="")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=100.0, price=50.0, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[2] = PlayerRoundInfo(round_number=2, score=2.0, price=50.0, eligible_positions=frozenset({Position.DEF}))
    p2.by_round[3] = PlayerRoundInfo(round_number=3, score=2.0, price=50.0, eligible_positions=frozenset({Position.DEF}))

    p3 = Player(player_id=3, first_name="P3", last_name="")
    p3.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=50.0, eligible_positions=frozenset({Position.DEF}))
    p3.by_round[2] = PlayerRoundInfo(round_number=2, score=20.0, price=50.0, eligible_positions=frozenset({Position.DEF}))
    p3.by_round[3] = PlayerRoundInfo(round_number=3, score=20.0, price=50.0, eligible_positions=frozenset({Position.DEF}))

    p4 = Player(player_id=4, first_name="P4", last_name="")
    p4.by_round[1] = PlayerRoundInfo(round_number=1, score=0.0, price=50.0, eligible_positions=frozenset({Position.DEF}))
    p4.by_round[2] = PlayerRoundInfo(round_number=2, score=19.0, price=50.0, eligible_positions=frozenset({Position.DEF}))
    p4.by_round[3] = PlayerRoundInfo(round_number=3, score=19.0, price=50.0, eligible_positions=frozenset({Position.DEF}))

    data = ModelInputData(players={1: p1, 2: p2, 3: p3, 4: p4}, rounds=rounds, team_rules=rules)

    problem = pulp.LpProblem("trade_limit_integration", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    add_objective(problem, data, dvs)
    add_constraints(problem, data, dvs)

    # Force the starting squad so round 2 genuinely presents two improving upgrade options.
    problem += dvs.x_selected[(1, 1)] == 1
    problem += dvs.x_selected[(2, 1)] == 1
    problem += dvs.x_selected[(3, 1)] == 0
    problem += dvs.x_selected[(4, 1)] == 0

    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    assert pulp.LpStatus[status] == "Optimal"

    # Round 1: as forced.
    assert dvs.x_selected[(1, 1)].value() == 1
    assert dvs.x_selected[(2, 1)].value() == 1
    assert dvs.x_selected[(3, 1)].value() == 0
    assert dvs.x_selected[(4, 1)].value() == 0

    # Round 2: must include p3 (best), and keep exactly one of p1/p2 due to max 1 trade.
    assert dvs.x_selected[(3, 2)].value() == 1
    # p4 is also great, but only one of p3/p4 can be added in round 2 given trade limit.
    # So we should have exactly one of (p3, p4) added and exactly one of (p1, p2) kept.
    assert (dvs.x_selected[(1, 2)].value() + dvs.x_selected[(2, 2)].value()) == 1
    assert (dvs.x_selected[(3, 2)].value() + dvs.x_selected[(4, 2)].value()) == 1

    # Trade limit enforcement: exactly one trade in and one trade out in round 2.
    traded_in_r2 = sum(dvs.traded_in[(p, 2)].value() for p in (1, 2, 3, 4))
    traded_out_r2 = sum(dvs.traded_out[(p, 2)].value() for p in (1, 2, 3, 4))
    assert traded_in_r2 == 1
    assert traded_out_r2 == 1

    # Round 3: should finish the upgrade so p3+p4 are selected.
    assert dvs.x_selected[(3, 3)].value() == 1
    assert dvs.x_selected[(4, 3)].value() == 1
    assert dvs.x_selected[(1, 3)].value() + dvs.x_selected[(2, 3)].value() == 0

    traded_in_r3 = sum(dvs.traded_in[(p, 3)].value() for p in (1, 2, 3, 4))
    traded_out_r3 = sum(dvs.traded_out[(p, 3)].value() for p in (1, 2, 3, 4))
    assert traded_in_r3 == 1
    assert traded_out_r3 == 1
