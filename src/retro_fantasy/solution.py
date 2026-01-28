from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import pulp

from retro_fantasy.data import ModelInputData, Position
from retro_fantasy.formulation import DecisionVariables


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
class RoundSummary:
    round_number: int
    total_team_points: float
    captain_player_name: str


@dataclass(frozen=True, slots=True)
class TeamEntry:
    player_id: int
    player_name: str
    slot: str
    position: Optional[str]
    price: float
    score: float


@dataclass(frozen=True, slots=True)
class RoundDetail:
    summary: RoundSummary
    trades: Optional[RoundTradeSummary]
    team: List[TeamEntry]


@dataclass(frozen=True, slots=True)
class SolutionSummary:
    status: str
    objective_value: float
    rounds: Dict[int, RoundDetail]


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
    """Build a JSON-serialisable, round-centric summary of the solved model."""

    decision_vars = decision_variables

    status = pulp.LpStatus[problem.status]
    objective_value = float(pulp.value(problem.objective) or 0.0)

    # Pre-build trades by round for easy attachment.
    trades_by_round: Dict[int, RoundTradeSummary] = {}
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

        trades_by_round[r] = RoundTradeSummary(round_number=r, traded_in=ins, traded_out=outs)

    # Build per-round details.
    rounds: Dict[int, RoundDetail] = {}

    # Sorting helpers
    position_order: dict[Optional[str], int] = {pos.value: i for i, pos in enumerate(Position.__members__.values())}
    position_order[None] = len(position_order)  # utility bench (no position) last
    slot_order: dict[str, int] = {"on_field": 0, "bench": 1, "utility_bench": 2}

    for r in model_input_data.idx_round:
        # Captain and scoring.
        captain_player_name = ""
        captain_bonus = 0.0

        for p in model_input_data.player_ids:
            if _is_selected(decision_vars.captain[(p, r)]):
                captain_player_name = model_input_data.players[p].name
                captain_bonus = float(model_input_data.score(p, r))
                break

        total_team_points = 0.0
        for p in model_input_data.player_ids:
            if _is_selected(decision_vars.scored[(p, r)]):
                total_team_points += float(model_input_data.score(p, r))
        total_team_points += captain_bonus

        summary = RoundSummary(
            round_number=r,
            total_team_points=total_team_points,
            captain_player_name=captain_player_name,
        )

        # Team listing for the round: everyone selected in any slot.
        team_entries: List[TeamEntry] = []
        for p in model_input_data.player_ids:
            slot: Optional[str] = None
            pos: Optional[Position] = None

            for k in model_input_data.positions:
                if _is_selected(decision_vars.y_onfield.get((p, k, r), 0)):
                    slot = "on_field"
                    pos = k
                    break
            if slot is None:
                for k in model_input_data.positions:
                    if _is_selected(decision_vars.y_bench.get((p, k, r), 0)):
                        slot = "bench"
                        pos = k
                        break
            if slot is None and _is_selected(decision_vars.y_utility[(p, r)]):
                slot = "utility_bench"
                pos = None

            if slot is None:
                continue

            player = model_input_data.players[p]
            team_entries.append(
                TeamEntry(
                    player_id=p,
                    player_name=player.name,
                    slot=slot,
                    position=pos.value if pos else None,
                    price=float(model_input_data.price(p, r)),
                    score=float(model_input_data.score(p, r)),
                )
            )

        team_entries.sort(
            key=lambda e: (
                position_order.get(e.position, 999),
                slot_order.get(e.slot, 999),
                -e.price,
            )
        )

        rounds[r] = RoundDetail(summary=summary, trades=trades_by_round.get(r), team=team_entries)

    return SolutionSummary(status=status, objective_value=objective_value, rounds=rounds)


def solution_summary_to_json_dict(summary: SolutionSummary) -> Dict[str, Any]:
    # dataclasses -> plain dict, with int keys preserved via python dict
    return asdict(summary)


def dumps_solution_summary_pretty(summary: SolutionSummary) -> str:
    return json.dumps(solution_summary_to_json_dict(summary), indent=2, sort_keys=False)
