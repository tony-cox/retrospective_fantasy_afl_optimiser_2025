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

\newpage

# Objective Function

Maximise the total points scored by the on-field selected players across all rounds:

$$
\text{Maximise} \quad \sum_{r \in R} \sum_{p \in P} s_{p,r} \cdot \left(x^{F,\mathrm{on}}_{p,r} + x^{M,\mathrm{on}}_{p,r} + x^{U,\mathrm{on}}_{p,r} + x^{D,\mathrm{on}}_{p,r}\right)
$$

\newpage

# Constraints

## Starting Team Salary Cap

The total price of the starting team (round 1) must be at or under the salary cap:

$$
\sum_{p \in P} c_{p,1} \cdot x_{p,1} \le \mathrm{SALARY\_CAP}
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

# Notes / Implementation Mapping
