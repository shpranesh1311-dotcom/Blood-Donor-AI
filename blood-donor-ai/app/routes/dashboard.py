"""
routes/dashboard.py
====================
Aggregated statistics for the dashboard overview cards and charts, plus
deeper analytics (response rate by blood group/urgency, ML model metrics)
used by the Analytics page.
"""

import json
import os
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import config
from app.database import get_db
from app.models.db_models import Donor, EmergencyRequest, Match, DonorResponse
from app.schemas.schemas import DashboardStats

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    total_donors = db.query(Donor).filter(Donor.donor_status == "active").count()
    available_donors = db.query(Donor).filter(
        Donor.donor_status == "active", Donor.current_availability == True  # noqa: E712
    ).count()

    active_requests = db.query(EmergencyRequest).filter(
        EmergencyRequest.request_status.in_(["pending", "matching_in_progress"])
    ).count()
    critical_requests = db.query(EmergencyRequest).filter(
        EmergencyRequest.urgency_level == "Critical",
        EmergencyRequest.request_status.in_(["pending", "matching_in_progress"]),
    ).count()
    successful_matches = db.query(EmergencyRequest).filter(
        EmergencyRequest.request_status == "fulfilled"
    ).count()

    donors_by_group_rows = (
        db.query(Donor.blood_group, func.count(Donor.id))
        .filter(Donor.donor_status == "active")
        .group_by(Donor.blood_group)
        .all()
    )
    donors_by_blood_group = {bg: count for bg, count in donors_by_group_rows}

    requests_by_urgency_rows = (
        db.query(EmergencyRequest.urgency_level, func.count(EmergencyRequest.id))
        .group_by(EmergencyRequest.urgency_level)
        .all()
    )
    requests_by_urgency = {u: count for u, count in requests_by_urgency_rows}

    availability_split = {
        "available": available_donors,
        "unavailable": max(total_donors - available_donors, 0),
    }

    # Monthly requests for the last 6 calendar months present in the data
    all_requests = db.query(EmergencyRequest.request_datetime).all()
    month_counter = Counter()
    for (dt_str,) in all_requests:
        try:
            dt = datetime.fromisoformat(dt_str)
            key = dt.strftime("%Y-%m")
            month_counter[key] += 1
        except (ValueError, TypeError):
            continue
    monthly_requests = dict(sorted(month_counter.items())[-6:])

    avg_response_time = db.query(func.avg(Donor.average_response_time_minutes)).filter(
        Donor.donor_status == "active"
    ).scalar() or 0.0

    total_responses = db.query(DonorResponse).count()
    positive_responses = db.query(DonorResponse).filter(DonorResponse.response == True).count()  # noqa: E712
    overall_response_rate = (positive_responses / total_responses) if total_responses else 0.0

    return DashboardStats(
        total_donors=total_donors,
        available_donors=available_donors,
        active_requests=active_requests,
        critical_requests=critical_requests,
        successful_matches=successful_matches,
        donors_by_blood_group=donors_by_blood_group,
        requests_by_urgency=requests_by_urgency,
        availability_split=availability_split,
        monthly_requests=monthly_requests,
        avg_response_time_minutes=round(float(avg_response_time), 1),
        overall_response_rate=round(overall_response_rate, 3),
    )


@router.get("/dashboard/analytics")
def dashboard_analytics(db: Session = Depends(get_db)):
    """
    Deeper analytics used by the Analytics page:
      - response rate by donor blood group
      - response rate by request urgency level
      - response time distribution buckets
      - ML model evaluation metrics (loaded from models/model_metadata.json)
    """
    # Response rate by blood group
    rows = (
        db.query(Donor.blood_group, DonorResponse.response, func.count(DonorResponse.id))
        .join(Donor, Donor.donor_id == DonorResponse.donor_id)
        .group_by(Donor.blood_group, DonorResponse.response)
        .all()
    )
    by_group = {}
    for group, responded, count in rows:
        by_group.setdefault(group, {"responded": 0, "total": 0})
        by_group[group]["total"] += count
        if responded:
            by_group[group]["responded"] += count
    response_rate_by_group = {
        g: round(v["responded"] / v["total"], 3) if v["total"] else 0.0
        for g, v in sorted(by_group.items())
    }

    # Response rate by urgency level
    rows2 = (
        db.query(EmergencyRequest.urgency_level, DonorResponse.response, func.count(DonorResponse.id))
        .join(EmergencyRequest, EmergencyRequest.request_id == DonorResponse.request_id)
        .group_by(EmergencyRequest.urgency_level, DonorResponse.response)
        .all()
    )
    by_urgency = {}
    for urgency, responded, count in rows2:
        by_urgency.setdefault(urgency, {"responded": 0, "total": 0})
        by_urgency[urgency]["total"] += count
        if responded:
            by_urgency[urgency]["responded"] += count
    urgency_order = ["Critical", "High", "Medium", "Low"]
    response_rate_by_urgency = {
        u: round(by_urgency[u]["responded"] / by_urgency[u]["total"], 3)
        for u in urgency_order if u in by_urgency and by_urgency[u]["total"]
    }

    # Response time distribution (completed donations)
    times = [t for (t,) in db.query(DonorResponse.response_time_minutes)
             .filter(DonorResponse.response == True).all() if t is not None]  # noqa: E712
    buckets = {"0-15 min": 0, "15-30 min": 0, "30-60 min": 0, "60-120 min": 0, "120+ min": 0}
    for t in times:
        if t <= 15:
            buckets["0-15 min"] += 1
        elif t <= 30:
            buckets["15-30 min"] += 1
        elif t <= 60:
            buckets["30-60 min"] += 1
        elif t <= 120:
            buckets["60-120 min"] += 1
        else:
            buckets["120+ min"] += 1

    # Total matches ever produced + average overall score
    total_matches = db.query(Match).count()
    avg_match_score = db.query(func.avg(Match.overall_score)).scalar() or 0.0

    # ML model metrics
    model_metrics = {}
    if os.path.exists(config.MODEL_METADATA_PATH):
        with open(config.MODEL_METADATA_PATH) as f:
            model_metrics = json.load(f)

    return {
        "response_rate_by_blood_group": response_rate_by_group,
        "response_rate_by_urgency": response_rate_by_urgency,
        "response_time_distribution": buckets,
        "total_matches_generated": total_matches,
        "avg_match_score": round(float(avg_match_score), 1),
        "model_metrics": model_metrics,
    }
