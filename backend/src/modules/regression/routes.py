"""Regression API routes"""

from fastapi import APIRouter
from .models import StepwiseRequest
from .service import stepwise_regression_logic

router = APIRouter()


@router.post("/stepwise")
async def stepwise_regression(request: StepwiseRequest):
    """
    Perform stepwise regression variable selection

    Methods:
        - forward: Start with no variables, add best at each step
        - backward: Start with all variables, remove worst at each step
        - both: Combination of forward and backward

    Returns:
        - selected_variables: List of selected variable names
        - coefficients: Regression coefficients
        - r_squared: Model R² value
        - adjusted_r_squared: Adjusted R²
        - p_values: P-values for each variable
        - steps: Selection process details
    """
    return stepwise_regression_logic(request)
