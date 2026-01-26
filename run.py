from __future__ import annotations

from pathlib import Path

from retro_fantasy.main import solve_retro_fantasy


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    data_dir = repo_root / "data"

    result = solve_retro_fantasy(
        players_json_path=data_dir / "players_final.json",
        position_updates_csv_path=data_dir / "position_updates.csv",
        solve=False,
    )

    print(f"Solve status: {result.status}")
    print(f"Objective value: {result.objective_value}")
    print(f"Constraints: {len(result.problem.constraints)}")
    print(f"Decision variables: {len(result.problem.variables())}")


if __name__ == "__main__":
    main()
