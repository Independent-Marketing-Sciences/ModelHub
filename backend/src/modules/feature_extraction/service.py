"""Feature extraction service using XGBoost and Random Forest"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from fastapi import HTTPException
import sys
import traceback

# Try to import xgboost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


def extract_features(request):
    """
    Extract top features using XGBoost and Random Forest models.

    Steps:
    1) Convert data dict to DataFrame
    2) Split into train/test
    3) Train XGBoost and Random Forest on all features
    4) Extract top n_features from each model
    5) Merge their unique top features
    6) Return the combined feature list with importance scores

    Parameters
    ----------
    request : FeatureExtractionRequest
        Request containing data, kpi_var, and parameters

    Returns
    -------
    dict
        A dictionary containing:
        - "combined_features": merged unique feature list
        - "top_features_xgb": list of top features from XGBoost
        - "top_features_rf": list of top features from Random Forest
        - "xgb_importances": feature importance scores from XGBoost
        - "rf_importances": feature importance scores from Random Forest
    """
    try:
        if not XGBOOST_AVAILABLE:
            raise HTTPException(
                status_code=500,
                detail="XGBoost library not installed. Please install: pip install xgboost"
            )

        # Convert data dict to DataFrame
        df = pd.DataFrame(request.data)

        # Check if KPI variable exists
        if request.kpi_var not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"KPI variable '{request.kpi_var}' not found in data"
            )

        # Extract target and features
        y = df[request.kpi_var]

        # Drop date column and KPI from features
        cols_to_drop = [request.kpi_var]
        if request.date_column in df.columns:
            cols_to_drop.append(request.date_column)

        X = df.drop(columns=cols_to_drop)

        # Check if we have features
        if X.shape[1] == 0:
            raise HTTPException(
                status_code=400,
                detail="No feature columns available after removing KPI and date column"
            )

        # Remove any columns with all NaN or infinite values
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.dropna(axis=1, how='all')

        # Remove rows with NaN
        valid_idx = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_idx]
        y = y[valid_idx]

        if len(X) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data points after cleaning. Need at least 10, got {len(X)}"
            )

        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=request.test_size,
            random_state=request.random_state,
            shuffle=request.shuffle,
        )

        # ---------------------------------------------------------------------
        # XGBoost Approach
        # ---------------------------------------------------------------------
        xgb_model = xgb.XGBRegressor(
            random_state=request.random_state,
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1
        )
        xgb_model.fit(X_train, y_train)

        # Get feature importances
        xgb_importances = xgb_model.feature_importances_
        xgb_feat_importance_df = (
            pd.DataFrame({
                "feature": X.columns,
                "importance": xgb_importances
            })
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )

        # Select top N features
        top_features_xgb = xgb_feat_importance_df["feature"].head(request.n_features).tolist()
        xgb_importance_dict = dict(zip(
            xgb_feat_importance_df["feature"],
            xgb_feat_importance_df["importance"].tolist()
        ))

        # ---------------------------------------------------------------------
        # Random Forest Approach
        # ---------------------------------------------------------------------
        rf_model = RandomForestRegressor(
            random_state=request.random_state,
            n_estimators=100,
            max_depth=10
        )
        rf_model.fit(X_train, y_train)

        # Get feature importances
        rf_importances = rf_model.feature_importances_
        rf_feat_importance_df = (
            pd.DataFrame({
                "feature": X.columns,
                "importance": rf_importances
            })
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )

        # Select top N features
        top_features_rf = rf_feat_importance_df["feature"].head(request.n_features).tolist()
        rf_importance_dict = dict(zip(
            rf_feat_importance_df["feature"],
            rf_feat_importance_df["importance"].tolist()
        ))

        # ---------------------------------------------------------------------
        # Combine top features from both models
        # ---------------------------------------------------------------------
        combined_features = list(set(top_features_xgb + top_features_rf))

        # Sort combined features by average importance
        combined_importance = []
        for feat in combined_features:
            avg_importance = (
                xgb_importance_dict.get(feat, 0) +
                rf_importance_dict.get(feat, 0)
            ) / 2
            combined_importance.append({
                "feature": feat,
                "xgb_importance": float(xgb_importance_dict.get(feat, 0)),
                "rf_importance": float(rf_importance_dict.get(feat, 0)),
                "avg_importance": float(avg_importance)
            })

        # Sort by average importance
        combined_importance.sort(key=lambda x: x["avg_importance"], reverse=True)

        return {
            "combined_features": [item["feature"] for item in combined_importance],
            "top_features_xgb": top_features_xgb,
            "top_features_rf": top_features_rf,
            "feature_importances": combined_importance,
            "n_samples_train": int(len(X_train)),
            "n_samples_test": int(len(X_test)),
            "n_features_total": int(X.shape[1]),
            "n_features_selected": len(combined_features)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Feature extraction error: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
