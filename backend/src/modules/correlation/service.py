"""Correlation analysis service logic"""

import pandas as pd
import numpy as np
import sys
import traceback
from fastapi import HTTPException
from scipy import stats


def correlation_matrix_logic(request):
    """
    Calculate correlation matrix with additional statistics

    Returns:
        - pearson: Pearson correlation coefficients
        - spearman: Spearman rank correlation
        - p_values: Statistical significance
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.variables)

        # Remove NaN values
        df = df.dropna()

        if len(df) < 2:
            raise HTTPException(status_code=400, detail="Insufficient valid data points")

        # Calculate correlations
        pearson = df.corr(method='pearson')
        spearman = df.corr(method='spearman')

        # Calculate p-values
        n = len(df)
        p_values = {}
        for col1 in df.columns:
            p_values[col1] = {}
            for col2 in df.columns:
                if col1 == col2:
                    p_values[col1][col2] = 0.0
                else:
                    r = pearson.loc[col1, col2]
                    # T-statistic for correlation
                    t_stat = r * np.sqrt(n - 2) / np.sqrt(1 - r**2)
                    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
                    p_values[col1][col2] = float(p_val)

        return {
            "pearson": pearson.to_dict(),
            "spearman": spearman.to_dict(),
            "p_values": p_values,
            "n_samples": int(n),
            "variables": list(df.columns)
        }

    except Exception as e:
        print(f"Correlation matrix error: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def correlation_ranked_logic(request):
    """
    Calculate correlations between a target variable and all other variables,
    returning results ranked by correlation strength.

    Returns:
        - correlations: List of correlations ranked by absolute value
        - Each item contains: variable, correlation, p_value, strength
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.variables)

        # Remove rows with NaN values
        df = df.dropna()

        if len(df) < 2:
            raise HTTPException(status_code=400, detail="Insufficient valid data points")

        # Check if target variable exists
        if request.target_variable not in df.columns:
            raise HTTPException(status_code=400, detail=f"Target variable '{request.target_variable}' not found")

        # Get target variable
        target = df[request.target_variable]

        # Calculate correlations with all other variables
        correlations = []
        n = len(df)

        for col in df.columns:
            if col != request.target_variable:
                # Calculate Pearson correlation
                r = df[col].corr(target)

                # Skip if correlation is NaN (happens with zero variance)
                if pd.isna(r) or np.isnan(r):
                    continue

                # Calculate p-value
                if abs(r) < 1.0:  # Avoid division by zero
                    try:
                        t_stat = r * np.sqrt(n - 2) / np.sqrt(1 - r**2)
                        if np.isnan(t_stat) or np.isinf(t_stat):
                            p_val = 1.0
                        else:
                            p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
                    except:
                        p_val = 1.0
                else:
                    p_val = 0.0

                # Determine strength
                abs_r = abs(r)
                if abs_r >= 0.7:
                    strength = "Strong"
                elif abs_r >= 0.4:
                    strength = "Moderate"
                elif abs_r >= 0.2:
                    strength = "Weak"
                else:
                    strength = "Very Weak"

                correlations.append({
                    "variable": col,
                    "correlation": float(r) if not np.isnan(r) else 0.0,
                    "p_value": float(p_val) if not np.isnan(p_val) else 1.0,
                    "strength": strength,
                    "abs_correlation": abs_r
                })

        # Sort by absolute correlation (highest to lowest)
        correlations.sort(key=lambda x: x['abs_correlation'], reverse=True)

        # Remove abs_correlation from output (it was just for sorting)
        for item in correlations:
            del item['abs_correlation']

        return {
            "target_variable": request.target_variable,
            "correlations": correlations,
            "n_samples": int(n)
        }

    except Exception as e:
        print(f"Ranked correlation error: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
