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

        # Prepare data for Prophet
        # Try to parse dates with dayfirst=True for DD/MM/YYYY format (British/European)
        df = pd.DataFrame({
            'ds': pd.to_datetime(request.dates, dayfirst=True, format='mixed'),
            'y': request.values
        })

        # Initialize and configure Prophet model
        model = Prophet(
            yearly_seasonality=request.yearly_seasonality,
            weekly_seasonality=request.weekly_seasonality,
            daily_seasonality=request.daily_seasonality,
        )

        # Fit the model
        model.fit(df)

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

    except Exception as e:
        print(f"Prophet forecast error: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
