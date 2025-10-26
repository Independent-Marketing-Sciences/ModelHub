"""Correlation API routes"""

from fastapi import APIRouter
from .models import CorrelationRequest, CorrelationRankedRequest
from .service import correlation_matrix_logic, correlation_ranked_logic

router = APIRouter()


@router.post("/matrix")
async def correlation_matrix(request: CorrelationRequest):
    """
    Calculate correlation matrix with additional statistics

    Returns:
        - pearson: Pearson correlation coefficients
        - spearman: Spearman rank correlation
        - p_values: Statistical significance
    """
    return correlation_matrix_logic(request)


@router.post("/ranked")
async def correlation_ranked(request: CorrelationRankedRequest):
    """
    Calculate correlations between a target variable and all other variables,
    returning results ranked by correlation strength.

    Returns:
        - correlations: List of correlations ranked by absolute value
        - Each item contains: variable, correlation, p_value, strength
    """
    return correlation_ranked_logic(request)
