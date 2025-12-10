"""
Integer Programming optimizer for AFL Fantasy squad selection.
"""

import pulp
from typing import List, Dict, Optional, Any
from .models import Player, Squad


class FantasyOptimizer:
    """Optimizes fantasy AFL squad selection using Integer Programming."""
    
    # Position constraints for a typical fantasy AFL squad
    POSITION_CONSTRAINTS = {
        'DEF': {'min': 6, 'max': 8},
        'MID': {'min': 8, 'max': 10},
        'RUC': {'min': 2, 'max': 3},
        'FWD': {'min': 6, 'max': 8}
    }
    
    def __init__(
        self,
        players: List[Player],
        salary_cap: int = 10_000_000,
        squad_size: int = 30
    ):
        """
        Initialize the optimizer.
        
        Args:
            players: List of available players.
            salary_cap: Maximum total cost in dollars (default $10M).
            squad_size: Target squad size (default 30).
        """
        self.players = players
        self.salary_cap = salary_cap
        self.squad_size = squad_size
        self.model: Optional[pulp.LpProblem] = None
        self.selection_vars: Dict[int, pulp.LpVariable] = {}
        self.selected_squad: Optional[Squad] = None
    
    def build_model(self, objective: str = 'max_score') -> pulp.LpProblem:
        """
        Build the Integer Programming model.
        
        Args:
            objective: Optimization objective ('max_score' or 'min_cost').
        
        Returns:
            PuLP LP problem instance.
        """
        # Create the LP problem
        self.model = pulp.LpProblem(
            "AFL_Fantasy_Optimizer",
            pulp.LpMaximize if objective == 'max_score' else pulp.LpMinimize
        )
        
        # Create binary decision variables for each player
        self.selection_vars = {}
        for player in self.players:
            var_name = f"player_{player.player_id}"
            self.selection_vars[player.player_id] = pulp.LpVariable(
                var_name,
                cat=pulp.LpBinary
            )
        
        # Objective function: maximize total score or minimize cost
        if objective == 'max_score':
            self.model += pulp.lpSum([
                player.average_score * self.selection_vars[player.player_id]
                for player in self.players
            ]), "Total_Score"
        else:
            self.model += pulp.lpSum([
                player.price * self.selection_vars[player.player_id]
                for player in self.players
            ]), "Total_Cost"
        
        # Constraint 1: Squad size
        self.model += pulp.lpSum([
            self.selection_vars[player.player_id]
            for player in self.players
        ]) == self.squad_size, "Squad_Size"
        
        # Constraint 2: Salary cap
        self.model += pulp.lpSum([
            player.price * self.selection_vars[player.player_id]
            for player in self.players
        ]) <= self.salary_cap, "Salary_Cap"
        
        # Constraint 3: Position requirements
        for position, constraints in self.POSITION_CONSTRAINTS.items():
            players_in_position = [
                p for p in self.players if p.position == position
            ]
            
            # Minimum players in position
            self.model += pulp.lpSum([
                self.selection_vars[p.player_id]
                for p in players_in_position
            ]) >= constraints['min'], f"Min_{position}"
            
            # Maximum players in position
            self.model += pulp.lpSum([
                self.selection_vars[p.player_id]
                for p in players_in_position
            ]) <= constraints['max'], f"Max_{position}"
        
        return self.model
    
    def solve(
        self,
        solver: Optional[pulp.LpSolver] = None,
        verbose: bool = True
    ) -> bool:
        """
        Solve the optimization model.
        
        Args:
            solver: PuLP solver to use (default: CBC).
            verbose: Whether to print solver output.
        
        Returns:
            True if optimal solution found, False otherwise.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        # Use default CBC solver if none provided
        if solver is None:
            solver = pulp.PULP_CBC_CMD(msg=verbose)
        
        # Solve the model
        status = self.model.solve(solver)
        
        return status == pulp.LpStatusOptimal
    
    def get_selected_squad(self) -> Squad:
        """
        Extract the selected squad from the solved model.
        
        Returns:
            Squad object with selected players.
        
        Raises:
            ValueError: If model hasn't been solved yet.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        if self.model.status != pulp.LpStatusOptimal:
            raise ValueError("Model not solved to optimality.")
        
        # Create squad and add selected players
        squad = Squad()
        
        for player in self.players:
            var = self.selection_vars[player.player_id]
            if pulp.value(var) == 1:
                # Directly add to squad, bypassing validation
                # since optimizer solution is already validated
                squad.players.append(player)
                squad.total_cost += player.price
                squad.total_score += player.average_score
        
        self.selected_squad = squad
        return squad
    
    def get_solution_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the optimization solution.
        
        Returns:
            Dictionary with solution details.
        """
        if self.model is None or self.selected_squad is None:
            return {}
        
        # Count players by position
        position_counts = {}
        for player in self.selected_squad.players:
            position_counts[player.position] = position_counts.get(player.position, 0) + 1
        
        return {
            'status': pulp.LpStatus[self.model.status],
            'objective_value': pulp.value(self.model.objective),
            'total_players': len(self.selected_squad.players),
            'total_cost': self.selected_squad.total_cost,
            'total_score': self.selected_squad.total_score,
            'position_breakdown': position_counts,
            'salary_cap_remaining': self.salary_cap - self.selected_squad.total_cost
        }
