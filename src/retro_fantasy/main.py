from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence

import pulp

from retro_fantasy.data import ModelInputData, Player, Position, Round, TeamStructureRules
from retro_fantasy.formulation import formulate_problem
from retro_fantasy.io import load_players_from_json


def configure_logging(*, level: int = logging.INFO) -> None:
    """Configure a simple root logger that writes to stdout.

    This is safe to call multiple times.
    """

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
    else:
        root.setLevel(level)


logger = logging.getLogger(__name__)


def load_players(
    *,
    players_json_path: str | Path,
    position_updates_csv_path: str | Path,
    squad_id_filter: frozenset[int] | None = None,
) -> Dict[int, Player]:
    """Load player data for the optimiser."""

    return load_players_from_json(
        players_json_path,
        position_updates_csv=position_updates_csv_path,
        squad_id_filter=squad_id_filter,
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


def summarise_problem(problem: pulp.LpProblem, *, max_name_examples: int = 5) -> None:
    """Log a short diagnostic summary of a PuLP problem.

    This is intentionally lightweight and avoids expensive operations (like
    exporting LP files or iterating coefficient-by-coefficient). The goal is to
    provide enough context to sanity-check what we're about to solve.
    """

    vars_list = problem.variables()
    num_vars = len(vars_list)
    num_constraints = len(problem.constraints)

    # Variable category counts (Binary/Integer/Continuous)
    cat_counts: dict[str, int] = {"Binary": 0, "Integer": 0, "Continuous": 0, "Other": 0}
    for v in vars_list:
        # PuLP uses single-letter category strings: 'Binary', 'Integer', 'Continuous'
        cat = getattr(v, "cat", None)
        if cat in cat_counts:
            cat_counts[cat] += 1
        else:
            cat_counts["Other"] += 1

    # Constraint sense counts: -1 (<=), 0 (=), 1 (>=)
    sense_counts: dict[str, int] = {"<=": 0, "=": 0, ">=": 0, "other": 0}
    for c in problem.constraints.values():
        s = getattr(c, "sense", None)
        if s == -1:
            sense_counts["<="] += 1
        elif s == 0:
            sense_counts["="] += 1
        elif s == 1:
            sense_counts[">="] += 1
        else:
            sense_counts["other"] += 1

    logger.info("PuLP problem summary:")
    logger.info("  name=%s sense=%s", problem.name, "Maximize" if problem.sense == pulp.LpMaximize else "Minimize")
    logger.info("  variables=%d constraints=%d", num_vars, num_constraints)
    logger.info("  variable categories=%s", cat_counts)
    logger.info("  constraint senses=%s", sense_counts)

    # Objective is an affine expression; log a short string form (truncated)
    obj_str = str(problem.objective) if problem.objective is not None else "<none>"
    if len(obj_str) > 300:
        obj_str = obj_str[:300] + "..."
    logger.info("  objective=%s", obj_str)

    # A few names for quick sanity.
    if vars_list:
        examples = [v.name for v in vars_list[:max_name_examples]]
        logger.info("  first_vars=%s", examples)
    if problem.constraints:
        c_names = list(problem.constraints.keys())
        logger.info("  first_constraints=%s", c_names[:max_name_examples])


def solve_retro_fantasy(
    *,
    players_json_path: str | Path,
    position_updates_csv_path: str | Path,
    team_rules: TeamStructureRules,
    rounds: Mapping[int, Round],
    squad_id_filter: frozenset[int] | None = None,
    time_limit_seconds: int | None = None,
    solve: bool = True,
    enable_solver_output: bool = False,
    log_level: int | None = logging.INFO,
) -> SolveResult:
    """Top-level entrypoint: load player data, formulate, and solve.

    The caller supplies all season configuration (team rules and rounds). This
    makes it easy to swap configurations (e.g. smaller problems) without code
    changes.

    Notes
    -----
    Players may be missing score/price data for some rounds (e.g. added
    mid-season). Missing scores are treated as 0 and missing prices as the full
    salary cap (prohibitively expensive) via :class:`retro_fantasy.data.ModelInputData`.
    """

    if log_level is not None:
        configure_logging(level=log_level)

    logger.info("Loading players from JSON: %s", players_json_path)
    players = load_players(
        players_json_path=players_json_path,
        position_updates_csv_path=position_updates_csv_path,
        squad_id_filter=squad_id_filter,
    )
    logger.info("Loaded %d players", len(players))

    logger.info("Using provided rounds: %d rounds (min=%d, max=%d)", len(rounds), min(rounds), max(rounds))

    logger.info(
        "Team structure: onfield=%d, bench=%d (utility=%d), squad=%d, salary_cap=%s",
        sum(team_rules.on_field_required.values()),
        sum(team_rules.bench_required.values()) + team_rules.utility_bench_count,
        team_rules.utility_bench_count,
        team_rules.squad_size,
        team_rules.salary_cap,
    )

    logger.info("Building ModelInputData")
    model_input_data = build_model_input_data(players=players, team_rules=team_rules, rounds=rounds)

    logger.info("Formulating PuLP problem")
    problem = formulate_problem(model_input_data)
    logger.info("Problem built: variables=%d constraints=%d", len(problem.variables()), len(problem.constraints))

    summarise_problem(problem)

    if not solve:
        logger.info("Skipping solve (solve=False)")
        return SolveResult(status="NotSolved", objective_value=0.0, problem=problem)

    logger.info("Solving with CBC (time_limit_seconds=%s, solver_output=%s)", time_limit_seconds, enable_solver_output)

    solver = (
        pulp.PULP_CBC_CMD(msg=enable_solver_output, timeLimit=time_limit_seconds)
        if time_limit_seconds
        else pulp.PULP_CBC_CMD(msg=enable_solver_output)
    )

    status_code = problem.solve(solver)
    status = pulp.LpStatus[status_code]

    obj = float(pulp.value(problem.objective) or 0.0)
    logger.info("Solve complete: status=%s objective=%s", status, obj)

    return SolveResult(status=status, objective_value=obj, problem=problem)
