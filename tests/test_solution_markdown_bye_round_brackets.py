from __future__ import annotations

from scripts.solution_to_markdown import solution_json_to_markdown


def test_round_by_round_detail_shows_brackets_for_onfield_not_scored_players() -> None:
    payload = {
        "status": "Optimal",
        "objective_value": 0.0,
        "rounds": {
            "1": {
                "summary": {"round_number": 1, "total_team_points": 100, "captain_player_name": ""},
                "trades": None,
                "team": [
                    {
                        "player_id": 1,
                        "player_name": "Onfield Counted",
                        "slot": "on_field",
                        "position": "MID",
                        "price": 500,
                        "score": 70,
                        "scored": True,
                        "captain": False,
                    },
                    {
                        "player_id": 2,
                        "player_name": "Onfield Not Counted",
                        "slot": "on_field",
                        "position": "MID",
                        "price": 400,
                        "score": 63,
                        "scored": False,
                        "captain": False,
                    },
                ],
            }
        },
    }

    md = solution_json_to_markdown(payload)

    # In the per-round team table we show:
    # - counted on-field: "63 pts" style without brackets
    # - not-counted on-field: "(63 pts)" to signal best-N exclusion
    assert "Onfield Counted" in md
    assert "70 pts" in md

    assert "Onfield Not Counted" in md
    assert "(63 pts)" in md
