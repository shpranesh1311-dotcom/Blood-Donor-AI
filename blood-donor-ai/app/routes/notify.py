"""
routes/notify.py
=================
Simulated "Notify Donor" endpoint used by the Donor Search page.
No real SMS/email is sent - see services/notification.py for details.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Donor, NotificationLog
from app.services.notification import simulate_notify_donor

router = APIRouter(prefix="/api", tags=["notify"])


@router.post("/notify/{donor_id}")
def notify_donor(donor_id: str, request_id: str = "GENERAL", db: Session = Depends(get_db)):
    donor = db.query(Donor).filter(Donor.donor_id == donor_id).first()
    if donor is None:
        raise HTTPException(status_code=404, detail=f"Donor '{donor_id}' not found")

    event = simulate_notify_donor(donor_id, request_id)

    log = NotificationLog(
        donor_id=donor_id,
        request_id=request_id,
        channel=event["channel"],
        status=event["status"],
        message=event["message"],
    )
    db.add(log)
    db.commit()

    return event
