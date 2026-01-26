from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import pulp

from retro_fantasy.data import ModelInputData, Position
from retro_fantasy.formulation import DecisionVariables


@dataclass(frozen=True, slots=True)
class StartingTeamEntry:
    player_id: int
    player_name: str
    slot: str
    position: Optional[str]
    price: float


@dataclass(frozen=True, slots=True)
class TradeEntry:
    player_id: int
    player_name: str
    price: float


@dataclass(frozen=True, slots=True)
class RoundTradeSummary:
    round_number: int
    traded_in: List[TradeEntry]
    traded_out: List[TradeEntry]


@dataclass(frozen=True, slots=True)
class RoundScoreSummary:
    round_number: int
    counted_team_points: float
    captain_player_id: int
    captain_player_name: str
    captain_raw_score: float
    captain_bonus_points: float


@dataclass(frozen=True, slots=True)
class SolutionSummary:
    status: str
    objective_value: float
    starting_team: List[StartingTeamEntry]
    bank_by_round: Dict[int, float]
    trades_by_round: List[RoundTradeSummary]
    score_by_round: List[RoundScoreSummary]


def _var_value(v: pulp.LpVariable) -> float:
    val = pulp.value(v)
    return float(val) if val is not None else 0.0


def _is_selected(v: pulp.LpVariable, *, tol: float = 1e-6) -> bool:
    return _var_value(v) >= 1.0 - tol


def build_solution_summary(
    *,
    model_input_data: ModelInputData,
    decision_variables: DecisionVariables,
    problem: pulp.LpProblem,
) -> SolutionSummary:
    """Build a JSON-serialisable summary of the solved model."""

    decision_vars = decision_variables

    status = pulp.LpStatus[problem.status]
    objective_value = float(pulp.value(problem.objective) or 0.0)

    # --- Starting team (round 1) ---
    starting_team: List[StartingTeamEntry] = []
    if 1 in model_input_data.round_numbers:
        r = 1
        for p in model_input_data.player_ids:
            # Determine slot allocation (onfield/bench/utility) and position.
            slot = None
            pos: Optional[Position] = None

            for k in model_input_data.positions:
                if _is_selected(decision_vars.y_onfield[(p, k, r)]):
                    slot = "on_field"
                    pos = k
                    break
            if slot is None:
                for k in model_input_data.positions:
                    if _is_selected(decision_vars.y_bench[(p, k, r)]):
                        slot = "bench"
                        pos = k
                        break
            if slot is None and _is_selected(decision_vars.y_utility[(p, r)]):
                slot = "utility_bench"
                pos = None

            if slot is None:
                continue

            player = model_input_data.players[p]
            starting_team.append(
                StartingTeamEntry(
                    player_id=p,
                    player_name=player.name,
                    slot=slot,
                    position=pos.value if pos else None,
                    price=float(model_input_data.price(p, r)),
                )
            )

    # --- Bank by round ---
    bank_by_round: Dict[int, float] = {r: _var_value(decision_vars.bank[r]) for r in model_input_data.idx_round}

    # --- Trades by round ---
    trades_by_round: List[RoundTradeSummary] = []
    for r in model_input_data.idx_round_excluding_1:
        ins: List[TradeEntry] = []
        outs: List[TradeEntry] = []

        for p in model_input_data.player_ids:
            if _is_selected(decision_vars.traded_in[(p, r)]):
                pl = model_input_data.players[p]
                ins.append(TradeEntry(player_id=p, player_name=pl.name, price=float(model_input_data.price(p, r))))
            if _is_selected(decision_vars.traded_out[(p, r)]):
                pl = model_input_data.players[p]
                outs.append(TradeEntry(player_id=p, player_name=pl.name, price=float(model_input_data.price(p, r))))

        trades_by_round.append(RoundTradeSummary(round_number=r, traded_in=ins, traded_out=outs))

    # --- Score/captain by round ---
    score_by_round: List[RoundScoreSummary] = []
    for r in model_input_data.idx_round:
        counted_points = 0.0
        for p in model_input_data.player_ids:
            if _is_selected(decision_vars.scored[(p, r)]):
                counted_points += float(model_input_data.score(p, r))

        captain_player_id = -1
        captain_player_name = ""
        captain_raw_score = 0.0
        captain_bonus = 0.0

        for p in model_input_data.player_ids:
            if _is_selected(decision_vars.captain[(p, r)]):
                captain_player_id = p
                captain_player_name = model_input_data.players[p].name
                captain_raw_score = float(model_input_data.score(p, r))
                captain_bonus = captain_raw_score
                break

        score_by_round.append(
            RoundScoreSummary(
                round_number=r,
                counted_team_points=counted_points + captain_bonus,
                captain_player_id=captain_player_id,
                captain_player_name=captain_player_name,
                captain_raw_score=captain_raw_score,
                captain_bonus_points=captain_bonus,
            )
        )

    return SolutionSummary(
        status=status,
        objective_value=objective_value,
        starting_team=starting_team,
        bank_by_round=bank_by_round,
        trades_by_round=trades_by_round,
        score_by_round=score_by_round,
    )


def solution_summary_to_json_dict(summary: SolutionSummary) -> Dict[str, Any]:
    # dataclasses -> plain dict, with int keys preserved via python dict
    return asdict(summary)


def dumps_solution_summary_pretty(summary: SolutionSummary) -> str:
    return json.dumps(solution_summary_to_json_dict(summary), indent=2, sort_keys=False)
