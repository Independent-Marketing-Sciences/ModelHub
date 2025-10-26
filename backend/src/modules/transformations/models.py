"""Data models for Transformations module"""

from pydantic import BaseModel
from typing import List


class TransformationStep(BaseModel):
    """Single transformation step"""
    type: str  # log, lag & lead, adstock, diminishing_returns_absolute, diminishing_returns_exponential, sma
    amount: float


class VariableTransformRequest(BaseModel):
    """Request model for transforming a variable with multiple steps"""
    variable_name: str
    data: List[float]
    transformations: List[TransformationStep]
