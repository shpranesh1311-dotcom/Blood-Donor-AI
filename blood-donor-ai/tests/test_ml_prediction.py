"""Tests for ml/predict.py (requires a trained model - run `python ml/train.py` first)"""

import os
import pytest

from ml.predict import predict_response_probability, ModelNotFoundError
from ml import predict as predict_module


MODEL_AVAILABLE = os.path.exists(predict_module.MODEL_PATH)
pytestmark = pytest.mark.skipif(not MODEL_AVAILABLE, reason="Trained model not found - run `python ml/train.py` first")


def base_sample(**overrides):
    sample = {
        "age": 29, "blood_group": "O+", "total_donations": 6,
        "previous_requests_received": 8, "previous_requests_responded": 6,
        "average_response_time_minutes": 25, "current_availability": True,
        "distance_km": 3.2, "urgency_level": "Critical", "units_required": 2,
    }
    sample.update(overrides)
    return sample


def test_prediction_returns_probability_in_range():
    result = predict_response_probability(base_sample())
    assert 0.0 <= result["response_probability"] <= 1.0


def test_prediction_has_expected_keys():
    result = predict_response_probability(base_sample())
    for key in ["response_probability", "predicted_label", "classification", "top_factors"]:
        assert key in result


def test_high_reliability_donor_scores_higher_than_low_reliability():
    strong = predict_response_probability(base_sample(
        previous_requests_received=10, previous_requests_responded=9,
        average_response_time_minutes=15, current_availability=True, distance_km=1,
    ))
    weak = predict_response_probability(base_sample(
        previous_requests_received=10, previous_requests_responded=1,
        average_response_time_minutes=180, current_availability=False, distance_km=28,
    ))
    assert strong["response_probability"] > weak["response_probability"]


def test_top_factors_is_non_empty_list():
    result = predict_response_probability(base_sample())
    assert isinstance(result["top_factors"], list)
    assert len(result["top_factors"]) > 0
