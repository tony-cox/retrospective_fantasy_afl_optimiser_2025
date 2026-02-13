"""Export helpers.

The primary export target is a JSON list compatible with the production file
format in `data/players_final.json` so that :func:`retro_fantasy.io.load_players_from_json`
can read it without special casing.

We intentionally export a *minimal* record schema. The retrospective optimiser
only depends on:
- player identity (id + names)
- position codes (positions + original_positions)
- per-round scores and prices under stats.scores / stats.prices

Most other production fields (status, ranks, ownership, etc.) are redundant for
this project and omitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from retro_fantasy.data import Position

from .data import ProjectedPlayer, RoundPrices, SimulatedScores


_POSITION_TO_CODE: Mapping[Position, int] = {
    Position.DEF: 1,
    Position.MID: 2,
    Position.RUC: 3,
    Position.FWD: 4,
}


def _position_codes(positions: Iterable[Position]) -> list[int]:
    codes = sorted({_POSITION_TO_CODE[p] for p in positions})
    if not codes:
        raise ValueError("Player has no positions")
    return codes


def build_players_final_records(
    *,
    players: Mapping[str, ProjectedPlayer],
    simulated_scores: SimulatedScores,
    round_prices: RoundPrices,
) -> list[dict[str, Any]]:
    """Build a `players_final.json`-compatible record list.

    Parameters
    ----------
    players:
        Mapping of player name -> ProjectedPlayer.

    simulated_scores:
        Mapping player name -> round -> score. Missing rounds are treated as did-not-play.

    round_prices:
        Mapping player name -> round -> price.

    Returns
    -------
    list[dict[str, Any]]
        A list of player dict records compatible with :func:`retro_fantasy.io.load_players_from_json`.

    Notes
    -----
    - We set `positions` and `original_positions` to the same value.
    - We export only {id, names, positions, squad_id, stats:{scores, prices}}.
      Additional fields in the production schema are not used by the optimiser.
    """

    records: list[dict[str, Any]] = []

    # Stable ordering for deterministic outputs
    for idx, name in enumerate(sorted(players.keys()), start=1):
        p = players[name]

        codes = _position_codes(p.positions)
        scores_by_round = simulated_scores.get(name, {})
        prices_by_round = round_prices.get(name, {})

        # The retro loader expects dict keys as strings representing round numbers.
        scores_out: dict[str, float] = {str(r): float(s) for r, s in sorted(scores_by_round.items())}
        prices_out: dict[str, float] = {str(r): float(v) for r, v in sorted(prices_by_round.items())}

        # Split name into first/last similarly to the production dataset.
        parts = p.name.split(" ")
        first_name = parts[0] if parts else p.name
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        records.append(
            {
                "id": idx,
                "first_name": first_name,
                "last_name": last_name,
                "squad_id": None,
                "positions": codes,
                "original_positions": codes,
                "stats": {
                    "scores": scores_out,
                    "prices": prices_out,
                },
            }
        )

    return records
