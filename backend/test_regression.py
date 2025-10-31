"""Test regression endpoint directly"""
import sys
sys.path.insert(0, 'src')

from modules.modelling.models import RegressionRequest, ModelConfiguration, VariableTransformation
from modules.modelling.service import run_modelling_regression

# Create test data
data = {
    "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
    "sales": [100, 110, 105, 115, 120],
    "advertising": [10, 12, 11, 13, 14]
}

# Create request
request = RegressionRequest(
    model_configuration=ModelConfiguration(
        kpi="sales",
        start_date="2024-01-01",
        end_date="2024-01-05",
        xs_weights="none",
        log_trans_bias=False,
        take_anti_logs_at_midpoints=False
    ),
    variable_transformations=[
        VariableTransformation(
            variable="sales",
            include=True,
            pre_transform=None,
            lag=0,
            lead=0,
            adstock=0,
            dimret=0,
            dimret_adstock=False,
            post_transform=None
        ),
        VariableTransformation(
            variable="advertising",
            include=True,
            pre_transform=None,
            lag=0,
            lead=0,
            adstock=0,
            dimret=0,
            dimret_adstock=False,
            post_transform=None
        )
    ],
    data=data
)

try:
    print("Running regression...")
    result = run_modelling_regression(request)
    print("SUCCESS!")
    print(f"R-squared: {result['r_squared']}")
    print(f"Coefficients: {result['coefficients']}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
