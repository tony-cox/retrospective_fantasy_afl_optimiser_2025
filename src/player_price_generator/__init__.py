"""Generate synthetic AFL Fantasy seasons from projections.

This package is intentionally separate from :mod:`retro_fantasy`.

The goal is to take some *prospective* inputs (player projections, opponent
strength adjustments, uncertainty assumptions), run a Monte Carlo simulation
to generate per-round scores, apply a pricing model to generate per-round
prices, then export a JSON payload compatible with :func:`retro_fantasy.io.load_players_from_json`.

Only a scaffold is provided for now. The real simulation and pricing logic
will be implemented incrementally.
"""

from .data import (
    PlayerMeta,
    PricingConfig,
    ProjectionDataset,
    ProjectionInput,
    SimulationConfig,
)
from .export import build_players_final_records
from .io import load_projection_dataset
from .pricing import generate_round_prices
from .simulate import simulate_round_scores

__all__ = [
    "PlayerMeta",
    "PricingConfig",
    "ProjectionDataset",
    "ProjectionInput",
    "SimulationConfig",
    "load_projection_dataset",
    "simulate_round_scores",
    "generate_round_prices",
    "build_players_final_records",
]
