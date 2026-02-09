from __future__ import annotations

from scripts.solution_to_markdown import solution_json_to_markdown


def test_solution_json_to_markdown_includes_starting_team_section_before_round_summary() -> None:
    payload = {
        "status": "Optimal",
        "objective_value": 0.0,
        "rounds": {
            "1": {
                "summary": {
                    "round_number": 1,
                    "total_team_points": 123,
                    "captain_player_name": "Cap",
                    "bank_balance": 1000,
                    "team_value": 9000,
                    "total_value": 10000,
                },
                "trades": None,
                "team": [
                    {"player_id": 1, "player_name": "Def A", "slot": "on_field", "position": "DEF", "price": 500, "score": 50},
                    {"player_id": 2, "player_name": "Def B", "slot": "bench", "position": "DEF", "price": 300, "score": 30},
                    {"player_id": 3, "player_name": "Util M", "slot": "utility_bench", "position": None, "price": 200, "score": 20},
                ],
            }
        },
    }

    md = solution_json_to_markdown(payload)

    start_idx = md.find("## Starting team")
    round_summary_idx = md.find("## Round summary")

    assert start_idx != -1
    assert round_summary_idx != -1
    assert start_idx < round_summary_idx

    assert "- Bank balance: $1,000" in md
    assert "- Team value: $9,000" in md
    assert "- Total value: $10,000" in md

    # Starting team should contain the round 1 team table.
    assert "| Position | On field | Bench |" in md
    assert "Def A" in md
    assert "Def B" in md
    assert "Util M" in md

    # But it should NOT show scores for the starting team.
    assert "pts" not in md[start_idx:round_summary_idx]
