import pulp

from retro_fantasy.data import ModelInputData, Player, Position, Round, TeamStructureRules
from retro_fantasy.formulation import formulate_problem


def test_formulate_problem_returns_pulp_problem() -> None:
    rules = TeamStructureRules(
        on_field_required={pos: 0 for pos in Position.__members__.values()},
        bench_required={pos: 0 for pos in Position.__members__.values()},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    data = ModelInputData(
        players={1: Player(player_id=1, first_name="A", last_name="B")},
        rounds={1: Round(number=1, max_trades=2, counted_onfield_players=22)},
        team_rules=rules,
    )

    problem = formulate_problem(data)

    assert isinstance(problem, pulp.LpProblem)
    assert problem.name == "retro_fantasy"
    assert problem.sense == pulp.LpMaximize

    # Objective is set (currently a placeholder 0 expression)
    assert problem.objective is not None

    # Constraints still not implemented
    assert len(problem.constraints) == 0
