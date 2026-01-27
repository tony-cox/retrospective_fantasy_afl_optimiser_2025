from __future__ import annotations

import hashlib
import json
import platform
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping

import pulp

from retro_fantasy.formulation import formulate_problem
from retro_fantasy.io import load_players_from_json, load_rounds_from_json, load_team_rules_from_json
from retro_fantasy.main import build_model_input_data
from retro_fantasy.solution import build_solution_summary, solution_summary_to_json_dict


@dataclass(frozen=True, slots=True)
class PerfScenario:
    name: str
    players_json_path: Path
    position_updates_csv_path: Path
    team_rules_json_path: Path
    rounds_json_path: Path
    data_filter_json_path: Path

    # How many repeated runs to take the median over.
    # Median makes results much less noisy than a single run.
    repeats: int = 3


@dataclass(frozen=True, slots=True)
class ProblemMetrics:
    num_variables: int
    num_constraints: int
    variable_categories: dict[str, int]
    constraint_senses: dict[str, int]


@dataclass(frozen=True, slots=True)
class PerfBaseline:
    scenario: dict[str, Any]
    created_utc: str
    python: str
    platform: str
    pulp: str
    solver: str
    status: str
    objective_value: float
    solution_fingerprint: str
    median_solve_seconds: float
    problem_metrics: ProblemMetrics


@dataclass(frozen=True, slots=True)
class PerfRunResult:
    status: str
    objective_value: float
    solution_fingerprint: str
    solve_seconds: float
    problem_metrics: ProblemMetrics


def _collect_problem_metrics(problem: pulp.LpProblem) -> ProblemMetrics:
    vars_list = problem.variables()

    # Variable category counts.
    cat_counts: dict[str, int] = {"Binary": 0, "Integer": 0, "Continuous": 0, "Other": 0}
    for v in vars_list:
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

    return ProblemMetrics(
        num_variables=len(vars_list),
        num_constraints=len(problem.constraints),
        variable_categories=cat_counts,
        constraint_senses=sense_counts,
    )


def run_solve_and_measure(
    scenario: PerfScenario,
    *,
    time_limit_seconds: int | None = None,
    enable_solver_output: bool = False,
) -> PerfRunResult:
    start = time.perf_counter()

    data_filter = json.loads(scenario.data_filter_json_path.read_text(encoding="utf-8-sig"))

    num_rounds = data_filter.get("num_rounds")
    squad_ids = data_filter.get("squad_ids") or []
    squad_id_filter = frozenset(int(x) for x in squad_ids) if squad_ids else None

    team_rules = load_team_rules_from_json(scenario.team_rules_json_path)
    rounds = load_rounds_from_json(scenario.rounds_json_path, num_rounds=int(num_rounds) if num_rounds else None)

    players = load_players_from_json(
        scenario.players_json_path,
        position_updates_csv=scenario.position_updates_csv_path,
        squad_id_filter=squad_id_filter,
    )
    model_input_data = build_model_input_data(players=players, team_rules=team_rules, rounds=rounds)

    problem, decision_variables = formulate_problem(model_input_data)
    problem_metrics = _collect_problem_metrics(problem)

    solver = (
        pulp.PULP_CBC_CMD(msg=enable_solver_output, timeLimit=time_limit_seconds)
        if time_limit_seconds
        else pulp.PULP_CBC_CMD(msg=enable_solver_output)
    )

    status_code = problem.solve(solver)
    status = pulp.LpStatus[status_code]
    objective_value = float(pulp.value(problem.objective) or 0.0)

    if status == "Optimal":
        summary = build_solution_summary(
            model_input_data=model_input_data,
            decision_variables=decision_variables,
            problem=problem,
        )
        payload = solution_summary_to_json_dict(summary)
    else:
        payload = {"status": status, "objective_value": objective_value}

    end = time.perf_counter()

    fingerprint = fingerprint_solution_payload(payload)

    return PerfRunResult(
        status=str(payload.get("status", "")),
        objective_value=float(payload.get("objective_value", 0.0)),
        solution_fingerprint=fingerprint,
        solve_seconds=end - start,
        problem_metrics=problem_metrics,
    )


def fingerprint_solution_payload(payload: Mapping[str, Any]) -> str:
    """Create a stable hash of the (JSON-serialisable) solution payload."""

    payload_copy: dict[str, Any] = dict(payload)

    # Defensive: ignore any future fields that might vary run-to-run.
    payload_copy.pop("created_utc", None)
    payload_copy.pop("solve_seconds", None)

    canonical = json.dumps(payload_copy, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_median_result(results: Iterable[PerfRunResult]) -> PerfRunResult:
    results = list(results)
    if not results:
        raise ValueError("results cannot be empty")

    # Correctness fields must be identical across repeats.
    statuses = {r.status for r in results}
    objectives = {r.objective_value for r in results}
    fingerprints = {r.solution_fingerprint for r in results}

    metric_jsons = {
        json.dumps(asdict(r.problem_metrics), sort_keys=True, separators=(",", ":")) for r in results
    }

    if len(statuses) != 1 or len(objectives) != 1 or len(fingerprints) != 1 or len(metric_jsons) != 1:
        raise AssertionError(
            "Perf run is not deterministic across repeats. "
            f"statuses={statuses}, objectives={objectives}, fingerprints={fingerprints}, metric_sets={len(metric_jsons)}"
        )

    return PerfRunResult(
        status=results[0].status,
        objective_value=results[0].objective_value,
        solution_fingerprint=results[0].solution_fingerprint,
        solve_seconds=float(median([r.solve_seconds for r in results])),
        problem_metrics=results[0].problem_metrics,
    )


def baseline_path_for(repo_root: Path, scenario_name: str) -> Path:
    return repo_root / "tests" / "perf_baselines" / f"{scenario_name}.json"


def load_baseline(path: Path) -> PerfBaseline:
    raw = json.loads(path.read_text(encoding="utf-8"))

    pm = raw.get("problem_metrics")
    if pm is None:
        pm = {
            "num_variables": 0,
            "num_constraints": 0,
            "variable_categories": {},
            "constraint_senses": {},
        }
    raw["problem_metrics"] = ProblemMetrics(**pm)

    return PerfBaseline(**raw)


def write_baseline(path: Path, baseline: PerfBaseline) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(baseline), indent=2, sort_keys=True), encoding="utf-8")


def make_baseline(scenario: PerfScenario, median_result: PerfRunResult) -> PerfBaseline:
    return PerfBaseline(
        scenario={
            "name": scenario.name,
            "players_json_path": str(scenario.players_json_path),
            "position_updates_csv_path": str(scenario.position_updates_csv_path),
            "team_rules_json_path": str(scenario.team_rules_json_path),
            "rounds_json_path": str(scenario.rounds_json_path),
            "data_filter_json_path": str(scenario.data_filter_json_path),
            "repeats": scenario.repeats,
        },
        created_utc=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(),
        platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
        pulp=getattr(pulp, "__version__", "unknown"),
        solver="CBC (via PuLP)",
        status=median_result.status,
        objective_value=median_result.objective_value,
        solution_fingerprint=median_result.solution_fingerprint,
        median_solve_seconds=median_result.solve_seconds,
        problem_metrics=median_result.problem_metrics,
    )
