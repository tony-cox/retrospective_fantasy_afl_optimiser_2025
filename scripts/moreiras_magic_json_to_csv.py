"""Convert 2026 Moreira's Magic JSON data to a CSV.

This script is intentionally standalone and does not depend on the optimiser code.

Usage (PowerShell):
    python scripts/moreiras_magic_json_to_csv.py \
        --input data/2026_moreiras_magic_data.json \
        --output output/2026_moreiras_magic_players.csv

Notes
-----
- Exports ONLY the objects inside the top-level `players` list.
- All keys across all player objects become CSV headers.
- `null` values become blank cells.
- Nested objects/lists are JSON-encoded into a single cell (defensive), but the
  dataset is expected to already be flat.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _cell_value(v: Any) -> str:
    """Convert a JSON value into a CSV cell string.

    - None -> ""
    - str -> unchanged
    - int/float/bool -> stringified without extra quoting
    - dict/list -> JSON string (defensive)
    """

    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        # Preserve numeric-looking values; csv module will not add quotes unless needed.
        return str(v)
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def convert_players_json_to_csv(*, input_path: Path, output_path: Path) -> None:
    raw = input_path.read_text(encoding="utf-8", errors="replace")
    data = json.loads(raw)

    players = data.get("players")
    if not isinstance(players, list):
        raise TypeError(f"Expected top-level 'players' to be a list, got: {type(players)}")

    # Collect stable header order: first player's keys, then any extras discovered later.
    header: list[str] = []
    seen: set[str] = set()

    for p in players:
        if not isinstance(p, dict):
            raise TypeError(f"Expected each element of 'players' to be an object/dict, got: {type(p)}")
        for k in p.keys():
            if k not in seen:
                seen.add(k)
                header.append(str(k))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=header,
            extrasaction="ignore",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()

        for p in players:
            row = {k: _cell_value(p.get(k)) for k in header}
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    convert_players_json_to_csv(input_path=args.input, output_path=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
