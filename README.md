# Retrospective AFL Fantasy Optimiser

Retrospectively determines the **optimal** starting team and set of trades for a past AFL Fantasy season using **mathematical programming**.

This repository is designed to answer a simple but surprisingly tricky question:

> *“If we could replay a season with perfect hindsight (all scores, prices, and position changes known), what would the best possible coaching decisions have been?”*

If you want the pop-culture version: imagine you’re **young Biff Tannen** in *Back to the Future Part II*, clutching the **Gray’s Sports Almanac** — except instead of boxing and horse racing results, it contains the entire AFL Fantasy season: every player’s scores, prices, and DPP changes.

You’d still face a non-obvious problem: **how do you convert perfect information into the best sequence of starting picks and weekly trades**, under salary caps, position rules, bye rounds, and trade limits? That’s exactly what this project models and solves.

The goal isn’t to “predict” a future season. It’s to use a solved past season to better understand which coaching ideas and trade patterns were genuinely effective.

---

## Background: How AFL Fantasy strategy evolved

AFL Fantasy coaches have developed (and debated) many approaches to building a team and trading through the season. A few major strategy families show up repeatedly:

### 1) “Best on field” (early-era intuition)
In the early days (before the current level of social media / content), many coaches focused on picking the best possible on-field team and paid less attention to bench composition.

Over time it became clear that this wasn’t optimal because bench rookies can generate cash and enable upgrades.

### 2) “Guns and rookies”
A very common modern baseline strategy:
- Start with many proven premium scorers (“guns”) in the best-22
- Fill remaining slots with cheap rookies
- Use rookies’ price rises to fund upgrades via the classic “one down, one up” approach

### 3) “Midprice madness”
A deliberate alternative that leans heavily into mid-priced players rather than extremes.

### 4) Value-based selection (“unders”)
A more flexible mindset:
- Select players expected to rise in price (i.e., projected to score above what their current price implies)
- Avoid players that are fairly priced or overpriced
- Recognise that “value” depends on price tier (e.g., a premium may only need to beat expectation slightly, while a basement rookie may need to significantly outperform to be worth it)

### 5) Bye-round and special-round tactics
The introduction of multi-round byes made team structure and trade timing even more important:
- Some rounds score only the **best N players** on field (e.g., best 18), which changes optimisation incentives
- Some rounds allow **extra trades**, changing the best trade cadence

More recently, “Opening Round” (Round 0) created additional early byes and a new decision:
- Avoid players with an early bye (common conservative approach)
- Or exploit the “free look” at Opening Round performance and decide whether the value outweighs the missed bye score

---

## What this project does

This project solves a past AFL Fantasy season **retrospectively**.

That means:
- All player scores by round are known
- All player prices by round are known
- Position eligibility changes (DPP updates) during the season are known

Given those known inputs, the project finds:
- An optimal **starting squad**
- An optimal sequence of **trades** and weekly **team selection decisions**

The model is expressed as a **Mixed-Integer Linear Program (MILP)**.

---

## What questions this project is trying to answer

Once an optimal solution is computed, it can be analysed like a “perfect coach” benchmark.

Examples of strategy questions worth interrogating:

### Starting team construction
- Does the optimal Round 1 team resemble:
  - guns and rookies?
  - midprice madness?
  - a value-driven blend?
  - something else entirely?
- How much cash (if any) does the optimal solution keep in the bank early?

### Trades and cash generation
- Does the solution make short-term “cash plays” (brief holds purely for price movement)?
- Does it make sideways trades before reaching a “completed team”?
- Does it clear rookies off field quickly, or tolerate rookies longer while upgrading midpricers first?

### Bye rounds and special rounds
- Does the optimal solution deliberately select early-bye players (Opening Round participants)?
- How early does it plan for mid-season bye rounds?
- Does it “backload” bye structures, or aim for an even split?

### Endgame structure
- Does it chase a “23rd premium” (extra top scorer beyond the usual on-field core)?
- Or does it settle into a stable best-22 and use remaining trades for marginal gains?

---

## How to navigate this repository

### Mathematical formulation
- `formulation.md` contains the MILP formulation.
- `formulation.pdf` is included because GitHub’s markdown rendering can be limiting for mathematical notation.

Even if you don’t have an operations research background, the plain-language descriptions around the notation can still be useful.

### Data
The 2025 season data used by the model lives in `data/`:
- `players_final.json`: players, scores, and prices by round
- `position_updates.csv`: DPP (position eligibility) changes and the round they take effect

### Outputs and write-up
- Outputs (solution artefacts) will be written to `output/`.
- A future write-up interpreting the optimal solution and discussing the questions above will be in `discussion.md`.

### Code
All Python source code lives in:
- `src/retro_fantasy/`

---

## Installation

This project is packaged as a Python distribution named `retro-fantasy` and uses a standard `pyproject.toml` + `src/` layout, so it can be installed on Windows, Linux, or macOS using `pip`.

### Windows (PowerShell)

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install in editable mode (recommended for development):

```powershell
pip install -e .
```

If you also want dev tooling (pytest):

```powershell
pip install -e ".[dev]"
```

### Linux / macOS (bash)

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install in editable mode (recommended for development):

```bash
pip install -e .
```

If you also want dev tooling (pytest):

```bash
pip install -e ".[dev]"
```

---

## Run

A simple runner script exists at the repo root:

```bash
python run.py
```

(Windows PowerShell users can run the same command.)

This loads the production data in `data/` and prints a small sample of players/rounds to sanity-check that:
- JSON parsing works
- position updates are being applied from the correct round onward

---

## Status / roadmap

This repository currently includes:
- The mathematical formulation (`formulation.md`)
- The 2025 input datasets under `data/`
- Python code for loading/validating the input data
- A basic runner script (`run.py`) for sanity-checking the loader
- A growing test suite (pytest)

Next steps are to:
- Implement the optimisation model in code based on the formulation
- Solve the 2025 season end-to-end and commit the resulting output artefacts to `output/`
- Add `discussion.md` with interpretation of the optimal solution and commentary against the strategy questions above
- Handle players only being made available from certain rounds onward (e.g., mid-season draftees)