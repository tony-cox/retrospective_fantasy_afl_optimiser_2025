"""Monte Carlo score simulation.

Scaffold only: implemented later.
"""

from __future__ import annotations

from .data import ProjectionDataset, SimulatedScores, SimulationConfig


def simulate_round_scores(
    *,
    dataset: ProjectionDataset,
    config: SimulationConfig,
) -> SimulatedScores:
    """Generate a per-round score series for each player.

    Returns
    -------
    SimulatedScores
        Mapping of player_id -> round -> simulated score.

    Notes
    -----
    - In future this may return full samples (n_sims) or summary statistics.
    - For now we expect a single representative season (e.g. one simulation draw,
      or the mean season) to be passed through to pricing.
    """

    raise NotImplementedError
