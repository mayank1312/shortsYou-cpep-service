from pydantic import BaseModel


class PredictFeatures(BaseModel):
    emotion_score: float
    semantic_score: float
    hook_score: float
    duration_seconds: float


class PredictRequest(BaseModel):
    user_id: str
    features: PredictFeatures


class PredictResponse(BaseModel):
    predicted_score: float
    performance_band: str
    confidence_low: float
    confidence_high: float
    model_version: str
    using_personalized: bool
    # "personalized" | "global" | "heuristic"
    prediction_source: str