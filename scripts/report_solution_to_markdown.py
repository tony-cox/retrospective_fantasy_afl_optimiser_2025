from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from scripts.solution_to_markdown import solution_json_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a markdown report from a Retro Fantasy solution.json")
    parser.add_argument("solution_json", type=Path, help="Path to solution.json")
    parser.add_argument("--out", type=Path, default=None, help="Optional output markdown path")

    args = parser.parse_args()

    solution: Mapping[str, Any] = json.loads(args.solution_json.read_text(encoding="utf-8-sig"))
    md = solution_json_to_markdown(solution)

    if args.out is None:
        print(md)
    else:
        args.out.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
