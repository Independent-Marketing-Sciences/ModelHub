"""Data models for Prophet module"""

from pydantic import BaseModel
from typing import List


class ProphetRequest(BaseModel):
    """Request model for Prophet forecasting"""
    dates: List[str]  # ISO date strings
    values: List[float]
    periods: int = 365  # Days to forecast
    yearly_seasonality: bool = True
    weekly_seasonality: bool = True
    daily_seasonality: bool = False
