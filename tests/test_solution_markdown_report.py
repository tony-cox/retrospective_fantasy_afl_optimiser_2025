from __future__ import annotations

from scripts.solution_to_markdown import solution_json_to_markdown


def test_solution_json_to_markdown_formats_cells_for_scored_non_scored_and_captain() -> None:
    # Minimal, hand-written solution.json-like payload.
    payload = {
        "status": "Optimal",
        "objective_value": 10.0,
        "rounds": {
            "1": {
                "summary": {"round_number": 1, "total_team_points": 10, "captain_player_name": "A"},
                "trades": None,
                "team": [
                    {
                        "player_id": 1,
                        "player_name": "A",
                        "slot": "on_field",
                        "position": "MID",
                        "price": 0,
                        "score": 5,
                        "scored": True,
                        "captain": True,
                    },
                    {
                        "player_id": 2,
                        "player_name": "B",
                        "slot": "bench",
                        "position": "DEF",
                        "price": 0,
                        "score": 7,
                        "scored": False,
                        "captain": False,
                    },
                ],
            }
        },
    }

    md = solution_json_to_markdown(payload)

    # Captain should be bold, and include position/slot on second line.
    assert "| A | **5**<br>MID / ON |" in md

    # Non-scored should be italic, and include position/slot on second line.
    assert "| B | *7*<br>DEF / BENCH |" in md

    # Total row should be bold.
    assert "| **Total scored** | **10** |" in md
