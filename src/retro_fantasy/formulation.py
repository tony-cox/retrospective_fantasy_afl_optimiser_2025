"""MILP formulation scaffold.

This module will incrementally implement the mathematical model described in
`formulation.md` using PuLP.

For now, we only provide the top-level problem builder and empty scaffolding
functions for decision variables/objective/constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

import pulp

from retro_fantasy.data import ModelInputData, Position


# ============================================================================
# Data structures
# ============================================================================


@dataclass(slots=True)
class DecisionVariables:
    """Container for all PuLP decision variables.

    Notes
    -----
    We keep each decision variable family in its own field so objective and
    constraints can reference them cleanly.

    All fields are placeholders for now and will be populated incrementally.
    """

    # Helper selection variable: is player p in the 30-player squad in round r?
    # x[p, r] ∈ {0,1}
    x_selected: Dict[Tuple[int, int], pulp.LpVariable] = field(default_factory=dict)

    # Positional selection variables:
    # y_onfield[p, k, r] ∈ {0,1}
    y_onfield: Dict[Tuple[int, Position, int], pulp.LpVariable] = field(default_factory=dict)

    # y_bench[p, k, r] ∈ {0,1}
    y_bench: Dict[Tuple[int, Position, int], pulp.LpVariable] = field(default_factory=dict)

    # Utility bench selection:
    # y_utility[p, r] ∈ {0,1}
    y_utility: Dict[Tuple[int, int], pulp.LpVariable] = field(default_factory=dict)

    # Captain selection:
    # z[p, r] ∈ {0,1}
    captain: Dict[Tuple[int, int], pulp.LpVariable] = field(default_factory=dict)

    # "Scored" selection for bye rounds:
    # y[p, r] ∈ {0,1}
    scored: Dict[Tuple[int, int], pulp.LpVariable] = field(default_factory=dict)

    # Trade indicator variables:
    # in[p, r] ∈ {0,1} and out[p, r] ∈ {0,1}
    traded_in: Dict[Tuple[int, int], pulp.LpVariable] = field(default_factory=dict)
    traded_out: Dict[Tuple[int, int], pulp.LpVariable] = field(default_factory=dict)

    # Bank balance:
    # bank[r] ≥ 0
    bank: Dict[int, pulp.LpVariable] = field(default_factory=dict)


# ============================================================================
# Top-level orchestrator
# ============================================================================


def formulate_problem(model_input_data: ModelInputData) -> pulp.LpProblem:
    """Create the PuLP optimisation problem.

    Parameters
    ----------
    model_input_data:
        Fully constructed model input data (players, rounds, team rules).

    Returns
    -------
    pulp.LpProblem
        A PuLP problem instance. Objectives/constraints/decision variables will be added
        incrementally as this module is implemented.
    """

    problem = pulp.LpProblem(name="retro_fantasy", sense=pulp.LpMaximize)

    decision_variables = create_decision_variables(problem, model_input_data)
    add_objective(problem, model_input_data, decision_variables)
    add_constraints(problem, model_input_data, decision_variables)

    return problem


# ============================================================================
# Second-level orchestrator: Decision variables
# ============================================================================


def create_decision_variables(problem: pulp.LpProblem, model_input_data: ModelInputData) -> DecisionVariables:
    """Create and register all decision variables."""

    x_selected = _create_squad_selection_decision_variables(problem, model_input_data)

    y_onfield, y_bench, y_utility = _create_positional_selection_decision_variables(problem, model_input_data)

    captain = _create_captain_decision_variables(problem, model_input_data)
    scored = _create_scored_decision_variables(problem, model_input_data)

    traded_in, traded_out = _create_trade_indicator_decision_variables(problem, model_input_data)

    bank = _create_bank_balance_decision_variables(problem, model_input_data)

    return DecisionVariables(
        x_selected=x_selected,
        y_onfield=y_onfield,
        y_bench=y_bench,
        y_utility=y_utility,
        captain=captain,
        scored=scored,
        traded_in=traded_in,
        traded_out=traded_out,
        bank=bank,
    )


def _create_squad_selection_decision_variables(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
) -> Dict[Tuple[int, int], pulp.LpVariable]:
    """Create x[p, r] selection decision variables (player is in squad)."""

    return {
        (p, r): pulp.LpVariable(f"x_selected_{p}_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)
        for (p, r) in model_input_data.idx_player_round
    }


def _create_positional_selection_decision_variables(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
) -> tuple[
    Dict[Tuple[int, Position, int], pulp.LpVariable],
    Dict[Tuple[int, Position, int], pulp.LpVariable],
    Dict[Tuple[int, int], pulp.LpVariable],
]:
    """Create positional decision variables.

    Returns
    -------
    (y_onfield, y_bench, y_utility)

    Notes
    -----
    We create the full cross-product variable families here for now.
    Eligibility and slot-count constraints will later constrain feasible
    combinations.
    """

    y_onfield = {
        (p, k, r): pulp.LpVariable(f"y_onfield_{p}_{k.value}_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)
        for (p, k, r) in model_input_data.idx_player_position_round
    }

    y_bench = {
        (p, k, r): pulp.LpVariable(f"y_bench_{p}_{k.value}_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)
        for (p, k, r) in model_input_data.idx_player_position_round
    }

    y_utility = {
        (p, r): pulp.LpVariable(f"y_utility_{p}_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)
        for (p, r) in model_input_data.idx_player_round
    }

    return y_onfield, y_bench, y_utility


def _create_captain_decision_variables(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
) -> Dict[Tuple[int, int], pulp.LpVariable]:
    """Create captain decision variables z[p, r]."""

    return {
        (p, r): pulp.LpVariable(f"captain_{p}_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)
        for (p, r) in model_input_data.idx_player_round
    }


def _create_scored_decision_variables(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
) -> Dict[Tuple[int, int], pulp.LpVariable]:
    """Create scored decision variables y[p, r] (which players are counted)."""

    return {
        (p, r): pulp.LpVariable(f"scored_{p}_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)
        for (p, r) in model_input_data.idx_player_round
    }


def _create_trade_indicator_decision_variables(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
) -> tuple[
    Dict[Tuple[int, int], pulp.LpVariable],
    Dict[Tuple[int, int], pulp.LpVariable],
]:
    """Create trade indicator decision variables (traded_in, traded_out).

    These are only meaningful for rounds r > 1 (they represent changes from r-1 to r).
    """

    traded_in = {
        (p, r): pulp.LpVariable(f"traded_in_{p}_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)
        for (p, r) in model_input_data.idx_player_round_excluding_1
    }

    traded_out = {
        (p, r): pulp.LpVariable(f"traded_out_{p}_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)
        for (p, r) in model_input_data.idx_player_round_excluding_1
    }

    return traded_in, traded_out


def _create_bank_balance_decision_variables(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
) -> Dict[int, pulp.LpVariable]:
    """Create bank balance decision variables bank[r]."""

    return {
        r: pulp.LpVariable(f"bank_{r}", lowBound=0, cat=pulp.LpContinuous) for r in model_input_data.idx_round
    }


# ============================================================================
# Second-level orchestrator: Objective
# ============================================================================


def add_objective(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Add the objective function to the problem.

    This function assembles the objective expression in parts and sets it once
    on the PuLP problem.
    """

    base_expr = _build_objective_base_scoring_expression(problem, model_input_data, decision_variables)
    captain_expr = _build_objective_captain_bonus_expression(problem, model_input_data, decision_variables)

    # Important: in PuLP, adding another objective typically overwrites the
    # previous one. So we build a single combined expression and set it once.
    problem += base_expr + captain_expr


def _build_objective_base_scoring_expression(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> pulp.LpAffineExpression:
    """Build the base scoring term of the objective.

    Represents:
        sum_{r in R} sum_{p in P} s[p,r] * scored[p,r]
    """

    _ = problem

    terms: list[pulp.LpAffineExpression] = []
    for (player_id, round_number), scored_var in decision_variables.scored.items():
        terms.append(model_input_data.score(player_id, round_number) * scored_var)

    return pulp.lpSum(terms)


def _build_objective_captain_bonus_expression(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> pulp.LpAffineExpression:
    """Build the captain bonus term of the objective.

    Represents:
        sum_{r in R} sum_{p in P} s[p,r] * captain[p,r]

    Adding this term to the base scoring term doubles the captain's counted
    score (assuming constraints later enforce captain implies scored).
    """

    _ = problem

    terms: list[pulp.LpAffineExpression] = []
    for (player_id, round_number), captain_var in decision_variables.captain.items():
        terms.append(model_input_data.score(player_id, round_number) * captain_var)

    return pulp.lpSum(terms)


# ============================================================================
# Linking Constraints
# ============================================================================


def _add_linking_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Linking Constraints section."""

    _add_linking_constraints_overall_selection_equals_positional_selection(problem, model_input_data, decision_variables)
    _add_linking_constraints_at_most_one_slot_per_player_per_round(problem, model_input_data, decision_variables)


def _add_linking_constraints_overall_selection_equals_positional_selection(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Linking constraint: overall selection equals sum of positional selections.

    In the full model, x_selected is a helper indicating whether the player is
    in the squad at all in round r.

    Given we also enforce "at most one slot per player per round", we can link
    x_selected to the slot indicator via equality.
    """

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round:
            slot_sum = pulp.lpSum(
                decision_variables.y_onfield[(p, k, r)] + decision_variables.y_bench[(p, k, r)]
                for k in model_input_data.positions
            ) + decision_variables.y_utility[(p, r)]
            problem += decision_variables.x_selected[(p, r)] == slot_sum, f"link_x_equals_positions_{p}_{r}"


def _add_linking_constraints_at_most_one_slot_per_player_per_round(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Linking constraint: each player occupies at most one slot per round."""

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round:
            slot_sum = pulp.lpSum(
                decision_variables.y_onfield[(p, k, r)] + decision_variables.y_bench[(p, k, r)]
                for k in model_input_data.positions
            ) + decision_variables.y_utility[(p, r)]
            problem += slot_sum <= 1, f"link_at_most_one_slot_{p}_{r}"


# ============================================================================
# Second-level orchestrator: Constraints
# ============================================================================


def add_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Add all constraints to the problem.

    This is an orchestrator that delegates to one function per formulation
    constraint section, with further decomposition where appropriate.
    """

    _add_initial_bank_balance_constraints(problem, model_input_data, decision_variables)
    _add_bank_balance_recurrence_constraints(problem, model_input_data, decision_variables)

    _add_trade_indicator_linking_constraints(problem, model_input_data, decision_variables)

    _add_linking_constraints(problem, model_input_data, decision_variables)

    _add_maximum_team_changes_per_round_constraints(problem, model_input_data, decision_variables)

    _add_positional_structure_constraints(problem, model_input_data, decision_variables)

    _add_position_eligibility_constraints(problem, model_input_data, decision_variables)

    _add_scoring_selection_constraints(problem, model_input_data, decision_variables)

    _add_captaincy_constraints(problem, model_input_data, decision_variables)


def _add_initial_bank_balance_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Initial Bank Balance constraints.

    bank[1] = salary_cap - sum_p price[p,1] * x_selected[p,1]
    """

    if 1 not in model_input_data.round_numbers:
        return

    r = 1
    total_spend = pulp.lpSum(
        model_input_data.price(p, r) * decision_variables.x_selected[(p, r)] for p in model_input_data.player_ids
    )

    problem += (
        decision_variables.bank[r] == model_input_data.salary_cap - total_spend
    ), "bank_initial_round_1"


def _add_bank_balance_recurrence_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Bank Balance Recurrence constraints.

    For r > 1:
        bank[r] = bank[r-1]
                  + sum_p price[p,r] * traded_out[p,r]
                  - sum_p price[p,r] * traded_in[p,r]

    Notes
    -----
    This uses the round-r price for both sold and bought players, matching the
    formulation.
    """

    for r in model_input_data.idx_round_excluding_1:
        sold_value = pulp.lpSum(
            model_input_data.price(p, r) * decision_variables.traded_out[(p, r)] for p in model_input_data.player_ids
        )
        bought_cost = pulp.lpSum(
            model_input_data.price(p, r) * decision_variables.traded_in[(p, r)] for p in model_input_data.player_ids
        )

        problem += (
            decision_variables.bank[r] == decision_variables.bank[r - 1] + sold_value - bought_cost
        ), f"bank_recurrence_{r}"


def _add_trade_indicator_linking_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Trade Indicator Linking section."""

    _add_trade_indicator_linking_lower_bound_constraints(problem, model_input_data, decision_variables)
    _add_trade_indicator_linking_upper_bound_constraints(problem, model_input_data, decision_variables)


def _add_trade_indicator_linking_lower_bound_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Trade Indicator Linking: lower bounds (trigger constraints).

    traded_in[p,r] >= x[p,r] - x[p,r-1]
    traded_out[p,r] >= x[p,r-1] - x[p,r]
    """

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round_excluding_1:
            problem += (
                decision_variables.traded_in[(p, r)]
                >= decision_variables.x_selected[(p, r)] - decision_variables.x_selected[(p, r - 1)]
            ), f"trade_link_lb_in_{p}_{r}"

            problem += (
                decision_variables.traded_out[(p, r)]
                >= decision_variables.x_selected[(p, r - 1)] - decision_variables.x_selected[(p, r)]
            ), f"trade_link_lb_out_{p}_{r}"


def _add_trade_indicator_linking_upper_bound_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Trade Indicator Linking: upper bounds (prevent false positives / enforce direction)."""

    _add_trade_indicator_linking_upper_bound_trade_in_requires_selected_constraints(
        problem, model_input_data, decision_variables
    )
    _add_trade_indicator_linking_upper_bound_trade_in_requires_not_previously_selected_constraints(
        problem, model_input_data, decision_variables
    )
    _add_trade_indicator_linking_upper_bound_trade_out_requires_previously_selected_constraints(
        problem, model_input_data, decision_variables
    )
    _add_trade_indicator_linking_upper_bound_trade_out_requires_not_selected_constraints(
        problem, model_input_data, decision_variables
    )


def _add_trade_indicator_linking_upper_bound_trade_in_requires_selected_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Trade Indicator Linking upper bound: traded_in[p,r] <= x[p,r]."""

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round_excluding_1:
            problem += (
                decision_variables.traded_in[(p, r)] <= decision_variables.x_selected[(p, r)]
            ), f"trade_link_ub_in_requires_selected_{p}_{r}"


def _add_trade_indicator_linking_upper_bound_trade_in_requires_not_previously_selected_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Trade Indicator Linking upper bound: traded_in[p,r] <= 1 - x[p,r-1]."""

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round_excluding_1:
            problem += (
                decision_variables.traded_in[(p, r)] <= 1 - decision_variables.x_selected[(p, r - 1)]
            ), f"trade_link_ub_in_requires_not_prev_{p}_{r}"


def _add_trade_indicator_linking_upper_bound_trade_out_requires_previously_selected_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Trade Indicator Linking upper bound: traded_out[p,r] <= x[p,r-1]."""

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round_excluding_1:
            problem += (
                decision_variables.traded_out[(p, r)] <= decision_variables.x_selected[(p, r - 1)]
            ), f"trade_link_ub_out_requires_prev_{p}_{r}"


def _add_trade_indicator_linking_upper_bound_trade_out_requires_not_selected_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Trade Indicator Linking upper bound: traded_out[p,r] <= 1 - x[p,r]."""

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round_excluding_1:
            problem += (
                decision_variables.traded_out[(p, r)] <= 1 - decision_variables.x_selected[(p, r)]
            ), f"trade_link_ub_out_requires_not_selected_{p}_{r}"


def _add_maximum_team_changes_per_round_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Maximum Team Changes Per Round constraints."""

    _add_maximum_team_changes_trade_in_limit_constraints(problem, model_input_data, decision_variables)
    _add_maximum_team_changes_trade_out_limit_constraints(problem, model_input_data, decision_variables)


def _add_maximum_team_changes_trade_in_limit_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Maximum Team Changes: sum_p traded_in[p,r] <= max_trades[r] for r>1."""

    for r in model_input_data.idx_round_excluding_1:
        expr = pulp.lpSum(decision_variables.traded_in[(p, r)] for p in model_input_data.player_ids)
        problem += expr <= model_input_data.max_trades(r), f"max_trades_in_{r}"


def _add_maximum_team_changes_trade_out_limit_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Maximum Team Changes: sum_p traded_out[p,r] <= max_trades[r] for r>1."""

    for r in model_input_data.idx_round_excluding_1:
        expr = pulp.lpSum(decision_variables.traded_out[(p, r)] for p in model_input_data.player_ids)
        problem += expr <= model_input_data.max_trades(r), f"max_trades_out_{r}"


def _add_positional_structure_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Positional Structure section."""

    _add_positional_structure_on_field_constraints(problem, model_input_data, decision_variables)
    _add_positional_structure_bench_constraints(problem, model_input_data, decision_variables)
    _add_positional_structure_utility_bench_constraints(problem, model_input_data, decision_variables)


def _add_positional_structure_on_field_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Positional Structure: on-field exact counts per position."""

    for r in model_input_data.idx_round:
        for k in model_input_data.positions:
            required = model_input_data.on_field_required(k)
            expr = pulp.lpSum(
                decision_variables.y_onfield[(p, k, r)] for p in model_input_data.player_ids
            )
            problem += expr == required, f"pos_onfield_count_{k.value}_{r}"


def _add_positional_structure_bench_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Positional Structure: bench exact counts per position."""

    for r in model_input_data.idx_round:
        for k in model_input_data.positions:
            required = model_input_data.bench_required(k)
            expr = pulp.lpSum(
                decision_variables.y_bench[(p, k, r)] for p in model_input_data.player_ids
            )
            problem += expr == required, f"pos_bench_count_{k.value}_{r}"


def _add_positional_structure_utility_bench_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Positional Structure: bench utility exact count."""

    for r in model_input_data.idx_round:
        expr = pulp.lpSum(decision_variables.y_utility[(p, r)] for p in model_input_data.player_ids)
        problem += expr == model_input_data.utility_bench_count, f"pos_utility_count_{r}"


def _add_position_eligibility_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Position Eligibility section."""

    _add_position_eligibility_on_field_constraints(problem, model_input_data, decision_variables)
    _add_position_eligibility_bench_constraints(problem, model_input_data, decision_variables)
    _add_position_eligibility_utility_bench_constraints(problem, model_input_data, decision_variables)


def _add_position_eligibility_on_field_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Position Eligibility: enforce on-field eligibility by position."""

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round:
            eligible_positions = model_input_data.eligible_positions(p, r)
            for k in model_input_data.positions:
                # If player isn't eligible for k in round r, y_onfield must be 0.
                if k in eligible_positions:
                    continue
                problem += (
                    decision_variables.y_onfield[(p, k, r)] == 0
                ), f"elig_onfield_{p}_{k.value}_{r}"


def _add_position_eligibility_bench_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Position Eligibility: enforce bench eligibility by position."""

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round:
            eligible_positions = model_input_data.eligible_positions(p, r)
            for k in model_input_data.positions:
                if k in eligible_positions:
                    continue
                problem += (
                    decision_variables.y_bench[(p, k, r)] == 0
                ), f"elig_bench_{p}_{k.value}_{r}"


def _add_position_eligibility_utility_bench_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Position Eligibility: utility bench has no position eligibility restriction."""

    _ = (problem, model_input_data, decision_variables)


def _add_scoring_selection_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Scoring Selection (Bye Rounds) section."""

    _add_scoring_selection_count_constraints(problem, model_input_data, decision_variables)
    _add_scoring_selection_only_if_on_field_constraints(problem, model_input_data, decision_variables)


def _add_scoring_selection_count_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Scoring Selection: count exactly N_r scores each round."""

    for r in model_input_data.idx_round:
        expr = pulp.lpSum(decision_variables.scored[(p, r)] for p in model_input_data.player_ids)
        problem += expr == model_input_data.counted_onfield_players(r), f"score_count_{r}"


def _add_scoring_selection_only_if_on_field_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Scoring Selection: only count scores for on-field selected players."""

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round:
            onfield_sum = pulp.lpSum(decision_variables.y_onfield[(p, k, r)] for k in model_input_data.positions)
            problem += decision_variables.scored[(p, r)] <= onfield_sum, f"score_only_if_onfield_{p}_{r}"


def _add_captaincy_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Captaincy section."""

    _add_captaincy_exactly_one_constraints(problem, model_input_data, decision_variables)
    _add_captaincy_must_be_counted_constraints(problem, model_input_data, decision_variables)


def _add_captaincy_exactly_one_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Captaincy: exactly one captain each round."""

    for r in model_input_data.idx_round:
        expr = pulp.lpSum(decision_variables.captain[(p, r)] for p in model_input_data.player_ids)
        problem += expr == 1, f"captain_exactly_one_{r}"


def _add_captaincy_must_be_counted_constraints(
    problem: pulp.LpProblem,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
) -> None:
    """Captaincy: captain must be one of the counted on-field players."""

    for p in model_input_data.player_ids:
        for r in model_input_data.idx_round:
            problem += (
                decision_variables.captain[(p, r)] <= decision_variables.scored[(p, r)]
            ), f"captain_requires_scored_{p}_{r}"
