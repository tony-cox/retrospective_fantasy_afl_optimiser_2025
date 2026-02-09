from __future__ import annotations

from scripts.solution_to_markdown import solution_json_to_markdown


def test_solution_json_to_markdown_includes_bank_and_values_in_round_summary_and_verbose_section() -> None:
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

    # Round summary table should include bank and total.
    assert "## Round summary" in md
    assert "| R1 | 0 | $1,000 | $10,000 |" in md

    # Verbose section should include round finances.
    assert "**Round finances**" in md
    assert "- Bank balance: $1,000" in md
    assert "- Team value: $9,000" in md
    assert "- Total value: $10,000" in md
