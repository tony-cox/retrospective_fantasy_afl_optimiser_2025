from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence

import pulp

from retro_fantasy.data import ModelInputData, Player, Position, Round, TeamStructureRules
from retro_fantasy.formulation import formulate_problem
from retro_fantasy.io import load_players_from_json


def load_players(
    *,
    players_json_path: str | Path,
    position_updates_csv_path: str | Path,
) -> Dict[int, Player]:
    """Load player data for the optimiser."""

    return load_players_from_json(
        players_json_path,
        position_updates_csv=position_updates_csv_path,
    )


def build_default_team_rules(*, salary_cap: float = 17_500_000.0, utility_bench_count: int = 1) -> TeamStructureRules:
    """Build the default AFL Fantasy team structure rules used by this project.

    Notes
    -----
    The salary cap is supplied as a float because the underlying dataset prices
    are floats. Adjust this if your dataset uses a different unit.
    """

    return TeamStructureRules(
        on_field_required={Position.DEF: 6, Position.MID: 8, Position.RUC: 2, Position.FWD: 6},
        bench_required={Position.DEF: 2, Position.MID: 2, Position.RUC: 1, Position.FWD: 2},
        salary_cap=salary_cap,
        utility_bench_count=utility_bench_count,
    )


def build_default_rounds(
    *,
    round_numbers: Iterable[int],
    trade_rounds_with_three: Sequence[int] = (12, 13, 14, 15, 16),
    default_max_trades: int = 2,
    counted_onfield_players_default: int = 22,
) -> Dict[int, Round]:
    """Build default per-round parameters.

    - max_trades: 3 for mid-season bye rounds, else 2
    - counted_onfield_players: 22 by default (bye-round 18 logic can be supplied later)
    """

    rounds: Dict[int, Round] = {}
    for r in sorted(set(round_numbers)):
        max_trades = 3 if r in set(trade_rounds_with_three) else default_max_trades
        rounds[r] = Round(number=r, max_trades=max_trades, counted_onfield_players=counted_onfield_players_default)
    return rounds


def build_model_input_data(
    *,
    players: Mapping[int, Player],
    team_rules: TeamStructureRules,
    rounds: Mapping[int, Round],
) -> ModelInputData:
    """Create ModelInputData from already-loaded players and rule objects."""

    return ModelInputData(players=dict(players), rounds=dict(rounds), team_rules=team_rules)


@dataclass(frozen=True, slots=True)
class SolveResult:
    status: str
    objective_value: float
    problem: pulp.LpProblem


def solve_retro_fantasy(
    *,
    players_json_path: str | Path,
    position_updates_csv_path: str | Path,
    salary_cap: float = 17_500_000.0,
    utility_bench_count: int = 1,
    time_limit_seconds: int | None = None,
    solve: bool = True,
) -> SolveResult:
    """Top-level entrypoint: load production data, formulate, and solve.

    Returns a small structured result to make it easier for `run.py` and future
    analysis code to consume.

    Notes
    -----
    Players may be missing score/price data for some rounds (e.g. added
    mid-season). Missing scores are treated as 0 and missing prices as the full
    salary cap (prohibitively expensive) via :class:`retro_fantasy.data.ModelInputData`.

    Solving the full-season model can take a long time depending on solver
    configuration and machine specs. Use ``time_limit_seconds`` for a bounded
    solve (useful for smoke tests), or ``solve=False`` to only build the model.
    """

    players = load_players(players_json_path=players_json_path, position_updates_csv_path=position_updates_csv_path)

    # Infer season rounds from the union of all round keys seen in the data.
    # This is a single pass over the (player,round) dictionaries and is fast.
    season_rounds: set[int] = set()
    for p in players.values():
        season_rounds.update(r for r in p.by_round.keys() if r >= 1)

    if not season_rounds:
        raise ValueError("No season rounds (>=1) found in player data")

    team_rules = build_default_team_rules(salary_cap=salary_cap, utility_bench_count=utility_bench_count)
    rounds = build_default_rounds(round_numbers=season_rounds)

    model_input_data = build_model_input_data(players=players, team_rules=team_rules, rounds=rounds)

    problem = formulate_problem(model_input_data)

    if not solve:
        return SolveResult(status="NotSolved", objective_value=0.0, problem=problem)

    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit_seconds) if time_limit_seconds else pulp.PULP_CBC_CMD(msg=False)

    status_code = problem.solve(solver)
    status = pulp.LpStatus[status_code]

    obj = float(pulp.value(problem.objective) or 0.0)

    return SolveResult(status=status, objective_value=obj, problem=problem)
