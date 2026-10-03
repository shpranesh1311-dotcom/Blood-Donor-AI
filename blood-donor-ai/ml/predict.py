"""
predict.py
==========
Standalone inference module. Loads the trained, calibrated model saved by
train.py and exposes a single function, predict_response_probability(),
that turns a raw feature dict into a probability + human-readable label.

This module has no FastAPI dependency so it can also be run/tested from
the command line or imported by other scripts.

Usage (CLI smoke test):
    python ml/predict.py
"""

import json
import os
import sys

import joblib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BASE_DIR)

from ml.features import build_feature_row, FEATURE_COLUMNS  # noqa: E402

MODEL_PATH = os.path.join(BASE_DIR, "models", "trained_model.joblib")
METADATA_PATH = os.path.join(BASE_DIR, "models", "model_metadata.json")

_model = None
_metadata = None


class ModelNotFoundError(RuntimeError):
    pass


def load_model():
    global _model, _metadata
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise ModelNotFoundError(
                "Trained model not found. Run `python ml/train.py` first to train and save it."
            )
        _model = joblib.load(MODEL_PATH)
        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH) as f:
                _metadata = json.load(f)
        else:
            _metadata = {}
    return _model, _metadata


def classify(probability: float) -> str:
    if probability >= 0.7:
        return "High likelihood of response"
    if probability >= 0.4:
        return "Medium likelihood of response"
    return "Low likelihood of response"


def explain_factors(raw: dict, feature_row: dict) -> list:
    """
    Simple, transparent (non-SHAP) explanation: surfaces the factors most
    commonly associated with higher/lower response probability, in plain
    language. This is NOT a medical or guaranteed causal explanation.
    """
    factors = []

    rate = feature_row["previous_response_rate"]
    factors.append({
        "factor": "Previous response rate",
        "value": f"{rate * 100:.0f}%",
        "impact": "positive" if rate >= 0.5 else "negative",
    })

    dist = feature_row["distance_km"]
    factors.append({
        "factor": "Distance to request",
        "value": f"{dist:.1f} km",
        "impact": "positive" if dist <= 10 else ("neutral" if dist <= 20 else "negative"),
    })

    avail = feature_row["current_availability"]
    factors.append({
        "factor": "Current availability",
        "value": "Available" if avail else "Not marked available",
        "impact": "positive" if avail else "negative",
    })

    rt = feature_row["average_response_time_minutes"]
    factors.append({
        "factor": "Historical response time",
        "value": f"{rt:.0f} minutes",
        "impact": "positive" if rt <= 45 else ("neutral" if rt <= 90 else "negative"),
    })

    urgency = raw.get("urgency_level", "Medium")
    factors.append({
        "factor": "Request urgency",
        "value": urgency,
        "impact": "neutral",
    })

    return factors


def predict_response_probability(raw: dict) -> dict:
    """
    raw: dict with keys matching PredictionIn schema / build_feature_row() inputs.
    Returns: dict with response_probability, predicted_label, classification,
             top_factors, feature_row (for logging).
    """
    model, metadata = load_model()
    feature_row = build_feature_row(raw)

    import pandas as pd
    X = pd.DataFrame([feature_row])[FEATURE_COLUMNS]

    probability = float(model.predict_proba(X)[0, 1])
    label = "likely" if probability >= 0.5 else "unlikely"

    return {
        "response_probability": round(probability, 4),
        "predicted_label": label,
        "classification": classify(probability),
        "top_factors": explain_factors(raw, feature_row),
        "feature_row": feature_row,
        "model_version": metadata.get("best_model_name", "unknown") if metadata else "unknown",
    }


if __name__ == "__main__":
    sample = {
        "age": 29,
        "blood_group": "O+",
        "total_donations": 6,
        "previous_requests_received": 8,
        "previous_requests_responded": 6,
        "average_response_time_minutes": 25,
        "current_availability": True,
        "distance_km": 3.2,
        "urgency_level": "Critical",
        "units_required": 2,
    }
    result = predict_response_probability(sample)
    print(json.dumps(result, indent=2))
