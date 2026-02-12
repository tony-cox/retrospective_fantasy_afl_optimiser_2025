"""Monte Carlo score simulation.

Scaffold only: implemented later.
"""

from __future__ import annotations

from collections import defaultdict

from .data import ProspectiveInputData, SimulatedScores, SimulationConfig


def simulate_round_scores(
    *,
    dataset: ProspectiveInputData,
    config: SimulationConfig,
) -> SimulatedScores:
    """Generate a per-round score series for each player.

    Basic implementation:
    - A player is considered to "play" in a round if their club appears in any
      fixture in that round.
    - For rounds they play, we set the simulated score to the player's
      `projection_mid`.
    - For rounds they do not play, no entry is created.

    Side-effect
    -----------
    Updates each :class:`~player_price_generator.data.ProjectedPlayer` instance
    by populating its ``simulated_scores_by_round`` dict.
    """

    # config is unused for the basic deterministic implementation, but kept for API stability.
    _ = config

    club_rounds: dict[str, set[int]] = defaultdict(set)
    for fixture in dataset.fixtures:
        club_rounds[fixture.home_club].add(fixture.round_number)
        club_rounds[fixture.away_club].add(fixture.round_number)

    results: SimulatedScores = {}
    for player in dataset.projected_players:
        played_rounds = club_rounds.get(player.club_code, set())
        score_by_round = {r: float(player.projection_mid) for r in played_rounds}

        # Store on the player instance as requested
        player.simulated_scores_by_round.clear()
        player.simulated_scores_by_round.update(score_by_round)

        results[player.name] = score_by_round

    return results
