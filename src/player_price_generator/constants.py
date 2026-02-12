"""Project-wide constants for :mod:`player_price_generator`.

This module exists to keep literal values and default assumptions centralized.
As algorithms solidify, we can move defaults from call sites into these symbols.

Scaffold-only for now.
"""

from __future__ import annotations

MAGIC_NUMBER: float = 10_502

# Monte Carlo simulation defaults
DEFAULT_N_SIMS: int = 1

# Placeholder for future:
# - default distribution settings
# - pricing model defaults (rolling window length, magic number, floors, etc.)
