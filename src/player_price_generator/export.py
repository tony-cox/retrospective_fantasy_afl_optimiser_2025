"""Export helpers.

The primary export target is a JSON list compatible with the production file
format in `data/players_final.json` so that :func:`retro_fantasy.io.load_players_from_json`
can read it without special casing.

Scaffold only: implemented later.
"""

from __future__ import annotations

from typing import Any, Mapping

from .data import ProjectedPlayer, RoundPrices, SimulatedScores


def build_players_final_records(
    *,
    players: Mapping[str, ProjectedPlayer],
    simulated_scores: SimulatedScores,
    round_prices: RoundPrices,
) -> list[dict[str, Any]]:
    """Build a `players_final.json` compatible record list.

    Parameters
    ----------
    players:
        Keyed by player name (as found in the projections input).

    Notes
    -----
    Still a scaffold.
    """

    raise NotImplementedError
