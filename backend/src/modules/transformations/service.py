"""Variable transformation service logic"""

import pandas as pd
import numpy as np
import sys
import traceback
from fastapi import HTTPException


def transform_variable_logic(request):
    """
    Apply a series of transformations to a variable

    Transformations are applied in sequence.
    Supports: log, lag & lead, adstock, diminishing_returns_absolute,
              diminishing_returns_exponential, sma

    Returns:
        - transformed_data: List of transformed values
        - variable_name: Name of the variable
    """
    try:
        # Convert to pandas Series for easier manipulation
        transformed_variable = pd.Series(request.data)

        for step in request.transformations:
            transformation_type = step.type
            amount = step.amount

            # Skip if amount is 0
            if amount == 0:
                continue

            if transformation_type == 'log':
                # Log transformation: log(x + amount)
                transformed_variable = np.log(transformed_variable + amount)

            elif transformation_type == 'lag & lead':
                # Lag & Lead: shift by amount periods
                transformed_variable = transformed_variable.shift(periods=int(amount))

            elif transformation_type == 'adstock':
                # Adstock transformation (cumulative decay)
                adstocked_var = transformed_variable.copy()
                for i in range(1, len(adstocked_var)):
                    adstocked_var.iloc[i] = adstocked_var.iloc[i] + amount * adstocked_var.iloc[i-1]
                transformed_variable = adstocked_var

            elif transformation_type == 'diminishing_returns_absolute':
                # Diminishing Returns Absolute: x / (x + |amount|)
                transformed_variable = transformed_variable.apply(lambda x: x / (x + abs(amount)))

            elif transformation_type == 'diminishing_returns_exponential':
                # Diminishing Returns Exponential: 1 - exp(-k * x)
                dr_x = transformed_variable.copy()
                if np.sum(dr_x) != 0:
                    mean_positive = np.mean(dr_x[dr_x > 0])
                    if mean_positive > 0:
                        k = -np.log(1 - amount) / mean_positive
                        dr_x = 1 - np.exp(-k * dr_x)
                transformed_variable = dr_x

            elif transformation_type == 'sma':
                # Simple Moving Average
                transformed_variable = transformed_variable.rolling(window=int(amount)).mean()

        # Convert back to list, handling NaN values
        result = transformed_variable.tolist()

        # Replace NaN with None for JSON compatibility
        result = [None if pd.isna(v) else float(v) for v in result]

        return {
            "variable_name": request.variable_name,
            "transformed_data": result,
            "n_transformations": len(request.transformations)
        }

    except Exception as e:
        print(f"Transformation error: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
