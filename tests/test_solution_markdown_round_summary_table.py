from __future__ import annotations

from scripts.solution_to_markdown import solution_json_to_markdown


def test_solution_json_to_markdown_includes_round_summary_table_with_trades_and_financials() -> None:
    payload = {
        "status": "Optimal",
        "objective_value": 0.0,
        "rounds": {
            "1": {
                "summary": {"round_number": 1, "total_team_points": 10, "captain_player_name": "", "bank_balance": 100, "total_value": 9100},
                "trades": None,
                "team": [],
            },
            "2": {
                "summary": {"round_number": 2, "total_team_points": 20, "captain_player_name": "", "bank_balance": 200, "total_value": 9200},
                "trades": {
                    "round_number": 2,
                    "traded_out": [{"player_id": 1, "player_name": "Out A", "price": 111}],
                    "traded_in": [{"player_id": 2, "player_name": "In B", "price": 222}],
                },
                "team": [],
            },
        },
    }

    md = solution_json_to_markdown(payload)

    assert "## Round summary" in md
    assert "| Round | Points | Bank balance | Total value | Traded out | Traded in |" in md

    assert "| R1 | 10 | $100 | $9,100 |  |  |" in md
    assert "| R2 | 20 | $200 | $9,200 | Out A | In B |" in md
