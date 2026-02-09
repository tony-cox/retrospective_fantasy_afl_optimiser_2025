from __future__ import annotations

from scripts.solution_to_markdown import solution_json_to_markdown


def test_solution_json_to_markdown_includes_verbose_round_sections_with_team_table_and_trades() -> None:
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
            },
            "2": {
                "summary": {
                    "round_number": 2,
                    "total_team_points": 456,
                    "captain_player_name": "Cap2",
                },
                "trades": {
                    "round_number": 2,
                    "traded_out": [{"player_id": 1, "player_name": "Def A", "price": 550}],
                    "traded_in": [{"player_id": 4, "player_name": "Mid X", "price": 600}],
                },
                "team": [
                    {"player_id": 4, "player_name": "Mid X", "slot": "on_field", "position": "MID", "price": 600, "score": 60},
                ],
            },
        },
    }

    md = solution_json_to_markdown(payload)

    assert "# Round-by-round detail" in md
    assert "## Round 1" in md
    assert "- Total scored points: **123**" in md
    assert "- Captain: **Cap**" in md

    # Trades section
    assert "- Trades: _None_" in md

    # Finances should appear after trades for round 1
    assert "**Round finances**" in md
    assert "- Bank balance: $1,000" in md
    assert "- Team value: $9,000" in md
    assert "- Total value: $10,000" in md

    assert "## Round 2" in md
    assert "- Traded out:" in md
    assert "Def A" in md
    assert "- Traded in:" in md
    assert "Mid X" in md

    # Team table section (utility is a ROW, not a column)
    assert "### Team" in md
    assert "| Position | On field | Bench |" in md
    # Ensure utility row exists
    assert "| UTIL |" in md
    # Utility bench player should appear under Bench
    assert "Util M" in md
