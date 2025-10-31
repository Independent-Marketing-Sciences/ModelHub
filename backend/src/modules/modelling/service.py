"""Modelling service layer - regression and diagnostics"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, het_white, acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy.optimize import minimize
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional
from .models import RegressionRequest, RegressionResult, ModelDiagnostics, VariableTransformation
from .transformations import apply_variable_transformation


def sanitize_float(value: float, default: float = 0.0) -> float:
    """Convert NaN/Inf values to valid floats for JSON serialization"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(np.nan_to_num(value, nan=default, posinf=default, neginf=default))
    return default


def sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize all float values in a dictionary"""
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = [sanitize_float(v) if isinstance(v, (int, float)) else v for v in value]
        elif isinstance(value, (int, float)):
            result[key] = sanitize_float(value)
        else:
            result[key] = value
    return result


def transform_data(
    data: Dict[str, List[Any]],
    variable_transformations: List[VariableTransformation],
    start_date: str,
    end_date: str,
    kpi: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform the dataset based on variable configurations

    Returns:
        - original_df: Original data filtered by date range
        - transformed_df: Transformed data ready for regression
    """
    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Filter by date range (assuming 'obs' or 'date' column exists)
    date_col = None
    for col in ['obs', 'OBS', 'date', 'Date']:
        if col in df.columns:
            date_col = col
            break

    if date_col:
        # Handle multiple date formats - try common formats
        df[date_col] = pd.to_datetime(df[date_col], format='mixed', dayfirst=True)
        start = pd.to_datetime(start_date, format='mixed', dayfirst=True)
        end = pd.to_datetime(end_date, format='mixed', dayfirst=True)
        df = df[(df[date_col] >= start) & (df[date_col] <= end)]

    original_df = df.copy()

    # Create transformed DataFrame
    transformed_data = {}

    # Always include KPI in transformed data (without transformations unless specified)
    if kpi in df.columns:
        kpi_transformed = False
        # Check if KPI has transformations specified
        for var_config in variable_transformations:
            if var_config.variable == kpi and var_config.include:
                series = df[kpi].values
                transformed_series = apply_variable_transformation(
                    series,
                    pre_transform=var_config.pre_transform,
                    lag=var_config.lag,
                    lead=var_config.lead,
                    adstock=var_config.adstock,
                    dimret=var_config.dimret,
                    dimret_adstock=var_config.dimret_adstock,
                    post_transform=var_config.post_transform
                )
                transformed_data[kpi] = transformed_series
                kpi_transformed = True
                break

        # If KPI not in transformations, include it as-is
        if not kpi_transformed:
            transformed_data[kpi] = df[kpi].values

    # Transform other variables
    for var_config in variable_transformations:
        if not var_config.include:
            continue

        var_name = var_config.variable

        # Skip KPI if already processed
        if var_name == kpi:
            continue

        if var_name not in df.columns:
            continue

        # Get the data
        series = df[var_name].values

        try:
            # Apply transformations
            transformed_series = apply_variable_transformation(
                series,
                pre_transform=var_config.pre_transform,
                lag=var_config.lag,
                lead=var_config.lead,
                adstock=var_config.adstock,
                dimret=var_config.dimret,
                dimret_adstock=var_config.dimret_adstock,
                post_transform=var_config.post_transform
            )
            transformed_data[var_name] = transformed_series
        except Exception as e:
            raise ValueError(f"Error transforming variable '{var_name}': {str(e)}")

    transformed_df = pd.DataFrame(transformed_data)

    # Add date column if it exists
    if date_col and date_col in df.columns:
        transformed_df[date_col] = df[date_col].values

    return original_df, transformed_df


def run_regression_with_bounds(
    y: np.ndarray,
    X: pd.DataFrame,
    bounds: Optional[List[Tuple[Optional[float], Optional[float]]]] = None,
    add_constant: bool = True
) -> Tuple[Dict[str, Any], Dict[str, List[float]]]:
    """
    Run OLS regression with optional coefficient bounds using scipy.optimize.minimize

    This matches the PySide6 implementation which uses constrained optimization
    to ensure coefficients stay within specified min/max bounds.

    Returns:
        - model_results: Dictionary with coefficients, statistics, and fit metrics
        - contributions: Variable contributions (coefficient * value) for each observation
    """
    # Prepare data
    if add_constant:
        X_array = sm.add_constant(X).values
        var_names = ['const'] + list(X.columns)
    else:
        X_array = X.values
        var_names = list(X.columns)

    y_array = np.asarray(y, dtype=np.float64)

    # Filter out invalid rows (only NaN/inf, keep zeros)
    valid_rows = np.isfinite(y_array) & ~np.isnan(y_array)
    for i in range(X_array.shape[1]):
        valid_rows &= np.isfinite(X_array[:, i]) & ~np.isnan(X_array[:, i])

    y_valid = y_array[valid_rows]
    X_valid = X_array[valid_rows]

    # Define RSS (Residual Sum of Squares) function to minimize
    def rss(params, X, y):
        predictions = X @ params
        residuals = y - predictions
        return np.sum(residuals**2)

    # Initial guess using least squares
    try:
        initial_guess = np.linalg.lstsq(X_valid, y_valid, rcond=None)[0]
    except:
        initial_guess = np.zeros(X_valid.shape[1])

    # Run optimization with bounds
    if bounds:
        result = minimize(
            rss,
            x0=initial_guess,
            args=(X_valid, y_valid),
            bounds=bounds,
            method='L-BFGS-B'
        )
    else:
        result = minimize(
            rss,
            x0=initial_guess,
            args=(X_valid, y_valid),
            method='L-BFGS-B'
        )

    # Extract coefficients
    coefficients = result.x

    # Calculate predicted values and residuals
    predictions = X_valid @ coefficients
    residuals = y_valid - predictions

    # Calculate R-squared
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_valid - np.mean(y_valid))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    # Calculate adjusted R-squared
    n = len(y_valid)
    p = len(coefficients)
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1) if (n - p - 1) > 0 else 0

    # Calculate standard errors
    mse = ss_res / (n - p) if (n - p) > 0 else 0
    try:
        var_coef = mse * np.linalg.inv(X_valid.T @ X_valid)
        std_errors = np.sqrt(np.diag(var_coef))
    except:
        std_errors = np.zeros(len(coefficients))

    # Calculate t-statistics and p-values (handle zeros in std_errors)
    with np.errstate(divide='ignore', invalid='ignore'):
        t_stats = coefficients / std_errors
        t_stats = np.nan_to_num(t_stats, nan=0.0, posinf=0.0, neginf=0.0)

    if (n - p) > 0:
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - p))
        p_values = np.nan_to_num(p_values, nan=1.0, posinf=1.0, neginf=1.0)
    else:
        p_values = np.ones(len(coefficients))

    # Calculate F-statistic (handle perfect fit case)
    ss_reg = ss_tot - ss_res
    if (n - p) > 0 and (p - 1) > 0 and ss_res > 1e-10:
        f_statistic = (ss_reg / (p - 1)) / (ss_res / (n - p))
        f_pvalue = 1 - stats.f.cdf(f_statistic, p - 1, n - p)
    else:
        # Perfect fit or insufficient data
        f_statistic = 0.0
        f_pvalue = 1.0

    # Calculate AIC and BIC (handle perfect fit case)
    if ss_res > 1e-10:
        log_likelihood = -0.5 * n * (np.log(2 * np.pi) + 1 + np.log(ss_res / n))
    else:
        # Perfect fit - use a reasonable value
        log_likelihood = n * 10  # High likelihood for perfect fit

    aic = 2 * p - 2 * log_likelihood
    bic = p * np.log(n) - 2 * log_likelihood

    # Ensure no inf/nan values
    f_statistic = float(np.nan_to_num(f_statistic, nan=0.0, posinf=0.0, neginf=0.0))
    f_pvalue = float(np.nan_to_num(f_pvalue, nan=1.0, posinf=1.0, neginf=1.0))
    aic = float(np.nan_to_num(aic, nan=0.0, posinf=0.0, neginf=0.0))
    bic = float(np.nan_to_num(bic, nan=0.0, posinf=0.0, neginf=0.0))

    # Create model results dictionary
    model_results = {
        'coefficients': {name: float(coef) for name, coef in zip(var_names, coefficients)},
        'std_errors': {name: float(se) for name, se in zip(var_names, std_errors)},
        't_stats': {name: float(t) for name, t in zip(var_names, t_stats)},
        'p_values': {name: float(p) for name, p in zip(var_names, p_values)},
        'r_squared': float(r_squared),
        'adj_r_squared': float(adj_r_squared),
        'f_statistic': float(f_statistic),
        'f_pvalue': float(f_pvalue),
        'aic': float(aic),
        'bic': float(bic),
        'n_obs': int(n),
        'df_resid': int(n - p),
        'residuals': residuals,
        'fitted_values': predictions,
        'optimization_success': result.success
    }

    # Calculate contributions (full array including invalid rows)
    contributions = {}
    full_predictions = X_array @ coefficients
    for i, col in enumerate(var_names):
        if col == 'const':
            contributions[col] = [float(coefficients[i])] * len(y_array)
        else:
            col_idx = i - 1 if add_constant else i
            contributions[col] = (X.iloc[:, col_idx].values * coefficients[i]).tolist()

    return model_results, contributions


def calculate_diagnostics(residuals: np.ndarray, X_array: np.ndarray, X_names: List[str]) -> Dict[str, Any]:
    """Calculate regression diagnostic statistics from residuals and design matrix"""

    diagnostics = {}

    # Jarque-Bera test for normality
    try:
        jb_stat, jb_pvalue, _, _ = jarque_bera(residuals)
        diagnostics['jarque_bera_stat'] = float(jb_stat)
        diagnostics['jarque_bera_pvalue'] = float(jb_pvalue)
    except:
        diagnostics['jarque_bera_stat'] = 0.0
        diagnostics['jarque_bera_pvalue'] = 1.0

    # Ljung-Box test for autocorrelation
    try:
        lb_test = acorr_ljungbox(residuals, lags=[min(10, len(residuals)//2)], return_df=False)
        diagnostics['ljung_box_stat'] = float(lb_test[0][0]) if len(lb_test[0]) > 0 else 0.0
        diagnostics['ljung_box_pvalue'] = float(lb_test[1][0]) if len(lb_test[1]) > 0 else 1.0
    except:
        diagnostics['ljung_box_stat'] = 0.0
        diagnostics['ljung_box_pvalue'] = 1.0

    # Breusch-Pagan test for heteroskedasticity
    try:
        bp_test = het_breuschpagan(residuals, X_array)
        diagnostics['breusch_pagan_stat'] = float(bp_test[0])
        diagnostics['breusch_pagan_pvalue'] = float(bp_test[1])
    except:
        diagnostics['breusch_pagan_stat'] = 0.0
        diagnostics['breusch_pagan_pvalue'] = 1.0

    # White test for heteroskedasticity
    try:
        white_test = het_white(residuals, X_array)
        diagnostics['white_test_stat'] = float(white_test[0])
        diagnostics['white_test_pvalue'] = float(white_test[1])
    except:
        diagnostics['white_test_stat'] = 0.0
        diagnostics['white_test_pvalue'] = 1.0

    # Condition number
    try:
        diagnostics['condition_number'] = float(np.linalg.cond(X_array))
    except:
        diagnostics['condition_number'] = 0.0

    # VIF (Variance Inflation Factor)
    vif_values = {}
    try:
        # Skip constant column (first column if present)
        start_idx = 1 if 'const' in X_names else 0
        for i, col in enumerate(X_names[start_idx:], start=start_idx):
            vif = variance_inflation_factor(X_array, i)
            vif_values[col] = sanitize_float(vif)
    except Exception as e:
        print(f"VIF calculation error: {e}")
        pass

    diagnostics['vif_values'] = vif_values

    # Sanitize all diagnostic values
    return sanitize_dict(diagnostics)


def run_modelling_regression(request: RegressionRequest) -> Dict[str, Any]:
    """
    Main function to run regression with transformations

    This implementation matches the successful PySide6 approach:
    - Uses scipy.optimize.minimize with L-BFGS-B for constrained optimization
    - Supports coefficient bounds (min/max constraints)
    - Handles variable transformations in the correct order

    Returns comprehensive results including:
    - Regression coefficients and statistics
    - Transformed data
    - Variable contributions
    - Diagnostic tests
    """

    # Get target variable (KPI)
    kpi = request.model_configuration.kpi

    # Transform the data
    original_df, transformed_df = transform_data(
        request.data,
        request.variable_transformations,
        request.model_configuration.start_date,
        request.model_configuration.end_date,
        kpi
    )

    if kpi not in transformed_df.columns:
        raise ValueError(f"KPI '{kpi}' not found in transformed data")

    y = transformed_df[kpi].values

    # Get independent variables (exclude KPI and date columns)
    exclude_cols = [kpi]
    for col in ['obs', 'OBS', 'date', 'Date']:
        if col in transformed_df.columns:
            exclude_cols.append(col)

    X = transformed_df.drop(columns=exclude_cols, errors='ignore')

    # Remove any columns with all zeros or NaN
    X = X.loc[:, (X != 0).any(axis=0)]
    X = X.dropna(axis=1, how='all')

    # Build coefficient bounds from variable transformations
    # Match the PySide6 implementation: bounds for each variable (excluding constant)
    bounds = []
    var_transform_dict = {vt.variable: vt for vt in request.variable_transformations if vt.include}

    # Constant gets no bounds (add None, None)
    bounds.append((None, None))

    # Add bounds for each variable
    for col in X.columns:
        if col in var_transform_dict:
            vt = var_transform_dict[col]
            # Note: Coefficient bounds are not in the current VariableTransformation model
            # For now, use unconstrained
            bounds.append((None, None))
        else:
            bounds.append((None, None))

    # Run regression with bounds
    model_results, contributions = run_regression_with_bounds(y, X, bounds=bounds, add_constant=True)

    # Prepare X array for diagnostics
    X_array = sm.add_constant(X).values
    var_names = ['const'] + list(X.columns)

    # Calculate diagnostics
    diagnostics = calculate_diagnostics(
        model_results['residuals'],
        X_array,
        var_names
    )

    # Calculate Durbin-Watson
    dw_stat = sanitize_float(durbin_watson(model_results['residuals']))

    # Prepare final results
    result = {
        'coefficients': model_results['coefficients'],
        'p_values': model_results['p_values'],
        't_stats': model_results['t_stats'],
        'r_squared': model_results['r_squared'],
        'adjusted_r_squared': model_results['adj_r_squared'],
        'f_statistic': model_results['f_statistic'],
        'f_pvalue': model_results['f_pvalue'],
        'aic': model_results['aic'],
        'bic': model_results['bic'],
        'durbin_watson': dw_stat,
        'residuals': model_results['residuals'].tolist(),
        'fitted_values': model_results['fitted_values'].tolist(),
        'transformed_data': {col: transformed_df[col].tolist() for col in transformed_df.columns},
        'variable_contributions': contributions,
        'diagnostics': diagnostics,
        'n_observations': model_results['n_obs'],
        'degrees_of_freedom': model_results['df_resid'],
        'optimization_success': model_results['optimization_success']
    }

    # Sanitize all values to ensure JSON compatibility
    return sanitize_dict(result)


def transform_single_variable(
    variable_name: str,
    data: List[float],
    transformation: VariableTransformation
) -> List[float]:
    """
    Transform a single variable (for preview purposes)
    """
    series = np.array(data, dtype=float)

    transformed = apply_variable_transformation(
        series,
        pre_transform=transformation.pre_transform,
        lag=transformation.lag,
        lead=transformation.lead,
        adstock=transformation.adstock,
        dimret=transformation.dimret,
        dimret_adstock=transformation.dimret_adstock,
        post_transform=transformation.post_transform
    )

    return transformed.tolist()
