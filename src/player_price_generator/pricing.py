"""Pricing model approximations.

Implements a rolling weighted-average pricing update, matching the formula
outlined in the project notes.

Key behaviour
------------
- Round 1 price is the provided starting price.
- From round 2 onward, price is updated using a rolling window of the player's
  *most recent games played*.
- If a player doesn't play in a round (no score entry), that round is skipped
  for the score window.

This module returns a per-round `prices` dict compatible with the schema
expected by :func:`retro_fantasy.io.load_players_from_json`.
"""

from __future__ import annotations

from typing import List

from .data import PricingConfig, RoundPrices, SimulatedScores


def _weights_for_previous_games(n_previous_games_available: int) -> tuple[int, List[int]]:
    """Return (alpha_numer, score_weights_numerators).

    The price update is:

        price_next = (alpha/60) * price_prev + magic_number * sum_i (w_i/60 * score_i)

    where score_i are the previous games played in recency order.

    For 1..5 previous games available:
      alpha is 55, 51, 48, 46, 45
      weights are [5], [5,4], [5,4,3], [5,4,3,2], [5,4,3,2,1]

    For >=5 games, it stays at alpha=45 and weights=[5,4,3,2,1].
    """

    if n_previous_games_available <= 0:
        raise ValueError("Must have at least 1 previous game to compute update")

    score_weights_full = [5, 4, 3, 2, 1]
    m = min(5, n_previous_games_available)
    score_weights = score_weights_full[:m]

    if m == 1:
        alpha = 55
    elif m == 2:
        alpha = 51
    elif m == 3:
        alpha = 48
    elif m == 4:
        alpha = 46
    else:
        alpha = 45

    return alpha, score_weights


def _compute_price_for_round(
    *,
    price_prev: float,
    previous_game_scores_most_recent_first: List[float],
    magic_number: float,
) -> float:
    """Compute the next-round price from previous price and prior-game scores."""

    alpha, weights = _weights_for_previous_games(len(previous_game_scores_most_recent_first))

    score_term = 0.0
    for w, s in zip(weights, previous_game_scores_most_recent_first):
        score_term += (w / 60.0) * s

    return (alpha / 60.0) * price_prev + magic_number * score_term


def generate_round_prices(
    *,
    starting_prices_round_1: dict[str, float],
    simulated_scores: SimulatedScores,
    max_round: int,
    config: PricingConfig,
) -> RoundPrices:
    """Generate per-round prices for each player.

    Parameters
    ----------
    starting_prices_round_1:
        Mapping of player_name -> known round-1 price from input data.
    simulated_scores:
        Mapping of player_name -> round -> score.

        Scores are expected to exist only for rounds the player played.
        Missing rounds are treated as "did not play" and skipped for the rolling
        score window.

    max_round:
        Last round to generate prices for (inclusive). Must be >= 1.

    config:
        PricingConfig controlling the approximation.

    Returns
    -------
    RoundPrices
        Mapping of player_name -> round -> price.

    Notes
    -----
    Pricing rules implemented:
    - price[1] = starting price
    - For r>=2:
        price[r] depends on price[r-1] and the most recent games played prior to r.
      If the player did not play in r-1, we still compute price[r] from price[r-1]
      but the score window ignores that round (it only uses previously played games).

    This matches the behaviour described: the "previous score" refers to the most
    recent score in which the player played.
    """

    if max_round < 1:
        raise ValueError("max_round must be >= 1")

    magic = float(config.magic_number)

    players = set(starting_prices_round_1.keys()) | set(simulated_scores.keys())

    prices: RoundPrices = {}

    for player in players:
        if player not in starting_prices_round_1:
            raise KeyError(f"Missing starting round-1 price for player {player!r}")

        p_prices: dict[int, float] = {1: float(starting_prices_round_1[player])}

        # Keep a history of previous *games played* scores, most-recent-first.
        prev_game_scores: List[float] = []

        # Seed the history with any pre-season / opening round (round 0) score and
        # the round-1 score if they played.
        #
        # Important: round-1 price is fixed to starting price and is NOT updated.
        # Round-2 pricing may include both round-0 and round-1 scores.
        p_scores = simulated_scores.get(player, {})
        if 0 in p_scores:
            prev_game_scores.insert(0, float(p_scores[0]))
        if 1 in p_scores:
            prev_game_scores.insert(0, float(p_scores[1]))

        for r in range(2, max_round + 1):
            if prev_game_scores:
                p_prices[r] = _compute_price_for_round(
                    price_prev=p_prices[r - 1],
                    previous_game_scores_most_recent_first=prev_game_scores,
                    magic_number=magic,
                )
            else:
                # No prior games: carry forward the starting price.
                # This is defensively defined; in realistic inputs, round 1 exists.
                p_prices[r] = p_prices[r - 1]

            # After computing price[r], if player played in round r, update history.
            if r in p_scores:
                prev_game_scores.insert(0, float(p_scores[r]))

            # Cap to last 5 games.
            if len(prev_game_scores) > 5:
                prev_game_scores = prev_game_scores[:5]

        prices[player] = p_prices

    return prices
