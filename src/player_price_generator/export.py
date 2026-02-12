"""Export helpers.

The primary export target is a JSON list compatible with the production file
format in `data/players_final.json` so that :func:`retro_fantasy.io.load_players_from_json`
can read it without special casing.

Scaffold only: implemented later.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Sequence

from .data import PlayerMeta, RoundPrices, SimulatedScores


def build_players_final_records(
    *,
    players: Mapping[int, PlayerMeta],
    simulated_scores: SimulatedScores,
    round_prices: RoundPrices,
) -> list[dict[str, Any]]:
    """Build a `players_final.json` compatible record list.

    Returns
    -------
    list[dict]
        Each entry is a dict similar to those found in `data/players_final.json`.

    Notes
    -----
    - Round keys in the JSON are typically strings ("1", "2", ...).
    - The schema in this repo expects `stats: {"scores": ..., "prices": ...}`.
    """

    raise NotImplementedError
