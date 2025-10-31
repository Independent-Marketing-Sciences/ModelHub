"""Modelling service layer - regression and diagnostics"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, het_white, acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import Dict, List, Tuple, Any
from .models import RegressionRequest, RegressionResult, ModelDiagnostics, VariableTransformation
from .transformations import apply_variable_transformation


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


def run_regression(
    y: np.ndarray,
    X: pd.DataFrame,
    add_constant: bool = True
) -> Tuple[sm.regression.linear_model.RegressionResultsWrapper, Dict[str, List[float]]]:
    """
    Run OLS regression

    Returns:
        - model: statsmodels regression results
        - contributions: Variable contributions (coefficient * value) for each observation
    """
    # Add constant if requested
    if add_constant:
        X_with_const = sm.add_constant(X)
    else:
        X_with_const = X

    # Fit the model
    model = sm.OLS(y, X_with_const).fit()

    # Calculate contributions
    contributions = {}
    for i, col in enumerate(X.columns):
        coef = model.params[col]
        contributions[col] = (X[col].values * coef).tolist()

    # Add constant contribution if present
    if add_constant and 'const' in model.params:
        const_value = model.params['const']
        contributions['const'] = [const_value] * len(y)

    return model, contributions


def calculate_diagnostics(model: sm.regression.linear_model.RegressionResultsWrapper, X: pd.DataFrame) -> Dict[str, Any]:
    """Calculate regression diagnostic statistics"""

    diagnostics = {}

    # Jarque-Bera test for normality
    jb_stat, jb_pvalue, _, _ = jarque_bera(model.resid)
    diagnostics['jarque_bera_stat'] = float(jb_stat)
    diagnostics['jarque_bera_pvalue'] = float(jb_pvalue)

    # Ljung-Box test for autocorrelation
    lb_test = acorr_ljungbox(model.resid, lags=[10], return_df=False)
    diagnostics['ljung_box_stat'] = float(lb_test[0][0]) if len(lb_test[0]) > 0 else 0.0
    diagnostics['ljung_box_pvalue'] = float(lb_test[1][0]) if len(lb_test[1]) > 0 else 1.0

    # Breusch-Pagan test for heteroskedasticity
    try:
        bp_test = het_breuschpagan(model.resid, model.model.exog)
        diagnostics['breusch_pagan_stat'] = float(bp_test[0])
        diagnostics['breusch_pagan_pvalue'] = float(bp_test[1])
    except:
        diagnostics['breusch_pagan_stat'] = 0.0
        diagnostics['breusch_pagan_pvalue'] = 1.0

    # White test for heteroskedasticity
    try:
        white_test = het_white(model.resid, model.model.exog)
        diagnostics['white_test_stat'] = float(white_test[0])
        diagnostics['white_test_pvalue'] = float(white_test[1])
    except:
        diagnostics['white_test_stat'] = 0.0
        diagnostics['white_test_pvalue'] = 1.0

    # Condition number
    diagnostics['condition_number'] = float(np.linalg.cond(model.model.exog))

    # VIF (Variance Inflation Factor)
    vif_values = {}
    try:
        for i, col in enumerate(X.columns):
            vif = variance_inflation_factor(model.model.exog, i + 1)  # +1 to skip constant
            vif_values[col] = float(vif)
    except:
        pass

    diagnostics['vif_values'] = vif_values

    return diagnostics


def run_modelling_regression(request: RegressionRequest) -> Dict[str, Any]:
    """
    Main function to run regression with transformations

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

    # Run regression
    model, contributions = run_regression(y, X, add_constant=True)

    # Calculate diagnostics
    diagnostics = calculate_diagnostics(model, X)

    # Prepare results
    result = {
        'coefficients': {name: float(coef) for name, coef in model.params.items()},
        'p_values': {name: float(pval) for name, pval in model.pvalues.items()},
        't_stats': {name: float(tstat) for name, tstat in model.tvalues.items()},
        'r_squared': float(model.rsquared),
        'adjusted_r_squared': float(model.rsquared_adj),
        'f_statistic': float(model.fvalue),
        'f_pvalue': float(model.f_pvalue),
        'aic': float(model.aic),
        'bic': float(model.bic),
        'durbin_watson': float(durbin_watson(model.resid)),
        'residuals': model.resid.tolist(),
        'fitted_values': model.fittedvalues.tolist(),
        'transformed_data': {col: transformed_df[col].tolist() for col in transformed_df.columns},
        'variable_contributions': contributions,
        'diagnostics': diagnostics,
        'n_observations': int(model.nobs),
        'degrees_of_freedom': int(model.df_resid)
    }

    return result


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
