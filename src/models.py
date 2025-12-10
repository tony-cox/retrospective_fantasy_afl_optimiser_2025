"""
Data models for AFL Fantasy Optimizer.
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Player:
    """Represents an AFL Fantasy player."""
    
    player_id: int
    first_name: str
    last_name: str
    team_id: int
    position: str
    price: int
    average_score: float
    games_played: int
    total_score: int
    
    @property
    def full_name(self) -> str:
        """Return the player's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @classmethod
    def from_json(cls, data: dict) -> 'Player':
        """Create a Player instance from JSON data."""
        return cls(
            player_id=data.get('id', 0),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            team_id=data.get('team_id', 0),
            position=data.get('position', ''),
            price=data.get('price', 0),
            average_score=data.get('average', 0.0),
            games_played=data.get('games_played', 0),
            total_score=data.get('total_points', 0)
        )


@dataclass
class Team:
    """Represents an AFL team."""
    
    team_id: int
    name: str
    abbreviation: str
    
    @classmethod
    def from_json(cls, data: dict) -> 'Team':
        """Create a Team instance from JSON data."""
        return cls(
            team_id=data.get('id', 0),
            name=data.get('name', ''),
            abbreviation=data.get('abbr', '')
        )



class Squad:
    """Represents a fantasy AFL squad with constraints."""
    
    # Fantasy AFL constraints
    MAX_SQUAD_SIZE: int = 30
    SALARY_CAP: int = 10_000_000  # $10M in dollars
    
    def __init__(self):
        """Initialize an empty squad."""
        self.players: List[Player] = []
        self.total_cost: int = 0
        self.total_score: float = 0.0
    
    def add_player(self, player: Player) -> bool:
        """
        Add a player to the squad if constraints are satisfied.
        
        Returns:
            True if player was added, False otherwise.
        """
        if len(self.players) >= self.MAX_SQUAD_SIZE:
            return False
        
        if self.total_cost + player.price > self.SALARY_CAP:
            return False
        
        self.players.append(player)
        self.total_cost += player.price
        self.total_score += player.average_score
        return True
    
    def is_valid(self) -> bool:
        """Check if the squad satisfies all constraints."""
        return (
            len(self.players) <= self.MAX_SQUAD_SIZE and
            self.total_cost <= self.SALARY_CAP
        )
    
    def __str__(self) -> str:
        """Return a string representation of the squad."""
        return (
            f"Squad: {len(self.players)} players, "
            f"Cost: ${self.total_cost:,}, "
            f"Total Score: {self.total_score:.2f}"
        )
