"""Transformation functions for modelling"""

import numpy as np
import pandas as pd
from typing import List, Optional


def apply_pre_transform(series: np.ndarray, transform_type: Optional[str]) -> np.ndarray:
    """Apply pre-transformation (log, sqrt, exp)"""
    if transform_type is None or transform_type == "none":
        return series

    series = np.array(series, dtype=float)

    if transform_type == "log":
        # Add small constant to avoid log(0)
        return np.log(series + 1e-10)
    elif transform_type == "sqrt":
        return np.sqrt(np.maximum(series, 0))
    elif transform_type == "exp":
        return np.exp(series)
    else:
        return series


def apply_post_transform(series: np.ndarray, transform_type: Optional[str]) -> np.ndarray:
    """Apply post-transformation (log, sqrt, exp)"""
    return apply_pre_transform(series, transform_type)


def apply_lag(series: np.ndarray, lag_value: int) -> np.ndarray:
    """Apply lag transformation"""
    if lag_value == 0:
        return series

    result = np.zeros_like(series)
    if lag_value > 0:
        result[lag_value:] = series[:-lag_value]
        result[:lag_value] = 0  # Fill with zeros
    return result


def apply_lead(series: np.ndarray, lead_value: int) -> np.ndarray:
    """Apply lead transformation"""
    if lead_value == 0:
        return series

    result = np.zeros_like(series)
    if lead_value > 0:
        result[:-lead_value] = series[lead_value:]
        result[-lead_value:] = 0  # Fill with zeros
    return result


def apply_adstock(series: np.ndarray, ads_rate: float) -> np.ndarray:
    """
    Apply adstock transformation
    ads_rate: decay rate between 0 and 1
    """
    if ads_rate == 0:
        return series

    ads_x = np.zeros_like(series, dtype=float)
    for i in range(len(series)):
        if i == 0:
            ads_x[i] = series[i]
        else:
            ads_x[i] = series[i] + ads_x[i - 1] * ads_rate
    return ads_x


def apply_normalized_adstock(series: np.ndarray, ads_rate: float) -> np.ndarray:
    """Apply normalized adstock"""
    if ads_rate == 0:
        return series

    ads_x = apply_adstock(series, ads_rate)
    return ads_x * (1 - ads_rate)


def apply_dimret(series: np.ndarray, dr_info: float, pct_conv: bool = True) -> np.ndarray:
    """
    Apply diminishing returns transformation
    dr_info: percentage conversion or alpha value
    pct_conv: if True, dr_info is percentage, else it's alpha directly
    """
    if dr_info == 0:
        return series

    series = np.array(series, dtype=float)
    dr_x = np.zeros_like(series)

    if np.sum(series) != 0:
        if pct_conv:
            # Calculate alpha from percentage
            positive_mean = np.mean(series[series > 0])
            if positive_mean > 0:
                dr_alpha = -1 * np.log(1 - dr_info) / positive_mean
            else:
                dr_alpha = 0
        else:
            dr_alpha = dr_info

        dr_x = 1 - np.exp(-1 * dr_alpha * series)

    return dr_x


def apply_normalized_dimret(series: np.ndarray, dr_info: float, pct_conv: bool = True) -> np.ndarray:
    """Apply normalized diminishing returns"""
    if dr_info == 0:
        return series

    dr_x = apply_dimret(series, dr_info, pct_conv)
    sum_original = np.sum(series)
    sum_transformed = np.sum(dr_x)

    if sum_transformed > 0:
        return dr_x * (sum_original / sum_transformed)
    return dr_x


def apply_dimret_adstock(series: np.ndarray, ads_rate: float, dr_info: float, pct_conv: bool = True) -> np.ndarray:
    """
    Apply combined diminishing returns and adstock
    First applies adstock, then diminishing returns
    """
    if ads_rate == 0 and dr_info == 0:
        return series

    # Step 1: Apply adstock
    dr_ads_x = apply_adstock(series, ads_rate)

    # Step 2: Apply diminishing returns to adstocked series
    if np.sum(series) != 0 and dr_info != 0:
        if pct_conv:
            positive_mean = np.mean(series[series > 0])
            if positive_mean > 0:
                dr_alpha = -1 * np.log(1 - dr_info) / positive_mean
            else:
                return dr_ads_x
        else:
            dr_alpha = dr_info

        dr_ads_x = np.asarray(dr_ads_x, dtype=float)
        dr_ads_x = 1 - np.exp(-1 * dr_ads_x * dr_alpha)

    return dr_ads_x


def apply_normalized_dimret_adstock(series: np.ndarray, ads_rate: float, dr_info: float, pct_conv: bool = True) -> np.ndarray:
    """Apply normalized combined diminishing returns and adstock"""
    dr_ads_x = apply_dimret_adstock(series, ads_rate, dr_info, pct_conv)
    sum_original = np.sum(series)
    sum_transformed = np.sum(dr_ads_x)

    if sum_transformed > 0:
        return dr_ads_x * (sum_original / sum_transformed)
    return dr_ads_x


def apply_variable_transformation(
    series: np.ndarray,
    pre_transform: Optional[str] = None,
    lag: int = 0,
    lead: int = 0,
    adstock: float = 0.0,
    dimret: float = 0.0,
    dimret_adstock: bool = False,
    post_transform: Optional[str] = None
) -> np.ndarray:
    """
    Apply full transformation pipeline to a variable

    Order of operations:
    1. Pre-transformation (log, sqrt, exp)
    2. Lag/Lead
    3. Adstock + Diminishing Returns (if dimret_adstock=True)
       OR separate Adstock and Diminishing Returns
    4. Post-transformation (log, sqrt, exp)
    """
    series = np.array(series, dtype=float)

    # Step 1: Pre-transformation
    if pre_transform:
        series = apply_pre_transform(series, pre_transform)

    # Step 2: Lag/Lead
    if lag > 0:
        series = apply_lag(series, lag)
    elif lead > 0:
        series = apply_lead(series, lead)

    # Step 3: Adstock and/or Diminishing Returns
    if dimret_adstock and (adstock > 0 or dimret > 0):
        # Combined transformation
        series = apply_dimret_adstock(series, adstock, dimret, pct_conv=True)
    else:
        # Separate transformations
        if adstock > 0:
            series = apply_adstock(series, adstock)
        if dimret > 0:
            series = apply_dimret(series, dimret, pct_conv=True)

    # Step 4: Post-transformation
    if post_transform:
        series = apply_post_transform(series, post_transform)

    return series
