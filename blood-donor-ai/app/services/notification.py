"""
notification.py
================
DEMO-ONLY simulated notification service.

This project does NOT send real SMS/email/push notifications. Clicking
"Notify Donor" in the UI simply records a simulated notification event
in the database (see models.db_models.NotificationLog) so the demo can
show a realistic workflow without contacting real people or requiring
a paid SMS gateway.
"""

from datetime import datetime
from typing import Optional


def simulate_notify_donor(donor_id: str, request_id: str, channel: str = "app_simulated") -> dict:
    """
    Simulate sending a notification to a donor about an emergency request.
    Returns a dict describing the simulated event; the caller is responsible
    for persisting it to the database if desired.
    """
    return {
        "donor_id": donor_id,
        "request_id": request_id,
        "channel": channel,
        "status": "simulated_sent",
        "message": (
            f"[SIMULATED] Donor {donor_id} would be notified about emergency "
            f"request {request_id}. No real message was sent (demo project)."
        ),
        "sent_at": datetime.now().isoformat(timespec="seconds"),
    }
