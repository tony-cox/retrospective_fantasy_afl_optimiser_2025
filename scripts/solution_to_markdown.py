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


def _format_cell(cell: Optional[PlayerRoundCell]) -> str:
    if cell is None:
        return ""

    score_text = _format_score(cell.score)

    # Style rules for score:
    # - captain: bold
    # - scored=False: italic
    if cell.captain:
        score_text = f"**{score_text}**"
    elif not cell.scored:
        score_text = f"*{score_text}*"

    where = _format_slot_position(slot=cell.slot, position=cell.position)

    # Two-line cell (markdown table supports <br> in most renderers)
    if where:
        return f"{score_text}<br>{where}"
    return score_text


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


def _extract_cells(
    solution: Mapping[str, Any],
) -> Tuple[List[int], Dict[int, Dict[int, PlayerRoundCell]], Dict[int, str]]:
    """Return (round_numbers, player_to_round_cells, player_names)."""

    rounds_obj: Mapping[str, Any] = solution.get("rounds") or {}
    round_numbers = _iter_round_numbers(solution)

    player_cells: Dict[int, Dict[int, PlayerRoundCell]] = {}
    player_names: Dict[int, str] = {}

    for r in round_numbers:
        r_obj = rounds_obj.get(str(r)) or {}
        team = r_obj.get("team") or []

        for entry in team:
            try:
                pid = int(entry["player_id"])
            except Exception:
                continue

            player_names[pid] = str(entry.get("player_name", pid))

            cell = PlayerRoundCell(
                score=float(entry.get("score", 0.0) or 0.0),
                scored=bool(entry.get("scored", False)),
                captain=bool(entry.get("captain", False)),
                slot=entry.get("slot"),
                position=entry.get("position"),
            )
            player_cells.setdefault(pid, {})[r] = cell

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


def solution_json_to_markdown(solution: Mapping[str, Any]) -> str:
    round_numbers, player_cells, player_names = _extract_cells(solution)
    round_totals = _round_scored_totals(solution, round_numbers)

    round_blocks = _chunk_rounds(round_numbers, chunk_size=8)

    lines: List[str] = []

    status = str(solution.get("status", ""))
    objective = solution.get("objective_value")
    lines.append("# Retro Fantasy – Solution Report")
    lines.append("")
    lines.append(f"- **Status**: {status}")
    if objective is not None:
        lines.append(f"- **Objective value**: {objective}")
    lines.append("")

    for i, block in enumerate(round_blocks, start=1):
        if not block:
            continue

        lines.append(f"## Rounds {block[0]}–{block[-1]}")
        lines.append("")

        # Only rows for players who are selected at least once in the block.
        block_player_ids = _players_in_round_block(player_cells, block)

        # Row order: by player name (within this block).
        block_player_ids = sorted(block_player_ids, key=lambda pid: player_names.get(pid, str(pid)).lower())

        # Table header
        header = ["Player"] + [f"R{r}" for r in block]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")

        for pid in block_player_ids:
            row = [player_names.get(pid, str(pid))]
            for r in block:
                row.append(_format_cell(player_cells.get(pid, {}).get(r)))
            lines.append("| " + " | ".join(row) + " |")

        # Final totals row
        totals_row = ["**Total scored**"]
        for r in block:
            totals_row.append(f"**{int(round(round_totals.get(r, 0.0)))}**")
        lines.append("| " + " | ".join(totals_row) + " |")

        lines.append("")

    lines.append("## Legend")
    lines.append("")
    lines.append("- Normal score text: on-field and counted towards your score")
    lines.append("- *Italic score*: selected but did **not** count towards your score (bench or not in best-N)")
    lines.append("- **Bold score**: captain (captain score is doubled in the objective)")
    lines.append("- Second line in each cell shows where the player was selected (Position / Slot)")

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
