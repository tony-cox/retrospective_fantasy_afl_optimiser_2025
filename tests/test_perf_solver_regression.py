from __future__ import annotations

from pathlib import Path

import pytest

from perf_utils import (
    PerfScenario,
    baseline_path_for,
    compute_median_result,
    load_baseline,
    make_baseline,
    run_solve_and_measure,
    write_baseline,
)


@pytest.mark.perf
def test_filtered_production_scenario_no_objective_degradation_and_no_large_slowdown(pytestconfig: pytest.Config) -> None:
    """Opt-in perf/regression test.

    This test is skipped unless you run pytest with `--run-perf`.

    What it validates
    -----------------
    1) We still solve to *Optimal* on a deterministic, filtered production scenario.
    2) The optimal objective value (and full solution fingerprint) does not change.
    3) Median wall time does not regress beyond an allowed ratio vs baseline.

    Notes
    -----
    We intentionally avoid asserting an absolute time threshold as wall-clock
    times vary across machines. Instead we compare to a stored baseline and use
    a ratio.
    """

    repo_root = Path(__file__).resolve().parents[1]

    scenario = PerfScenario(
        name="filtered_production_2_teams_3_rounds",
        players_json_path=repo_root / "data" / "players_final.json",
        position_updates_csv_path=repo_root / "data" / "position_updates.csv",
        team_rules_json_path=repo_root / "data" / "team_rules.json",
        rounds_json_path=repo_root / "data" / "rounds.json",
        data_filter_json_path=repo_root / "data" / "data_filter.json",
        repeats=3,
    )

    # Run multiple times to reduce noise and take the median.
    results = [run_solve_and_measure(scenario) for _ in range(scenario.repeats)]
    median_result = compute_median_result(results)

    assert median_result.status == "Optimal"

    baseline_path = baseline_path_for(repo_root, scenario.name)
    update_baseline = bool(pytestconfig.getoption("--update-perf-baseline"))

    baseline_missing = not baseline_path.exists()
    baseline_uninitialised = False
    if not baseline_missing:
        existing = load_baseline(baseline_path)
        baseline_uninitialised = existing.status == "UNINITIALISED"

    if update_baseline or baseline_missing or baseline_uninitialised:
        baseline = make_baseline(scenario, median_result)
        write_baseline(baseline_path, baseline)
        pytest.skip(
            "Perf baseline "
            f"{'updated' if update_baseline else 'created'} at: {baseline_path} "
            f"(median_solve_seconds={median_result.solve_seconds:.3f})"
        )

    baseline = load_baseline(baseline_path)

    # Correctness guardrails: no solution degradation.
    assert median_result.status == baseline.status
    assert median_result.objective_value == pytest.approx(baseline.objective_value, abs=1e-6)
    assert median_result.solution_fingerprint == baseline.solution_fingerprint

    # Performance guardrail: no large regressions (ratio-based).
    max_ratio = float(pytestconfig.getoption("--perf-max-regression-ratio"))
    assert median_result.solve_seconds <= baseline.median_solve_seconds * max_ratio
