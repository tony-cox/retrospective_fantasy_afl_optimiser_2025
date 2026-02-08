from __future__ import annotations

from scripts.solution_to_markdown import solution_json_to_markdown


def test_solution_json_to_markdown_adds_bank_team_total_value_rows_when_present() -> None:
    payload = {
        "status": "Optimal",
        "objective_value": 0.0,
        "rounds": {
            "1": {
                "summary": {
                    "round_number": 1,
                    "total_team_points": 0,
                    "captain_player_name": "",
                    "bank_balance": 1000,
                    "team_value": 9000,
                    "total_value": 10000,
                },
                "trades": None,
                "team": [],
            }
        },
    }

    md = solution_json_to_markdown(payload)

    assert "| **Bank balance** |" in md
    assert "| **Team value** |" in md
    assert "| **Total value** |" in md

    # Values should be present in round column.
    assert "| **Bank balance** | $1,000 |" in md
    assert "| **Team value** | $9,000 |" in md
    assert "| **Total value** | $10,000 |" in md
