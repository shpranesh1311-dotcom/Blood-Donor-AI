"""Tests for app/services/eligibility.py"""

from datetime import datetime, timedelta
from app.services.eligibility import check_donor_eligibility, load_eligibility_config


def make_donor(**overrides):
    donor = {
        "age": 30,
        "donor_status": "active",
        "last_donation_date": (datetime.now() - timedelta(days=200)).date().isoformat(),
        "current_availability": True,
    }
    donor.update(overrides)
    return donor


def test_eligible_donor_passes():
    result = check_donor_eligibility(make_donor())
    assert result.eligible
    assert result.reasons == []


def test_too_young_donor_is_ineligible():
    result = check_donor_eligibility(make_donor(age=16))
    assert not result.eligible
    assert any("Age" in r for r in result.reasons)


def test_too_old_donor_is_ineligible():
    result = check_donor_eligibility(make_donor(age=90))
    assert not result.eligible


def test_suspended_donor_is_ineligible():
    result = check_donor_eligibility(make_donor(donor_status="suspended"))
    assert not result.eligible
    assert any("status" in r for r in result.reasons)


def test_recent_donation_makes_donor_ineligible():
    recent = (datetime.now() - timedelta(days=5)).date().isoformat()
    result = check_donor_eligibility(make_donor(last_donation_date=recent))
    assert not result.eligible
    assert any("days since last donation" in r for r in result.reasons)


def test_donor_with_no_prior_donation_is_eligible():
    result = check_donor_eligibility(make_donor(last_donation_date=None))
    assert result.eligible


def test_config_loads_with_expected_keys():
    cfg = load_eligibility_config()
    for key in ["min_age", "max_age", "min_days_since_last_donation", "max_search_radius_km"]:
        assert key in cfg
