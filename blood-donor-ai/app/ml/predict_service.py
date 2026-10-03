"""
predict_service.py
===================
Thin wrapper around ml/predict.py so the FastAPI app can call the trained
model without duplicating any ML logic. Keeping this separate from
ml/predict.py means the core ML module stays framework-agnostic and
independently testable/runnable from the command line.
"""

from ml.predict import predict_response_probability, load_model, ModelNotFoundError  # noqa: F401

DISCLAIMER = (
    "This is a probabilistic estimate for prioritisation/assistance only. "
    "It does not guarantee donor behaviour, and final eligibility and "
    "donation decisions remain with the donor, hospital, and medical professionals."
)


def get_prediction(raw: dict) -> dict:
    result = predict_response_probability(raw)
    result["disclaimer"] = DISCLAIMER
    return result
