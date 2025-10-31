"""Modelling API routes"""

from fastapi import APIRouter, HTTPException
from .models import RegressionRequest, TransformDataRequest, VariableTransformation
from .service import run_modelling_regression, transform_single_variable

router = APIRouter()


@router.post("/regression")
async def run_regression(request: RegressionRequest):
    """
    Run econometric regression with variable transformations

    Supports:
    - Pre/post transformations (log, sqrt, exp)
    - Lag and lead operations
    - Adstock transformations
    - Diminishing returns
    - Combined adstock + diminishing returns

    Returns:
    - Regression coefficients, p-values, t-statistics
    - Model fit statistics (R², Adjusted R², F-statistic, AIC, BIC)
    - Durbin-Watson statistic
    - Residuals and fitted values
    - Transformed data
    - Variable contributions
    - Diagnostic tests (Jarque-Bera, Ljung-Box, Breusch-Pagan, White, VIF)
    """
    try:
        result = run_modelling_regression(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regression failed: {str(e)}")


@router.post("/transform-preview")
async def transform_preview(request: TransformDataRequest):
    """
    Preview transformation on a single variable without running regression

    Useful for:
    - Testing transformation parameters
    - Visualizing transformed data before regression
    - Debugging transformation issues

    Returns:
    - Transformed data array
    """
    try:
        transformed = transform_single_variable(
            request.variable_name,
            request.data,
            request.transformation
        )
        return {
            "variable": request.variable_name,
            "original": request.data,
            "transformed": transformed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transformation failed: {str(e)}")


@router.get("/transformation-types")
async def get_transformation_types():
    """
    Get available transformation types

    Returns lists of supported transformations
    """
    return {
        "pre_transforms": ["none", "log", "sqrt", "exp"],
        "post_transforms": ["none", "log", "sqrt", "exp"],
        "special_transforms": {
            "adstock": {
                "description": "Carry-over effect",
                "parameter": "ads_rate",
                "range": [0, 1]
            },
            "dimret": {
                "description": "Diminishing returns",
                "parameter": "dr_info",
                "range": [0, 1]
            },
            "dimret_adstock": {
                "description": "Combined adstock and diminishing returns",
                "parameters": ["ads_rate", "dr_info"],
                "range": [0, 1]
            }
        },
        "temporal": {
            "lag": "Shift values backward in time",
            "lead": "Shift values forward in time"
        }
    }
