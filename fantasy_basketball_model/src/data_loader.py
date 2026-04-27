"""Load and preprocess NBA stats data."""

import pandas as pd
import numpy as np
from pathlib import Path


class NBADataLoader:
    """Load historical NBA stats from 2017-2024."""
    
    STATS = [
        'PTS', 'REB', 'AST', 'STL', 'BLK',
        'FG%', 'FT%', '3P%', 'TOV', 'ORB',
        'DRB', 'PF', 'FGA'
    ]
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self.raw_data = None
        self.processed_data = None
    
    def load_raw_stats(self, filepath: str) -> pd.DataFrame:
        """Load raw NBA stats CSV."""
        df = pd.read_csv(self.data_dir / filepath)
        self.raw_data = df
        return df
    
    def preprocess(self) -> pd.DataFrame:
        """Clean and prepare data for model."""
        df = self.raw_data.copy()
        
        # Handle missing values
        df = df.fillna(df.mean(numeric_only=True))
        
        # Normalize stats to 0-1 range
        for stat in self.STATS:
            if stat in df.columns:
                df[f'{stat}_norm'] = (df[stat] - df[stat].min()) / (df[stat].max() - df[stat].min())
        
        self.processed_data = df
        return df
    
    def get_player_history(self, player_name: str, games: int = 7) -> pd.DataFrame:
        """Get last N games for a player."""
        return self.processed_data[self.processed_data['Player'] == player_name].tail(games)