"""Transformations API routes"""

from fastapi import APIRouter
from .models import VariableTransformRequest
from .service import transform_variable_logic

router = APIRouter()


@router.post("/variable")
async def transform_variable(request: VariableTransformRequest):
    """
    Apply a series of transformations to a variable

    Transformations are applied in sequence.
    Supports: log, lag & lead, adstock, diminishing_returns_absolute,
              diminishing_returns_exponential, sma

    Returns:
        - transformed_data: List of transformed values
        - variable_name: Name of the variable
    """
    return transform_variable_logic(request)
