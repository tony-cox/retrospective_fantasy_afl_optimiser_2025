---
title: Retro Fantasy AFL Optimiser Formulation
date: \today
header-includes:
  - \usepackage{mathtools}
  - \usepackage{amssymb}
  - \usepackage{booktabs}
  - \usepackage{siunitx}
numbersections: true
---

\newpage

# Description

\newpage

# Sets

Let $P$, subscripted by $p$, be the set of players.

Let $R = \{1,2,\ldots,24\}$, subscripted by $r$, be the set of rounds.

Let $F \subseteq P$ be the set of forwards.

Let $M \subseteq P$ be the set of midfielders.

Let $U \subseteq P$ be the set of rucks.

Let $D \subseteq P$ be the set of defenders.

\newpage

# Parameters (Vectors)

Let $s_{p,r}$ be the (known) number of points scored by player $p$ in round $r$.

Let $c_{p,r}$ be the (known) price of player $p$ in round $r$.

Let $e^{F}_p$ be a binary parameter indicating whether player $p$ is eligible to be selected as a forward (1 if eligible, 0 otherwise).

Let $e^{M}_p$ be a binary parameter indicating whether player $p$ is eligible to be selected as a midfielder (1 if eligible, 0 otherwise).

Let $e^{U}_p$ be a binary parameter indicating whether player $p$ is eligible to be selected as a ruck (1 if eligible, 0 otherwise).

Let $e^{D}_p$ be a binary parameter indicating whether player $p$ is eligible to be selected as a defender (1 if eligible, 0 otherwise).

\newpage

# Constants

Let $\mathrm{SALARY\_CAP}$ be the starting salary cap.

\newpage

# Decision Variables

Let $x_{p,r}$ be a binary decision variable indicating whether player $p$ is selected in the team (in any position, on-field or bench) in round $r$ (1 if selected, 0 otherwise).

Let $x^{F,\mathrm{on}}_{p,r}$ be a binary decision variable indicating whether player $p$ is selected as an on-field forward in round $r$ (1 if selected, 0 otherwise).

Let $x^{M,\mathrm{on}}_{p,r}$ be a binary decision variable indicating whether player $p$ is selected as an on-field midfielder in round $r$ (1 if selected, 0 otherwise).

Let $x^{U,\mathrm{on}}_{p,r}$ be a binary decision variable indicating whether player $p$ is selected as an on-field ruck in round $r$ (1 if selected, 0 otherwise).

Let $x^{D,\mathrm{on}}_{p,r}$ be a binary decision variable indicating whether player $p$ is selected as an on-field defender in round $r$ (1 if selected, 0 otherwise).

Let $x^{F,\mathrm{bench}}_{p,r}$ be a binary decision variable indicating whether player $p$ is selected as a bench forward in round $r$ (1 if selected, 0 otherwise).

Let $x^{M,\mathrm{bench}}_{p,r}$ be a binary decision variable indicating whether player $p$ is selected as a bench midfielder in round $r$ (1 if selected, 0 otherwise).

Let $x^{U,\mathrm{bench}}_{p,r}$ be a binary decision variable indicating whether player $p$ is selected as a bench ruck in round $r$ (1 if selected, 0 otherwise).

Let $x^{D,\mathrm{bench}}_{p,r}$ be a binary decision variable indicating whether player $p$ is selected as a bench defender in round $r$ (1 if selected, 0 otherwise).

Let $x^{Q,\mathrm{bench}}_{p,r}$ be a binary decision variable indicating whether player $p$ is selected in the bench utility position in round $r$ (1 if selected, 0 otherwise).

Let $b_r$ be a continuous decision variable representing the amount of cash in the bank at the end of round $r$.

Let $\mathrm{in}_{p,r}$ be a binary decision variable indicating whether player $p$ is traded into the team in round $r$ (present in round $r$ but not in round $r-1$).

Let $\mathrm{out}_{p,r}$ be a binary decision variable indicating whether player $p$ is traded out of the team in round $r$ (present in round $r-1$ but not in round $r$).

\newpage

# Objective Function

Maximise the total points scored by the on-field selected players across all rounds:

$$
\text{Maximise} \quad \sum_{r \in R} \sum_{p \in P} s_{p,r} \cdot \left(x^{F,\mathrm{on}}_{p,r} + x^{M,\mathrm{on}}_{p,r} + x^{U,\mathrm{on}}_{p,r} + x^{D,\mathrm{on}}_{p,r}\right)
$$

\newpage

# Constraints

## Initial Bank Balance

Cash in the bank in round 1 is the salary cap minus the total price of the selected starting team:

$$
b_1 = \mathrm{SALARY\_CAP} - \sum_{p \in P} c_{p,1} \cdot x_{p,1}
$$

## Bank Non-negativity

The bank balance cannot be negative in any round:

$$
b_r \ge 0 \quad \forall r \in R
$$

## Bank Balance Recurrence

The bank balance carries forward between rounds and is adjusted by the round-$r$ prices of players traded out and traded in:

$$
b_r = b_{r-1} + \sum_{p \in P} c_{p,r} \cdot \mathrm{out}_{p,r} - \sum_{p \in P} c_{p,r} \cdot \mathrm{in}_{p,r}
\quad \forall r \in R \setminus \{1\}
$$

## Trade Indicator Linking

Trade-in and trade-out indicators are linked to changes in overall selection $x_{p,r}$. The following constraints linearise:

- $\mathrm{in}_{p,r} = 1$ iff $(x_{p,r-1}, x_{p,r}) = (0,1)$
- $\mathrm{out}_{p,r} = 1$ iff $(x_{p,r-1}, x_{p,r}) = (1,0)$

**Lower bounds (force the indicator to switch on when a change occurs):**

If the player was not selected in $r-1$ but is selected in $r$, then $x_{p,r} - x_{p,r-1} = 1$, which forces $\mathrm{in}_{p,r} \ge 1$.

This is the "trigger" constraint for trade-ins.

$$
\mathrm{in}_{p,r} \ge x_{p,r} - x_{p,r-1} \quad \forall p \in P, \forall r \in R \setminus \{1\}
$$

If the player was selected in $r-1$ but is not selected in $r$, then $x_{p,r-1} - x_{p,r} = 1$, which forces $\mathrm{out}_{p,r} \ge 1$.

This is the "trigger" constraint for trade-outs.

$$
\mathrm{out}_{p,r} \ge x_{p,r-1} - x_{p,r} \quad \forall p \in P, \forall r \in R \setminus \{1\}
$$

**Upper bounds (prevent false positives / enforce the correct direction of change):**

A trade-in can only occur if the player is selected in round $r$.

This prevents $\mathrm{in}_{p,r}=1$ when the player is not actually in the round-$r$ team.

$$
\mathrm{in}_{p,r} \le x_{p,r} \quad \forall p \in P, \forall r \in R \setminus \{1\}
$$

A trade-in can only occur if the player was not selected in round $r-1$.

This prevents $\mathrm{in}_{p,r}=1$ when the player was already owned in round $r-1$ (i.e. no trade-in happened).

$$
\mathrm{in}_{p,r} \le 1 - x_{p,r-1} \quad \forall p \in P, \forall r \in R \setminus \{1\}
$$

A trade-out can only occur if the player was selected in round $r-1$.

This prevents $\mathrm{out}_{p,r}=1$ when the player wasn't owned in round $r-1$.

$$
\mathrm{out}_{p,r} \le x_{p,r-1} \quad \forall p \in P, \forall r \in R \setminus \{1\}
$$

A trade-out can only occur if the player is not selected in round $r$.

This prevents $\mathrm{out}_{p,r}=1$ when the player is still owned in round $r$.

$$
\mathrm{out}_{p,r} \le 1 - x_{p,r} \quad \forall p \in P, \forall r \in R \setminus \{1\}
$$

## Linking Constraints

Overall selection must match positional selection:

$$
x_{p,r} = x^{F,\mathrm{on}}_{p,r} + x^{M,\mathrm{on}}_{p,r} + x^{U,\mathrm{on}}_{p,r} + x^{D,\mathrm{on}}_{p,r} + x^{F,\mathrm{bench}}_{p,r} + x^{M,\mathrm{bench}}_{p,r} + x^{U,\mathrm{bench}}_{p,r} + x^{D,\mathrm{bench}}_{p,r} + x^{Q,\mathrm{bench}}_{p,r} \quad \forall p \in P, \forall r \in R
$$

## Maximum Team Changes Per Round

Between consecutive rounds, at most two players may differ in the selected team (players may change positions freely; this constraint applies only to $x_{p,r}$).

To express this linearly, introduce auxiliary binary variables $\delta_{p,r}$ indicating whether player $p$ changes selection status between rounds $r-1$ and $r$:

$$
\delta_{p,r} \ge x_{p,r} - x_{p,r-1} \quad \forall p \in P, \forall r \in R \setminus \{1\}
$$

$$
\delta_{p,r} \ge x_{p,r-1} - x_{p,r} \quad \forall p \in P, \forall r \in R \setminus \{1\}
$$

Then limit the number of changes per round:

$$
\sum_{p \in P} \delta_{p,r} \le 4 \quad \forall r \in R \setminus \{1\}
$$

\newpage

## Positional Structure

The team must have the following positional structure in every round.

On-field defenders:

$$
\sum_{p \in P} x^{D,\mathrm{on}}_{p,r} = 6 \quad \forall r \in R
$$

Bench defenders:

$$
\sum_{p \in P} x^{D,\mathrm{bench}}_{p,r} = 2 \quad \forall r \in R
$$

On-field midfielders:

$$
\sum_{p \in P} x^{M,\mathrm{on}}_{p,r} = 8 \quad \forall r \in R
$$

Bench midfielders:

$$
\sum_{p \in P} x^{M,\mathrm{bench}}_{p,r} = 2 \quad \forall r \in R
$$

On-field rucks:

$$
\sum_{p \in P} x^{U,\mathrm{on}}_{p,r} = 2 \quad \forall r \in R
$$

Bench rucks:

$$
\sum_{p \in P} x^{U,\mathrm{bench}}_{p,r} = 1 \quad \forall r \in R
$$

On-field forwards:

$$
\sum_{p \in P} x^{F,\mathrm{on}}_{p,r} = 6 \quad \forall r \in R
$$

Bench forwards:

$$
\sum_{p \in P} x^{F,\mathrm{bench}}_{p,r} = 2 \quad \forall r \in R
$$

Bench utility:

$$
\sum_{p \in P} x^{Q,\mathrm{bench}}_{p,r} = 1 \quad \forall r \in R
$$

\newpage

## Position Eligibility

Players can only be selected into a position if they are eligible for that position (eligibility may be multi-position):

$$
x^{F,\mathrm{on}}_{p,r} \le e^{F}_p \quad \forall p \in P, \forall r \in R
$$

$$
x^{F,\mathrm{bench}}_{p,r} \le e^{F}_p \quad \forall p \in P, \forall r \in R
$$

$$
x^{M,\mathrm{on}}_{p,r} \le e^{M}_p \quad \forall p \in P, \forall r \in R
$$

$$
x^{M,\mathrm{bench}}_{p,r} \le e^{M}_p \quad \forall p \in P, \forall r \in R
$$

$$
x^{U,\mathrm{on}}_{p,r} \le e^{U}_p \quad \forall p \in P, \forall r \in R
$$

$$
x^{U,\mathrm{bench}}_{p,r} \le e^{U}_p \quad \forall p \in P, \forall r \in R
$$

$$
x^{D,\mathrm{on}}_{p,r} \le e^{D}_p \quad \forall p \in P, \forall r \in R
$$

$$
x^{D,\mathrm{bench}}_{p,r} \le e^{D}_p \quad \forall p \in P, \forall r \in R
$$

\newpage

# Notes / Implementation Mapping
