from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


@dataclass(frozen=True)
class PlayerRoundCell:
    score: float
    scored: bool
    captain: bool
    slot: Optional[str]
    position: Optional[str]
    price: Optional[float]
    traded_out: bool


def _format_score(score: float) -> str:
    # Keep integers as integers for readability.
    if abs(score - round(score)) < 1e-9:
        return str(int(round(score)))
    return f"{score:.2f}".rstrip("0").rstrip(".")


def _format_slot_position(*, slot: Optional[str], position: Optional[str]) -> str:
    if not slot:
        return ""

    slot_label_map = {
        "on_field": "ON",
        "bench": "BENCH",
        "utility_bench": "UTIL",
    }
    slot_label = slot_label_map.get(slot, slot)

    if position:
        return f"{position} / {slot_label}"
    return slot_label


def _format_price(price: Optional[float]) -> str:
    if price is None:
        return ""
    # Prices are in whole dollars in this dataset; show with commas.
    try:
        return f"${int(round(float(price))):,}"
    except Exception:
        return str(price)


def _format_cell(cell: Optional[PlayerRoundCell]) -> str:
    if cell is None:
        return ""

    price_text = _format_price(cell.price)

    # Special case: traded out this round.
    # Requirement: don't show score/position/slot, but still show price;
    # and add 'Traded Out' line.
    if cell.traded_out:
        if price_text:
            return f"Traded Out<br>{price_text}"
        return "Traded Out"

    score_text = _format_score(cell.score)

    # Style rules for score:
    # - captain: bold
    # - scored=False: italic
    if cell.captain:
        score_text = f"**{score_text}**"
    elif not cell.scored:
        score_text = f"*{score_text}*"

    where = _format_slot_position(slot=cell.slot, position=cell.position)

    # Render as multi-line cell.
    parts: list[str] = [score_text]
    if where:
        parts.append(where)
    if price_text:
        parts.append(price_text)

    return "<br>".join(parts)


def _iter_round_numbers(solution: Mapping[str, Any]) -> List[int]:
    rounds_obj = solution.get("rounds") or {}

    # solution.json is produced by dataclasses.asdict, with int keys serialised as strings.
    round_nums: List[int] = []
    for k in rounds_obj.keys():
        try:
            round_nums.append(int(k))
        except ValueError:
            continue
    return sorted(round_nums)


def _extract_traded_out_player_ids_for_round(solution: Mapping[str, Any], r: int) -> List[int]:
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    r_obj = rounds_obj.get(str(r)) or {}
    trades = r_obj.get("trades") or {}
    traded_out = trades.get("traded_out") or []
    player_ids: List[int] = []
    for entry in traded_out:
        try:
            player_ids.append(int(entry["player_id"]))
        except Exception:
            continue
    return player_ids


def _extract_traded_out_entries_for_round(solution: Mapping[str, Any], r: int) -> List[Mapping[str, Any]]:
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    r_obj = rounds_obj.get(str(r)) or {}
    trades = r_obj.get("trades") or {}
    return trades.get("traded_out") or []


def _extract_cells(
    solution: Mapping[str, Any],
) -> Tuple[List[int], Dict[int, Dict[int, PlayerRoundCell]], Dict[int, str]]:
    """Return (round_numbers, player_to_round_cells, player_names)."""

    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    round_numbers = _iter_round_numbers(solution)

    player_cells: Dict[int, Dict[int, PlayerRoundCell]] = {}
    player_names: Dict[int, str] = {}

    # Pre-compute traded-out player sets by round.
    traded_out_by_round: Dict[int, set[int]] = {
        r: {int(e["player_id"]) for e in _extract_traded_out_entries_for_round(solution, r) if "player_id" in e}
        for r in round_numbers
    }

    for r in round_numbers:
        r_obj = rounds_obj.get(str(r)) or {}
        team = r_obj.get("team") or []

        # 1) Cells for players in the team list
        for entry in team:
            try:
                pid = int(entry["player_id"])
            except Exception:
                continue

            player_names[pid] = str(entry.get("player_name", pid))

            cell = PlayerRoundCell(
                score=float(entry.get("score", 0.0) or 0.0),
                scored=bool(entry.get("scored", entry.get("slot") == "on_field")),
                captain=bool(entry.get("captain", False)),
                slot=entry.get("slot"),
                position=entry.get("position"),
                price=float(entry.get("price")) if entry.get("price") is not None else None,
                traded_out=(pid in traded_out_by_round.get(r, set())),
            )
            # Fallback: infer captain if not present in JSON.
            if not cell.captain:
                summary = (r_obj.get("summary") or {})
                cap_name = summary.get("captain_player_name")
                if cap_name and str(entry.get("player_name")) == str(cap_name):
                    cell = PlayerRoundCell(
                        score=cell.score,
                        scored=cell.scored,
                        captain=True,
                        slot=cell.slot,
                        position=cell.position,
                        price=cell.price,
                        traded_out=cell.traded_out,
                    )

            player_cells.setdefault(pid, {})[r] = cell

        # 2) Synthesise cells for players traded out in this round.
        # Typically these players are NOT in the team list for the same round.
        for out_entry in _extract_traded_out_entries_for_round(solution, r):
            try:
                pid = int(out_entry["player_id"])
            except Exception:
                continue

            # Preserve name if provided.
            if "player_name" in out_entry:
                player_names[pid] = str(out_entry.get("player_name", pid))

            # Only add if not already present from team list.
            if r in player_cells.get(pid, {}):
                continue

            player_cells.setdefault(pid, {})[r] = PlayerRoundCell(
                score=0.0,
                scored=False,
                captain=False,
                slot=None,
                position=None,
                price=float(out_entry.get("price")) if out_entry.get("price") is not None else None,
                traded_out=True,
            )

    return round_numbers, player_cells, player_names


def _round_scored_totals(solution: Mapping[str, Any], round_numbers: Iterable[int]) -> Dict[int, float]:
    totals: Dict[int, float] = {}
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}

    for r in round_numbers:
        r_obj = rounds_obj.get(str(r)) or {}
        summary = r_obj.get("summary") or {}
        totals[r] = float(summary.get("total_team_points", 0.0) or 0.0)

    return totals


def _chunk_rounds(round_numbers: List[int], *, chunk_size: int = 8) -> List[List[int]]:
    return [round_numbers[i : i + chunk_size] for i in range(0, len(round_numbers), chunk_size)]


def _players_in_round_block(
    player_cells: Dict[int, Dict[int, PlayerRoundCell]],
    round_block: List[int],
) -> List[int]:
    """Only include players who appear in at least one round of this block."""

    player_ids: List[int] = []
    round_set = set(round_block)
    for pid, cells_by_round in player_cells.items():
        if any(r in round_set for r in cells_by_round.keys()):
            player_ids.append(pid)
    return player_ids


def _extract_selected_player_ids_for_round(solution: Mapping[str, Any], r: int) -> List[int]:
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    r_obj = rounds_obj.get(str(r)) or {}
    team = r_obj.get("team") or []
    player_ids: List[int] = []
    for entry in team:
        try:
            player_ids.append(int(entry["player_id"]))
        except Exception:
            continue
    return player_ids


def _extract_traded_in_player_ids_for_round(solution: Mapping[str, Any], r: int) -> List[int]:
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    r_obj = rounds_obj.get(str(r)) or {}
    trades = r_obj.get("trades") or {}
    traded_in = trades.get("traded_in") or []
    player_ids: List[int] = []
    for entry in traded_in:
        try:
            player_ids.append(int(entry["player_id"]))
        except Exception:
            continue
    return player_ids


def _cascade_player_order_for_block(
    solution: Mapping[str, Any],
    block: List[int],
    player_cells: Dict[int, Dict[int, PlayerRoundCell]],
) -> List[int]:
    """Return player ids in cascade order, restricted to players present in this block.

    Order:
      1) Round-1 team (in the order shown in solution.json)
      2) For r>=2: players traded in for round r (in traded_in order)
      3) Any remaining players present in the block (fallback deterministic ordering)

    The idea is to read like a timeline: initial squad, then additions.
    """

    if not block:
        return []

    # Players present in the block (at least once).
    present = set(_players_in_round_block(player_cells, block))

    ordered: List[int] = []
    seen: set[int] = set()

    # 1) Round 1 team.
    r1_ids = _extract_selected_player_ids_for_round(solution, 1)
    for pid in r1_ids:
        if pid in present and pid not in seen:
            ordered.append(pid)
            seen.add(pid)

    # 2) Traded-in players by round.
    for r in block:
        if r <= 1:
            continue
        for pid in _extract_traded_in_player_ids_for_round(solution, r):
            if pid in present and pid not in seen:
                ordered.append(pid)
                seen.add(pid)

    # 3) Fallback for anything else (should be rare): stable ordering by name.
    remaining = [pid for pid in sorted(present) if pid not in seen]
    ordered.extend(remaining)

    return ordered


def _format_currency(value: float | int | None) -> str:
    if value is None:
        return ""
    try:
        return f"${int(round(float(value))):,}"
    except Exception:
        return str(value)


def _round_bank_balances(solution: Mapping[str, Any], round_numbers: Iterable[int]) -> Dict[int, float | None]:
    out: Dict[int, float | None] = {}
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    for r in round_numbers:
        summary = (rounds_obj.get(str(r)) or {}).get("summary") or {}
        val = summary.get("bank_balance")
        out[r] = float(val) if val is not None else None
    return out


def _round_team_values_from_team_list(solution: Mapping[str, Any], round_numbers: Iterable[int]) -> Dict[int, float]:
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    out: Dict[int, float] = {}
    for r in round_numbers:
        team = (rounds_obj.get(str(r)) or {}).get("team") or []
        out[r] = float(sum(float(e.get("price") or 0.0) for e in team))
    return out


def _round_team_values(solution: Mapping[str, Any], round_numbers: Iterable[int]) -> Dict[int, float | None]:
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    computed = _round_team_values_from_team_list(solution, round_numbers)

    out: Dict[int, float | None] = {}
    for r in round_numbers:
        summary = (rounds_obj.get(str(r)) or {}).get("summary") or {}
        val = summary.get("team_value")
        out[r] = float(val) if val is not None else computed.get(r)
    return out


def _round_total_values(solution: Mapping[str, Any], round_numbers: Iterable[int]) -> Dict[int, float | None]:
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    bank = _round_bank_balances(solution, round_numbers)
    team = _round_team_values(solution, round_numbers)

    out: Dict[int, float | None] = {}
    for r in round_numbers:
        summary = (rounds_obj.get(str(r)) or {}).get("summary") or {}
        val = summary.get("total_value")
        if val is not None:
            out[r] = float(val)
        else:
            b = bank.get(r)
            t = team.get(r)
            out[r] = (None if b is None or t is None else float(b + t))
    return out


def _format_player_line(*, name: str, price: float | None, score: float | None, score_in_brackets: bool = False) -> str:
    parts: list[str] = [name]
    if price is not None:
        parts.append(_format_currency(price))
    if score is not None:
        pts = f"{_format_score(float(score))} pts"
        if score_in_brackets:
            pts = f"({pts})"
        parts.append(pts)
    return " – ".join(parts)


def _format_price_change(delta: float | None) -> str:
    if delta is None:
        return ""
    try:
        d = float(delta)
    except Exception:
        return ""

    sign = "+" if d >= 0 else "-"
    return f"({sign}{_format_currency(abs(d))})"


def _get_round_obj(solution: Mapping[str, Any], r: int) -> Mapping[str, Any]:
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    return rounds_obj.get(str(r)) or {}


def _get_round_summary(solution: Mapping[str, Any], r: int) -> Mapping[str, Any]:
    return (_get_round_obj(solution, r).get("summary") or {})


def _get_round_trades(solution: Mapping[str, Any], r: int) -> Mapping[str, Any] | None:
    return _get_round_obj(solution, r).get("trades")


def _get_round_team(solution: Mapping[str, Any], r: int) -> list[Mapping[str, Any]]:
    return list(_get_round_obj(solution, r).get("team") or [])


def _trade_lines_for_round(solution: Mapping[str, Any], r: int) -> list[str]:
    trades = _get_round_trades(solution, r)
    if not trades:
        return ["- Trades: _None_" if r == 1 else "- Trades: _None_"]

    traded_out = trades.get("traded_out") or []
    traded_in = trades.get("traded_in") or []

    lines: list[str] = []
    if traded_out:
        lines.append("- Traded out:")
        for e in traded_out:
            delta = e.get("price_change")
            delta_text = _format_price_change(delta)
            base = _format_player_line(name=str(e.get('player_name','?')), price=e.get('price'), score=None)
            if delta_text:
                base = f"{base} {delta_text}"
            lines.append(f"  - {base}")
    else:
        lines.append("- Traded out: _None_")

    if traded_in:
        lines.append("- Traded in:")
        for e in traded_in:
            lines.append(f"  - {_format_player_line(name=str(e.get('player_name','?')), price=e.get('price'), score=None)}")
    else:
        lines.append("- Traded in: _None_")

    return lines


def _trade_names_for_round(solution: Mapping[str, Any], r: int) -> tuple[list[str], list[str]]:
    trades = _get_round_trades(solution, r)
    if not trades:
        return [], []

    outs = [str(e.get("player_name", "")) for e in (trades.get("traded_out") or []) if e.get("player_name")]
    ins = [str(e.get("player_name", "")) for e in (trades.get("traded_in") or []) if e.get("player_name")]
    return outs, ins


def _round_summary_table(solution: Mapping[str, Any], round_numbers: list[int]) -> str:
    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}

    lines: list[str] = []
    header = ["Round", "Points", "Bank balance", "Total value", "Traded out", "Traded in"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    for r in round_numbers:
        summary = (rounds_obj.get(str(r)) or {}).get("summary") or {}
        pts = summary.get("total_team_points")
        bank = summary.get("bank_balance")
        total_val = summary.get("total_value")

        # Fallbacks if schema doesn't include these.
        if bank is None:
            bank = _round_bank_balances(solution, [r]).get(r)
        if total_val is None:
            total_val = _round_total_values(solution, [r]).get(r)

        traded_out_names, traded_in_names = _trade_names_for_round(solution, r)

        row = [
            f"R{r}",
            _format_score(float(pts)) if pts is not None else "",
            _format_currency(bank),
            _format_currency(total_val),
            ", ".join(traded_out_names),
            ", ".join(traded_in_names),
        ]
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def _position_row_order() -> list[str]:
    # Keep consistent with your Position enum ordering / formulation.
    return ["DEF", "MID", "RUC", "FWD"]


def _slot_column_order() -> list[str]:
    # Utility is a bench slot; we don't need a separate column for it.
    return ["on_field", "bench"]


def _slot_label(slot: str) -> str:
    return {"on_field": "On field", "bench": "Bench"}.get(slot, slot)


def _team_table_for_round(solution: Mapping[str, Any], r: int, *, include_scores: bool = True) -> str:
    team = _get_round_team(solution, r)

    # Bucket: (position, slot) -> list[team_entry]
    buckets: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for e in team:
        slot = str(e.get("slot") or "")
        pos = e.get("position")

        # Map utility bench into the bench column.
        if slot == "utility_bench":
            slot = "bench"

        # Utility has no position; show it in a dedicated utility row.
        if pos is None:
            pos_key = "UTIL"
        else:
            pos_key = str(pos)

        buckets.setdefault((pos_key, slot), []).append(e)

    # Sort each bucket by price desc
    for k, lst in buckets.items():
        lst.sort(key=lambda x: float(x.get("price") or 0.0), reverse=True)

    positions = _position_row_order() + ["UTIL"]
    slots = _slot_column_order()

    lines: list[str] = []
    header = ["Position"] + [_slot_label(s) for s in slots]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    for pos in positions:
        row: list[str] = [pos]
        for slot in slots:
            players = buckets.get((pos, slot), [])
            if not players:
                row.append("")
                continue

            cell_lines: list[str] = []
            for p in players:
                scored_flag = p.get("scored")
                score_in_brackets = bool(slot == "on_field" and scored_flag is False)

                cell_lines.append(
                    _format_player_line(
                        name=str(p.get("player_name", "?")),
                        price=p.get("price"),
                        score=(p.get("score") if include_scores else None),
                        score_in_brackets=(score_in_brackets and include_scores),
                    )
                )
            row.append("<br>".join(cell_lines))

        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def _verbose_round_sections(solution: Mapping[str, Any], round_numbers: list[int]) -> str:
    out: list[str] = []
    out.append("# Round-by-round detail")
    out.append("")

    for r in round_numbers:
        summary = _get_round_summary(solution, r)
        total_pts = summary.get("total_team_points")
        captain_name = summary.get("captain_player_name") or ""

        out.append(f"## Round {r}")
        out.append("")
        if total_pts is not None:
            out.append(f"- Total scored points: **{_format_score(float(total_pts))}**")
        if captain_name:
            out.append(f"- Captain: **{captain_name}**")
        out.append("")

        out.extend(_trade_lines_for_round(solution, r))
        out.append("")

        # Financial summary for the round (after trades)
        bank = summary.get("bank_balance")
        team_val = summary.get("team_value")
        total_val = summary.get("total_value")

        # Fallbacks if solution.json doesn't contain these explicitly
        if bank is None:
            bank_by_round = _round_bank_balances(solution, [r])
            bank = bank_by_round.get(r)
        if team_val is None:
            team_by_round = _round_team_values(solution, [r])
            team_val = team_by_round.get(r)
        if total_val is None:
            total_by_round = _round_total_values(solution, [r])
            total_val = total_by_round.get(r)

        if bank is not None or team_val is not None or total_val is not None:
            out.append("**Round finances**")
            if bank is not None:
                out.append(f"- Bank balance: {_format_currency(bank)}")
            if team_val is not None:
                out.append(f"- Team value: {_format_currency(team_val)}")
            if total_val is not None:
                out.append(f"- Total value: {_format_currency(total_val)}")
            out.append("")

        out.append("### Team")
        out.append("")
        out.append(_team_table_for_round(solution, r))
        out.append("")

    return "\n".join(out)


def _starting_team_section(solution: Mapping[str, Any], round_numbers: list[int]) -> str:
    if not round_numbers or 1 not in round_numbers:
        return ""

    r = 1
    summary = _get_round_summary(solution, r)

    bank = summary.get("bank_balance")
    team_val = summary.get("team_value")
    total_val = summary.get("total_value")

    # Fallbacks if solution.json doesn't contain these explicitly.
    if bank is None:
        bank = _round_bank_balances(solution, [r]).get(r)
    if team_val is None:
        team_val = _round_team_values(solution, [r]).get(r)
    if total_val is None:
        total_val = _round_total_values(solution, [r]).get(r)

    lines: list[str] = []
    lines.append("## Starting team")
    lines.append("")

    # Finances above the table.
    if bank is not None or team_val is not None or total_val is not None:
        if bank is not None:
            lines.append(f"- Bank balance: {_format_currency(bank)}")
        if team_val is not None:
            lines.append(f"- Team value: {_format_currency(team_val)}")
        if total_val is not None:
            lines.append(f"- Total value: {_format_currency(total_val)}")
        lines.append("")

    lines.append(_team_table_for_round(solution, r, include_scores=False))
    lines.append("")

    return "\n".join(lines)


def solution_json_to_markdown(solution: Mapping[str, Any]) -> str:
    round_numbers, player_cells, player_names = _extract_cells(solution)

    lines: List[str] = []

    status = str(solution.get("status", ""))
    objective = int(solution.get("objective_value"))
    lines.append("# Retro Fantasy – Solution Report")
    lines.append("")
    lines.append(f"- **Status**: {status}")
    if objective is not None:
        lines.append(f"- **Objective value (total score over all rounds)**: {objective}")
    lines.append("")

    # Starting team section (Round 1)
    starting_section = _starting_team_section(solution, round_numbers)
    if starting_section:
        lines.append(starting_section)

    # Compact one-row-per-round table.
    lines.append("## Round summary")
    lines.append("")
    lines.append(_round_summary_table(solution, round_numbers))
    lines.append("")

    # Round-by-round detail (more narrative / verbose).
    lines.append(_verbose_round_sections(solution, round_numbers))
    lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Convert solution.json to a markdown report")
    parser.add_argument("solution_json", type=Path, help="Path to solution.json")
    parser.add_argument("--out", type=Path, default=None, help="Optional output markdown path")

    args = parser.parse_args(argv)

    solution = json.loads(args.solution_json.read_text(encoding="utf-8-sig"))
    md = solution_json_to_markdown(solution)

    if args.out is None:
        print(md)
    else:
        args.out.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
