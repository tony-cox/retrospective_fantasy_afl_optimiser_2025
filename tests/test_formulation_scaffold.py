import pulp

from retro_fantasy.data import ModelInputData, Player, PlayerRoundInfo, Position, Round, TeamStructureRules
from retro_fantasy.formulation import formulate_problem


def test_formulate_problem_returns_pulp_problem() -> None:
    rules = TeamStructureRules(
        on_field_required={pos: 0 for pos in Position.__members__.values()},
        bench_required={pos: 0 for pos in Position.__members__.values()},
        salary_cap=0.0,
        utility_bench_count=0,
    )

    player = Player(player_id=1, first_name="A", last_name="B")
    player.by_round[1] = PlayerRoundInfo(
        round_number=1,
        score=0.0,
        price=0.0,
        eligible_positions=frozenset({Position.DEF}),
    )

    data = ModelInputData(
        players={1: player},
        rounds={1: Round(number=1, max_trades=2, counted_onfield_players=22)},
        team_rules=rules,
    )

    problem = formulate_problem(data)

    assert isinstance(problem, pulp.LpProblem)
    assert problem.name == "retro_fantasy"
    assert problem.sense == pulp.LpMaximize

    # Objective is set
    assert problem.objective is not None

    # Constraints still not implemented
    assert len(problem.constraints) == 0
