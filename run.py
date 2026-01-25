from __future__ import annotations

from pathlib import Path

from retro_fantasy.main import load_players


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    data_dir = repo_root / "data"

    players = load_players(
        players_json_path=data_dir / "players_final.json",
        position_updates_csv_path=data_dir / "position_updates.csv",
    )

    print(f"Loaded {len(players)} players")

    # Print a small sample to verify eligibility updates look sensible.
    sample_names = [
        "Patrick Dangerfield",
        "Harry Perryman",
        "Darcy Cameron",
    ]

    for name in sample_names:
        player = next((p for p in players.values() if p.name == name), None)
        if player is None:
            print(f"- {name}: not found in loaded data")
            continue

        rounds = sorted(player.by_round)
        if not rounds:
            print(f"- {name}: no round data")
            continue

        def _fmt_round(r: int) -> str:
            info = player.by_round[r]
            elig = ",".join(sorted(pos.value for pos in info.eligible_positions))
            return f"r{r}: score={info.score}, price={info.price}, elig=[{elig}]"

        interesting = [r for r in (1, 5, 6, 11, 12, 18) if r in player.by_round]
        if not interesting:
            interesting = [rounds[0], rounds[-1]]

        print(f"\n{name} (id={player.player_id})")
        print(f"  original_positions={[p.value for p in sorted(player.original_positions, key=lambda x: x.value)]}")
        for r in interesting:
            print(f"  {_fmt_round(r)}")


if __name__ == "__main__":
    main()
