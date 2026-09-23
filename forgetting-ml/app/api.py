"""
api.py

Defines the FastAPI router for the Forgetting Prediction Engine.
"""

from fastapi import APIRouter, HTTPException

from app.schemas import (
    TaskFeatures, PredictionResponse, BatchPredictionRequest,
    BatchPredictionResponse, HealthResponse,
)
from app.inference import ForgettingPredictor

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["meta"])
def health():
    try:
        predictor = ForgettingPredictor.instance()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Model unavailable.") from exc
    return HealthResponse(
        status="ok",
        model_version=predictor.model_version,
        model_name=predictor.model_name,
    )


@router.post("/api/v1/predictions/forgetting", response_model=PredictionResponse, tags=["predictions"])
def predict_forgetting(task: TaskFeatures):
    try:
        predictor = ForgettingPredictor.instance()
        result = predictor.predict_single(task.model_dump())
        return PredictionResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail="Prediction service unavailable.") from e


@router.post("/api/v1/predictions/forgetting/batch", response_model=BatchPredictionResponse, tags=["predictions"])
def predict_forgetting_batch(request: BatchPredictionRequest):
    try:
        predictor = ForgettingPredictor.instance()
        tasks = [t.model_dump() for t in request.tasks]
        results = predictor.predict_batch(tasks)
        return BatchPredictionResponse(predictions=[PredictionResponse(**r) for r in results])
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail="Prediction service unavailable.") from e
