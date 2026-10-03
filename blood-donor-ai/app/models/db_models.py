"""
db_models.py
============
SQLAlchemy ORM models for the Blood Donor AI system.

Tables:
    donors                  - donor master data (synthetic/demo only)
    donation_history        - past completed/deferred/cancelled donations
    emergency_requests      - hospital/patient blood requests
    donor_responses         - donor responses to specific requests (also ML training source)
    matches                 - final ranked donor <-> request matches produced by the system
    admin_users             - simple demo admin accounts (hashed passwords)
    prediction_logs         - every ML prediction made, for auditability/analytics
    notification_logs       - simulated "Notify Donor" events (no real messages sent)

Relationships, primary keys, foreign keys and indexes are declared below.
See README.md for the accompanying ER-diagram description.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    donor_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)  # FICTIONAL demo name only
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    blood_group = Column(String(5), nullable=False, index=True)
    city = Column(String(80), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    last_donation_date = Column(String(20), nullable=True)
    total_donations = Column(Integer, default=0)
    previous_requests_received = Column(Integer, default=0)
    previous_requests_responded = Column(Integer, default=0)
    average_response_time_minutes = Column(Float, default=60.0)
    availability_preference = Column(String(30), default="anytime")
    current_availability = Column(Boolean, default=True)
    donor_status = Column(String(20), default="active", index=True)

    donations = relationship("DonationHistory", back_populates="donor")
    responses = relationship("DonorResponse", back_populates="donor")
    matches = relationship("Match", back_populates="donor")


class DonationHistory(Base):
    __tablename__ = "donation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    donation_id = Column(String(20), unique=True, nullable=False, index=True)
    donor_id = Column(String(20), ForeignKey("donors.donor_id"), nullable=False, index=True)
    donation_date = Column(String(20), nullable=False)
    donation_status = Column(String(20), nullable=False)
    response_time_minutes = Column(Float, nullable=True)

    donor = relationship("Donor", back_populates="donations")


class EmergencyRequest(Base):
    __tablename__ = "emergency_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(20), unique=True, nullable=False, index=True)
    blood_group_required = Column(String(5), nullable=False, index=True)
    units_required = Column(Integer, nullable=False)
    urgency_level = Column(String(10), nullable=False, index=True)
    hospital_area = Column(String(80), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    request_datetime = Column(String(30), nullable=False)
    request_status = Column(String(30), default="pending", index=True)
    notes = Column(Text, nullable=True)

    responses = relationship("DonorResponse", back_populates="request")
    matches = relationship("Match", back_populates="request")


class DonorResponse(Base):
    __tablename__ = "donor_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(20), ForeignKey("emergency_requests.request_id"), nullable=False, index=True)
    donor_id = Column(String(20), ForeignKey("donors.donor_id"), nullable=False, index=True)
    distance_km = Column(Float, nullable=True)
    response = Column(Boolean, nullable=False)
    response_time_minutes = Column(Float, nullable=True)
    timestamp = Column(String(30), nullable=False)
    will_respond = Column(Integer, nullable=False)  # ML training label (0/1), duplicated for clarity

    donor = relationship("Donor", back_populates="responses")
    request = relationship("EmergencyRequest", back_populates="responses")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(20), ForeignKey("emergency_requests.request_id"), nullable=False, index=True)
    donor_id = Column(String(20), ForeignKey("donors.donor_id"), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    overall_score = Column(Float, nullable=False)
    ml_response_probability = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)
    expected_response_label = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    donor = relationship("Donor", back_populates="matches")
    request = relationship("EmergencyRequest", back_populates="matches")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    donor_id = Column(String(20), nullable=True, index=True)
    request_id = Column(String(20), nullable=True, index=True)
    input_features_json = Column(Text, nullable=False)
    predicted_probability = Column(Float, nullable=False)
    predicted_label = Column(String(20), nullable=False)
    model_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    donor_id = Column(String(20), nullable=False, index=True)
    request_id = Column(String(20), nullable=False, index=True)
    channel = Column(String(30), default="app_simulated")
    status = Column(String(30), default="simulated_sent")
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Index("ix_donors_group_city", Donor.blood_group, Donor.city)
Index("ix_requests_status_urgency", EmergencyRequest.request_status, EmergencyRequest.urgency_level)
