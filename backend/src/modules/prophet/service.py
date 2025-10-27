"""Prophet forecasting service logic"""

import pandas as pd
import sys
import traceback
from fastapi import HTTPException

try:
    from prophet import Prophet
except ImportError:
    Prophet = None


def generate_forecast(request):
    """
    Generate Prophet forecast with seasonality decomposition

    Returns:
        - forecast: future predictions with confidence intervals
        - components: trend, yearly, weekly seasonality
        - model_params: fitted model parameters
    """
    try:
        if Prophet is None:
            raise HTTPException(
                status_code=500,
                detail="Prophet library not installed. Please install: pip install prophet"
            )

        # Validate input data
        if not request.dates or not request.values:
            raise HTTPException(
                status_code=400,
                detail="Both 'dates' and 'values' are required and cannot be empty"
            )

        if len(request.dates) != len(request.values):
            raise HTTPException(
                status_code=400,
                detail=f"Length mismatch: dates has {len(request.dates)} items but values has {len(request.values)} items"
            )

        # Check minimum data points
        MIN_DATA_POINTS = 2
        if len(request.dates) < MIN_DATA_POINTS:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data: Prophet requires at least {MIN_DATA_POINTS} data points, but only {len(request.dates)} provided. For meaningful forecasts, consider using at least 10 data points."
            )

        # Prepare data for Prophet
        # Try to parse dates with dayfirst=True for DD/MM/YYYY format (British/European)
        try:
            dates_parsed = pd.to_datetime(request.dates, dayfirst=True, format='mixed')
        except Exception as date_error:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {str(date_error)}. Supported formats include YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY"
            )

        df = pd.DataFrame({
            'ds': dates_parsed,
            'y': request.values
        })

        # Check for NaN or infinite values
        if df['y'].isna().any():
            raise HTTPException(
                status_code=400,
                detail="Values contain NaN (missing) values. Please ensure all data points are valid numbers."
            )

        if not pd.Series(df['y']).apply(lambda x: isinstance(x, (int, float)) and not pd.isna(x)).all():
            raise HTTPException(
                status_code=400,
                detail="Values must be numeric. Please check your data for non-numeric values."
            )

        # Initialize and configure Prophet model
        model = Prophet(
            yearly_seasonality=request.yearly_seasonality,
            weekly_seasonality=request.weekly_seasonality,
            daily_seasonality=request.daily_seasonality,
        )

        # Fit the model with better error handling
        try:
            model.fit(df)
        except Exception as fit_error:
            error_msg = str(fit_error)
            if "stan_backend" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="Prophet compatibility error (stan_backend). This usually indicates a version mismatch. Please upgrade Prophet: pip install --upgrade prophet"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Model fitting failed: {error_msg}"
                )

        # Create future dataframe
        future = model.make_future_dataframe(periods=request.periods)

        # Generate forecast
        forecast = model.predict(future)

        # Extract components
        components = model.predict(df)

        # Prepare response
        response = {
            "forecast": {
                "dates": forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
                "yhat": forecast['yhat'].tolist(),
                "yhat_lower": forecast['yhat_lower'].tolist(),
                "yhat_upper": forecast['yhat_upper'].tolist(),
            },
            "components": {
                "dates": components['ds'].dt.strftime('%Y-%m-%d').tolist(),
                "trend": components['trend'].tolist(),
            },
            "model_info": {
                "changepoint_prior_scale": model.changepoint_prior_scale,
                "seasonality_prior_scale": model.seasonality_prior_scale,
            }
        }

        # Add seasonality components if available
        if 'yearly' in components.columns:
            response["components"]["yearly"] = components['yearly'].tolist()
        if 'weekly' in components.columns:
            response["components"]["weekly"] = components['weekly'].tolist()

        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Prophet forecast error: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        # Provide more user-friendly error messages
        error_msg = str(e)
        if "datetime" in error_msg.lower() or "date" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Date parsing error: {error_msg}"
            )
        else:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {error_msg}")
