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

This model retrospectively determines the optimal AFL Fantasy team selection, captain choice, and trade sequence across a past season.

For each round $r \in R$, it chooses which players $p \in P$ are in the squad and allocates them to the required on-field and bench slots by position $k \in K$ (plus a bench utility slot). It also selects exactly one captain per round. The objective is to maximise the total realised points scored by the counted on-field players across all rounds, with the captain's counted score doubled.

The model respects:

- **Positional structure**: each round has required counts for on-field and bench positional slots by position ($n^{\mathrm{on}}_{k}$ and $n^{\mathrm{bench}}_{k}$), plus $\mathrm{UTILITY\_BENCH\_COUNT}$ bench utility slots.
- **Position eligibility**: a player may only be assigned to a position in $K$ (DEF/MID/RUC/FWD) if they are eligible for that position in that round.
- **Trade limits**: between consecutive rounds, at most $T_r$ players may be traded in (and at most $T_r$ traded out).
- **Budget / bank**: the initial bank is salary cap minus the cost of the starting squad; the bank balance is carried forward and updated each round using the round-$r$ prices of traded-out and traded-in players; and the bank is constrained to be non-negative via its domain ($b_r \in \mathbb{R}_{\ge 0}$).
- **Scoring (bye rounds)**: in each round, exactly $N_r$ on-field players are chosen to have their scores counted.
- **Captaincy**: exactly one of the counted on-field players is designated as captain each round, and their counted score is doubled.

This formulation is designed to be implemented as a mixed-integer linear program (MILP).

\newpage

# Sets

Let $P$, subscripted by $p$, be the set of players.

Let $R$, subscripted by $r$, be the set of rounds.

Let $K = \{\mathrm{DEF}, \mathrm{MID}, \mathrm{RUC}, \mathrm{FWD}\}$, subscripted by $k$, be the set of positions.

\newpage

# Parameters (Vectors)

Let $s_{p,r} \in \mathbb{R}$ be the (known) number of points scored by player $p$ in round $r$.

Let $c_{p,r} \in \mathbb{R}_{\ge 0}$ be the (known) price of player $p$ in round $r$.

Let $e_{p,k,r} \in \{0,1\}$ be a binary parameter indicating whether player $p$ is eligible to be selected in position $k$ in round $r$ (1 if eligible, 0 otherwise).

Let $n^{\mathrm{on}}_{k} \in \mathbb{Z}_{\ge 0}$ be the (known) number of on-field players required in position $k$.

Let $n^{\mathrm{bench}}_{k} \in \mathbb{Z}_{\ge 0}$ be the (known) number of bench players required in position $k$.

Let $T_r \in \mathbb{Z}_{\ge 0}$ be the (known) maximum number of trades allowed in round $r$.

Let $N_r \in \mathbb{Z}_{\ge 0}$ be the (known) number of on-field players whose scores count toward the team total in round $r$ (e.g. $N_r=22$ in normal rounds and $N_r=18$ in bye rounds).

\newpage

# Constants

Let $\mathrm{SALARY\_CAP} \in \mathbb{R}_{\ge 0}$ be the starting salary cap.

Let $\mathrm{UTILITY\_BENCH\_COUNT} \in \mathbb{Z}_{\ge 0}$ be the number of bench utility slots.

\newpage

# Decision Variables

Let $x_{p,r} \in \{0,1\}$ be a binary decision variable indicating whether player $p$ is selected in the team (in any position, on-field or bench) in round $r$.

Let $x^{\mathrm{on}}_{p,k,r} \in \{0,1\}$ be a binary decision variable indicating whether player $p$ is selected on-field in position $k$ in round $r$.

Let $x^{\mathrm{bench}}_{p,k,r} \in \{0,1\}$ be a binary decision variable indicating whether player $p$ is selected on the bench in position $k$ in round $r$.

Let $x^{Q,\mathrm{bench}}_{p,r} \in \{0,1\}$ be a binary decision variable indicating whether player $p$ is selected in the bench utility position in round $r$.

Let $b_r \in \mathbb{R}_{\ge 0}$ be a continuous decision variable representing the amount of cash in the bank in round $r$.

Let $\mathrm{in}_{p,r} \in \{0,1\}$ be a binary decision variable indicating whether player $p$ is traded into the team in round $r$.

Let $\mathrm{out}_{p,r} \in \{0,1\}$ be a binary decision variable indicating whether player $p$ is traded out of the team in round $r$.

Let $z_{p,r} \in \{0,1\}$ be a binary decision variable indicating whether player $p$ is selected as captain in round $r$.

Let $y_{p,r} \in \{0,1\}$ be a binary decision variable indicating whether player $p$'s score is counted towards the team total in round $r$.

\newpage

# Objective Function

Maximise the total points scored by the counted on-field players across all rounds, with the captain's counted score doubled:

$$
\text{Maximise} \quad \sum_{r \in R} \sum_{p \in P} s_{p,r} \cdot \left(y_{p,r} + z_{p,r}\right)
$$

\newpage

# Constraints

## Initial Bank Balance

Cash in the bank in round 1 is the salary cap minus the total price of the selected starting team:

$$
b_1 = \mathrm{SALARY\_CAP} - \sum_{p \in P} c_{p,1} \cdot x_{p,1}
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
x_{p,r} = \sum_{k \in K} x^{\mathrm{on}}_{p,k,r} + \sum_{k \in K} x^{\mathrm{bench}}_{p,k,r} + x^{Q,\mathrm{bench}}_{p,r} \quad \forall p in P, \forall r \in R
$$

A player can occupy at most one lineup slot in a given round:

$$
\sum_{k \in K} x^{\mathrm{on}}_{p,k,r} + \sum_{k \in K} x^{\mathrm{bench}}_{p,k,r} + x^{Q,\mathrm{bench}}_{p,r} \le 1 \quad \forall p \in P, \forall r \in R
$$

\newpage

## Maximum Team Changes Per Round

Between consecutive rounds, at most $T_r$ players may be traded into the team (and at most $T_r$ traded out) between rounds $r-1$ and $r$.

Using the trade indicators, this is enforced by limiting the number of trade-ins (equivalently trade-outs) each round:

$$
\sum_{p \in P} \mathrm{in}_{p,r} \le T_r \quad \forall r \in R \setminus \{1\}
$$

$$
\sum_{p \in P} \mathrm{out}_{p,r} \le T_r \quad \forall r \in R \setminus \{1\}
$$

\newpage

## Positional Structure

The team must have the following positional structure in every round.

On-field positions:

$$
\sum_{p \in P} x^{\mathrm{on}}_{p,k,r} = n^{\mathrm{on}}_{k} \quad \forall k \in K, \forall r \in R
$$

Bench positions:

$$
\sum_{p \in P} x^{\mathrm{bench}}_{p,k,r} = n^{\mathrm{bench}}_{k} \quad \forall k \in K, \forall r \in R
$$

Bench utility:

$$
\sum_{p \in P} x^{Q,\mathrm{bench}}_{p,r} = \mathrm{UTILITY\_BENCH\_COUNT} \quad \forall r \in R
$$

\newpage

## Position Eligibility

Players can only be selected into a position if they are eligible for that position (eligibility may be multi-position):

$$
x^{\mathrm{on}}_{p,k,r} \le e_{p,k,r} \quad \forall p \in P, \forall k \in K, \forall r \in R
$$

$$
x^{\mathrm{bench}}_{p,k,r} \le e_{p,k,r} \quad \forall p \in P, \forall k \in K, \forall r \in R
$$

\newpage

## Scoring Selection (Bye Rounds)

In each round, select which on-field players have their scores counted, up to $N_r$:

$$
\sum_{p \in P} y_{p,r} = N_r \quad \forall r \in R
$$

A player's score can only be counted if they are selected on-field in that round:

$$
y_{p,r} \le \sum_{k \in K} x^{\mathrm{on}}_{p,k,r} \quad \forall p \in P, \forall r \in R
$$

## Captaincy

Exactly one captain must be selected each round:

$$
\sum_{p \in P} z_{p,r} = 1 \quad \forall r \in R
$$

The captain must be one of the counted on-field players in that round:

$$
z_{p,r} \le y_{p,r} \quad \forall p \in P, \forall r \in R
$$
