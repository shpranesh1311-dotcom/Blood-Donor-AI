"""
eligibility.py
===============
Configurable, DEMO-ONLY donor eligibility layer.

This module NEVER makes a final medical eligibility decision. It only
applies simple, transparent, configurable rules (age range, days since
last donation, account status, etc.) to filter a candidate list down to
donors who are "potentially eligible" for a demo emergency request.

Every result produced by this module must be interpreted as:

    "Potentially eligible based on configured demo rules -
     medical eligibility must be confirmed by the blood bank."

Configuration lives in eligibility_config.json (next to this file) so
demo rules are not scattered across the codebase.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eligibility_config.json")

ELIGIBILITY_DISCLAIMER = (
    "Potentially eligible based on configured demo rules - medical eligibility "
    "must be confirmed by the blood bank."
)


def load_eligibility_config() -> dict:
    with open(_CONFIG_PATH, "r") as f:
        return json.load(f)


@dataclass
class EligibilityResult:
    eligible: bool
    reasons: list  # list of human-readable reasons (why ineligible, if applicable)


def _days_since(date_str: Optional[str]) -> Optional[int]:
    if not date_str or (isinstance(date_str, float)):
        return None
    try:
        d = datetime.fromisoformat(str(date_str))
    except ValueError:
        return None
    return (datetime.now() - d).days


def check_donor_eligibility(donor: dict, config: Optional[dict] = None) -> EligibilityResult:
    """
    Apply configurable DEMO eligibility rules to a single donor record.

    `donor` is expected to be a dict-like object with at least:
        age, donor_status, last_donation_date, current_availability

    Returns an EligibilityResult. This is a SOFTWARE FILTER ONLY, not a
    medical determination.
    """
    cfg = config or load_eligibility_config()
    reasons = []

    age = donor.get("age")
    if age is not None:
        if age < cfg["min_age"]:
            reasons.append(f"Age {age} is below configured minimum of {cfg['min_age']}")
        if age > cfg["max_age"]:
            reasons.append(f"Age {age} is above configured maximum of {cfg['max_age']}")

    status = donor.get("donor_status")
    if status in cfg.get("excluded_donor_status", []):
        reasons.append(f"Donor status '{status}' is excluded by demo configuration")

    last_donation_date = donor.get("last_donation_date")
    days_since = _days_since(last_donation_date)
    if days_since is not None and days_since < cfg["min_days_since_last_donation"]:
        reasons.append(
            f"Only {days_since} days since last donation "
            f"(minimum configured gap is {cfg['min_days_since_last_donation']} days)"
        )

    if cfg.get("require_current_availability") and not donor.get("current_availability"):
        reasons.append("Donor is not currently marked as available")

    return EligibilityResult(eligible=(len(reasons) == 0), reasons=reasons)
