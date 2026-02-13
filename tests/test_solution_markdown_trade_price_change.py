from __future__ import annotations

from scripts.solution_to_markdown import solution_json_to_markdown


def test_solution_markdown_traded_out_includes_price_change() -> None:
    payload = {
        "status": "Optimal",
        "objective_value": 0.0,
        "rounds": {
            "1": {
                "summary": {"round_number": 1, "total_team_points": 0, "captain_player_name": ""},
                "trades": None,
                "team": [],
            },
            "2": {
                "summary": {"round_number": 2, "total_team_points": 0, "captain_player_name": ""},
                "trades": {
                    "round_number": 2,
                    "traded_in": [],
                    "traded_out": [
                        {
                            "player_id": 1,
                            "player_name": "Daniel McStay",
                            "price": 547000,
                            "acquisition_price": 447000,
                            "price_change": 100000,
                        }
                    ],
                },
                "team": [],
            },
        },
    }

    md = solution_json_to_markdown(payload)
    assert "Daniel McStay – $547,000 (+$100,000)" in md
