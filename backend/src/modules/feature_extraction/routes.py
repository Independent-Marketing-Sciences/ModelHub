"""Feature extraction API routes"""

from fastapi import APIRouter
from .models import FeatureExtractionRequest
from .service import extract_features

router = APIRouter()


@router.post("/extract")
async def feature_extraction(request: FeatureExtractionRequest):
    """
    Extract top features using XGBoost and Random Forest

    Returns:
        - combined_features: merged unique feature list
        - top_features_xgb: list of top features from XGBoost
        - top_features_rf: list of top features from Random Forest
        - feature_importances: importance scores from both models
    """
    return extract_features(request)
