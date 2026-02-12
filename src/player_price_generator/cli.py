"""Command-line entry point for :mod:`player_price_generator`.

This CLI currently just exercises the IO layer so we can validate the new
source CSVs can be loaded successfully.

Example
-------
python -m player_price_generator.cli --data-dir ./data
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Sequence

from .io import load_prospective_input_data
from .simulate import simulate_round_scores
from .data import SimulationConfig


def _print_summary(*, prospective_data, sample_players: int) -> None:
    rounds = sorted(prospective_data.rounds)
    print("Prospective input data loaded")
    print(f"- Clubs: {len(prospective_data.clubs)}")
    print(f"- Fixtures: {len(prospective_data.fixtures)}")
    print(f"- Projected players: {len(prospective_data.projected_players)}")
    if rounds:
        print(f"- Rounds: {rounds[0]}..{rounds[-1]} (count={len(rounds)})")
    else:
        print("- Rounds: <none>")

    early_bye_count = sum(1 for c in prospective_data.clubs.values() if c.early_bye_round is not None)
    print(f"- Clubs with early bye: {early_bye_count}/{len(prospective_data.clubs)}")
    print(f"- Mid-season bye rounds: {sorted({c.mid_season_bye_round for c in prospective_data.clubs.values()})}")

    club_counts = Counter(p.club_code for p in prospective_data.projected_players)
    print("\nTop clubs by number of projected players:")
    for club_code, n in club_counts.most_common(5):
        club_name = prospective_data.clubs.get(club_code).fixture_name if club_code in prospective_data.clubs else "<unknown>"
        print(f"- {club_code} ({club_name}): {n}")

    position_counts = Counter(pos for p in prospective_data.projected_players for pos in p.positions)
    print("\nPosition counts (note: DPP players contribute to multiple positions):")
    for pos, n in position_counts.most_common():
        print(f"- {pos.name}: {n}")

    n_round_scores = sum(len(p.simulated_scores_by_round) for p in prospective_data.projected_players)
    print("\nSimulation complete")
    print(f"- Total per-player round scores generated: {n_round_scores}")

    sample_n = max(0, int(sample_players))
    sample = sorted(prospective_data.projected_players, key=lambda x: (x.club_code, x.name))[:sample_n]
    if not sample:
        return

    print(f"\nSample of {len(sample)} players:")
    for p in sample:
        pos_str = "/".join(sorted([pp.name for pp in p.positions]))
        priced_at_str = f" priced_at={p.priced_at:.1f}" if p.priced_at is not None else ""

        played_rounds = sorted(p.simulated_scores_by_round)
        rounds_str = f" rounds={played_rounds[:5]}..." if len(played_rounds) > 5 else f" rounds={played_rounds}"

        # Show a few simulated scores
        example_rounds = played_rounds[:3]
        if example_rounds:
            example_scores = ", ".join(f"R{r}={p.simulated_scores_by_round[r]:.1f}" for r in example_rounds)
            scores_str = f" sim_scores=[{example_scores}{', ...' if len(played_rounds) > 3 else ''}]"
        else:
            scores_str = " sim_scores=[]"

        print(
            f"- {p.name} ({p.club_code}) {pos_str} price={p.price:,.0f}{priced_at_str} "
            f"proj_low/mid/high={p.projection_low:.1f}/{p.projection_mid:.1f}/{p.projection_high:.1f}"
            + rounds_str
            + scores_str
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="player_price_generator")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Directory containing club_byes.csv, fixtures.csv, player_projections.csv (default: ./data)",
    )
    parser.add_argument(
        "--club-byes-csv",
        type=Path,
        default=None,
        help="Override path to club_byes.csv (default: <data-dir>/club_byes.csv)",
    )
    parser.add_argument(
        "--fixtures-csv",
        type=Path,
        default=None,
        help="Override path to fixtures.csv (default: <data-dir>/fixtures.csv)",
    )
    parser.add_argument(
        "--player-projections-csv",
        type=Path,
        default=None,
        help="Override path to player_projections.csv (default: <data-dir>/player_projections.csv)",
    )
    parser.add_argument(
        "--sample-players",
        type=int,
        default=10,
        help="Number of sample players to print (default: 10)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    data_dir: Path = args.data_dir
    club_byes_csv: Path = args.club_byes_csv or (data_dir / "club_byes.csv")
    fixtures_csv: Path = args.fixtures_csv or (data_dir / "fixtures.csv")
    player_projections_csv: Path = args.player_projections_csv or (data_dir / "player_projections.csv")

    prospective_data = load_prospective_input_data(
        club_byes_csv=club_byes_csv,
        fixtures_csv=fixtures_csv,
        player_projections_csv=player_projections_csv,
    )

    # Run simulation
    simulate_round_scores(dataset=prospective_data, config=SimulationConfig())

    _print_summary(prospective_data=prospective_data, sample_players=args.sample_players)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
