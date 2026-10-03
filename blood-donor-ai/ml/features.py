"""
features.py
============
Shared feature engineering used by both training (train.py) and inference
(predict.py / app/ml/predict_service.py) so the exact same transformations
are applied at train time and prediction time.

Target variable: will_respond (0 = unlikely/did not respond, 1 = likely/responded)
"""

from datetime import datetime
import numpy as np
import pandas as pd

URGENCY_MAP = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}

# Feature columns used by the model, IN ORDER. Keeping an explicit list avoids
# silent column-order mismatches between training and inference.
FEATURE_COLUMNS = [
    "age",
    "total_donations",
    "previous_requests_received",
    "previous_response_rate",
    "average_response_time_minutes",
    "current_availability",
    "distance_km",
    "urgency_score",
    "units_required",
    "hour_of_day",
    "day_of_week",
    "is_o_negative",  # universal donor indicator - relevant, non-sensitive behavioural/clinical fact
]


def safe_response_rate(received: float, responded: float) -> float:
    received = max(received, 0)
    responded = max(responded, 0)
    if received <= 0:
        return 0.0
    return float(np.clip(responded / received, 0, 1))


def build_feature_row(raw: dict) -> dict:
    """
    Build one feature row (as a plain dict, in FEATURE_COLUMNS order) from raw
    donor/request attributes. Used identically by training and inference code.

    Expected keys in `raw`:
        age, blood_group, total_donations, previous_requests_received,
        previous_requests_responded, average_response_time_minutes,
        current_availability, distance_km, urgency_level, units_required
        (hour_of_day / day_of_week optional -> default to "now")
    """
    now = datetime.now()
    hour_of_day = raw.get("hour_of_day")
    if hour_of_day is None:
        hour_of_day = now.hour
    day_of_week = raw.get("day_of_week")
    if day_of_week is None:
        day_of_week = now.weekday()

    response_rate = raw.get("previous_response_rate")
    if response_rate is None:
        response_rate = safe_response_rate(
            raw.get("previous_requests_received", 0),
            raw.get("previous_requests_responded", 0),
        )

    row = {
        "age": float(raw.get("age", 30)),
        "total_donations": float(raw.get("total_donations", 0)),
        "previous_requests_received": float(raw.get("previous_requests_received", 0)),
        "previous_response_rate": float(response_rate),
        "average_response_time_minutes": float(raw.get("average_response_time_minutes", 60)),
        "current_availability": float(bool(raw.get("current_availability", False))),
        "distance_km": float(raw.get("distance_km", 10)),
        "urgency_score": float(URGENCY_MAP.get(raw.get("urgency_level", "Medium"), 1)),
        "units_required": float(raw.get("units_required", 1)),
        "hour_of_day": float(hour_of_day),
        "day_of_week": float(day_of_week),
        "is_o_negative": float(1.0 if raw.get("blood_group") == "O-" else 0.0),
    }
    return row


def build_feature_dataframe(raw_rows) -> pd.DataFrame:
    return pd.DataFrame([build_feature_row(r) for r in raw_rows])[FEATURE_COLUMNS]
