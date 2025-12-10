"""
AFL Fantasy Optimizer package.
"""

from .models import Player, Team, Squad
from .data_loader import DataLoader
from .optimizer import FantasyOptimizer

__all__ = ['Player', 'Team', 'Squad', 'DataLoader', 'FantasyOptimizer']
