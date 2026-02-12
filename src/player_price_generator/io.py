"""Input loading helpers for :mod:`player_price_generator`.

This module is responsible for file-format knowledge (CSV/JSON/etc) and for
assembling :class:`player_price_generator.data.ProjectionDataset`.

Scaffold only: functions are stubs for now.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from .data import ProjectionDataset


def load_projection_dataset(
    *,
    players_path: str | Path,
    projections_path: str | Path,
    rounds_path: str | Path | None = None,
) -> ProjectionDataset:
    """Load player metadata + projection inputs.

    Parameters
    ----------
    players_path:
        File containing player identity info (ids, names, squad, original positions).
        This may be derived from a prior season's `players_final.json`.
    projections_path:
        File containing per-player projection parameters (e.g. average and variance).
    rounds_path:
        Optional file specifying which rounds to generate.

    Returns
    -------
    ProjectionDataset
        In-memory representation suitable for simulation.

    Notes
    -----
    Not implemented yet.
    """

    raise NotImplementedError
