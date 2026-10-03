"""
routes/donors.py
=================
Donor listing/search/detail endpoints. Contact information is intentionally
never exposed - only demo-safe fields are returned.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.db_models import Donor
from app.schemas.schemas import DonorOut
from app.services.compatibility import get_compatible_donor_groups, is_valid_blood_group, VALID_BLOOD_GROUPS
from app.services.distance import haversine_km

router = APIRouter(prefix="/api", tags=["donors"])


@router.get("/blood-groups")
def list_blood_groups():
    return {"blood_groups": VALID_BLOOD_GROUPS}


@router.get("/donors", response_model=list[DonorOut])
def list_donors(
    db: Session = Depends(get_db),
    blood_group: Optional[str] = None,
    city: Optional[str] = None,
    availability: Optional[bool] = None,
    compatible_with: Optional[str] = Query(None, description="Recipient blood group; returns compatible donors"),
    near_lat: Optional[float] = None,
    near_lon: Optional[float] = None,
    max_distance_km: Optional[float] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
):
    query = db.query(Donor).filter(Donor.donor_status == "active")

    if blood_group:
        if not is_valid_blood_group(blood_group):
            raise HTTPException(status_code=400, detail=f"Invalid blood group '{blood_group}'")
        query = query.filter(Donor.blood_group == blood_group)

    if compatible_with:
        if not is_valid_blood_group(compatible_with):
            raise HTTPException(status_code=400, detail=f"Invalid blood group '{compatible_with}'")
        compatible_groups = get_compatible_donor_groups(compatible_with)
        query = query.filter(Donor.blood_group.in_(compatible_groups))

    if city:
        query = query.filter(Donor.city.ilike(f"%{city}%"))

    if availability is not None:
        query = query.filter(Donor.current_availability == availability)

    donors = query.offset(offset).limit(limit).all()

    if near_lat is not None and near_lon is not None:
        filtered = []
        for d in donors:
            dist = haversine_km(near_lat, near_lon, d.latitude, d.longitude)
            if max_distance_km is None or dist <= max_distance_km:
                filtered.append(d)
        donors = filtered

    return donors


@router.get("/donors/{donor_id}", response_model=DonorOut)
def get_donor(donor_id: str, db: Session = Depends(get_db)):
    donor = db.query(Donor).filter(Donor.donor_id == donor_id).first()
    if donor is None:
        raise HTTPException(status_code=404, detail=f"Donor '{donor_id}' not found")
    return donor
