"""
routes/match.py
================
The core "intelligent matching" endpoint. Given an emergency request:
    1. Find blood-compatible donors (services/compatibility.py)
    2. Apply demo eligibility filters (services/eligibility.py)
    3. Calculate distance (services/distance.py)
    4. Run the ML response-probability prediction (app/ml/predict_service.py)
    5. Compute the configurable ranking score (services/ranking.py)
    6. Persist the resulting matches and return the ranked list
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Donor, EmergencyRequest, Match
from app.schemas.schemas import MatchResponse, MatchedDonorOut
from app.services.compatibility import get_compatible_donor_groups, is_valid_blood_group, COMPATIBILITY_DISCLAIMER
from app.services.eligibility import check_donor_eligibility, load_eligibility_config, ELIGIBILITY_DISCLAIMER
from app.services.distance import haversine_km
from app.services.ranking import RankingInput, rank_donors, load_ranking_config
from app.ml.predict_service import get_prediction

router = APIRouter(prefix="/api", tags=["match"])

MATCH_DISCLAIMER = (
    COMPATIBILITY_DISCLAIMER + " " + ELIGIBILITY_DISCLAIMER +
    " All scores are probabilistic predictions for prioritisation/assistance only "
    "and do not guarantee donor behaviour."
)


@router.post("/match/{request_id}", response_model=MatchResponse)
def match_donors(request_id: str, top_n: int = 15, db: Session = Depends(get_db)):
    req = db.query(EmergencyRequest).filter(EmergencyRequest.request_id == request_id).first()
    if req is None:
        raise HTTPException(status_code=404, detail=f"Emergency request '{request_id}' not found")

    try:
        compatible_groups = get_compatible_donor_groups(req.blood_group_required)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    candidates = db.query(Donor).filter(Donor.blood_group.in_(compatible_groups)).all()
    total_compatible = len(candidates)

    if total_compatible == 0:
        return MatchResponse(
            request_id=request_id,
            blood_group_required=req.blood_group_required,
            total_compatible_donors=0,
            total_eligible_donors=0,
            matches=[],
            disclaimer=MATCH_DISCLAIMER,
        )

    eligibility_cfg = load_eligibility_config()
    ranking_cfg = load_ranking_config()

    eligible_donors = []
    for donor in candidates:
        result = check_donor_eligibility(
            {
                "age": donor.age,
                "donor_status": donor.donor_status,
                "last_donation_date": donor.last_donation_date,
                "current_availability": donor.current_availability,
            },
            eligibility_cfg,
        )
        if result.eligible:
            eligible_donors.append(donor)

    if not eligible_donors:
        return MatchResponse(
            request_id=request_id,
            blood_group_required=req.blood_group_required,
            total_compatible_donors=total_compatible,
            total_eligible_donors=0,
            matches=[],
            disclaimer=MATCH_DISCLAIMER,
        )

    max_radius = eligibility_cfg.get("max_search_radius_km", 30)
    ranking_inputs = []
    donor_lookup = {}
    prediction_cache = {}

    for donor in eligible_donors:
        distance_km = haversine_km(req.latitude, req.longitude, donor.latitude, donor.longitude)
        if distance_km > max_radius:
            continue

        prev_rate = 0.0
        if donor.previous_requests_received > 0:
            prev_rate = donor.previous_requests_responded / donor.previous_requests_received

        pred = get_prediction({
            "age": donor.age,
            "blood_group": donor.blood_group,
            "total_donations": donor.total_donations,
            "previous_requests_received": donor.previous_requests_received,
            "previous_requests_responded": donor.previous_requests_responded,
            "average_response_time_minutes": donor.average_response_time_minutes,
            "current_availability": donor.current_availability,
            "distance_km": distance_km,
            "urgency_level": req.urgency_level,
            "units_required": req.units_required,
        })
        prediction_cache[donor.donor_id] = pred

        ranking_inputs.append(RankingInput(
            donor_id=donor.donor_id,
            ml_response_probability=pred["response_probability"],
            distance_km=distance_km,
            previous_response_rate=prev_rate,
            current_availability=bool(donor.current_availability),
            average_response_time_minutes=donor.average_response_time_minutes,
            urgency_level=req.urgency_level,
        ))
        donor_lookup[donor.donor_id] = (donor, distance_km, prev_rate)

    ranked = rank_donors(ranking_inputs, ranking_cfg)[:top_n]

    # Persist matches (replace any previous matches for this request)
    db.query(Match).filter(Match.request_id == request_id).delete()
    matches_out = []
    for i, r in enumerate(ranked, start=1):
        donor, distance_km, prev_rate = donor_lookup[r.donor_id]
        pred = prediction_cache[r.donor_id]

        db.add(Match(
            request_id=request_id,
            donor_id=r.donor_id,
            rank=i,
            overall_score=r.overall_score,
            ml_response_probability=pred["response_probability"],
            distance_km=round(distance_km, 2),
            expected_response_label=r.expected_response_label,
        ))

        matches_out.append(MatchedDonorOut(
            rank=i,
            donor_id=r.donor_id,
            city=donor.city,
            blood_group=donor.blood_group,
            distance_km=round(distance_km, 2),
            ml_response_probability=pred["response_probability"],
            previous_response_rate=round(prev_rate, 3),
            expected_response_label=r.expected_response_label,
            current_availability=bool(donor.current_availability),
            overall_score=r.overall_score,
            sub_scores=r.sub_scores,
        ))

    req.request_status = "matching_in_progress" if req.request_status == "pending" else req.request_status
    db.commit()

    return MatchResponse(
        request_id=request_id,
        blood_group_required=req.blood_group_required,
        total_compatible_donors=total_compatible,
        total_eligible_donors=len(eligible_donors),
        matches=matches_out,
        disclaimer=MATCH_DISCLAIMER,
    )


@router.get("/search-donors", response_model=MatchResponse)
def search_donors(
    blood_group_required: str,
    db: Session = Depends(get_db),
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    urgency_level: str = "Medium",
    max_distance_km: Optional[float] = None,
    city: Optional[str] = None,
    availability_only: bool = False,
    min_probability: float = 0.0,
    top_n: int = 20,
):
    """
    Ad-hoc, read-only donor search + ranking (used by the 'Find Donors' page).
    Unlike /match/{request_id}, this does NOT require or create a stored
    EmergencyRequest, and results are NOT persisted to the matches table.
    Useful for browsing/what-if searches before formally logging a request.
    """
    if not is_valid_blood_group(blood_group_required):
        raise HTTPException(status_code=400, detail=f"Invalid blood group '{blood_group_required}'")

    compatible_groups = get_compatible_donor_groups(blood_group_required)
    query = db.query(Donor).filter(Donor.blood_group.in_(compatible_groups))
    if city:
        query = query.filter(Donor.city.ilike(f"%{city}%"))
    if availability_only:
        query = query.filter(Donor.current_availability == True)  # noqa: E712

    candidates = query.all()
    total_compatible = len(candidates)
    if total_compatible == 0:
        return MatchResponse(
            request_id="AD-HOC", blood_group_required=blood_group_required,
            total_compatible_donors=0, total_eligible_donors=0, matches=[],
            disclaimer=MATCH_DISCLAIMER,
        )

    eligibility_cfg = load_eligibility_config()
    ranking_cfg = load_ranking_config()
    radius = max_distance_km or eligibility_cfg.get("max_search_radius_km", 30)

    # default search origin: Coimbatore Central if no location given
    origin_lat = latitude if latitude is not None else 11.0016
    origin_lon = longitude if longitude is not None else 76.9558

    eligible_donors = []
    for donor in candidates:
        result = check_donor_eligibility({
            "age": donor.age, "donor_status": donor.donor_status,
            "last_donation_date": donor.last_donation_date,
            "current_availability": donor.current_availability,
        }, eligibility_cfg)
        if result.eligible:
            eligible_donors.append(donor)

    ranking_inputs, donor_lookup, prediction_cache = [], {}, {}
    for donor in eligible_donors:
        distance_km = haversine_km(origin_lat, origin_lon, donor.latitude, donor.longitude)
        if distance_km > radius:
            continue
        prev_rate = (donor.previous_requests_responded / donor.previous_requests_received) \
            if donor.previous_requests_received > 0 else 0.0

        pred = get_prediction({
            "age": donor.age, "blood_group": donor.blood_group,
            "total_donations": donor.total_donations,
            "previous_requests_received": donor.previous_requests_received,
            "previous_requests_responded": donor.previous_requests_responded,
            "average_response_time_minutes": donor.average_response_time_minutes,
            "current_availability": donor.current_availability,
            "distance_km": distance_km, "urgency_level": urgency_level, "units_required": 1,
        })
        if pred["response_probability"] < min_probability:
            continue
        prediction_cache[donor.donor_id] = pred
        ranking_inputs.append(RankingInput(
            donor_id=donor.donor_id, ml_response_probability=pred["response_probability"],
            distance_km=distance_km, previous_response_rate=prev_rate,
            current_availability=bool(donor.current_availability),
            average_response_time_minutes=donor.average_response_time_minutes,
            urgency_level=urgency_level,
        ))
        donor_lookup[donor.donor_id] = (donor, distance_km, prev_rate)

    ranked = rank_donors(ranking_inputs, ranking_cfg)[:top_n]
    matches_out = []
    for i, r in enumerate(ranked, start=1):
        donor, distance_km, prev_rate = donor_lookup[r.donor_id]
        pred = prediction_cache[r.donor_id]
        matches_out.append(MatchedDonorOut(
            rank=i, donor_id=r.donor_id, city=donor.city, blood_group=donor.blood_group,
            distance_km=round(distance_km, 2), ml_response_probability=pred["response_probability"],
            previous_response_rate=round(prev_rate, 3), expected_response_label=r.expected_response_label,
            current_availability=bool(donor.current_availability), overall_score=r.overall_score,
            sub_scores=r.sub_scores,
        ))

    return MatchResponse(
        request_id="AD-HOC", blood_group_required=blood_group_required,
        total_compatible_donors=total_compatible, total_eligible_donors=len(eligible_donors),
        matches=matches_out, disclaimer=MATCH_DISCLAIMER,
    )
