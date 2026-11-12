# ShortsYou CPEP Service Contribution Documentation

## Overview

This document records the contribution made by **mayank1312** to the
`shortsYou-cpep-service` repository.

The project is a small, independently deployable FastAPI microservice that
loads trained CPEP models from MongoDB and predicts a normalized content
performance score for a creator’s video features. It is designed to work with
the model artifacts produced by the ShortsYou NLP training pipeline.

## Contribution Summary

The repository was built as a complete prediction service with:

- A FastAPI application and health endpoint.
- A protected `POST /predict` API.
- Pydantic request and response contracts.
- MongoDB lookup for the latest creator model.
- Personalized-model prediction for creators with their own trained model.
- Global pooled-model fallback using the `global-model` identifier.
- A labeled heuristic fallback when no trained model is available.
- XGBoost model deserialization and inference.
- Normalized performance scores and performance bands.
- Confidence bounds derived from stored model RMSE.
- Environment-based configuration.
- Optional API-key authentication with raw or `Bearer` credentials.
- A Python 3.11 Docker deployment.

The initial implementation contains approximately **270 lines across 11
files**, delivered in the repository’s first commit.

## Architecture

```text
app/
├── main.py           FastAPI app, health route, prediction route
├── schema.py         Request and response models
├── service.py        Prediction tiers and score conversion
├── db.py             MongoDB model retrieval
├── auth.py           API-key verification
└── configuration.py  Environment-backed settings
```

The service is intentionally narrow: model training is performed by the
ShortsYou NLP service, while this repository focuses on low-latency prediction
and graceful fallback behavior.

## Public API

### `GET /health`

Returns:

```json
{
  "status": "ok",
  "service": "shorts-cpep"
}
```

### `POST /predict`

The endpoint accepts a creator identifier and four model features:

```json
{
  "user_id": "creator-123",
  "features": {
    "emotion_score": 0.72,
    "semantic_score": 0.81,
    "hook_score": 0.76,
    "duration_seconds": 42.5
  }
}
```

The response contains:

- `predicted_score`: normalized score from `0.0` to `1.0`
- `performance_band`: `low`, `medium`, `high`, or `viral`
- `confidence_low` and `confidence_high`
- `model_version`
- `using_personalized`
- `prediction_source`: `personalized`, `global`, or `heuristic`

When `API_ACCESS_KEY` is configured, `/predict` requires the configured key in
the `Authorization` header. Both a raw key and `Bearer <key>` format are
accepted.

## Prediction Flow

Prediction uses three ordered tiers:

### Tier 1: Personalized creator model

The service queries MongoDB for the newest model where `userId` matches the
requested creator. If a model exists, it:

1. Loads the serialized XGBoost booster from `modelJson`.
2. Uses the stored `featureOrder` when available.
3. Builds the feature row in the required order.
4. Predicts the log-scaled performance target.
5. Converts it to a normalized score.
6. Calculates a performance band and RMSE-based confidence interval.

### Tier 2: Global pooled model

If the creator does not have a model, or their model fails to load, the service
looks for the pooled model stored under:

```text
global-model
```

The response identifies this source as `global` and marks
`using_personalized` as `false`.

### Tier 3: Heuristic fallback

If neither trained model is available, the service remains usable by averaging
the emotion, semantic, and hook scores. Duration is not included in this
fallback because the heuristic is intended to provide a simple content-quality
signal rather than emulate the trained model.

The heuristic returns:

- `model_version: "fallback-heuristic"`
- `prediction_source: "heuristic"`
- A confidence range of ±0.2, clipped to `[0.0, 1.0]`

## Score Conversion

The training target is stored in log-scaled view space. The prediction service
normalizes the model output against a reference of one million views:

```text
normalized_score =
    clip(log_prediction / log1p(1,000,000), 0.0, 1.0)
```

Performance bands are assigned using these thresholds:

| Normalized score | Band |
| --- | --- |
| `< 0.25` | `low` |
| `0.25` to `< 0.50` | `medium` |
| `0.50` to `< 0.75` | `high` |
| `>= 0.75` | `viral` |

Confidence bounds apply the stored model RMSE in log space before converting
both endpoints to the normalized score range.

## Integration Contract

The service expects model documents in the shared MongoDB database and
`cpep_models` collection. The lookup and inference code uses these fields:

- `userId`
- `versionNumber`
- `modelVersion`
- `modelJson`
- `featureOrder`
- `rmse`

The default feature order is:

```text
emotion_score
semantic_score
hook_score
duration_seconds
```

The MongoDB database name must match the database used by the ShortsYou NLP
training service. This keeps model training and model serving decoupled while
allowing the prediction service to consume the latest available artifact.

## Deployment

The repository includes a Docker image based on Python 3.11. The container:

1. Installs the dependencies from `requirements.txt`.
2. Copies the application into `/app`.
3. Starts Uvicorn on the `PORT` environment variable.
4. Defaults to port `8002` when `PORT` is not set.

Required environment variables:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=shortsyou_nlp
API_ACCESS_KEY=replace-with-a-secure-api-key
```

`MONGODB_DATABASE` should be the same database used by the training service.

## Commit History

| Date | Commit | Contribution |
| --- | --- | --- |
| 2026-11-09 | `ec144b9` | Initialized the CPEP prediction route, FastAPI service, schemas, MongoDB model lookup, personalized/global/heuristic prediction tiers, authentication, configuration, dependency manifest, Dockerfile, and environment template. |

## Current Limitations and Follow-up Areas

These are known design boundaries of the current implementation:

- The service assumes MongoDB is reachable during application startup.
- There is no model-management or model-upload endpoint; models are written by
  the training service.
- The prediction endpoint is synchronous because inference is intended to be
  lightweight after model loading.
- The fallback heuristic does not use duration.
- Confidence bounds are based on the stored aggregate RMSE and are not
  calibrated per individual prediction.
- No automated test suite is currently included in the repository.
- Operational observability is currently provided through standard logging and
  the health endpoint.

## Files Added

- `.dockerignore`
- `.env.example`
- `.gitignore`
- `Dockerfile`
- `requirements.txt`
- `app/auth.py`
- `app/configuration.py`
- `app/db.py`
- `app/main.py`
- `app/schema.py`
- `app/service.py`

