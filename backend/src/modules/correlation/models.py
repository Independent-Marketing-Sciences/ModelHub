"""Data models for Correlation module"""

from pydantic import BaseModel
from typing import Dict, List


class CorrelationRequest(BaseModel):
    """Request model for correlation analysis"""
    variables: Dict[str, List[float]]  # {name: values}


class CorrelationRankedRequest(BaseModel):
    """Request model for ranked correlation analysis with a target variable"""
    target_variable: str
    variables: Dict[str, List[float]]  # {name: values} - includes target
