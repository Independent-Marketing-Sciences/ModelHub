"""Data models for Regression module"""

from pydantic import BaseModel
from typing import Dict, List


class StepwiseRequest(BaseModel):
    """Request model for stepwise regression"""
    y: List[float]  # Dependent variable
    X: Dict[str, List[float]]  # Independent variables {name: values}
    method: str = "forward"  # forward, backward, or both
    significance_level: float = 0.05
