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

### 5) The season’s trading “phases”
Even when coaches broadly agree on *what* a good team looks like, they often disagree on the best *path* to get there. In practice, many coaches describe the year as moving through a few informal phases:

- **Fix-up season (Rounds ~1–4):** early rounds are often used to correct Round 1 assumptions. Coaches may make several **sideways trades** (especially among rookies and midpricers) to chase role changes, better job security, or clearer value.
- **Upgrade season (from ~Round 5 through the byes):** the classic pattern is **"one down, one up"** — trade a cash-generating bench rookie down to a cheaper rookie, then use the freed cash to upgrade a midpricer (or an on-field rookie) up to a premium. This often continues until the end of the mid-season byes. During this phase, it is heavily discouraged by most coaches to make sideways trades as this costs you the ability to get bench cash onto the field.
- **Luxury season (post-byes):** once the on-field team is close to "completed", trades become less about cash generation and more about points. Coaches may:
  - make **sideways trades** to target good fixtures and form
  - aim for a **23rd premium** (a "bonus" premium beyond the best on-field core) to add cover and flexibility

### 6) Bye-round and special-round tactics
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
- Does it make sideways trades during upgrade season before reaching a “completed team”?
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
- `team_rules.json`: squad structure rules and salary cap
- `rounds.json`: trading/bye-round scoring parameters by round
- `data_filter.json`: optional filters for solving smaller instances

### Outputs and write-up
- Solver outputs are written to `output/` (ignored by git).
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

By default this loads the production-style inputs from `data/`, applies any filters from `data/data_filter.json`, formulates the MILP, solves it, and writes a `output/solution.json`.

---

## Status / roadmap

### Current status (implemented)

- ✅ **Input pipeline**: production-style data loading from `data/` (players, prices/scores, and positional updates).
- ✅ **Full MILP implemented in code** (PuLP): team selection (on-field + bench + utility), bye-round “best N” scoring selection, captaincy, trades per round, and bank balance dynamics.
- ✅ **Solver choice (CBC or Gurobi)**:
  - Default solver is **CBC** (via PuLP).
  - If **Gurobi** is installed and licensed (and `GUROBI_HOME` is present), the project can solve using **Gurobi** for improved performance and richer solver logs.
  - Solver options (e.g. MIP gap) can be configured via a JSON config file in `data/`.
- ✅ **Full-season production solve**: the model has been solved successfully on the full **2025** dataset (all rounds), without requiring formulation refactors to reduce variable counts.
- ✅ **Solution export**: writes a structured `output/solution.json` with per-round team composition, trades, scoring, bank balance, and captain.
- ✅ **Reporting**: generates a readable **markdown report** from `output/solution.json`, including:
  - starting team summary
  - a round-by-round summary table
  - detailed per-round breakdowns (trades, finances, and team tables)
- ✅ **Test suite**: unit tests for data loading and key model-building pieces, plus integration tests across small instances.

### Roadmap (next steps)

**Reporting / analysis**
- Add a `discussion.md` write-up interpreting the optimal solution against the strategy questions in this README.
- Consider additional report outputs (CSV summaries, charts) for easier analysis.

**Solver / runtime ergonomics**
- Improve command-line UX for running filtered vs full solves (explicit CLI flags, clearer presets).
- Persist solver run metadata (solver used, time, MIP gap, objective) alongside outputs for comparison.

**Prospective solving (2026+)**
- Extend the pipeline to run the optimiser on **future seasons** (e.g. 2026) using **projected player scores** instead of known scores.
- Add an **in-season** mode: given a **current team state** (selected squad, bank balance, and trades/rounds already completed), optimise the remaining season from the next round onward.
- Add a **Monte Carlo simulation** mode that:
  - samples player scores from a reasonable per-player distribution around projections (variance calibrated from historical data)
  - optionally applies an **opponent difficulty / fixture hardness** adjustment by position (e.g. DEF/MID/RUC/FWD), to shift projections based on the week’s matchup
  - runs many scenarios and reports robust strategies (e.g. expected score, downside risk, probability of beating a baseline)
  - can be used both for **pre-season** planning and **weekly trade recommendations** during the season
- Add **price movement modelling** for prospective runs:
  - implement an approximation of the AFL Fantasy pricing formula to update player prices round-by-round based on simulated scores
  - validate/calibrate the approximation against historical seasons (e.g. 2025) to ensure simulated price paths are realistic
