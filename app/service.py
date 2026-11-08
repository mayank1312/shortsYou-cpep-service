import logging

import numpy as np
import xgboost as xgb

from app.db import get_latest_model
from app.schema import PredictFeatures, PredictResponse

logger = logging.getLogger(__name__)

GLOBAL_MODEL_USER_ID = "global-model"
REFERENCE_VIRAL_VIEWS = 1_000_000
PERFORMANCE_BAND_THRESHOLDS = [(0.25, "low"), (0.5, "medium"), (0.75, "high")]


def _band(score: float) -> str:
    for limit, name in PERFORMANCE_BAND_THRESHOLDS:
        if score < limit:
            return name
    return "viral"


def _normalize_log_prediction(log_pred: float) -> float:
    value = log_pred / np.log1p(REFERENCE_VIRAL_VIEWS)
    return round(float(np.clip(value, 0.0, 1.0)), 4)


def _predict_with_model(model_document: dict, features: PredictFeatures, source: str) -> PredictResponse:
    booster = xgb.Booster()
    booster.load_model(bytearray(model_document["modelJson"], "utf-8"))

    order = model_document.get("featureOrder") or [
        "emotion_score", "semantic_score", "hook_score", "duration_seconds",
    ]
    row = np.array([[getattr(features, name) for name in order]], dtype=float)
    log_pred = float(booster.predict(xgb.DMatrix(row, feature_names=None))[0])
    rmse = float(model_document.get("rmse", 0.0))

    score = _normalize_log_prediction(log_pred)
    return PredictResponse(
        predicted_score=score,
        performance_band=_band(score),
        confidence_low=_normalize_log_prediction(log_pred - rmse),
        confidence_high=_normalize_log_prediction(log_pred + rmse),
        model_version=model_document.get("modelVersion", "unknown"),
        using_personalized=(source == "personalized"),
        prediction_source=source,
    )


def _predict_with_fallback_heuristic(features: PredictFeatures) -> PredictResponse:
    parts = [features.emotion_score, features.semantic_score, features.hook_score]
    score = round(float(np.clip(np.mean(parts), 0.0, 1.0)), 4)
    return PredictResponse(
        predicted_score=score,
        performance_band=_band(score),
        confidence_low=round(max(score - 0.2, 0.0), 4),
        confidence_high=round(min(score + 0.2, 1.0), 4),
        model_version="fallback-heuristic",
        using_personalized=False,
        prediction_source="heuristic",
    )


def _try_tier(user_id: str, features: PredictFeatures, source: str):
    try:
        doc = get_latest_model(user_id)
        if doc:
            return _predict_with_model(doc, features, source)
    except Exception:
        logger.exception("%s model failed for %s - falling through", source, user_id)
    return None


def predict(user_id: str, features: PredictFeatures) -> PredictResponse:
    # Tier 1: creator's own model
    result = _try_tier(user_id, features, "personalized")
    if result:
        return result
    # Tier 2: pooled global model
    result = _try_tier(GLOBAL_MODEL_USER_ID, features, "global")
    if result:
        return result
    # Tier 3: labeled heuristic
    return _predict_with_fallback_heuristic(features)