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

## 1) Starting team: midprice-madness

The Round 1 squad (see **Starting team** in `output/solution.md`) is strongly midprice-heavy.

### A small number of mega-premiums
The starting team has only one player above $1M:
- Jordan Dawson ($1.080M)
- Nasiah Wanganeen-Milera ($1.003M)

Many human coaches typically start with several set-and-forget premiums (especially captaincy candidates). The optimiser doesn’t.

### Not many  rookies on-field
There are some cheap players, but the on-field squad only has 3 rookies on field. The bench also includes multiple non-rookie prices (e.g. Jack Gunston at $575k, Ryan Maric at $421k).

This supports an observation that the starting structure looks closer to **midprice madness** than to the conventional rookie-cash ramp.

### Starting bank
The starting bank is:
- **$75,000**

---

## 2) Trades: Constant sideways moves

There are almost no rounds that look like classic “upgrade season” behaviour (i.e. downgrade a cashed up rookie down to a lower priced one), but the overall pattern is closer to:
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

## 3) Bank balance: highly variable

The bank balance is highly variable, with some rounds being very high, especially towards the end where the team value is so high (near $30M) that it just doesn't matter anymore.

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

## 5) How does this map to common coaching heuristics?

### Guns and rookies?
Not really. The Round 1 team is not a classic guns-and-basement-rookies shape.

### Midprice madness?
Yes. The starting team and the overall trade cadence strongly resemble a midprice-heavy optimisation, not an early rush to lock in a premium spine.

### One down, one up?
Not as a dominant theme. There are rounds that partially resemble it, but the optimiser doesn’t appear to treat it as the primary organising principle.

With hindsight, “upgrade season” is less about a narrative arc and more about *which move increases total future points the most*, given the constraints.

### Fix-up / upgrade / luxury?
The human “phases” still aren’t a perfect fit.

The optimiser’s behaviour looks like:
- aggressive point-chasing via trades when it’s profitable
- less attachment to any particular season narrative

---

## 6) Endgame: why the optimiser finishes with “30 premiums”

One of the most counter-intuitive outcomes in the solution is the **end-of-season wealth**.

Human context (typical 2025 top-coach shape):
- Many strong human coaches end the year with a team value around **$25M** (very rough), and
- they often talk about reaching **"23 premiums"** (a completed on-field premium team plus one extra), but rarely more than that.

In the optimiser’s solved season, the end state looks fundamentally different:
- by Round 24 the **total value** is **$30.488M**
- and the Round 24 squad list is essentially **premium-priced across almost all 30 slots** (even bench/utility), i.e. it ends with something that looks like **"30 premiums"**.

### Why this happens under perfect hindsight
The key point: the optimiser isn’t trying to mimic the human narrative of "build cash via rookies, then upgrade". It’s trying to maximise **total scored points**, subject to constraints, with full knowledge of:
- which players will spike in score
- which players will rise in price
- which players will fall in price
- when each of those changes happens

That enables patterns that humans can’t reliably execute:

1) **Avoiding dead money and dead holds**
   Humans often "hold" midpricers or early picks longer than ideal because they don’t know whether upcoming form/role changes will persist.
   With hindsight, the optimiser can exit exactly when a player stops being valuable (either in points or price trajectory).

2) **Systematically harvesting value through sideways trades**
   Sideways trades are usually framed as "wasting trades".
   But in a perfect-information world, a sideways move can be the single best way to:
   - capture a price rise that happens to one player over a short window, then
   - rotate into a different player who has the next short window of growth and/or points.

   In other words: trades become a way to *chain together* multiple small value edges.
   If those edges compound across 24 rounds, you can end up with a squad that is far more expensive than what a human coach typically reaches.

3) **Bench as an asset, not a liability**
   Humans commonly accept that the bench contains cheap players because they’re mostly there for cash generation and emergencies.

   But the optimiser has two advantages:
   - it can plan bench value with hindsight (bring in bench players exactly when they’re about to rise), and
   - it can exploit bye-round/best-N scoring structure to sometimes tolerate non-contributing bench or on-field selections without losing points.

   Over time, this can turn the bench into part of the same value-harvesting engine, rather than something that stays cheap.

4) **A different interpretation of "completed team"**
   For humans, a "completed team" usually means: you’ve got the best on-field 22, and trades become luxury.

   For the optimiser, the objective never changes. If the best way to gain points is to keep rebalancing, it will. It doesn’t care about the psychological comfort of stability.

### What to take away from this (and what not to)

- This does **not** mean humans should always aim for constant sideways trades. Humans don’t have perfect information, and sideways trades are exactly where forecast error is most damaging.
- It *does* suggest that "one down, one up" is not a fundamental law — it’s a practical heuristic that works well under uncertainty.
- The optimiser’s end-state wealth is a sign that there is a lot of **value transfer opportunity** available in the game’s pricing + trade system if you can time it perfectly.

A useful way to frame the result is:

> A human coach is trying to be robust to uncertainty; the retrospective optimiser is trying to be perfectly opportunistic.

That difference alone can explain why it can reach something like **30 premium-priced players** by Round 24.

---

## 7) What would be worth analysing next?

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

