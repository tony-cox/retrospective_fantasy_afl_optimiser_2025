from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import (
    _add_captaincy_constraints,
    _add_linking_constraints,
    _add_positional_structure_constraints,
    _add_scoring_selection_constraints,
    create_decision_variables,
)


def _make_rules() -> TeamStructureRules:
    return TeamStructureRules(
        on_field_required={Position.DEF: 1, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        bench_required={Position.DEF: 0, Position.MID: 0, Position.RUC: 0, Position.FWD: 0},
        salary_cap=0.0,
        utility_bench_count=0,
    )


def _make_data() -> ModelInputData:
    rules = _make_rules()

    rounds = {
        1: Round(number=1, max_trades=2, counted_onfield_players=1),
    }

    p1 = Player(player_id=1, first_name="A", last_name="A")
    p1.by_round[1] = PlayerRoundInfo(round_number=1, score=10.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    p2 = Player(player_id=2, first_name="B", last_name="B")
    p2.by_round[1] = PlayerRoundInfo(round_number=1, score=7.0, price=0.0, eligible_positions=frozenset({Position.DEF}))

    return ModelInputData(players={1: p1, 2: p2}, rounds=rounds, team_rules=rules)


def test_add_positional_structure_constraints_adds_constraints() -> None:
    data = _make_data()
    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_positional_structure_constraints(problem, data, dvs)

    # Expect at least the on-field DEF count constraint and utility constraint for round 1
    assert "pos_onfield_count_DEF_1" in problem.constraints
    assert "pos_utility_count_1" in problem.constraints


def test_add_linking_constraints_adds_constraints() -> None:
    data = _make_data()
    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_linking_constraints(problem, data, dvs)

    assert "link_x_equals_positions_1_1" in problem.constraints
    assert "link_at_most_one_slot_1_1" in problem.constraints


def test_add_scoring_selection_constraints_adds_constraints() -> None:
    data = _make_data()
    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_scoring_selection_constraints(problem, data, dvs)

    assert "score_count_1" in problem.constraints
    assert "score_only_if_onfield_1_1" in problem.constraints


def test_add_captaincy_constraints_adds_constraints() -> None:
    data = _make_data()
    problem = pulp.LpProblem("t", pulp.LpMaximize)
    dvs = create_decision_variables(problem, data)

    _add_captaincy_constraints(problem, data, dvs)

    assert "captain_exactly_one_1" in problem.constraints
    assert "captain_requires_scored_1_1" in problem.constraints
