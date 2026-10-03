"""
schemas.py
==========
Pydantic request/response models for the FastAPI API layer.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DonorOut(BaseModel):
    donor_id: str
    age: int
    gender: str
    blood_group: str
    city: str
    latitude: float
    longitude: float
    total_donations: int
    average_response_time_minutes: float
    availability_preference: str
    current_availability: bool
    donor_status: str

    model_config = ConfigDict(from_attributes=True)


class EmergencyRequestIn(BaseModel):
    blood_group_required: str
    units_required: int = Field(gt=0, le=20)
    urgency_level: str
    hospital_area: str
    latitude: float
    longitude: float
    request_datetime: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("blood_group_required")
    @classmethod
    def validate_blood_group(cls, v):
        allowed = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
        if v not in allowed:
            raise ValueError(f"blood_group_required must be one of {allowed}")
        return v

    @field_validator("urgency_level")
    @classmethod
    def validate_urgency(cls, v):
        allowed = ["Critical", "High", "Medium", "Low"]
        if v not in allowed:
            raise ValueError(f"urgency_level must be one of {allowed}")
        return v

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v):
        if not (-90 <= v <= 90):
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lon(cls, v):
        if not (-180 <= v <= 180):
            raise ValueError("longitude must be between -180 and 180")
        return v


class EmergencyRequestOut(BaseModel):
    request_id: str
    blood_group_required: str
    units_required: int
    urgency_level: str
    hospital_area: str
    latitude: float
    longitude: float
    request_datetime: str
    request_status: str

    model_config = ConfigDict(from_attributes=True)


class MatchedDonorOut(BaseModel):
    rank: int
    donor_id: str
    city: str
    blood_group: str
    distance_km: float
    ml_response_probability: float
    previous_response_rate: float
    expected_response_label: str
    current_availability: bool
    overall_score: float
    sub_scores: dict


class MatchResponse(BaseModel):
    request_id: str
    blood_group_required: str
    total_compatible_donors: int
    total_eligible_donors: int
    matches: List[MatchedDonorOut]
    disclaimer: str


class PredictionIn(BaseModel):
    age: int = Field(ge=18, le=80)
    blood_group: str
    total_donations: int = Field(ge=0)
    previous_requests_received: int = Field(ge=0)
    previous_requests_responded: int = Field(ge=0)
    average_response_time_minutes: float = Field(ge=1)
    current_availability: bool
    distance_km: float = Field(ge=0)
    urgency_level: str
    hour_of_day: Optional[int] = Field(default=None, ge=0, le=23)
    day_of_week: Optional[int] = Field(default=None, ge=0, le=6)


class PredictionOut(BaseModel):
    response_probability: float
    predicted_label: str
    classification: str
    top_factors: List[dict]
    disclaimer: str


class DashboardStats(BaseModel):
    total_donors: int
    available_donors: int
    active_requests: int
    critical_requests: int
    successful_matches: int
    donors_by_blood_group: dict
    requests_by_urgency: dict
    availability_split: dict
    monthly_requests: dict
    avg_response_time_minutes: float
    overall_response_rate: float


class LoginIn(BaseModel):
    username: str
    password: str
