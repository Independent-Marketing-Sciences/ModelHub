"""Stepwise regression service logic"""

import numpy as np
import sys
import traceback
from fastapi import HTTPException
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import f_regression


def stepwise_regression_logic(request):
    """
    Perform stepwise regression variable selection

    Methods:
        - forward: Start with no variables, add best at each step
        - backward: Start with all variables, remove worst at each step
        - both: Combination of forward and backward

    Returns:
        - selected_variables: List of selected variable names
        - coefficients: Regression coefficients
        - r_squared: Model R² value
        - adjusted_r_squared: Adjusted R²
        - p_values: P-values for each variable
        - steps: Selection process details
    """
    try:
        # Convert to numpy arrays
        y = np.array(request.y)
        X_dict = request.X
        variable_names = list(X_dict.keys())
        X = np.column_stack([X_dict[name] for name in variable_names])

        # Remove NaN values
        valid_idx = ~(np.isnan(y) | np.any(np.isnan(X), axis=1))
        y = y[valid_idx]
        X = X[valid_idx]

        if len(y) < 2:
            raise HTTPException(status_code=400, detail="Insufficient valid data points")

        n_samples, n_features = X.shape

        if request.method == "forward":
            selected = forward_selection(X, y, variable_names, request.significance_level)
        elif request.method == "backward":
            selected = backward_elimination(X, y, variable_names, request.significance_level)
        else:  # both
            selected = stepwise_both(X, y, variable_names, request.significance_level)

        # Fit final model with selected variables
        if len(selected['selected_indices']) > 0:
            X_selected = X[:, selected['selected_indices']]
            model = LinearRegression()
            model.fit(X_selected, y)

            # Calculate statistics
            y_pred = model.predict(X_selected)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)

            # Adjusted R²
            n = len(y)
            p = len(selected['selected_indices'])
            adjusted_r_squared = 1 - ((1 - r_squared) * (n - 1) / (n - p - 1))

            # P-values
            _, p_values = f_regression(X_selected, y)

            response = {
                "selected_variables": selected['selected_variables'],
                "coefficients": {
                    "intercept": float(model.intercept_),
                    "variables": {
                        name: float(coef)
                        for name, coef in zip(selected['selected_variables'], model.coef_)
                    }
                },
                "r_squared": float(r_squared),
                "adjusted_r_squared": float(adjusted_r_squared),
                "p_values": {
                    name: float(p_val)
                    for name, p_val in zip(selected['selected_variables'], p_values)
                },
                "steps": selected['steps'],
                "n_samples": int(n),
                "n_features_original": int(n_features),
                "n_features_selected": len(selected['selected_indices'])
            }
        else:
            response = {
                "selected_variables": [],
                "message": "No variables met the significance criteria",
                "steps": selected['steps']
            }

        return response

    except Exception as e:
        print(f"Stepwise regression error: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def forward_selection(X, y, variable_names, significance_level):
    """Forward stepwise selection"""
    n_features = X.shape[1]
    selected_indices = []
    remaining_indices = list(range(n_features))
    steps = []

    while remaining_indices:
        best_p_value = 1.0
        best_idx = None

        for idx in remaining_indices:
            test_indices = selected_indices + [idx]
            X_test = X[:, test_indices]

            model = LinearRegression()
            model.fit(X_test, y)

            # Calculate p-value for new variable
            _, p_values = f_regression(X_test, y)
            p_value = p_values[-1]  # P-value of newly added variable

            if p_value < best_p_value:
                best_p_value = p_value
                best_idx = idx

        if best_p_value < significance_level:
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
            steps.append({
                "step": len(selected_indices),
                "action": "add",
                "variable": variable_names[best_idx],
                "p_value": float(best_p_value)
            })
        else:
            break

    return {
        "selected_indices": selected_indices,
        "selected_variables": [variable_names[i] for i in selected_indices],
        "steps": steps
    }


def backward_elimination(X, y, variable_names, significance_level):
    """Backward stepwise elimination"""
    n_features = X.shape[1]
    selected_indices = list(range(n_features))
    steps = []

    while len(selected_indices) > 0:
        X_selected = X[:, selected_indices]
        _, p_values = f_regression(X_selected, y)

        max_p_value = np.max(p_values)
        max_p_idx = np.argmax(p_values)

        if max_p_value > significance_level:
            removed_idx = selected_indices[max_p_idx]
            selected_indices.remove(removed_idx)
            steps.append({
                "step": len(steps) + 1,
                "action": "remove",
                "variable": variable_names[removed_idx],
                "p_value": float(max_p_value)
            })
        else:
            break

    return {
        "selected_indices": selected_indices,
        "selected_variables": [variable_names[i] for i in selected_indices],
        "steps": steps
    }


def stepwise_both(X, y, variable_names, significance_level):
    """Bidirectional stepwise selection"""
    # Start with forward selection
    result = forward_selection(X, y, variable_names, significance_level)

    # Then apply backward elimination on selected variables
    if len(result['selected_indices']) > 1:
        X_subset = X[:, result['selected_indices']]
        backward_result = backward_elimination(
            X_subset, y, result['selected_variables'], significance_level
        )

        # Map back to original indices
        final_indices = [
            result['selected_indices'][i]
            for i in range(len(result['selected_indices']))
            if result['selected_variables'][i] in backward_result['selected_variables']
        ]

        result['selected_indices'] = final_indices
        result['selected_variables'] = backward_result['selected_variables']
        result['steps'].extend(backward_result['steps'])

    return result
