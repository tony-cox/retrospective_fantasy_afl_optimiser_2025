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

    # Captain should be bold, include position/slot on second line, and price on third line.
    assert "| A | **5**<br>MID / ON<br>$0 |" in md

    # Non-scored should be italic, include position/slot on second line, and price on third line.
    assert "| B | *7*<br>DEF / BENCH<br>$0 |" in md

    # Total row should be bold.
    assert "| **Total scored** | **10** |" in md


def test_solution_json_to_markdown_orders_rows_as_cascade_r1_then_traded_in() -> None:
    payload = {
        "status": "Optimal",
        "objective_value": 0.0,
        "rounds": {
            "1": {
                "summary": {"round_number": 1, "total_team_points": 0, "captain_player_name": ""},
                "trades": None,
                "team": [
                    {
                        "player_id": 1,
                        "player_name": "P1",
                        "slot": "on_field",
                        "position": "DEF",
                        "price": 0,
                        "score": 1,
                        "scored": True,
                        "captain": False,
                    },
                    {
                        "player_id": 2,
                        "player_name": "P2",
                        "slot": "on_field",
                        "position": "MID",
                        "price": 0,
                        "score": 2,
                        "scored": True,
                        "captain": False,
                    },
                ],
            },
            "2": {
                "summary": {"round_number": 2, "total_team_points": 0, "captain_player_name": ""},
                "trades": {
                    "round_number": 2,
                    "traded_in": [
                        {"player_id": 3, "player_name": "P3", "price": 0},
                        {"player_id": 4, "player_name": "P4", "price": 0},
                    ],
                    "traded_out": [],
                },
                "team": [
                    {
                        "player_id": 1,
                        "player_name": "P1",
                        "slot": "on_field",
                        "position": "DEF",
                        "price": 0,
                        "score": 1,
                        "scored": True,
                        "captain": False,
                    },
                    {
                        "player_id": 3,
                        "player_name": "P3",
                        "slot": "on_field",
                        "position": "MID",
                        "price": 0,
                        "score": 3,
                        "scored": True,
                        "captain": False,
                    },
                    {
                        "player_id": 4,
                        "player_name": "P4",
                        "slot": "bench",
                        "position": "DEF",
                        "price": 0,
                        "score": 4,
                        "scored": False,
                        "captain": False,
                    },
                ],
            },
        },
    }

    md = solution_json_to_markdown(payload)

    # Grab the first table's row order by finding the first occurrences of each player row.
    pos_p1 = md.find("| P1 |")
    pos_p2 = md.find("| P2 |")
    pos_p3 = md.find("| P3 |")
    pos_p4 = md.find("| P4 |")

    assert pos_p1 != -1 and pos_p2 != -1 and pos_p3 != -1 and pos_p4 != -1

    # Cascade expectation: r1 team first (P1 then P2), then traded-in (P3 then P4).
    assert pos_p1 < pos_p2 < pos_p3 < pos_p4

