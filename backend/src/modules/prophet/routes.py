"""Prophet API routes"""

from fastapi import APIRouter
from .models import ProphetRequest
from .service import generate_forecast

router = APIRouter()


@router.post("/forecast")
async def prophet_forecast(request: ProphetRequest):
    """
    Generate Prophet forecast with seasonality decomposition

    Returns:
        - forecast: future predictions with confidence intervals
        - components: trend, yearly, weekly seasonality
        - model_params: fitted model parameters
    """
    return generate_forecast(request)
