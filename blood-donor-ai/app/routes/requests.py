"""
routes/requests.py
===================
Emergency blood request endpoints: create a new request, list/view requests.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import EmergencyRequest
from app.schemas.schemas import EmergencyRequestIn, EmergencyRequestOut

router = APIRouter(prefix="/api", tags=["requests"])


def _generate_request_id(db: Session) -> str:
    count = db.query(EmergencyRequest).count()
    candidate = f"REQ{count + 1:05d}"
    # ensure uniqueness even if some requests were deleted
    while db.query(EmergencyRequest).filter(EmergencyRequest.request_id == candidate).first():
        candidate = f"REQ{uuid.uuid4().hex[:8].upper()}"
    return candidate


@router.post("/requests", response_model=EmergencyRequestOut, status_code=201)
def create_request(payload: EmergencyRequestIn, db: Session = Depends(get_db)):
    try:
        request_id = _generate_request_id(db)
        req_datetime = payload.request_datetime or datetime.now().isoformat(timespec="minutes")

        new_request = EmergencyRequest(
            request_id=request_id,
            blood_group_required=payload.blood_group_required,
            units_required=payload.units_required,
            urgency_level=payload.urgency_level,
            hospital_area=payload.hospital_area,
            latitude=payload.latitude,
            longitude=payload.longitude,
            request_datetime=req_datetime,
            request_status="pending",
            notes=payload.notes,
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        return new_request
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create request: {str(e)}")


@router.get("/requests", response_model=list[EmergencyRequestOut])
def list_requests(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
):
    query = db.query(EmergencyRequest).order_by(EmergencyRequest.id.desc())
    if status:
        query = query.filter(EmergencyRequest.request_status == status)
    if urgency:
        query = query.filter(EmergencyRequest.urgency_level == urgency)
    return query.offset(offset).limit(limit).all()


@router.get("/requests/{request_id}", response_model=EmergencyRequestOut)
def get_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(EmergencyRequest).filter(EmergencyRequest.request_id == request_id).first()
    if req is None:
        raise HTTPException(status_code=404, detail=f"Request '{request_id}' not found")
    return req
