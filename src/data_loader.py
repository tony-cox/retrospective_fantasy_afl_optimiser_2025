"""
Data loader module for fetching and parsing AFL Fantasy data.
"""

import json
import requests
from typing import List, Dict, Optional
from .models import Player, Team


class DataLoader:
    """Loads and parses AFL Fantasy data from the API."""
    
    DEFAULT_URL = "https://fantasy.afl.com.au/data/afl/players.json"
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize the data loader.
        
        Args:
            url: URL to fetch player data from. Defaults to AFL Fantasy API.
        """
        self.url = url or self.DEFAULT_URL
        self.raw_data: Optional[Dict] = None
        self.players: List[Player] = []
        self.teams: Dict[int, Team] = {}
    
    def fetch_data(self) -> Dict:
        """
        Fetch data from the URL.
        
        Returns:
            Raw JSON data as a dictionary.
        
        Raises:
            requests.RequestException: If the request fails.
        """
        response = requests.get(self.url, timeout=30)
        response.raise_for_status()
        self.raw_data = response.json()
        return self.raw_data
    
    def load_from_file(self, filepath: str) -> Dict:
        """
        Load data from a local JSON file.
        
        Args:
            filepath: Path to the JSON file.
        
        Returns:
            Raw JSON data as a dictionary.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        return self.raw_data
    
    def parse_players(self) -> List[Player]:
        """
        Parse player data from the raw JSON.
        
        Returns:
            List of Player objects.
        """
        if not self.raw_data:
            raise ValueError("No data loaded. Call fetch_data() or load_from_file() first.")
        
        self.players = []
        
        # Handle different possible JSON structures
        player_data = self.raw_data
        if isinstance(self.raw_data, dict):
            # Check for common keys that might contain player list
            for key in ['players', 'data', 'player_list']:
                if key in self.raw_data:
                    player_data = self.raw_data[key]
                    break
        
        if isinstance(player_data, list):
            for player_dict in player_data:
                try:
                    player = Player.from_json(player_dict)
                    self.players.append(player)
                except Exception as e:
                    print(f"Warning: Failed to parse player: {e}")
                    continue
        
        return self.players
    
    def parse_teams(self) -> Dict[int, Team]:
        """
        Parse team data from the raw JSON.
        
        Returns:
            Dictionary mapping team_id to Team objects.
        """
        if not self.raw_data:
            raise ValueError("No data loaded. Call fetch_data() or load_from_file() first.")
        
        self.teams = {}
        
        # Look for teams in the data
        team_data = None
        if isinstance(self.raw_data, dict):
            for key in ['teams', 'team_list']:
                if key in self.raw_data:
                    team_data = self.raw_data[key]
                    break
        
        if team_data and isinstance(team_data, list):
            for team_dict in team_data:
                try:
                    team = Team.from_json(team_dict)
                    self.teams[team.team_id] = team
                except Exception as e:
                    print(f"Warning: Failed to parse team: {e}")
                    continue
        
        return self.teams
    
    def load_all(self) -> tuple[List[Player], Dict[int, Team]]:
        """
        Fetch and parse all data (players and teams).
        
        Returns:
            Tuple of (players list, teams dictionary).
        """
        self.fetch_data()
        players = self.parse_players()
        teams = self.parse_teams()
        return players, teams
