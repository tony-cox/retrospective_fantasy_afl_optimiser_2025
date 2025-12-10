# AFL Fantasy Optimizer 2025

Retrospectively determines the optimal starting team and set of trades for the 2025 AFL Fantasy season using mathematical programming.

## Overview

This command-line application uses Integer Programming (via PuLP) to find the optimal AFL Fantasy squad selection. It reads player data from the AFL Fantasy API (or a local JSON file) and solves an optimization problem to maximize expected fantasy points while staying within salary cap and position constraints.

## Features

- **Data Models**: Player, Team, and Squad classes for structured data representation
- **Data Loading**: Fetch player data from AFL Fantasy API or load from local JSON files
- **Integer Programming**: Uses PuLP to solve the squad selection optimization problem
- **Position Constraints**: Enforces AFL Fantasy position requirements (DEF, MID, RUC, FWD)
- **Salary Cap**: Respects the fantasy salary cap constraint
- **Flexible Objectives**: Maximize expected score or minimize total cost

## Installation

1. Clone the repository:
```bash
git clone https://github.com/tony-cox/retrospective_fantasy_afl_optimiser_2025.git
cd retrospective_fantasy_afl_optimiser_2025
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Fetch data from AFL Fantasy API and optimize:
```bash
python main.py
```

### Load from Local File

Use a local JSON file instead of fetching from API:
```bash
python main.py --file path/to/players.json
```

### Customize Parameters

Adjust salary cap, squad size, and optimization objective:
```bash
python main.py --salary-cap 12000000 --squad-size 22 --objective max_score
```

### Command Line Options

- `--file FILE`: Path to local JSON file (optional, will fetch from API if not provided)
- `--url URL`: Custom URL to fetch player data from (defaults to AFL Fantasy API)
- `--salary-cap AMOUNT`: Salary cap in cents (default: 10,000,000 = $10M)
- `--squad-size SIZE`: Target squad size (default: 30)
- `--objective {max_score,min_cost}`: Optimization objective (default: max_score)
- `--quiet`: Suppress solver output

### Examples

Maximize expected score with default settings:
```bash
python main.py --quiet
```

Find cheapest squad that meets all constraints:
```bash
python main.py --objective min_cost
```

## Architecture

### Data Models (`src/models.py`)

- **Player**: Represents an AFL Fantasy player with attributes like name, position, price, and average score
- **Team**: Represents an AFL team
- **Squad**: Represents a fantasy squad with validation for salary cap and squad size constraints

### Data Loader (`src/data_loader.py`)

- **DataLoader**: Fetches and parses player data from the AFL Fantasy API or local JSON files
- Supports different JSON structures
- Handles errors gracefully

### Optimizer (`src/optimizer.py`)

- **FantasyOptimizer**: Builds and solves the Integer Programming model using PuLP
- Constraints:
  - Exact squad size requirement
  - Salary cap limit
  - Position minimums and maximums (DEF: 6-8, MID: 8-10, RUC: 2-3, FWD: 6-8)
- Objectives:
  - Maximize total expected score
  - Minimize total cost

### Main Application (`main.py`)

Command-line interface that orchestrates the data loading, optimization, and result display.

## Position Constraints

The optimizer enforces the following position requirements:

| Position | Minimum | Maximum |
|----------|---------|---------|
| DEF      | 6       | 8       |
| MID      | 8       | 10      |
| RUC      | 2       | 3       |
| FWD      | 6       | 8       |

## Requirements

- Python 3.10+
- pandas >= 2.0.0
- pulp >= 2.7.0
- requests >= 2.31.0

## License

See LICENSE file for details.
