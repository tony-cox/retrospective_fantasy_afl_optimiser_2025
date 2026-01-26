"""MILP formulation scaffold.

This module will incrementally implement the mathematical model described in
`formulation.md` using PuLP.

For now, we only provide the top-level problem builder.
"""

from __future__ import annotations

import pulp

from retro_fantasy.data import ModelInputData


def formulate_problem(model_input_data: ModelInputData) -> pulp.LpProblem:
    """Create the PuLP optimisation problem.

    Parameters
    ----------
    model_input_data:
        Fully constructed model input data (players, rounds, team rules).

    Returns
    -------
    pulp.LpProblem
        A PuLP problem instance. Objectives/constraints/variables will be added
        in subsequent steps.
    """

    # Defaulting to maximisation because our eventual objective is to maximise points.
    problem = pulp.LpProblem(name="retro_fantasy", sense=pulp.LpMaximize)

    # Placeholder. Next steps will add variables, objective, and constraints.
    _ = model_input_data

    return problem
