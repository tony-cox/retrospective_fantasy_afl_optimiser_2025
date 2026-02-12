"""Pricing model approximations.

This module will contain one or more price generation models based on a score
stream. The end goal is to output a per-round `prices` dict compatible with the
schema expected by :func:`retro_fantasy.io.load_players_from_json`.

Scaffold only: implemented later.
"""

from __future__ import annotations

from .data import PricingConfig, RoundPrices, SimulatedScores


def generate_round_prices(
    *,
    simulated_scores: SimulatedScores,
    config: PricingConfig,
) -> RoundPrices:
    """Generate per-round prices for each player.

    Parameters
    ----------
    simulated_scores:
        Mapping of player_id -> round -> score.
    config:
        PricingConfig controlling the approximation.

    Returns
    -------
    RoundPrices
        Mapping of player_id -> round -> price.

    Notes
    -----
    Not implemented yet.
    """

    raise NotImplementedError
