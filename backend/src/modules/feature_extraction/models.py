"""Data models for feature extraction module"""

from pydantic import BaseModel
from typing import Dict, List


class FeatureExtractionRequest(BaseModel):
    """Request model for feature extraction"""
    data: Dict[str, List[float]]  # {column_name: values}
    kpi_var: str  # Target variable name
    date_column: str = "OBS"  # Date/index column name
    n_features: int = 10  # Number of top features to extract
    test_size: float = 0.1  # Test split size
    random_state: int = 42
    shuffle: bool = False
