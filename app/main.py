import logging

from fastapi import Depends, FastAPI

from app.auth import verify_api_key
from app.schema import PredictRequest, PredictResponse
from app.service import predict

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ShortsYou CPEP", version="1.0.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "shorts-cpep"}


@app.post("/predict", response_model=PredictResponse, dependencies=[Depends(verify_api_key)])
def predict_route(request: PredictRequest) -> PredictResponse:
    return predict(request.user_id, request.features)