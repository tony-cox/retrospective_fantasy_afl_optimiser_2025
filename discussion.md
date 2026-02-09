# Discussion – What the optimal 2025 season looked like

This write-up interprets the optimiser’s **fully retrospective** 2025 solution.

It’s written in the spirit of the questions in `README.md`: not “what happened” (we already know that), but *what a perfectly-informed coach would have done* — and what that implies about popular coaching heuristics.

Primary reference:
- `output/solution.md` (the generated markdown report)

## A quick reminder of what “optimal” means here

This is the **optimal** solution *given the model’s rules and the input data*:
- weekly squad selection constraints (positions, bench, utility)
- trade limits per round
- salary cap and bank balance dynamics
- bye rounds where only the best **N** on-field players count
- all scores/prices/DPP changes are known with hindsight

So: it’s not “what a human should have done with imperfect information”. It’s “what the best possible sequence of decisions was, if you knew the future”.

That matters because some patterns that look strange to humans can be perfectly rational when uncertainty is removed.

---

## 1) Starting team: midprice-heavy, but not a pure “guns and rookies” build

The Round 1 squad (see **Starting team** in `output/solution.md`) is strongly midprice-heavy.

### A small number of mega-premiums
The starting team has only one player above $1M:
- Jordan Dawson ($1.080M)

Many human coaches typically start with several set-and-forget premiums (especially captaincy candidates). The optimiser doesn’t.

### Not many basement rookies on-field
There are some cheap players, but the on-field squad is not “stacked with basement rookies”. The bench also includes multiple non-rookie prices (e.g. Jack Gunston at $575k, Connor O’Sullivan / Daniel Curtin at $300k).

This supports your observation that the starting structure looks closer to **midprice madness** than to the conventional rookie-cash ramp.

### Starting bank is low (not high)
After the missing-price bugfix and re-run, the starting bank is:
- **$75,000** (Round 1)

So the earlier observation that the optimiser held unusually high cash from the start is **no longer true**. In Round 1, it spends almost the entire cap.

---

## 2) Trades: it still makes lots of sideways moves

Your biggest qualitative observation survives the re-run: the solution makes a lot of **sideways trades** throughout the year.

There are certainly rounds that look like classic “upgrade season” behaviour (a cheaper player traded in for a more expensive one), but the overall pattern is closer to:
- constant rebalancing of the 30
- frequent swapping of mid/high-priced players
- moving money and points between lines

Even without building a full classification system for every trade, the round summary makes it clear that the optimiser rarely settles into long set-and-forget holds. It keeps using trades as a lever to chase known future points.

### Why sideways trades become rational with hindsight
Sideways trades are often discouraged in human play because:
- they burn limited trades
- they can derail cash generation plans
- humans are uncertain the incoming player will outperform

With hindsight, those objections mostly disappear.

If you *know* a player is about to underperform (injury, role change, variance, matchup, role), and you *know* another player is about to spike, then sideways trades are direct point conversion.

In that sense, the optimiser behaves like a “perfect information” version of what humans loosely call **fix-up season** — but extended across the entire year.

---

## 3) Bank balance: not huge, but often non-trivial

With the pricing bug fixed, the bank balance behaviour is now realistic.

A few examples from the round summary:
- Round 1 bank: $75k
- Round 2 bank: $498k
- Round 6 bank: $8k
- Round 11 bank: $2k
- Round 24 bank: $1.701M

This is still interesting: the optimiser is willing to hold meaningfully more cash than many humans would in some parts of the season (e.g. Round 2), but it also frequently runs the bank close to zero.

### What does holding cash mean here?
Holding cash is not automatically bad. It’s only suboptimal if there existed a feasible alternative team that:
- spent more cash, *and*
- turned that spend into more scored points, *and*
- didn’t compromise future rounds via bank/trade constraints.

With perfect information, if the best future point trajectory involves waiting for particular buying opportunities later, the model will happily keep cash now.

### Late-season bank growth
By Round 23–24, bank balance becomes large ($1.091M then $1.701M). This likely indicates that by season end:
- there are fewer valuable upgrades remaining under the trade constraints
- the best use of trades is points-driven reshuffling rather than fully spending the cap

In other words, cash becomes less scarce than *opportunity*.

---

## 4) Captaincy and bye rounds: best-N selection has visible effects

The report makes bye rounds / best-N rounds obvious because on-field players who didn’t count are shown in brackets, e.g. **(72 pts)**.

This has two implications:
1. The model can tolerate some weaker on-field selections in bye rounds, because they might not be part of the best-N counted group.
2. The “scored” selection becomes an important lever: the optimiser chooses which on-field players actually contribute to the objective.

Captaincy behaves as expected:
- the captain is always a counted player
- the captain choice follows known future spikes (e.g. Nick Daicos / Max Gawn style weeks)

---

## 5) How does this map to common coaching heuristics?

### Guns and rookies?
Not really. The Round 1 team is not a classic guns-and-basement-rookies shape.

### Midprice madness?
Yes. The starting team and the overall trade cadence strongly resemble a midprice-heavy optimisation, not an early rush to lock in a premium spine.

### One down, one up?
Not as a dominant theme. There are rounds that resemble it, but the optimiser doesn’t appear to treat it as the primary organising principle.

With hindsight, “upgrade season” is less about a narrative arc and more about *which move increases total future points the most*, given the constraints.

### Fix-up / upgrade / luxury?
The human “phases” still aren’t a perfect fit.

The optimiser’s behaviour looks like:
- aggressive point-chasing via trades when it’s profitable
- less attachment to any particular season narrative

---

## 6) What would be worth analysing next?

This discussion is intentionally qualitative. The next step to make it sharper is to compute metrics from `output/solution.json`, for example:
- number of unique players used during the season
- trade classification counts (sideways vs upgrade/downgrade by price)
- distribution of bank balance by “phase” (early / pre-byes / byes / post-byes)
- how often a “bench rookie down” trade occurs vs a midprice/premium reshuffle

That would let us answer the README questions with hard numbers:
- how midprice-heavy was the starting 22 vs the starting 30?
- how quickly does the optimal solution converge to a premium-heavy composition (if at all)?
- does it ever chase a true “23rd premium”, or is that mostly a human heuristic?

---

## Solver optimality gap (1%): what it means

This solution was generated with a **1% MIP optimality gap** setting.

In practical terms, the solver stops once it has proven that the current best solution is within 1% of the (unknown) true optimum. That means:
- the reported solution is **very likely optimal**, but
- there *may* exist a better solution, and the solver has not guaranteed it has found the absolute best possible one.

How to interpret the 1% bound depends on whether your objective is framed as maximisation or minimisation:
- In a **maximisation** problem (our case), a 1% gap means the solver has an upper bound on the true optimum that is at most ~1% higher than the value of the best solution it has found.

So, if the objective value reported in `output/solution.md` is **59,237**, then a 1% gap implies the true optimal objective can’t be more than roughly:
- 59,237 × 1.01 ≈ **59,829**

That’s an upper bound, not an expectation. In many cases the solver finds the true optimum well before it can *prove* it, but the gap is a good way to trade off runtime vs provable optimality.

If we want to be absolutely certain the solution is optimal, we can re-run with a smaller gap (e.g. 0.1%) or with a proven optimal solve (0% gap), at the cost of more solve time.
