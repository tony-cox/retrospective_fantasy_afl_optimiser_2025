#!/usr/bin/env python3
"""
Main command-line application for AFL Fantasy Optimizer.

This application fetches AFL Fantasy player data and uses Integer Programming
to find the optimal squad selection that maximizes expected points while
staying within the salary cap and position constraints.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_loader import DataLoader
from src.optimizer import FantasyOptimizer
from src.models import Squad


def print_squad_details(squad: Squad):
    """Print detailed information about a squad."""
    print("\n" + "="*70)
    print("SELECTED SQUAD")
    print("="*70)
    
    # Group players by position
    by_position = {}
    for player in squad.players:
        if player.position not in by_position:
            by_position[player.position] = []
        by_position[player.position].append(player)
    
    # Print by position
    for position in ['DEF', 'MID', 'RUC', 'FWD']:
        if position in by_position:
            print(f"\n{position} ({len(by_position[position])} players):")
            print("-" * 70)
            for player in sorted(by_position[position], key=lambda p: p.average_score, reverse=True):
                print(f"  {player.full_name:30s} ${player.price:>10,}  Avg: {player.average_score:>6.2f}")
    
    print("\n" + "="*70)
    print(f"Total Players: {len(squad.players)}")
    print(f"Total Cost: ${squad.total_cost:,}")
    print(f"Expected Total Score: {squad.total_score:.2f}")
    print("="*70 + "\n")


def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description='Optimize AFL Fantasy squad selection using Integer Programming.'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Path to local JSON file (optional, will fetch from API if not provided)'
    )
    parser.add_argument(
        '--url',
        type=str,
        help='URL to fetch player data from (defaults to AFL Fantasy API)'
    )
    parser.add_argument(
        '--salary-cap',
        type=int,
        default=10_000_000,
        help='Salary cap in dollars (default: 10,000,000 = $10M)'
    )
    parser.add_argument(
        '--squad-size',
        type=int,
        default=30,
        help='Target squad size (default: 30)'
    )
    parser.add_argument(
        '--objective',
        type=str,
        choices=['max_score', 'min_cost'],
        default='max_score',
        help='Optimization objective (default: max_score)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress solver output'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize data loader
        print("Initializing AFL Fantasy Optimizer...")
        loader = DataLoader(url=args.url)
        
        # Load data
        if args.file:
            print(f"Loading data from file: {args.file}")
            loader.load_from_file(args.file)
        else:
            print("Fetching data from AFL Fantasy API...")
            loader.fetch_data()
        
        # Parse players
        print("Parsing player data...")
        players = loader.parse_players()
        print(f"Loaded {len(players)} players")
        
        if len(players) == 0:
            print("Error: No players found in the data.")
            return 1
        
        # Filter out players with no games or zero price
        valid_players = [
            p for p in players
            if p.games_played > 0 and p.price > 0
        ]
        print(f"Found {len(valid_players)} valid players (played games and have a price)")
        
        if len(valid_players) == 0:
            print("Error: No valid players available for optimization.")
            return 1
        
        # Initialize optimizer
        print(f"\nInitializing optimizer...")
        print(f"  Salary cap: ${args.salary_cap:,}")
        print(f"  Squad size: {args.squad_size}")
        print(f"  Objective: {args.objective}")
        
        optimizer = FantasyOptimizer(
            players=valid_players,
            salary_cap=args.salary_cap,
            squad_size=args.squad_size
        )
        
        # Build model
        print("\nBuilding Integer Programming model...")
        optimizer.build_model(objective=args.objective)
        
        # Solve
        print("Solving optimization problem...")
        success = optimizer.solve(verbose=not args.quiet)
        
        if not success:
            print("\nOptimization failed to find optimal solution.")
            return 1
        
        # Get results
        print("\nOptimization completed successfully!")
        squad = optimizer.get_selected_squad()
        summary = optimizer.get_solution_summary()
        
        # Print summary
        print(f"\nStatus: {summary['status']}")
        print(f"Objective Value: {summary['objective_value']:.2f}")
        
        # Print detailed squad
        print_squad_details(squad)
        
        # Print position breakdown
        print("Position Breakdown:")
        for position, count in sorted(summary['position_breakdown'].items()):
            print(f"  {position}: {count} players")
        
        print(f"\nSalary Cap Remaining: ${summary['salary_cap_remaining']:,}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
