from __future__ import annotations

import json
from pathlib import Path

from retro_fantasy.io import load_rounds_from_json, load_team_rules_from_json
from retro_fantasy.main import solve_retro_fantasy


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    data_dir = repo_root / "data"

    team_rules = load_team_rules_from_json(data_dir / "team_rules.json")

    # Optional data filtering for small problems.
    # data_filter.json format:
    #   {"num_rounds": 3, "squad_ids": [40, 130]}
    data_filter_path = data_dir / "data_filter.json"
    num_rounds = None
    squad_id_filter = None
    if data_filter_path.exists():
        raw_filter = json.loads(data_filter_path.read_text(encoding="utf-8-sig"))

        nr = raw_filter.get("num_rounds")
        if nr is not None:
            num_rounds = int(nr)

        squad_ids = [int(x) for x in (raw_filter.get("squad_ids") or [])]
        if squad_ids:
            squad_id_filter = frozenset(squad_ids)

    rounds = load_rounds_from_json(data_dir / "rounds.json", num_rounds=num_rounds)

    result = solve_retro_fantasy(
        players_json_path=data_dir / "players_final.json",
        position_updates_csv_path=data_dir / "position_updates.csv",
        team_rules=team_rules,
        rounds=rounds,
        squad_id_filter=squad_id_filter,
        solve=False,
    )

    print(f"Solve status: {result.status}")
    print(f"Objective value: {result.objective_value}")
    print(f"Constraints: {len(result.problem.constraints)}")
    print(f"Decision variables: {len(result.problem.variables())}")


if __name__ == "__main__":
    main()
