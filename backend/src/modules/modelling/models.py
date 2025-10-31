"""Pydantic models for modelling API"""

from pydantic import BaseModel
from typing import Dict, List, Optional, Any


class VariableTransformation(BaseModel):
    """Configuration for a single variable's transformation"""
    variable: str
    include: bool = True
    pre_transform: Optional[str] = None  # 'log', 'sqrt', 'exp', None
    lag: int = 0
    lead: int = 0
    adstock: float = 0.0  # 0-1 range
    dimret: float = 0.0  # 0-1 range for percentage conversion
    dimret_adstock: bool = False  # Combined dimret + adstock
    post_transform: Optional[str] = None  # 'log', 'sqrt', 'exp', None


class ModelConfiguration(BaseModel):
    """Model details configuration"""
    kpi: str
    start_date: str
    end_date: str
    xs_weights: str = "weights"
    log_trans_bias: bool = False
    take_anti_logs_at_midpoints: bool = True


class RegressionRequest(BaseModel):
    """Request to run regression with transformations"""
    model_configuration: ModelConfiguration
    variable_transformations: List[VariableTransformation]
    data: Dict[str, List[Any]]  # Column name -> values


class TransformDataRequest(BaseModel):
    """Request to transform data without running regression"""
    variable_name: str
    data: List[float]
    transformation: VariableTransformation


class RegressionResult(BaseModel):
    """Regression results"""
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    t_stats: Dict[str, float]
    r_squared: float
    adjusted_r_squared: float
    f_statistic: float
    f_pvalue: float
    aic: float
    bic: float
    durbin_watson: float
    residuals: List[float]
    fitted_values: List[float]
    transformed_data: Dict[str, List[float]]
    variable_contributions: Dict[str, List[float]]


class ModelDiagnostics(BaseModel):
    """Model diagnostic statistics"""
    jarque_bera_stat: float
    jarque_bera_pvalue: float
    ljung_box_stat: float
    ljung_box_pvalue: float
    breusch_pagan_stat: float
    breusch_pagan_pvalue: float
    white_test_stat: float
    white_test_pvalue: float
    condition_number: float
    vif_values: Dict[str, float]
