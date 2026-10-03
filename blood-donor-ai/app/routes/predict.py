"""
routes/predict.py
==================
Standalone prediction endpoint for the "Prediction" page - lets a user
enter arbitrary donor/request-like features and see the model's raw
output, independent of any specific stored donor or request.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import PredictionLog
from app.schemas.schemas import PredictionIn, PredictionOut
from app.ml.predict_service import get_prediction
from ml.predict import ModelNotFoundError
import json

router = APIRouter(prefix="/api", tags=["predict"])


@router.post("/predict", response_model=PredictionOut)
def predict(payload: PredictionIn, db: Session = Depends(get_db)):
    try:
        result = get_prediction(payload.model_dump())
    except ModelNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    log = PredictionLog(
        donor_id=None,
        request_id=None,
        input_features_json=json.dumps(payload.model_dump()),
        predicted_probability=result["response_probability"],
        predicted_label=result["predicted_label"],
        model_version=result.get("model_version"),
    )
    db.add(log)
    db.commit()

    return PredictionOut(
        response_probability=result["response_probability"],
        predicted_label=result["predicted_label"],
        classification=result["classification"],
        top_factors=result["top_factors"],
        disclaimer=result["disclaimer"],
    )
