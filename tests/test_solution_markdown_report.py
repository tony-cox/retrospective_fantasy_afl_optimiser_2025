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

    # In the per-round team table, we show "Name – $Price – Score pts".
    assert "A – $0 – 5 pts" in md
    assert "B – $0 – 7 pts" in md


def test_solution_json_to_markdown_includes_round_summary_table_heading() -> None:
    payload = {
        "status": "Optimal",
        "objective_value": 0.0,
        "rounds": {
            "1": {
                "summary": {"round_number": 1, "total_team_points": 0, "captain_player_name": ""},
                "trades": None,
                "team": [],
            }
        },
    }

    md = solution_json_to_markdown(payload)
    assert "## Round summary" in md
